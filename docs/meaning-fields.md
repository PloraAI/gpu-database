# GPU Specification Fields Explained

A detailed reference for every field in the GPU specification JSON, organized by category.

The GPU model used as an example is the `NVIDIA GeForce RTX 4070`

---

## 🏷️ Identity & Branding

| Field | Value | Meaning |
|---|---|---|
| `manufacturer` | NVIDIA | The company that designed and markets the GPU. |
| `name` | GeForce RTX 4070 | The consumer-facing product name. |
| `gpu_name` | AD104 | The internal silicon die name used by NVIDIA. Different board models can share the same die (e.g., RTX 4070 Ti also uses AD104). |
| `generation` | GeForce 40 | The product generation family. Corresponds to a specific microarchitecture era. |
| `architecture` | Ada Lovelace | The microarchitecture name, honoring mathematician Ada Lovelace. Defines the fundamental design of the shader cores, caches, and feature set. |

---

## ⚙️ Clock Speeds

| Field | Unit | Meaning |
|---|---|---|
| `base_clock_mhz` | MHz | The guaranteed minimum operating frequency of the GPU cores under any load. The GPU will never run slower than this under normal thermal conditions. |
| `boost_clock_mhz` | MHz | The maximum frequency the GPU can reach when power, temperature, and current headroom allow. Modern GPUs spend most of their time at or near this clock. |

> **MHz (Megahertz)** = millions of cycles per second. Higher clocks mean more operations executed per second, all else being equal.

---

## 🏭 Manufacturing / Silicon

| Field | Meaning |
|---|---|
| `foundry` | The semiconductor fab that physically manufactures the chip. TSMC (Taiwan Semiconductor Manufacturing Company) is the world's leading contract chipmaker. |
| `process_size_nm` | The lithography node in **nanometers**. Smaller = more transistors per mm², lower power consumption, and usually better performance. 5 nm is TSMC's N4 node. |
| `transistor_count_m` | Total number of transistors on the die, in **millions**. The RTX 4070 has ~35.8 billion transistors. More transistors enable more functional units. |
| `transistor_density_k_mm2` | Transistors per mm² in **thousands**. Measures how efficiently the manufacturing process packs transistors. 121,800K/mm² = ~121.8 million transistors per mm². |
| `die_size_mm2` | Physical area of the silicon die in **square millimeters**. Larger dies are more expensive to produce and have lower yield per wafer. |
| `chip_package` | Describes the physical packaging format (e.g., monolithic die, MCM/chiplet). `null` here means a standard single-die package. |

---

## 📅 Release & Interface

| Field | Meaning |
|---|---|
| `release_date` | The official launch date of the product (April 12, 2023). |
| `bus_interface` | How the GPU connects to the CPU/motherboard. **PCIe 4.0 x16** means 16 lanes of PCIe Gen 4, providing ~32 GB/s of bidirectional bandwidth. Compatible with PCIe 3.0 and 5.0 slots (with speed adjustment). |

---

## 🧠 Memory Subsystem

| Field | Unit | Meaning |
|---|---|---|
| `memory_type` | — | **GDDR6X** is a high-speed graphics memory standard. The "X" variant uses PAM4 (Pulse Amplitude Modulation 4) signaling for higher bandwidth than standard GDDR6. |
| `memory_size_gb` | GB | Total VRAM capacity. 12 GB is sufficient for 1080p/1440p gaming and most AI inference workloads at this tier. |
| `memory_bus_bits` | bits | Width of the memory bus. A **192-bit** bus with GDDR6X is a sweet spot — wider buses allow more data to flow per clock cycle. |
| `memory_clock_mhz` | MHz | Effective memory clock (base). GDDR6X uses quad-rate signaling, so the effective data rate is much higher than this raw figure. |
| `memory_bandwidth_gb_s` | GB/s | Total sustained memory bandwidth: **504.2 GB/s**. Calculated as `(bus_width / 8) × effective_data_rate`. Critical for GPU-bound workloads. |

---

## 🔢 Compute Units

| Field | Meaning |
|---|---|
| `shading_units` | Also called **CUDA Cores** (NVIDIA) or shader processors. Each unit executes one floating-point or integer operation per clock. 5,888 cores at 2,475 MHz gives the RTX 4070 its ~29 TFLOPS of FP32 throughput. |
| `texture_mapping_units` (TMUs) | Handle texture sampling and filtering operations. 184 TMUs produce 455 GT/s of texture fill rate. |
| `render_output_processors` (ROPs) | Responsible for writing final pixel colors to the framebuffer, handling anti-aliasing blending. 64 ROPs yield 158 GPixel/s fill rate. |
| `streaming_multiprocessors` (SMs) | The top-level compute cluster unit in NVIDIA GPUs. Each SM contains a fixed set of CUDA cores, tensor cores, an RT core, caches, and schedulers. 46 SMs × 128 CUDA cores = 5,888 total shaders. |
| `tensor_cores` | Specialized matrix-multiply units, 184 in total (4 per SM). Accelerate AI inference, DLSS, and scientific matrix operations by an order of magnitude vs. standard FP32 cores. |
| `ray_tracing_cores` | Dedicated fixed-function units for BVH (Bounding Volume Hierarchy) traversal and ray-triangle intersection tests. 46 RT cores (one per SM) dramatically accelerate real-time ray tracing. |

