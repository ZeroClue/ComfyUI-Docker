"""
Unit tests for configuration generator script
Tests the extra_model_paths.yaml creation and configuration management
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from generate_extra_model_paths import (
        ConfigGenerator,
        parse_environment_vars,
        validate_config,
        merge_configs
    )
except ImportError:
    # Fallback for testing without actual module
    pytest.skip("Config generator module not found", allow_module_level=True)


@pytest.mark.unit
class TestConfigGenerator:
    """Test ConfigGenerator class functionality"""

    def test_initialization(self, temp_dir):
        """Test ConfigGenerator initialization"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        assert generator.workspace_path == temp_dir
        assert generator.config_path == temp_dir / "config.yaml"
        assert generator.config == {}

    def test_generate_basic_config(self, temp_dir):
        """Test basic configuration generation"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        config = generator.generate()

        assert config is not None
        assert 'comfyui' in config
        assert 'models' in config['comfyui']

    def test_generate_with_custom_paths(self, temp_dir):
        """Test configuration generation with custom model paths"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        custom_paths = {
            'checkpoints': '/custom/models/checkpoints',
            'vae': '/custom/models/vae'
        }

        config = generator.generate(custom_paths=custom_paths)

        assert config['comfyui']['models']['checkpoints'] == '/custom/models/checkpoints'
        assert config['comfyui']['models']['vae'] == '/custom/models/vae'

    def test_save_config(self, temp_dir):
        """Test saving configuration to file"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        config = generator.generate()
        output_path = temp_dir / "extra_model_paths.yaml"

        generator.save(config, output_path)

        assert output_path.exists()

        # Verify the saved file can be loaded
        with open(output_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config == config

    def test_save_config_with_backup(self, temp_dir):
        """Test that existing config files are backed up"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        output_path = temp_dir / "extra_model_paths.yaml"

        # Create initial config
        config1 = generator.generate()
        generator.save(config1, output_path)

        # Modify and save again
        config2 = generator.generate()
        generator.save(config2, output_path)

        # Check for backup
        backup_files = list(temp_dir.glob("extra_model_paths.yaml.backup*"))
        assert len(backup_files) >= 1

    def test_validate_valid_config(self, temp_dir):
        """Test validation of valid configuration"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        config = generator.generate()
        is_valid, errors = validate_config(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_config_missing_key(self, temp_dir):
        """Test validation fails with missing required keys"""
        config = {'invalid': 'config'}

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert len(errors) > 0
        assert any('comfyui' in error for error in errors)

    def test_validate_invalid_config_wrong_type(self, temp_dir):
        """Test validation fails with wrong data types"""
        config = {
            'comfyui': "should be a dict not string"
        }

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert len(errors) > 0


@pytest.mark.unit
class TestEnvironmentVariableParsing:
    """Test environment variable parsing functionality"""

    def test_parse_empty_vars(self):
        """Test parsing with no environment variables"""
        result = parse_environment_vars({})

        assert result == {}

    def test_parse_model_path_vars(self):
        """Test parsing model path environment variables"""
        env_vars = {
            'MODEL_PATH_CHECKPOINTS': '/custom/checkpoints',
            'MODEL_PATH_VAE': '/custom/vae'
        }

        result = parse_environment_vars(env_vars)

        assert 'checkpoints' in result
        assert result['checkpoints'] == '/custom/checkpoints'
        assert result['vae'] == '/custom/vae'

    def test_parse_workspace_path(self):
        """Test parsing workspace path from environment"""
        env_vars = {
            'WORKSPACE_PATH': '/custom/workspace'
        }

        result = parse_environment_vars(env_vars)

        assert 'workspace' in result
        assert result['workspace'] == '/custom/workspace'

    def test_ignore_unknown_vars(self):
        """Test that unknown environment variables are ignored"""
        env_vars = {
            'UNKNOWN_VAR': 'value',
            'ANOTHER_UNKNOWN': 'another_value'
        }

        result = parse_environment_vars(env_vars)

        assert len(result) == 0

    def test_parse_mixed_vars(self):
        """Test parsing mix of valid and invalid variables"""
        env_vars = {
            'MODEL_PATH_CHECKPOINTS': '/custom/checkpoints',
            'UNKNOWN_VAR': 'value',
            'WORKSPACE_PATH': '/workspace',
            'RANDOM_VAR': 'random'
        }

        result = parse_environment_vars(env_vars)

        assert len(result) == 2  # Only 2 valid vars
        assert result['checkpoints'] == '/custom/checkpoints'
        assert result['workspace'] == '/workspace'


@pytest.mark.unit
class TestConfigMerge:
    """Test configuration merge functionality"""

    def test_merge_empty_configs(self):
        """Test merging empty configurations"""
        base = {}
        override = {}

        result = merge_configs(base, override)

        assert result == {}

    def test_merge_simple_override(self):
        """Test simple key override"""
        base = {'key1': 'value1'}
        override = {'key1': 'new_value'}

        result = merge_configs(base, override)

        assert result['key1'] == 'new_value'

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries"""
        base = {
            'models': {
                'checkpoints': '/base/checkpoints',
                'vae': '/base/vae'
            }
        }
        override = {
            'models': {
                'checkpoints': '/override/checkpoints'
            }
        }

        result = merge_configs(base, override)

        assert result['models']['checkpoints'] == '/override/checkpoints'
        assert result['models']['vae'] == '/base/vae'  # Should preserve base value

    def test_merge_new_keys(self):
        """Test that new keys are added"""
        base = {'key1': 'value1'}
        override = {'key2': 'value2'}

        result = merge_configs(base, override)

        assert result['key1'] == 'value1'
        assert result['key2'] == 'value2'

    def test_merge_preserves_base(self):
        """Test that base config is not modified"""
        base = {'key1': 'value1'}
        override = {'key1': 'new_value'}

        original_base = base.copy()
        merge_configs(base, override)

        assert base == original_base  # Base should be unchanged


