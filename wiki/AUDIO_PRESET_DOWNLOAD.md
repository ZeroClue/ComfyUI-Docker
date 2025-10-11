# AUDIO_PRESET_DOWNLOAD Environment Variable ⚠️ **EXPERIMENTAL**

> ⚠️ **Experimental Notice**: The audio generation presets are in **experimental/beta** state. These presets rely on third-party custom nodes that may be unstable, incompatible with certain ComfyUI versions, or contain bugs. Models and workflows may change without notice. Use at your own risk and please report issues to the respective custom node developers.

> The `AUDIO_PRESET_DOWNLOAD` environment variable accepts either a **single preset** or **multiple presets** separated by commas. \
> When set, the container will automatically download the corresponding audio generation models and custom nodes on startup.

## Usage Examples ⚠️ **Experimental**

> ⚠️ **Reminder**: The following examples use experimental audio presets that may be unstable or contain bugs. Use with caution.

### Single Preset
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multiple Presets
```bash
docker run -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,TTS_AUDIO_SUITE" zeroclue/comfyui:base-torch2.8.0-cu126
```

### Manual Download (inside container)
```bash
bash /download_audio_presets.sh BARK_BASIC,MUSICGEN_SMALL
```

### Combined with Image and Video Presets
```bash
docker run \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Available Presets ⚠️ **Experimental**

> ⚠️ **Note**: The following presets rely on experimental custom nodes that may have compatibility issues with different ComfyUI versions.

### Text-to-Speech Models

| Preset Name | Description | Models | Custom Nodes | Size |
|-------------|-------------|---------|--------------|------|
| **BARK_BASIC** | High-quality text-to-speech | Bark model | ComfyUI Custom Scripts | ~1.2GB |
| **TTS_AUDIO_SUITE** | Comprehensive TTS toolkit | Multiple TTS models | TTS Audio Suite | ~2-4GB |
| **PARLER_TTS** | Natural voice synthesis | ParlerTTS models | ComfyUI_ParlerTTS | ~1-2GB |

### Music Generation Models

| Preset Name | Description | Models | Custom Nodes | Size |
|-------------|-------------|---------|--------------|------|
| **MUSICGEN_SMALL** | Compact music generation | MusicGen Small | ComfyUI Custom Scripts | ~1.5GB |
| **MUSICGEN_MEDIUM** | High-quality music generation | MusicGen Medium | ComfyUI Custom Scripts | ~3GB |
| **ACE_STEP** | Rhythm and melody generation | Ace-Step model | AceStep-ComfyUI-Nodes | ~800MB |
| **SONGBLOOM** | Creative music composition | SongBloom model | SongBloom-ComfyUI | ~1.2GB |

### Sound Effects & Audio Processing

| Preset Name | Description | Models | Custom Nodes | Size |
|-------------|-------------|---------|--------------|------|
| **STABLE_AUDIO_OPEN** | High-quality audio generation | Stable Audio Open models | ComfyUI-StableAudioOpen | ~2.5GB |

### Complete Audio Workflows

| Preset Name | Description | Models | Custom Nodes | Size |
|-------------|-------------|---------|--------------|------|
| **AUDIO_SPEECH_COMPLETE** | Complete speech workflow | Bark + TTS nodes | Multiple TTS nodes | ~3-5GB |
| **AUDIO_MUSIC_COMPLETE** | Complete music workflow | MusicGen + rhythm nodes | Music + rhythm nodes | ~4-6GB |
| **AUDIO_PRODUCTION** | Professional audio suite | All audio models | All audio nodes | ~6-10GB |
| **AUDIO_ALL** | Complete audio collection | All available models | All audio nodes | ~8-15GB |

## Model Details

### BARK_BASIC
```
- Bark text-to-speech model (high-quality voice synthesis)
- Supports multiple languages and voice styles
- Natural-sounding speech generation
- Download URL: suno/bark model.safetetensors
- Target: /workspace/ComfyUI/models/TTS/
- Custom Node: ComfyUI Custom Scripts (for integration)
```

### TTS_AUDIO_SUITE
```
- Multiple TTS models and voice synthesis tools
- Comprehensive text-to-speech toolkit
- Supports various voice styles and languages
- Models downloaded via custom node
- Custom Node: TTS Audio Suite (handles own model downloads)
```

### PARLER_TTS
```
- ParlerTTS natural voice synthesis models
- High-quality, natural-sounding speech
- Advanced voice cloning capabilities
- Models downloaded via custom node
- Custom Node: ComfyUI_ParlerTTS
```

### MUSICGEN_SMALL/MEDIUM
```
- Facebook's MusicGen music generation models
- Text-to-music generation with high quality
- Small: ~1.5GB (faster, lower quality)
- Medium: ~3GB (higher quality)
- Download URLs: Multiple model components from facebook/musicgen
- Target: /workspace/ComfyUI/models/audio/
- Custom Node: ComfyUI Custom Scripts (for integration)
```

### ACE_STEP
```
- Ace-Step rhythm and melody generation model
- Specialized for beat and melody creation
- ~800MB (compact size)
- Download URL: LonelyNights/AceStep-Base
- Target: /workspace/ComfyUI/models/TTS/
- Custom Node: AceStep-ComfyUI-Nodes
```

### SONGBLOOM
```
- SongBloom creative music composition model
- Advanced music generation and arrangement
- ~1.2GB
- Download URL: CookieConsistency/songbloom
- Target: /workspace/ComfyUI/models/audio/
- Custom Node: SongBloom-ComfyUI
```

### STABLE_AUDIO_OPEN
```
- Stability AI's high-quality audio generation model
- Text-to-audio with exceptional quality
- Supports various audio styles and effects
- Download URLs: Multiple model components from stabilityai/stable-audio-open-1.0
- Targets: /workspace/ComfyUI/models/audio/, /workspace/ComfyUI/models/text_encoders/
- Custom Node: ComfyUI-StableAudioOpen
```

## Usage Examples

### Quick Start with Speech Generation
```bash
# Get started with high-quality text-to-speech
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Music Generation Setup
```bash
# Complete music generation workflow
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Professional Audio Production
```bash
# Complete audio production suite
docker run -e AUDIO_PRESET_DOWNLOAD=AUDIO_PRODUCTION \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Voice Synthesis Toolkit
```bash
# Comprehensive TTS toolkit
docker run -e AUDIO_PRESET_DOWNLOAD=TTS_AUDIO_SUITE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Creative Music Suite
```bash
# Multiple music generation tools
docker run -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,ACE_STEP,SONGBLOOM" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Complete Audio Collection
```bash
# All available audio models and tools
docker run -e AUDIO_PRESET_DOWNLOAD=AUDIO_ALL \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Mixed Media Generation
```bash
# Combined image, video, and audio generation
docker run \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## File Organization

