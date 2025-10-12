# Custom Nodes

The **base** images include 24 carefully selected custom nodes for ComfyUI. These nodes provide enhanced functionality for AI image and video generation workflows, from basic utilities to advanced model optimization.

## Included Custom Nodes

### Core Workflow Nodes

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI Manager** | Package manager for ComfyUI | Install/manage custom nodes |
| **ComfyUI-Easy-Use** | User-friendly workflow nodes | Simplify complex operations |
| **ComfyUI_essentials** | Essential utility nodes | Core workflow enhancements |
| **efficiency-nodes-comfyui** | Performance optimization | Faster execution |
| **ComfyUI-Impact-Pack** | Advanced conditioning nodes | Enhanced control |
| **ComfyUI-Impact-Subpack** | Additional Impact nodes | Extended functionality |

### Video Generation & Processing

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI-WanVideoWrapper** | WAN 2.2 video generation | Text/Image-to-Video |
| **ComfyUI-VideoHelperSuite** | Video processing utilities | Video format handling |
| **ComfyUI-Frame-Interpolation** | Frame rate enhancement | Smooth video output |
| **ComfyUI-wanBlockswap** | WAN model optimization | Memory-efficient generation |

### Model Optimization & Performance

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI-GGUF** | GGUF model support | Memory-efficient models |
| **ComfyUI-TensorRT** | TensorRT acceleration | GPU optimization |
| **ComfyUI-MultiGPU** | Multi-GPU support | Distributed processing |

### Image Enhancement & Processing

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI_UltimateSDUpscale** | Advanced image upscaling | High-resolution output |
| **ComfyUI-Image-Saver** | Enhanced image saving | Better file management |
| **ComfyUI-Crystools** | Crystal generation tools | Specialized effects |

### Workflow Enhancement & Utilities

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI-KJNodes** | Advanced workflow nodes | Complex operations |
| **ComfyUI-mxToolkit** | Math and logic nodes | Computational workflows |
| **ComfyUI-Custom-Scripts** | Custom functionality | Extended features |
| **ComfyUI_JPS-Nodes** | Specialized operations | Unique workflows |
| **cg-use-everywhere** | Node connection utility | Flexible connections |
| **rgthree-comfy** | Utility nodes | Workflow helpers |
| **ComfyUI-KJNodes** | Additional advanced nodes | Extended capabilities |

### Text & Prompt Management

| Node | Description | Purpose |
|------|-------------|---------|
| **comfyui-prompt-reader-node** | Prompt analysis tools | Text processing |
| **comfy-ex-tagcomplete** | Auto-completion | Faster workflow building |

### Connectivity & Integration

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI-Openrouter_node** | External API integration | Cloud model access |
| **ComfyUI-KJNodes** | Network and connectivity | External services |

### Development & Quality of Life

| Node | Description | Purpose |
|------|-------------|---------|
| **ComfyUI-Custom-Scripts** | Development tools | Custom workflows |
| **ComfyUI-JPS-Nodes** | Debugging utilities | Development support |

## Detailed Node Information

### Video Generation & Processing

#### **ComfyUI-WanVideoWrapper**
- **Repository**: kijai/ComfyUI-WanVideoWrapper
- **Purpose**: Primary interface for WAN 2.2 video generation models
- **Key Features**:
  - Text-to-Video (T2V) generation
  - Image-to-Video (I2V) conversion
  - Support for multiple model formats (FP8, GGUF)
  - LoRA integration for style and speed enhancement
- **Dependencies**: PyTorch, transformers, diffusers
- **Usage**: Core node for all WAN video generation workflows

#### **ComfyUI-VideoHelperSuite**
- **Repository**: Kosinkadink/ComfyUI-VideoHelperSuite
- **Purpose**: Comprehensive video processing and format conversion
- **Key Features**:
  - Video format conversion (MP4, GIF, WebM)
  - Frame extraction and manipulation
  - Video concatenation and splitting
  - Metadata handling
- **Dependencies**: OpenCV, imageio, ffmpeg
- **Usage**: Post-processing and format handling for video outputs

#### **ComfyUI-Frame-Interpolation**
- **Repository**: Fannovel16/ComfyUI-Frame-Interpolation
- **Purpose**: Increase frame rate and smooth video output
- **Key Features**:
  - Frame interpolation algorithms (RIFE, FILM)
  - Motion compensation
  - Adjustable smoothness settings
  - Multiple interpolation methods