@pytest.mark.unit
class TestConfigFileHandling:
    """Test configuration file reading and writing"""

    def test_read_existing_config(self, temp_dir, sample_preset_file):
        """Test reading existing configuration file"""
        config_path = temp_dir / "test_config.yaml"

        with open(config_path, 'w') as f:
            yaml.dump({'test': 'config'}, f)

        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=config_path
        )

        config = generator.read_config()

        assert config == {'test': 'config'}

    def test_read_nonexistent_config(self, temp_dir):
        """Test reading non-existent configuration file"""
        config_path = temp_dir / "nonexistent.yaml"

        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=config_path
        )

        config = generator.read_config()

        assert config == {}

    def test_write_config_creates_directories(self, temp_dir):
        """Test that write creates parent directories"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        output_path = temp_dir / "subdir" / "nested" / "config.yaml"

        generator.save({'test': 'config'}, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_write_yaml_format(self, temp_dir):
        """Test that written YAML is properly formatted"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        config = generator.generate()
        output_path = temp_dir / "test.yaml"

        generator.save(config, output_path)

        # Verify file is valid YAML
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded == config

    def test_write_invalid_yaml_path(self, temp_dir):
        """Test writing to invalid path raises error"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        invalid_path = Path("/root/readonly/config.yaml")  # Likely unwritable

        with pytest.raises((IOError, OSError, PermissionError)):
            generator.save({'test': 'config'}, invalid_path)


@pytest.mark.unit
class TestConfigTemplates:
    """Test configuration template functionality"""

    def test_default_template(self, temp_dir):
        """Test default configuration template"""
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml"
        )

        config = generator.generate()

        # Verify expected keys exist
        assert 'comfyui' in config
        assert 'models' in config['comfyui']

        # Verify standard model paths
        expected_paths = [
            'checkpoints', 'vae', 'loras', 'text_encoders',
            'clip_vision', 'upscale_models'
        ]
        for path in expected_paths:
            assert path in config['comfyui']['models']

    def test_custom_template(self, temp_dir):
        """Test custom configuration template"""
        template_path = temp_dir / "custom_template.yaml"

        custom_template = {
            'custom': {
                'setting': 'value'
            }
        }

        with open(template_path, 'w') as f:
            yaml.dump(custom_template, f)

        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml",
            template_path=template_path
        )

        config = generator.generate()

        assert 'custom' in config
        assert config['custom']['setting'] == 'value'

    def test_merge_template_with_base(self, temp_dir):
        """Test merging template with base configuration"""
        template_path = temp_dir / "template.yaml"

        template = {
            'comfyui': {
                'models': {
                    'custom_models': '/custom/path'
                }
            }
        }

        with open(template_path, 'w') as f:
            yaml.dump(template, f)

        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=temp_dir / "config.yaml",
            template_path=template_path
        )

        config = generator.generate()

        # Should have both default and custom paths
        assert 'checkpoints' in config['comfyui']['models']
        assert 'custom_models' in config['comfyui']['models']
        assert config['comfyui']['models']['custom_models'] == '/custom/path'


@pytest.mark.unit
class TestConfigValidationErrors:
    """Test configuration validation error handling"""

    def test_invalid_yaml_syntax(self, temp_dir):
        """Test handling of invalid YAML syntax"""
        config_path = temp_dir / "invalid.yaml"

        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")

        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=config_path
        )

        with pytest.raises(yaml.YAMLError):
            generator.read_config()

    def test_missing_required_model_path(self, temp_dir):
        """Test validation when required model path is missing"""
        config = {
            'comfyui': {
                'models': {
                    # Missing 'checkpoints' which should be required
                    'vae': '/models/vae'
                }
            }
        }

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert any('checkpoints' in error.lower() for error in errors)

    def test_empty_model_paths(self, temp_dir):
        """Test validation when model paths are empty"""
        config = {
            'comfyui': {
                'models': {}  # Empty models dict
            }
        }

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert len(errors) > 0


@pytest.mark.unit
class TestConfigGeneratorCLI:
    """Test CLI interface for config generator"""

    def test_main_with_output_arg(self, temp_dir, capsys):
        """Test main function with output argument"""
        output_path = temp_dir / "output.yaml"

        with patch('sys.argv', ['generate_extra_model_paths.py', '-o', str(output_path)]):
            try:
                from generate_extra_model_paths import main
                main()
            except SystemExit:
                pass

        # Check if file was created
        assert output_path.exists()

    def test_main_with_backup_flag(self, temp_dir):
        """Test main function with backup flag"""
        output_path = temp_dir / "output.yaml"

        # Create existing config
        with open(output_path, 'w') as f:
            yaml.dump({'old': 'config'}, f)

        with patch('sys.argv', ['generate_extra_model_paths.py', '-o', str(output_path), '--backup']):
            try:
                from generate_extra_model_paths import main
                main()
            except SystemExit:
                pass

        # Check for backup
        backup_files = list(temp_dir.glob("*.backup*"))
        assert len(backup_files) >= 1

    def test_main_with_validate_flag(self, temp_dir):
        """Test main function with validate flag"""
        config_path = temp_dir / "config.yaml"

        # Create valid config
        generator = ConfigGenerator(
            workspace_path=temp_dir,
            config_path=config_path
        )
        config = generator.generate()
        generator.save(config, config_path)

        with patch('sys.argv', ['generate_extra_model_paths.py', '--validate', str(config_path)]):
            try:
                from generate_extra_model_paths import main
                main()
            except SystemExit as e:
                assert e.code == 0  # Should exit with 0 for valid config
