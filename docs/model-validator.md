# Model Validator Documentation

## Overview

The Model Validator (`scripts/model_validator.py`) provides comprehensive validation of downloaded ComfyUI preset models against their specifications. It ensures that downloaded models are complete, correct, and usable.

## Features

### Core Validation Checks

1. **File Existence Validation**
   - Verifies all required files for a preset are present
   - Reports missing files with clear error messages

2. **Size Validation**
   - Compares actual file sizes against expected sizes
   - Uses ±2% tolerance for size variations
   - Supports size specifications in GB, MB, KB, and bytes

3. **Integrity Verification**
   - SHA256 checksum validation where available
   - File header validation for corruption detection
   - Readability and permission checks

4. **Usability Verification**
   - File permission validation
   - Empty file detection
   - File extension validation for model formats

5. **Structure Validation**
   - Verifies correct directory layout
   - Ensures model files are in expected locations

### Auto-Fix Capabilities

The validator can attempt to fix common issues:
- **Permission Issues**: Automatically fixes read permission problems
- **Empty Files**: Detects and reports zero-byte files

## Usage

### Basic Commands

```bash
# Validate a specific preset
python scripts/model_validator.py --preset SD1_5_TEXT_TO_IMAGE_BASIC

# Validate all presets
python scripts/model_validator.py --all

# Validate presets in a specific category
python scripts/model_validator.py --all --category "Video Generation"

# Output in JSON format
python scripts/model_validator.py --preset WAN_2_2_T2V_BASIC --json

# Verbose output with detailed file information
python scripts/model_validator.py --preset FLUX_SCHNELL_BASIC --verbose

# Attempt to fix issues automatically
python scripts/model_validator.py --preset SD1_5_TEXT_TO_IMAGE_BASIC --fix

# Save report to file
python scripts/model_validator.py --all --output validation_report.json
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--preset PRESET` | Validate a specific preset by ID |
| `--all` | Validate all presets |
| `--category CATEGORY` | Filter presets by category |
| `--models-dir PATH` | Specify models directory path |
| `--json` | Output in JSON format |
| `--verbose, -v` | Enable detailed output |
| `--fix` | Attempt to fix fixable issues |
| `--output, -o PATH` | Save report to file |

## Exit Codes

- **0**: All validations passed (or no issues found)
- **1**: Validation failed or issues detected
- **130**: Interrupted by user (Ctrl+C)

## Output Formats

### Console Output (Default)

Color-coded terminal output with status indicators:
- ✓ Green checkmark for valid items
- ✗ Red X for invalid items
- ⚠ Yellow warning for potential issues

Example:
```
✓ SD1.5 Text to Image Basic (SD1_5_TEXT_TO_IMAGE_BASIC)
Status: VALID
Files: 2 total, 0 missing, 0 corrupted, 0 size mismatches

Detailed File Information:
  ✓ checkpoints/v1-5-pruned-emaonly-fp16.safetensors
    Size: 4.27GB
    ✓ SHA256 verified
  ✓ text_encoders/clip_l.safetensors
    Size: 1.7GB
```

### JSON Output

Structured JSON format for programmatic processing:

```json
{
  "preset_id": "SD1_5_TEXT_TO_IMAGE_BASIC",
  "preset_name": "SD1.5 Text to Image Basic",
  "category": "Image Generation",
  "valid": true,
  "files": [
    {
      "path": "checkpoints/v1-5-pruned-emaonly-fp16.safetensors",
      "expected_size": "4.27GB",
      "valid": true,
      "actual_size": 4586721280,
      "actual_size_mb": 4374.47,
      "actual_size_gb": 4.27,
      "sha256_verified": true
    }
  ],
  "missing": [],
  "corrupted": [],
  "size_mismatch": [],
  "validated_at": "2026-02-15T20:52:28.700632+00:00"
}
```

## Integration Examples

### With Download System

```bash
# Download preset and validate immediately
python scripts/unified_preset_downloader.py download --preset WAN_2_2_T2V_BASIC
python scripts/model_validator.py --preset WAN_2_2_T2V_BASIC
```

### CI/CD Integration

```bash
# Validate all models in production environment
python scripts/model_validator.py --all --json --output validation_report.json
if [ $? -ne 0 ]; then
    echo "Model validation failed - check validation_report.json"
    exit 1
fi
```

### Monitoring Integration

```bash
# Regular validation checks via cron
0 */6 * * * cd /path/to/ComfyUI-docker && python scripts/model_validator.py --all --json --output /var/log/model_validation.json
```

## API Usage

The validator can also be used as a Python module:

```python
from scripts.model_validator import ModelValidator, ValidationReporter

# Initialize validator
validator = ModelValidator(models_dir="/workspace/ComfyUI/models")

# Validate specific preset
report = validator.validate_preset("SD1_5_TEXT_TO_IMAGE_BASIC")

# Generate reports
reporter = ValidationReporter(validator)
console_output = reporter.generate_console_report(report, verbose=True)
json_output = reporter.generate_json_report(report)

# Validate all presets
results = validator.validate_all_presets(category="Video Generation")
summary = validator.get_summary()
```

## Validation Categories

The validator supports the same categories as the preset system:

1. **Video Generation** - T2V, I2V, S2V models
2. **Image Generation** - SDXL, FLUX, Qwen models
3. **Audio Generation** - MusicGen, Bark, TTS models

## Error Handling

The validator handles various error scenarios:

- **Missing Configuration**: Falls back to minimal preset configuration
- **Permission Issues**: Attempts automatic fixes or provides clear error messages
- **Corrupted Files**: Detects and reports file corruption
- **Network Issues**: Graceful degradation when remote checks fail

## Performance Considerations

- **SHA256 Calculation**: Can be slow for large models (8GB+) - only performed when checksums are available
- **File Access**: Uses efficient directory scanning for large model collections
- **Memory Usage**: Minimal - streams file operations for large files

## Troubleshooting

### Permission Denied Errors

```bash
# Run with automatic fixing
python scripts/model_validator.py --preset PRESET_ID --fix
```

### Missing Preset Configuration

Ensure `config/presets.yaml` exists and contains the preset definition.

### Large File Performance

For validation of many large files, consider using category filtering:
```bash
python scripts/model_validator.py --all --category "Video Generation"
```

## Future Enhancements

Planned improvements:
- [ ] Model format validation (safetensors structure checking)
- [ ] Metadata extraction from model files
- [ ] Cross-reference with download system for re-download capability
- [ ] Integration with preset manager web UI
- [ ] Historical validation tracking and trending

## See Also

- [Preset Manager Documentation](./preset-manager.md)
- [Unified Preset Downloader](./unified-preset-downloader.md)
- [ComfyUI Documentation](https://docs.comfy.org/)