- **Dependencies**: PyTorch, OpenCV, numpy
- **Usage**: Enhance video quality by increasing frame rate

#### **ComfyUI-wanBlockswap**
- **Repository**: orssorbit/ComfyUI-wanBlockswap
- **Purpose**: Memory optimization for large WAN models
- **Key Features**:
  - Block-wise model loading
  - Memory usage reduction (30-50%)
  - Maintains quality while reducing VRAM requirements
  - Compatible with all WAN model variants
- **Dependencies**: Custom CUDA kernels, PyTorch
- **Usage**: Enable larger models on limited VRAM systems

### Model Optimization & Performance

#### **ComfyUI-GGUF**
- **Repository**: city96/ComfyUI-GGUF
- **Purpose**: Support for GGUF quantized models
- **Key Features**:
  - Load GGUF quantized diffusion models
  - Significant memory reduction (50-70%)
  - Support for various quantization levels (Q4, Q8, etc.)
  - Maintains good quality with lower memory usage
- **Dependencies**: ggml-python, PyTorch
- **Usage**: Use quantized models for memory efficiency

#### **ComfyUI-TensorRT**
- **Repository**: comfyanonymous/ComfyUI_TensorRT
- **Purpose**: NVIDIA TensorRT acceleration
- **Key Features**:
  - Convert models to TensorRT engines
  - 2-5x faster inference speed
  - Optimized for NVIDIA GPUs
  - Support for dynamic shapes
- **Dependencies**: TensorRT, PyTorch, CUDA
- **Usage**: Maximum performance on NVIDIA hardware

#### **ComfyUI-MultiGPU**
- **Repository**: pollockjj/ComfyUI-MultiGPU
- **Purpose**: Distributed processing across multiple GPUs
- **Key Features**:
  - Automatic workload distribution
  - Load balancing across GPUs
  - Memory pooling
  - Support for different GPU configurations
- **Dependencies**: PyTorch distributed, NCCL
- **Usage**: Scale processing across multiple GPUs

### Core Workflow Enhancement

#### **ComfyUI-Easy-Use**
- **Repository**: yolain/ComfyUI-Easy-Use
- **Purpose**: Simplify complex operations with user-friendly nodes
- **Key Features**:
  - Simplified sampling and generation nodes
  - Automatic prompt enhancement
  - Easy model switching
  - Pre-configured workflows
- **Dependencies**: transformers, diffusers
- **Usage**: Beginner-friendly alternative to complex nodes

#### **ComfyUI-Impact-Pack**
- **Repository**: ltdrdata/ComfyUI-Impact-Pack
- **Purpose**: Advanced conditioning and control mechanisms
- **Key Features**:
  - Detail transfer nodes
  - Advanced conditioning methods
  - Regional prompting
  - Batch processing utilities
- **Dependencies**: PyTorch, OpenCV
- **Usage**: Fine-grained control over generation process

#### **efficiency-nodes-comfyui**
- **Repository**: jags111/efficiency-nodes-comfyui
- **Purpose**: Performance optimization and workflow efficiency
- **Key Features**:
  - Memory-efficient sampling
  - Batch processing optimization
  - Cached computations
  - Smart workflow routing
- **Dependencies**: PyTorch, numpy
- **Usage**: Optimize workflow performance and memory usage

### Connectivity & Integration

#### **ComfyUI-Openrouter_node**
- **Repository**: gabe-init/ComfyUI-Openrouter_node
- **Purpose**: Integration with OpenRouter API for external model access
- **Key Features**:
  - Access to cloud-based language models
  - API key management
  - Model selection interface
  - Cost tracking and limits
- **Dependencies**: requests, openai
- **Usage**: Connect to external language models via OpenRouter

## WAN 2.2 Video Generation

The ZeroClue ComfyUI images are optimized for **WAN 2.2** video generation workflows:

### Required Components
- **ComfyUI-WanVideoWrapper**: Core WAN 2.2 implementation
- **ComfyUI-GGUF**: Support for GGUF-quantized models
- **ComfyUI-wanBlockswap**: Memory optimization for large models

### Supported Model Formats
- **FP8**: High-quality models (4.8GB)
- **GGUF Q4/Q8**: Memory-efficient models (2.9-5.2GB)
- **LoRAs**: Lightweight adapters (236MB each)

### Usage Examples