---

## 🗂️ Cache Hierarchy

| Field | Meaning |
|---|---|
| `l1_cache_kb` | **128 KB** of L1 cache per SM. Acts as an ultra-fast scratch space for shader data, reducing memory latency. Shared between texture cache and shared memory. |
| `l2_cache_mb` | **36 MB** of on-die L2 cache shared across all SMs. Ada Lovelace dramatically increased L2 size versus previous generations to reduce VRAM bandwidth pressure. |

---

## ⚡ Power & Thermal

| Field | Unit | Meaning |
|---|---|---|
| `thermal_design_power_w` | Watts | **TDP** is the maximum sustained power the GPU draws under full load. Cooling solutions and PSU selection must accommodate this. 200 W is relatively efficient for this performance tier. |
| `suggested_psu_w` | Watts | Recommended minimum PSU wattage for the full system. 550 W accounts for the GPU, CPU, and other components with headroom. |
| `power_connectors` | — | The physical power cable from the PSU. **1× 16-pin** (PCIe 5.0 connector, also called 12VHPWR) delivers up to 600 W through a single cable, though an adapter from 3×8-pin is usually included. |

---

## 📐 Physical Dimensions

| Field | Unit | Meaning |
|---|---|---|
| `board_length_mm` | mm | PCB length of the card. At 240 mm, this is a compact card that fits in most mid-tower and even some ITX cases. |
| `board_width_mm` | mm | Card width. 40 mm combined with dual-slot design gives the total cooler volume. |
| `board_slot_width` | — | How many expansion slots the card occupies in the chassis. **Dual-slot** is standard; some high-end cards require 3–4 slots. |

---

## 🖥️ Display Output

| Field | Meaning |
|---|---|
| `display_connectors` | Physical video output ports. **1× HDMI 2.1** supports 4K@120Hz, 8K@60Hz, and VRR. **3× DisplayPort 1.4a** supports 4K@144Hz (with DSC), and allows daisy-chaining monitors. Maximum 4 simultaneous displays. |

---

## 🛠️ API & Software Support

### Graphics APIs

| Field | Meaning |
|---|---|
| `directx_major/minor_version` | **DirectX 12 Ultimate (12.2)** — Microsoft's graphics API. Version 12.2 adds DirectX Raytracing tier 1.1, mesh shaders, sampler feedback, and variable rate shading. Required for modern AAA games. |
| `opengl_major/minor_version` | **OpenGL 4.6** — A legacy cross-platform graphics API, still used in professional CAD/simulation software and older game engines. |
| `vulkan_major/minor_version` | **Vulkan 1.4** — A modern low-overhead cross-platform API (the cross-platform alternative to DirectX 12). Preferred by Linux gaming (via Proton) and many modern engines. |

### Compute APIs

| Field | Meaning |
|---|---|
| `opencl_major/minor_version` | **OpenCL 3.0** — An open standard for GPU compute across different vendors. Used in image processing, scientific computing, and some ML frameworks. |
| `cuda_major/minor_version` | **CUDA 8.9** — NVIDIA's proprietary parallel compute platform. The de facto standard for AI/ML (PyTorch, TensorFlow), scientific computing, and video encoding. Version 8.9 corresponds to the Ada Lovelace SM architecture. |
| `shader_model_major/minor_version` | **Shader Model 6.8** — Microsoft's versioning for programmable shader capabilities. 6.8 adds features like wave matrix operations useful for ML workloads on the GPU. |

---

## 📊 Performance Metrics

| Field | Unit | Meaning |
|---|---|---|
| `pixel_rate_gpixel_s` | GPixel/s | Maximum pixels the ROPs can write per second. **158.4 GPixel/s** = ROPs × boost clock. Important for high-resolution, high-refresh-rate rendering. |
| `texture_rate_gtexel_s` | GTexel/s | Maximum textels (texture elements) the TMUs can sample and filter per second. **455.4 GTexel/s** = TMUs × boost clock. |
| `half_float_performance_gflop_s` | GFLOP/s | FP16 throughput. **29,150 GFLOP/s (~29 TFLOPS)**. On Ada, FP16 and FP32 have the same rate because FP16 operations are executed two at a time in FP32 units. Used heavily in AI inference. |
| `single_float_performance_gflop_s` | GFLOP/s | FP32 (standard 32-bit float) throughput. **29,150 GFLOP/s** — the primary metric for gaming and general GPU compute performance. Calculated as `shading_units × 2 × boost_clock`. |
| `double_float_performance_gflop_s` | GFLOP/s | FP64 (64-bit double precision) throughput. **455.4 GFLOP/s** — only 1/64th of FP32 rate. Consumer GPUs deliberately cripple FP64 to differentiate from workstation-class GPUs (e.g., NVIDIA A/H series). |

---

## 🔗 Reference

| Field | Meaning |
|---|---|
| `tpu_id` | Unique identifier for this GPU entry in the TechPowerUp GPU database (`c3924`). |
| `tpu_url` | Direct link to the full specification page on [TechPowerUp](https://www.techpowerup.com/gpu-specs/geforce-rtx-4070.c3924), a trusted GPU database. |

---

*All specifications are for the reference/Founders Edition RTX 4070. AIB (Add-In Board) partner models may vary in clock speeds, cooling, power limits, and dimensions.*