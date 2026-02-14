# BARK_BASIC - High-Quality Text-to-Speech

Suno BARK model for realistic voice synthesis and text-to-speech generation.

## Quick Start

```bash
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 2GB
- **Type**: Text-to-Speech (TTS)
- **Company**: Suno AI
- **Voice Quality**: Very realistic
- **Languages**: Primarily English
- **Specialty**: Voice generation

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 3060 (12GB)** - Works well
- **GTX 1080 Ti (11GB)** - Minimum

### Storage
- **Minimum**: 8GB
- **Recommended**: 10GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **RTX 3060**: ~$0.35/hour
- **Spot instance**: ~$0.20/hour

## Performance

### Speed
- **Generation**: 5-15 seconds per clip
- **Inference**: Fast for speech
- **Memory Usage**: ~4GB VRAM

### Quality
- **Voice Quality**: Very realistic
- **Emotion**: Good expression
- **Clarity**: Excellent
- **Naturalness**: High

## Use Cases

### Best For
- Voice narration
- Podcast creation
- Audio book slim
- Educational content
- Character voices

### Good For
- Social media audio
- Presentations
- Voice assistants
- Accessibility features
- Creative projects

### Not Ideal For
- Music generation
- Long-form audio (>30 seconds)
- Multiple speaker conversations
- Real-time voice chat

## Example Prompts

```text
Hello and welcome to our podcast about technology
In today's episode, we'll discuss artificial intelligence
The weather today is sunny with a chance of rain
Welcome to our educational series on science
Character voice: deep, mysterious narrator
```

## Advanced Usage

### Complete Speech Setup
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=AUDIO_SPEECH_COMPLETE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Music Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD="BARK_BASIC,MUSICGEN_MEDIUM" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs MUSICGEN_MEDIUM
- **This Model**: Speech synthesis, realistic voices
- **MusicGen**: Music composition, instrumental

### vs TTS_AUDIO_SUITE
- **This Model**: Higher quality, simpler setup
- **TTS Suite**: More features, more complex

### vs PARLER_TTS
- **This Model**: More established, reliable
- **Parler TTS**: Newer, potentially better

## Tips for Best Results

### Prompt Engineering
- Use clear, well-structured text
- Include punctuation for natural pauses
- Keep text segments under 30 seconds
- Use emotional descriptors
- Specify voice characteristics

### Technical Settings
- Break long text into segments
- Use appropriate sampling rates
- Monitor audio quality output
- Test different voice parameters

### Content Guidelines
- Write conversationally
- Include emotional cues
- Use proper grammar and spelling
- Consider audio length limitations

## Advanced Features

### Professional Workflow
```bash
# Complete professional audio setup
docker run -e AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multimedia Setup
```bash
# Speech with music and images
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  -e IMAGE_PRESET_DOWNLOAD=SDXL_BASE_V1 \
  -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_SMALL \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Robot-like voice**: Improve text structure
2. **Cut-off audio**: Reduce text length
3. **Poor quality**: Check audio output settings
4. **Slow generation**: Monitor GPU usage

### Performance Tips
- Very efficient on RTX 4000 Ada
- Batch similar text segments
- Monitor memory usage
- Use appropriate audio formats

## Integration Examples

### With Video Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Image Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=BARK_BASIC \
  -e IMAGE_PRESET_DOWNLOAD=REALISTIC_VISION_V6 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Very cost-effective for speech synthesis
- Fast generation reduces costs
- Small model size reduces storage
- Efficient GPU usage

### Quality Assurance
- Consistent voice quality
- Reliable performance
- Well-documented behavior
- Good for slim use

## Voice Style Examples

### Professional Narration
```text
Welcome to our presentation on modern technology. Today we'll explore how artificial intelligence is transforming industries worldwide.
```

### Educational Content
```text
In this lesson, we'll learn about the water cycle. Water evaporates from oceans, forms clouds, and returns as rain.
```

### Character Voice
```text
[In a deep, mysterious voice] Welcome, dear listener, to tales of the unknown. Tonight's story begins in a dark forest...
```

## Audio Formats and Quality

### Output Options
- **WAV**: High quality, larger files
- **MP3**: Good compression, smaller files
- **Sample Rate**: 22050 Hz recommended
- **Bit Depth**: 16-bit standard

### Best Practices
- Use appropriate sample rates
- Test different output formats
- Monitor audio clipping
- Consider post-processing needs

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (recommended)
2. **Set environment variable** `AUDIO_PRESET_DOWNLOAD=BARK_BASIC`
3. **Access ComfyUI** at port 3000
4. **Test with short text segments**
5. **Create longer audio** content as needed

## Alternatives

- **MUSICGEN_MEDIUM** - For music generation (6GB)
- **TTS_AUDIO_SUITE** - More TTS features (3GB)
- **PARLER_TTS** - Alternative TTS model (4GB)
- **AUDIO_SPEECH_COMPLETE** - Complete speech workflow (5GB)