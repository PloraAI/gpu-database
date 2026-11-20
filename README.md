# Plora AI GPU Database

Comprehensive GPU specifications database with architecture, manufacturing, API support, performance details, and kernel development specs.

**2,876 GPUs** across NVIDIA, AMD, and Intel

## Data

| Vendor | GPUs | File |
|--------|------|------|
| NVIDIA | 1,307 | [`data/nvidia.json`](data/nvidia.json) |
| AMD | 1,310 | [`data/amd.json`](data/amd.json) |
| Intel | 193 | [`data/intel.json`](data/intel.json) |
| **All** | 2,876 | [`data/all.json`](data/all.json) |

> It is available on ATI cards under AMD. The table for AMD is as follows:

| Vendor | GPUs |
|--------|------|
| AMD    | 760  |
| ATI    | 550  |

## Schema

Each GPU contains up to 55 fields:

```json
{
  "manufacturer": "NVIDIA",
  "name": "GeForce RTX 4070",
  "gpu_name": "AD104",
  "generation": "GeForce 40",
  "base_clock_mhz": 1920.0,
  "boost_clock_mhz": 2475.0,
  "architecture": "Ada Lovelace",
  "foundry": "TSMC",
  "process_size_nm": 5,
  "transistor_count_m": 35800.0,
  "transistor_density_k_mm2": 121800.0,
  "die_size_mm2": 294.0,
  "chip_package": null,
  "release_date": "2023-04-12",
  "bus_interface": "PCIe 4.0 x16",
  "memory_clock_mhz": 1313.0,
  "memory_size_gb": 12.0,
  "memory_bus_bits": 192,
  "memory_bandwidth_gb_s": 504.2,
  "memory_type": "GDDR6X",
  "shading_units": 5888,
  "texture_mapping_units": 184,
  "render_output_processors": 64,
  "streaming_multiprocessors": 46,
  "tensor_cores": 184,
  "ray_tracing_cores": 46,
  "l1_cache_kb": 128.0,
  "l2_cache_mb": 36.0,
  "thermal_design_power_w": 200,
  "board_length_mm": 240.0,
  "board_width_mm": 40.0,
  "board_slot_width": "Dual-slot",
  "suggested_psu_w": 550,
  "power_connectors": "1x 16-pin",
  "display_connectors": "1x HDMI 2.1, 3x DisplayPort 1.4a",
  "directx_major_version": 12,
  "directx_minor_version": 2,
  "opengl_major_version": 4,
  "opengl_minor_version": 6,
  "vulkan_major_version": 1,
  "vulkan_minor_version": 4,
  "opencl_major_version": 3,
  "opencl_minor_version": 0,
  "cuda_major_version": 8,
  "cuda_minor_version": 9,
  "shader_model_major_version": 6,
  "shader_model_minor_version": 8,
  "pixel_rate_gpixel_s": 158.4,
  "texture_rate_gtexel_s": 455.4,
  "half_float_performance_gflop_s": 29150.0,
  "single_float_performance_gflop_s": 29150.0,
  "double_float_performance_gflop_s": 455.4,
  "tpu_id": "c3924",
  "tpu_url": "https://www.techpowerup.com/gpu-specs/geforce-rtx-4070.c3924"
},
```

Take a look at [`docs/meaning-fields.md`](docs/meaning-fields.md) to understand the meaning of the fields 

## GPU Image
You can use the following URL to capture GPU screenshots. You can retrieve the `tpu_id` value from the JSON.

```
https://raw.githubusercontent.com/PloraAI/gpu-images/refs/heads/main/front-thumb/{tpu_id}.jpg
```

## Usage

**Direct URL:**
```
https://raw.githubusercontent.com/PloraAI/gpu-database/main/data/nvidia.json
```

**JavaScript:**
```javascript
const gpus = await fetch(
  'https://raw.githubusercontent.com/PloraAI/gpu-database/main/data/nvidia.json'
).then(r => r.json());

const rtx4090 = gpus.find(g => g.name === 'GeForce RTX 4090');
console.log(rtx4090.memory_bandwidth_gb_s); // 1010.0
console.log(rtx4090.memory_size_gb);     // 24.0
```

**Python:**
```python
import requests

gpus = requests.get(
    'https://raw.githubusercontent.com/PloraAI/gpu-database/main/data/nvidia.json'
).json()

rtx4090 = next(g for g in gpus if g['name'] == 'GeForce RTX 4090')
print(rtx4090['memory_bandwidth_gb_s']) # 1010.0
print(rtx4090['memory_size_gb']) # 24.0
```

**Rust**
```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct Gpu {
    name: String,
    memory_bandwidth_gb_s: Option<f64>,
    memory_size_gb: Option<f64>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let url = "https://raw.githubusercontent.com/PloraAI/gpu-database/main/data/nvidia.json";
    
    let gpus: Vec<Gpu> = reqwest::get(url)
        .await?
        .json()
        .await?;

    let rtx4090 = gpus
        .iter()
        .find(|g| g.name == "GeForce RTX 4090")
        .expect("RTX 4090 not found");

    println!("{}", rtx4090.memory_bandwidth_gb_s.unwrap_or(0.0)); // 1010.0
    println!("{}", rtx4090.memory_size_gb.unwrap_or(0.0));         // 24.0

    Ok(())
}
```

### Installation

1) Install libraries:
```pip install -r requirements.txt```

2) Auth:
Copy `.env.example` as `.env`
On the `TechPowerUP` website, enter your browser's cookie and user agent information into the required fields in the [`.env`](.env).

3) Run:
```python main.py```
Output: `data/all.json`

`calculate.py` is used to display the number of graphics cards in a file by brand
`split_gpus.py` is used to export graphics cards into separate files by brand (nvidia.json, amd.json, intel.json, and other.json)
Output directory is: `data/`

## Source

Data sourced from [TechPowerUp GPU Database](https://www.techpowerup.com/gpu-specs/) via [dbgpu](https://github.com/painebenjamin/dbgpu).

If this repository is no longer up to date, you can update it using the Python scripts in the repository.

## License

[MIT](LICENSE)

---

Built by [Plora AI](https://www.yorastudioplus.com)