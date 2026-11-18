import os
import dataclasses
import json
import re
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from dbgpu import GPUDatabase, TechPowerUp, json_serialize
from dbgpu.gpu import GPUSpecification
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def load_env(env_path: Path = Path(__file__).with_name(".env")) -> None:
    """Load key=value pairs from a .env file into os.environ without
    overwriting variables that are already set in the environment."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip("\"'"))


load_env()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Session credentials required to pass TechPowerUp's bot-protection layer
COOKIE = os.getenv("TPU_COOKIE", "").strip()
USER_AGENT = os.getenv(
    "TPU_USER_AGENT",
    "Mozilla/5.0 (Linux; Android 9) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Version/4.0 Chrome/95.0.4638.74 Mobile DuckDuckGo/5 Safari/537.36",
).strip()

if not COOKIE:
    raise RuntimeError("TPU_COOKIE is missing. Set it in .env or as an environment variable.")

# GPU manufacturers whose pages will be scraped live
MANUFACTURERS = ["NVIDIA", "AMD", "Intel"]

# When True, the built-in dbgpu database provides all years before START_YEAR
# and only 2025-2026 cards are fetched from the live site. Set to False to
# scrape everything from scratch (much slower and heavier on the server).
USE_BUILTIN_BASE = True
START_YEAR = 2025 if USE_BUILTIN_BASE else 1980
END_YEAR = 2026

# Seconds to wait between HTTP requests to avoid triggering rate-limiting
COURTESY_DELAY = 1.5

# Incremental cache so a partial run can be resumed without re-fetching
CACHE_FILE = Path("scrape_cache.jsonl")
OUTPUT_FILE = Path(f"data/all-{datetime.now():%Y%m%d-%H%M}.json")

# Spec values that carry no useful information and should be treated as missing
INVALID_VALUES = {"not supported", "unknown", "n/a", "-", "tbd", "none", ""}


# ---------------------------------------------------------------------------
# Monkey-patch 1: transistor count parser
# Extends the upstream parser to handle "billion" and "thousand" unit suffixes
# that TechPowerUp started using for newer high-transistor-count GPUs.
# All values are normalised to millions so the rest of the pipeline is uniform.
# ---------------------------------------------------------------------------

_orig_transistor_parser = GPUSpecification._get_transistor_count_from_string


@staticmethod
def _patched_transistor_count(transistor_string: str):
    if not transistor_string or transistor_string.strip().lower() in INVALID_VALUES:
        return None
    m = re.search(r"([\d.,]+)\s*(billion|million|thousand)?", transistor_string.strip(), re.I)
    if m:
        val = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "million").lower()
        if unit == "billion":
            return val * 1000.0   # convert to millions
        if unit == "thousand":
            return val / 1000.0   # convert to millions
        return val
    # Fall back to the original parser for any format not matched above
    return _orig_transistor_parser(transistor_string)


GPUSpecification._get_transistor_count_from_string = _patched_transistor_count


# ---------------------------------------------------------------------------
# Monkey-patch 2: DirectX / Vulkan / OpenGL version parser
# The upstream parser raises on None or invalid strings; we guard against
# that so a missing version field never aborts the entire spec parse.
# Returns (None, None) instead of raising, matching the expected tuple shape.
# ---------------------------------------------------------------------------

_orig_version_parser = GPUSpecification._get_version_from_string


@staticmethod
def _patched_version_parser(version_string):
    if version_string is None or (
        isinstance(version_string, str) and version_string.strip().lower() in INVALID_VALUES
    ):
        return (None, None)
    try:
        return _orig_version_parser(version_string)
    except (ValueError, TypeError, AttributeError):
        return (None, None)


GPUSpecification._get_version_from_string = _patched_version_parser


# ---------------------------------------------------------------------------
# Monkey-patch 3: blanket guard for all remaining _get_* spec parsers
# Any parser that receives None or an invalid sentinel string returns None
# instead of propagating a ValueError up the call stack.
# ---------------------------------------------------------------------------

def _wrap_safe_parser(orig_fn):
    """Wrap a staticmethod parser so it returns None on bad input."""
    @staticmethod
    def _safe_fn(*args, **kwargs):
        if args and (
            args[0] is None
            or (isinstance(args[0], str) and args[0].strip().lower() in INVALID_VALUES)
        ):
            return None
        try:
            return orig_fn(*args, **kwargs)
        except ValueError:
            return None
    return _safe_fn


# Skip the two parsers we already patched above
_SKIP_PARSERS = {"_get_transistor_count_from_string", "_get_version_from_string"}
for _attr in dir(GPUSpecification):
    if _attr.startswith("_get_") and _attr not in _SKIP_PARSERS:
        _fn = getattr(GPUSpecification, _attr)
        if callable(_fn):
            setattr(GPUSpecification, _attr, _wrap_safe_parser(_fn))


# ---------------------------------------------------------------------------
# Monkey-patch 4: GPUSpecification.__init__ null-safety
# Pydantic rejects None for required non-optional fields. When a spec value
# arrives as None we substitute a typed zero/empty default so the object can
# be constructed and the GPU record is still included in the output.
# ---------------------------------------------------------------------------

_orig_gpu_init = GPUSpecification.__init__


def _safe_gpu_init(self, *args, **kwargs):
    """Replace None values on required fields with safe type defaults before
    passing kwargs to the original __init__. If Pydantic still raises a
    ValidationError, patch only the offending fields and retry once."""
    fields = getattr(GPUSpecification, "__dataclass_fields__", {})
    for fname, fobj in fields.items():
        if fname in kwargs and kwargs[fname] is None:
            ftype = str(fobj.type)
            if "Optional" not in ftype and "None" not in ftype:
                # Prefer the field's declared default when available
                if fobj.default is not dataclasses.MISSING and fobj.default is not None:
                    kwargs[fname] = fobj.default
                elif "float" in ftype:
                    kwargs[fname] = 0.0
                elif "int" in ftype:
                    kwargs[fname] = 0
                elif "bool" in ftype:
                    kwargs[fname] = False
                elif "str" in ftype:
                    kwargs[fname] = ""

    try:
        return _orig_gpu_init(self, *args, **kwargs)
    except ValidationError as exc:
        # Second pass: target only the fields Pydantic explicitly complained about
        patched = False
        for err in exc.errors():
            loc = err.get("loc")
            if not loc:
                continue
            fname = loc[0]
            if fname in kwargs and kwargs[fname] is None:
                etype = err.get("type", "")
                if "float" in etype:
                    kwargs[fname] = 0.0
                    patched = True
                elif "int" in etype:
                    kwargs[fname] = 0
                    patched = True
                elif "bool" in etype:
                    kwargs[fname] = False
                    patched = True
                elif "string" in etype:
                    kwargs[fname] = ""
                    patched = True
        if patched:
            return _orig_gpu_init(self, *args, **kwargs)
        raise


GPUSpecification.__init__ = _safe_gpu_init


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class BypassTechPowerUp(TechPowerUp):
    """TechPowerUp scraper that uses curl_cffi to impersonate a real Chrome
    browser, bypassing Cloudflare and similar bot-detection challenges."""

    @property
    def session(self):
        """Lazily create and cache a curl_cffi session with browser headers."""
        if not hasattr(self, "_session"):
            self._session = cffi_requests.Session(impersonate="chrome")
            self._session.proxies.update(self.proxies)
            self._session.headers.update({
                "User-Agent": USER_AGENT,
                "Cookie": COOKIE,
                "Referer": "https://www.techpowerup.com/gpu-specs/",
            })
        return self._session

    @session.deleter
    def session(self) -> None:
        if hasattr(self, "_session"):
            del self._session

    def _get_checked(self, url: str, params: dict | None = None):
        """Perform a GET request with up to 3 retries on HTTP 429 responses.
        Raises RuntimeError if the bot-protection wall is detected in the body."""
        for attempt in range(3):
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"[429 Rate Limit] Waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            if "Automated bot check in progress" in resp.text:
                raise RuntimeError(
                    "Bot protection triggered. Refresh COOKIE from your browser and try again."
                )
            return resp
        raise RuntimeError(f"Request failed after 3 attempts: {url}")

    def fetch_gpu_list(self, manufacturer: str, year: int, num_retries: int = 0):
        """Yield (name, relative_href) pairs for every GPU listed on the
        TechPowerUp specs index page for the given manufacturer and year."""
        url = f"{self.base_url}{self.list_url}"
        response = self._get_checked(url, params={"mfgr": manufacturer, "year": year})

        soup = BeautifulSoup(response.text, "html.parser")
        # Try the most common table selectors; fall back to the first table found
        table = soup.select_one("table.processors, table.items-desktop-table") or soup.find("table")
        if not table:
            return

        seen = set()
        for a in table.select("a[href*='/gpu-specs/']"):
            href = a.get("href", "")
            # Only follow links that contain a numeric ID (".c<digits>")
            if ".c" not in href or href in seen:
                continue
            seen.add(href)
            name = a.get_text(strip=True)
            if name:
                yield name, href

    def fetch_gpu_details(self, url: str, num_retries: int = 0):
        """Scrape the full spec sheet for a single GPU detail page.
        Returns a nested dict keyed by section title then spec name."""
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"
        response = self._get_checked(url)

        soup = BeautifulSoup(response.text, "html.parser")
        # Seed the dict with the source URL so the record is always traceable
        specs = {"TechPowerUp": {"ID": url.split(".")[-1], "URL": url}}
        for sec in soup.find_all("section", {"class": "details"}):
            h2 = sec.find("h2")
            if not h2:
                continue
            title = h2.get_text(strip=True)
            specs[title] = {}
            for row in sec.find_all("dl"):
                dt, dd = row.find("dt"), row.find("dd")
                if dt and dd:
                    specs[title][dt.get_text(strip=True)] = dd.get_text(strip=True)
        return specs


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def load_cache() -> dict[tuple[str, str], dict]:
    """Read the incremental JSONL cache and return a dict keyed by
    (manufacturer, name) so previously fetched cards are skipped."""
    cached = {}
    if CACHE_FILE.exists():
        with CACHE_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    cached[(row["manufacturer"], row["name"])] = row
    return cached


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    # Start with either the built-in database or an empty dict
    merged: dict[tuple[str, str], dict] = {}

    if USE_BUILTIN_BASE:
        base_db = GPUDatabase.default()
        for spec in base_db.specs:
            merged[(spec.manufacturer, spec.name)] = spec.to_dict()
        print(f"[Built-in DB] {len(merged)} records loaded.")

    # Overlay any cards already scraped in a previous run
    cached = load_cache()
    merged.update(cached)
    if cached:
        print(f"[Cache] {len(cached)} live-scraped records loaded.")

    tpu = BypassTechPowerUp(manufacturers=MANUFACTURERS, timeout=20)

    with CACHE_FILE.open("a", encoding="utf-8") as cache_f:
        for year in range(START_YEAR, END_YEAR + 1):
            for mfr in MANUFACTURERS:
                cards = list(tpu.fetch_gpu_list(mfr, year))
                print(f"[{year} | {mfr}] {len(cards)} cards listed.")
                time.sleep(COURTESY_DELAY)

                for idx, (name, href) in enumerate(cards, start=1):
                    # Skip cards we already have in the cache
                    if (mfr, name) in cached:
                        continue

                    raw_specs = tpu.fetch_gpu_details(href)
                    spec = GPUSpecification.from_tpu_dict(
                        name=name, manufacturer=mfr, data=raw_specs
                    )
                    row = spec.to_dict()

                    # Append to the cache immediately so a crash doesn't lose progress
                    cache_f.write(
                        json.dumps(row, default=json_serialize, ensure_ascii=False) + "\n"
                    )
                    cache_f.flush()

                    cached[(mfr, name)] = row
                    merged[(mfr, name)] = row
                    print(f"  + ({idx}/{len(cards)}) {mfr} {name}")
                    time.sleep(COURTESY_DELAY)

    # Write the final consolidated output file
    with OUTPUT_FILE.open("w", encoding="utf-8") as out_f:
        json.dump(list(merged.values()), out_f, indent=2, default=json_serialize, ensure_ascii=False)

    print(f"\nDone! {len(merged)} cards written to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()