#### Basic Text-to-Video
```python
# Load WAN 2.2 model
wan_model = WanModelLoader("diffusion_transformer_5b_fp8.safetensors")

# Generate video from text
video = WanTextToVideo(
    model=wan_model,
    prompt="A beautiful sunset over mountains",
    width=1024,
    height=576,
    num_frames=81
)
```

#### Image-to-Video with GGUF
```python
# Load GGUF model (memory efficient)
gguf_model = GGUFModelLoader("Wan2.2-I2V-5B-Q4_K_M.gguf")

# Generate video from image
video = WanImageToVideo(
    model=gguf_model,
    input_image="input.jpg",
    prompt="Camera zooms into the scene",
    motion_strength=0.7
)
```

#### Lightning Fast Generation
```python
# Load Lightning LoRA
lightning_lora = LoRALoader("wan_lightning.safetensors")

# Apply for faster inference
fast_video = ApplyLoRA(
    model=wan_model,
    lora=lightning_lora,
    strength=1.0
)
```

## Installation Notes

### Base Images
All custom nodes are pre-installed in **base** images:
- `zeroclue/comfyui:base-torch2.8.0-cu126`
- `zeroclue/comfyui:base-torch2.8.0-cu128`
- etc.

### Slim/Minimal Images
Custom nodes are **NOT** included in:
- `slim` images (ComfyUI + Manager only)
- `minimal` images (ComfyUI only)

### Manual Installation
For slim/minimal images, install nodes via ComfyUI Manager:
1. Access ComfyUI at http://localhost:3000
2. Open ComfyUI Manager
3. Browse and install desired nodes
4. Restart ComfyUI

## Node Updates

Custom nodes are updated during Docker image builds (every 8 hours). To get the latest versions:

### Automatic Updates
```bash
# Pull latest image
docker pull zeroclue/comfyui:base-torch2.8.0-cu126

# Run with updated nodes
docker run --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Manual Updates (inside container)
```bash
# Update ComfyUI Manager
python /workspace/ComfyUI/custom_nodes/ComfyUI-Manager/update.py

# Update all custom nodes
python /workspace/ComfyUI/custom_nodes/ComfyUI-Manager/update_all.py
```

## Troubleshooting

### Common Issues

#### Node Not Found
```bash
# Check if node is installed
ls /workspace/ComfyUI/custom_nodes/

# Reinstall via ComfyUI Manager
# Access ComfyUI web interface → Manager → Install Custom Nodes
```

#### Model Loading Errors
```bash
# Check model paths
ls /workspace/ComfyUI/models/diffusion_models/
ls /workspace/ComfyUI/models/loras/

# Verify model formats
file /workspace/ComfyUI/models/diffusion_models/*.safetensors
```

#### Memory Issues
```bash
# Use GGUF models for lower memory
docker run -e PRESET_DOWNLOAD=WAN_22_5B_I2V_GGUF_Q4_K_M \
  zeroclue/comfyui:base-torch2.8.0-cu126

# Monitor memory usage
nvtop
```

### Performance Optimization

#### For Best Performance
```bash
# Use Lightning LoRA for faster generation
PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN_22_LIGHTNING_LORA"

# Enable SageAttention for Ampere+ GPUs
docker run -e INSTALL_SAGEATTENTION=True \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

#### For Memory Efficiency
```bash
# Use GGUF models
PRESET_DOWNLOAD=WAN_22_5B_I2V_GGUF_Q4_K_M

# Use minimal image if custom nodes not needed
docker run zeroclue/comfyui:minimal-torch2.8.0-cu126
```

## Contributing

To suggest additional custom nodes or report issues:

1. **GitHub Issues**: [ZeroClue/ComfyUI-Docker Issues](https://github.com/ZeroClue/ComfyUI-Docker/issues)
2. **Node Requests**: Create an issue with node name and purpose
3. **Bug Reports**: Include error logs and system information

## Node Versions

The custom nodes included are tested for compatibility with:
- **ComfyUI**: Latest version (auto-updated)
- **Python**: 3.13
- **PyTorch**: 2.8.0
- **CUDA**: 12.4, 12.6, 12.8, 12.9, 13.0

For specific version information, check inside the container:
```bash
# Check ComfyUI version
python /workspace/ComfyUI/main.py --version

# Check node versions
ls /workspace/ComfyUI/custom_nodes/*/
```