Downloaded audio models are organized as follows:

```
/workspace/ComfyUI/models/
├── TTS/                    # Text-to-speech models
│   ├── model.safetensors   # Bark model
│   └── Ace-Step-v1.0.safetensors
├── audio/                  # Music and audio generation models
│   ├── model.safetensors   # MusicGen models
│   ├── config.json
│   ├── compression_model.safetensors
│   ├── decoder_model.safetensors
│   └── enCodec_model_*.safetensors
└── text_encoders/          # Text encoder models for audio
    └── text_encoder.safetensors
```

Custom nodes are installed in:
```
/workspace/ComfyUI/custom_nodes/
├── ComfyUI_Custom-Scripts/     # Audio integration scripts
├── TTS-Audio-Suite/            # TTS toolkit
├── ComfyUI_ParlerTTS/          # ParlerTTS integration
├── AceStep-ComfyUI-Nodes/      # Rhythm generation nodes
├── SongBloom-ComfyUI/          # Music composition nodes
└── ComfyUI-StableAudioOpen/    # High-quality audio generation
```

## Performance Notes

### Model Size Comparison
- **BASIC Models**: 800MB-1.5GB - Fast generation, lower quality
- **MEDIUM Models**: 2-4GB - Balanced quality and performance
- **LARGE Models**: 4-6GB - Highest quality, slower generation
- **COMPLETE Workflows**: 6-15GB total - Multiple models for complete pipelines

### Hardware Requirements
- **CPU-only**: Basic TTS models work but will be slow
- **GPU Recommended**: For music generation and high-quality audio
- **VRAM**: 8GB+ recommended for music generation models
- **Storage**: 15GB+ free space for complete audio collection

### Recommended Combinations

#### For Beginners
```bash
AUDIO_PRESET_DOWNLOAD="BARK_BASIC"
```

#### For Musicians
```bash
AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,ACE_STEP"
```

#### For Voice Artists
```bash
AUDIO_PRESET_DOWNLOAD="TTS_AUDIO_SUITE,PARLER_TTS"
```

#### For Audio Engineers
```bash
AUDIO_PRESET_DOWNLOAD="STABLE_AUDIO_OPEN,MUSICGEN_MEDIUM"
```

#### For Complete Audio Production
```bash
AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION"
```

#### For Maximum Flexibility
```bash
AUDIO_PRESET_DOWNLOAD="AUDIO_ALL"
```

## Workflow Recommendations

### Text-to-Speech Workflow
1. Choose `BARK_BASIC` for high-quality speech synthesis
2. Use `TTS_AUDIO_SUITE` for comprehensive TTS toolkit
3. Add `PARLER_TTS` for natural voice synthesis
4. Experiment with different voice styles and languages

