# MUSICGEN_MEDIUM - High-Quality Music Generation

Facebook MusicGen Medium model for creating high-quality music and audio compositions.

## Quick Start

```bash
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM --gpus all -p 3000:3000 zeroclue/comfyui:base-torch2.8.0-cu126
```

## Model Details

- **Size**: 6GB
- **Type**: Text-to-Music
- **Company**: Meta (Facebook)
- **Quality**: High-quality music generation
- **Duration**: Up to 30 seconds
- **Styles**: Various music genres

## RunPod Requirements

### Recommended GPU
- **RTX 4000 Ada (16GB)** - Perfect fit
- **RTX 3060 (12GB)** - Works well
- **RTX 3090 (24GB)** - Overkill but fine

### Storage
- **Minimum**: 15GB
- **Recommended**: 20GB

### Cost Estimate
- **RTX 4000 Ada**: ~$0.50/hour
- **RTX 3060**: ~$0.35/hour
- **Spot instance**: ~$0.25/hour

## Performance

### Speed
- **Generation**: 10-30 seconds per clip
- **Inference**: Medium speed
- **Memory Usage**: ~8GB VRAM

### Quality
- **Audio Quality**: Very good
- **Musical Coherence**: Good
- **Genre Adaptation**: Excellent
- **Instrument Separation**: Decent

## Use Cases

### Best For
- Background music creation
- Social media content
- Podcast intros/outros
- Video game audio
- Creative projects

### Good For
- Music prototyping
- Educational content
- Presentation music
- Advertisement audio
- Personal projects

### Not Ideal For
- Professional music slim
- Long-form compositions
- Real-time generation
- Complex orchestral pieces

## Example Prompts

```text
Upbeat electronic dance music with synth leads
Acoustic folk guitar melody with strings
Epic orchestral cinematic score
Lo-fi hip hop beat with jazz samples
Rock music with electric guitars and drums
```

## Advanced Usage

### Complete Music Setup
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=AUDIO_MUSIC_COMPLETE \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Development Setup
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Voice Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD="MUSICGEN_MEDIUM,BARK_BASIC" \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Comparison with Other Models

### vs BARK_BASIC
- **This Model**: Music generation, instrumental
- **BARK**: Speech synthesis, voice

### vs MUSICGEN_SMALL
- **This Model**: Higher quality, larger model
- **Small**: Faster, less capable

### vs STABLE_AUDIO_OPEN
- **This Model**: More established, reliable
- **Stable Audio**: Higher quality, more expensive

## Tips for Best Results

### Prompt Engineering
- Be specific about music style
- Include instrument preferences
- Mention tempo and mood
- Use music terminology
- Describe genre characteristics

### Technical Settings
- 30-second clips work best
- Use appropriate sample rates
- Monitor audio quality output
- Test different prompt variations

### Music Creation Tips
- Start with simple descriptions
- Add specific instrument details
- Include emotional qualities
- Experiment with different genres

## Advanced Features

### Professional Workflow
```bash
# Complete professional music setup
docker run -e AUDIO_PRESET_DOWNLOAD="AUDIO_PRODUCTION" \
  -e ACCESS_PASSWORD=mypassword \
  --gpus all -p 3000:3000 -p 8080:8080 -p 8888:8888 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### Multimedia Setup
```bash
# Music with images and video
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  -e IMAGE_PRESET_DOWNLOAD=FLUX_SCHNELL_FP8 \
  -e PRESET_DOWNLOAD=LTXV_2B_FP8_SCALED \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Troubleshooting

### Common Issues
1. **Repetitive music**: Add more descriptive details
2. **Poor quality**: Increase generation parameters
3. **Wrong genre**: Be more specific in prompts
4. **Audio artifacts**: Check output settings

### Performance Tips
- Efficient on RTX 4000 Ada
- Batch similar music prompts
- Monitor memory usage
- Use appropriate audio formats

## Integration Examples

### With Video Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  -e PRESET_DOWNLOAD=WAN_22_5B_TIV2 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

### With Image Generation
```bash
docker run -e AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM \
  -e IMAGE_PRESET_DOWNLOAD=JUGGERNAUT_XL_V8 \
  --gpus all -p 3000:3000 \
  zeroclue/comfyui:base-torch2.8.0-cu126
```

## Production Considerations

### Cost Management
- Cost-effective for music generation
- Good balance of quality and speed
- Reasonable GPU requirements
- Efficient for batch processing

### Quality Assurance
- Consistent music quality
- Reliable genre adaptation
- Good for background music
- Suitable for commercial use

## Music Style Examples

### Electronic Music
```text
Upbeat electronic dance music with pulsing synths, driving beat at 128 BPM, bright melodic leads, energetic atmosphere
```

### Classical/Orchestral
```text
Emotional orchestral piece with strings, piano melody, dramatic dynamics, cinematic quality, heartfelt mood
```

### Jazz/Blues
```text
Smooth jazz combo with saxophone solo, upright bass, gentle piano chords, relaxed tempo, smoky atmosphere
```

### Rock Music
```text
Classic rock with electric guitars, powerful drums, bass guitar riff, energetic vocals, anthemic chorus
```

## Audio Formats and Quality

### Output Options
- **WAV**: High quality, uncompressed
- **MP3**: Good compression, smaller files
- **Sample Rate**: 44100 Hz recommended
- **Bit Depth**: 16-bit or 24-bit

### Best Practices
- Use appropriate sample rates
- Test different output formats
- Monitor for audio clipping
- Consider post-processing needs

## Next Steps

1. **Deploy RunPod** with RTX 4000 Ada (recommended)
2. **Set environment variable** `AUDIO_PRESET_DOWNLOAD=MUSICGEN_MEDIUM`
3. **Access ComfyUI** at port 3000
4. **Start with simple music prompts**
5. **Experiment with different genres**

## Alternatives

- **MUSICGEN_SMALL** - Faster generation (3GB)
- **STABLE_AUDIO_OPEN** - Higher quality (8GB)
- **ACE_STEP** - Specialized music (2GB)
- **AUDIO_MUSIC_COMPLETE** - Complete music workflow (10GB)