### Music Generation Workflow
1. Start with `MUSICGEN_SMALL` for faster iteration
2. Upgrade to `MUSICGEN_MEDIUM` for higher quality
3. Add `ACE_STEP` for rhythm and beat generation
4. Use `SONGBLOOM` for creative music composition

### Professional Audio Workflow
1. Use `STABLE_AUDIO_OPEN` for highest quality generation
2. Combine with music generation models for complete production
3. Use TTS models for voiceovers and narration
4. Apply custom nodes for post-processing and effects

### Complete Audio Production Workflow
1. Start with `AUDIO_PRODUCTION` for comprehensive toolkit
2. Use TTS models for voice content
3. Use music generation for background music
4. Apply rhythm models for beat creation
5. Use audio processing tools for final polish

## Troubleshooting ⚠️ **Experimental Issues**

### ⚠️ Experimental-Specific Issues
- **Custom Node Compatibility**: Audio custom nodes may be incompatible with certain ComfyUI versions
- **Model Instability**: Audio models may produce unexpected results or fail to load
- **Workflow Changes**: Audio workflows may change or break between updates
- **Reporting Issues**: Please report bugs to the respective custom node repositories, not this Docker repository

### Download Issues
- Check internet connectivity
- Verify HuggingFace URLs are accessible
- Ensure sufficient disk space (models are 800MB-6GB each)

### Model Not Found
- Verify preset name spelling
- Check that models downloaded to correct folders
- Restart ComfyUI after downloading new models

### Performance Issues
- Use smaller models for testing and development
- Monitor GPU memory usage with nvtop
- Consider CPU-only mode for basic TTS models
- Close other GPU applications when generating audio

### Audio Quality Issues
- Use higher quality models (Medium over Small)
- Ensure proper audio format settings in ComfyUI
- Check that all required model components are downloaded
- Verify custom nodes are properly installed

### Custom Node Issues
- **⚠️ Common Experimental Problems**:
  - Custom nodes may fail to load with certain ComfyUI versions
  - Audio processing may be slow or crash frequently
  - Workflows may not appear in ComfyUI interface
  - Models may fail to download or load properly
- Check that custom nodes installed correctly
- Verify requirements.txt files were processed
- Restart ComfyUI after installing new custom nodes
- Check custom node documentation for specific setup instructions
- **For experimental issues**: Check the GitHub issues page for each custom node

## Comparison with Other Preset Systems

| Feature | AUDIO_PRESET_DOWNLOAD | IMAGE_PRESET_DOWNLOAD | PRESET_DOWNLOAD |
|---------|----------------------|-----------------------|-----------------|
| **Purpose** | Audio generation models | Image generation models | Video generation models |
| **Model Types** | TTS, Music, Sound Effects | SDXL, SD 1.5, Flux | WAN 2.2 Video |
| **File Sizes** | 800MB-6GB per model | 2-7GB per model | 3-5GB per model |
| **Use Cases** | Speech, Music, Audio | Art, Photography, Design | Video Creation, Animation |
| **Workflow** | Text-to-Audio, Music Generation | Text-to-Image, Image Editing | Text-to-Video, Image-to-Video |
| **Custom Nodes** | Required for integration | Optional for enhancement | Required for video processing |
| **Hardware** | CPU/GPU (GPU recommended) | GPU recommended | GPU required |
| **Stability** | ⚠️ **Experimental** | Stable | Stable |

All three systems can be used together for comprehensive AI media generation capabilities, enabling the creation of videos with custom soundtracks, images with audio descriptions, and complete multimedia projects.

> ⚠️ **Important Note**: When combining systems, be aware that audio presets are experimental and may cause instability in otherwise stable workflows.

## Integration Examples ⚠️ **Experimental Combinations**

> ⚠️ **Warning**: The following examples combine stable image/video workflows with experimental audio presets. Audio components may cause instability or failures.

### Video with Custom Soundtrack
```bash
docker run \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,ACE_STEP" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```
> ⚠️ Audio presets may cause video generation instability

### Multimedia Storytelling
```bash
docker run \
  -e IMAGE_PRESET_DOWNLOAD="SDXL_BASE_V1,REALISTIC_VISION_V6" \
  -e AUDIO_PRESET_DOWNLOAD="BARK_BASIC,TTS_AUDIO_SUITE" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```
> ⚠️ Audio presets may cause multimedia workflow failures

### Complete Media Production
```bash
docker run \
  -e IMAGE_PRESET_DOWNLOAD="FLUX_DEV_BASIC" \
  -e AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION" \
  -e PRESET_DOWNLOAD="WAN_22_5B_TIV2,WAN22_LIGHTNING_LORA" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```
> ⚠️ Audio presets may cause complete production pipeline instability

This enables creators to generate comprehensive multimedia content with AI, including videos with custom soundtracks, images with audio narration, and complete media productions.

> ⚠️ **Final Reminder**: Audio presets are experimental. Start with image/video workflows first, then add audio components separately to isolate any issues.