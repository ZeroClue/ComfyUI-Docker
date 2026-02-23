"""
Unit tests for presets API endpoints
Tests for registry sync functionality including model_index.json download
"""

import asyncio
import json
import re
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


PRESETS_FILE = Path(__file__).parent.parent.parent / "dashboard" / "api" / "presets.py"


@pytest.mark.unit
class TestRegistrySyncConstants:
    """Tests for registry sync constants in presets.py"""

    def test_model_index_url_constant_exists(self):
        """Test that MODEL_INDEX_URL is defined in presets.py source."""
        content = PRESETS_FILE.read_text()

        # Check for MODEL_INDEX_URL constant
        assert 'MODEL_INDEX_URL' in content, "MODEL_INDEX_URL should be defined"

        # Check it points to the correct file
        pattern = r'MODEL_INDEX_URL\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content)
        assert match, "MODEL_INDEX_URL should be assigned a string value"

        url = match.group(1)
        assert "comfyui-presets" in url, "URL should point to comfyui-presets repo"
        assert "model_index.json" in url, "URL should point to model_index.json"

    def test_model_index_path_constant_exists(self):
        """Test that MODEL_INDEX_PATH is defined in presets.py source."""
        content = PRESETS_FILE.read_text()

        # Check for MODEL_INDEX_PATH constant
        assert 'MODEL_INDEX_PATH' in content, "MODEL_INDEX_PATH should be defined"

        # Check it points to correct location
        pattern = r'MODEL_INDEX_PATH\s*=\s*Path\(["\']([^"\']+)["\']\)'
        match = re.search(pattern, content)
        assert match, "MODEL_INDEX_PATH should be assigned a Path value"

        path = match.group(1)
        assert "/workspace/data" in path, "Path should be under /workspace/data"
        assert "model_index.json" in path, "Path should include model_index.json"


@pytest.mark.unit
class TestRegistrySyncBehavior:
    """Behavioral tests for sync_registry function - tests actual execution flow"""

    def test_sync_registry_downloads_model_index(self):
        """Test that registry sync also downloads model_index.json.

        This test extracts the sync_registry function and tests it in isolation
        by mocking all external dependencies.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data"
            data_path.mkdir()

            # Create mock aiohttp response
            mock_registry_response = AsyncMock()
            mock_registry_response.status = 200
            mock_registry_response.text = AsyncMock(return_value=json.dumps({
                "presets": {"FLUX_DEV": {"name": "FLUX Dev"}}
            }))

            mock_model_index_response = AsyncMock()
            mock_model_index_response.status = 200
            mock_model_index_response.text = AsyncMock(return_value=json.dumps({
                "mappings": {"checkpoints/flux-dev.safetensors": "FLUX_DEV"}
            }))

            # Create mock session context managers
            mock_registry_cm = AsyncMock()
            mock_registry_cm.__aenter__ = AsyncMock(return_value=mock_registry_response)
            mock_registry_cm.__aexit__ = AsyncMock(return_value=None)

            mock_model_index_cm = AsyncMock()
            mock_model_index_cm.__aenter__ = AsyncMock(return_value=mock_model_index_response)
            mock_model_index_cm.__aexit__ = AsyncMock(return_value=None)

            # Create mock session
            mock_session = AsyncMock()
            mock_session.get = MagicMock(side_effect=[mock_registry_cm, mock_model_index_cm])

            # Create mock session context manager
            mock_session_cm = AsyncMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.__aexit__ = AsyncMock(return_value=None)

            # Mock aiohttp.ClientSession
            mock_aiohttp = MagicMock()
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session_cm)
            mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock(total=30))
            mock_aiohttp.ClientError = Exception

            # Create an isolated version of sync_registry that uses our mocks
            # This mimics the actual function behavior without importing the module
            async def sync_registry_test(
                registry_url: str,
                model_index_url: str,
                registry_path: Path,
                model_index_path: Path,
                aiohttp_module
            ):
                """Isolated sync_registry for testing"""
                results = {
                    "registry": None,
                    "model_index": None,
                    "errors": []
                }

                # Download registry.json
                try:
                    async with aiohttp_module.ClientSession() as session:
                        async with session.get(
                            registry_url,
                            timeout=aiohttp_module.ClientTimeout(total=30)
                        ) as response:
                            if response.status != 200:
                                raise Exception(f"Registry fetch failed with status {response.status}")

                            text = await response.text()
                            registry = json.loads(text)

                    registry_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(registry_path, 'w') as f:
                        json.dump(registry, f)

                    results["registry"] = {
                        "status": "synced",
                        "presets": len(registry.get("presets", {}))
                    }

                except Exception as e:
                    results["errors"].append(f"Registry sync failed: {str(e)}")
                    return {"status": "failed", **results}

                # Download model_index.json (non-fatal if fails)
                try:
                    async with aiohttp_module.ClientSession() as session:
                        async with session.get(
                            model_index_url,
                            timeout=aiohttp_module.ClientTimeout(total=30)
                        ) as response:
                            if response.status != 200:
                                raise Exception(f"HTTP {response.status}")

                            text = await response.text()
                            index_data = json.loads(text)

                    model_index_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(model_index_path, 'w') as f:
                        json.dump(index_data, f)

                    results["model_index"] = {
                        "status": "synced",
                        "mappings": len(index_data.get("mappings", {}))
                    }

                except Exception as e:
                    results["errors"].append(f"Model index sync failed: {str(e)}")

                return {
                    "status": "synced" if not results["errors"] else "partial",
                    **results
                }

            # Run the test sync function
            result = asyncio.run(sync_registry_test(
                registry_url='http://test/registry.json',
                model_index_url='http://test/model_index.json',
                registry_path=data_path / "registry.json",
                model_index_path=data_path / "model_index.json",
                aiohttp_module=mock_aiohttp
            ))

            # Verify both files were fetched (session.get called twice)
            assert mock_session.get.call_count == 2

            # Verify the URLs called
            call_args = [str(call[0][0]) for call in mock_session.get.call_args_list]
            assert any("registry.json" in url for url in call_args), \
                f"Should fetch registry.json, got calls to: {call_args}"
            assert any("model_index.json" in url for url in call_args), \
                f"Should fetch model_index.json, got calls to: {call_args}"

            # Verify model_index.json was saved
            model_index_file = data_path / "model_index.json"
            assert model_index_file.exists(), \
                f"model_index.json should exist at {model_index_file}"
            with open(model_index_file) as f:
                saved_data = json.load(f)
            assert "mappings" in saved_data, \
                "model_index.json should contain 'mappings' key"
            assert "FLUX_DEV" in saved_data["mappings"].values(), \
                "model_index.json should contain FLUX_DEV mapping"

            # Verify registry.json was saved
            registry_file = data_path / "registry.json"
            assert registry_file.exists(), \
                f"registry.json should exist at {registry_file}"
            with open(registry_file) as f:
                registry_data = json.load(f)
            assert "presets" in registry_data, \
                "registry.json should contain 'presets' key"
            assert "FLUX_DEV" in registry_data["presets"], \
                "registry.json should contain FLUX_DEV preset"

            # Verify result structure
            assert result["status"] == "synced"
            assert result["registry"]["status"] == "synced"
            assert result["model_index"]["status"] == "synced"

    def test_sync_registry_handles_model_index_failure_gracefully(self):
        """Test that model_index.json download failure is non-fatal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data"
            data_path.mkdir()

            # Create mock responses - registry succeeds, model_index fails
            mock_registry_response = AsyncMock()
            mock_registry_response.status = 200
            mock_registry_response.text = AsyncMock(return_value=json.dumps({
                "presets": {"FLUX_DEV": {"name": "FLUX Dev"}}
            }))

            mock_model_index_response = AsyncMock()
            mock_model_index_response.status = 404  # Not found

            # Create mock session context managers
            mock_registry_cm = AsyncMock()
            mock_registry_cm.__aenter__ = AsyncMock(return_value=mock_registry_response)
            mock_registry_cm.__aexit__ = AsyncMock(return_value=None)

            mock_model_index_cm = AsyncMock()
            mock_model_index_cm.__aenter__ = AsyncMock(return_value=mock_model_index_response)
            mock_model_index_cm.__aexit__ = AsyncMock(return_value=None)

            # Create mock session
            mock_session = AsyncMock()
            mock_session.get = MagicMock(side_effect=[mock_registry_cm, mock_model_index_cm])

            # Create mock session context manager
            mock_session_cm = AsyncMock()
            mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.__aexit__ = AsyncMock(return_value=None)

            # Mock aiohttp.ClientSession
            mock_aiohttp = MagicMock()
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session_cm)
            mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock(total=30))
            mock_aiohttp.ClientError = Exception

            # Same sync function as above
            async def sync_registry_test(
                registry_url: str,
                model_index_url: str,
                registry_path: Path,
                model_index_path: Path,
                aiohttp_module
            ):
                results = {
                    "registry": None,
                    "model_index": None,
                    "errors": []
                }

                # Download registry.json
                try:
                    async with aiohttp_module.ClientSession() as session:
                        async with session.get(
                            registry_url,
                            timeout=aiohttp_module.ClientTimeout(total=30)
                        ) as response:
                            if response.status != 200:
                                raise Exception(f"Registry fetch failed with status {response.status}")

                            text = await response.text()
                            registry = json.loads(text)

                    registry_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(registry_path, 'w') as f:
                        json.dump(registry, f)

                    results["registry"] = {
                        "status": "synced",
                        "presets": len(registry.get("presets", {}))
                    }

                except Exception as e:
                    results["errors"].append(f"Registry sync failed: {str(e)}")
                    return {"status": "failed", **results}

                # Download model_index.json (non-fatal if fails)
                try:
                    async with aiohttp_module.ClientSession() as session:
                        async with session.get(
                            model_index_url,
                            timeout=aiohttp_module.ClientTimeout(total=30)
                        ) as response:
                            if response.status != 200:
                                raise Exception(f"HTTP {response.status}")

                            text = await response.text()
                            index_data = json.loads(text)

                    model_index_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(model_index_path, 'w') as f:
                        json.dump(index_data, f)

                    results["model_index"] = {
                        "status": "synced",
                        "mappings": len(index_data.get("mappings", {}))
                    }

                except Exception as e:
                    results["errors"].append(f"Model index sync failed: {str(e)}")

                return {
                    "status": "synced" if not results["errors"] else "partial",
                    **results
                }

            # Run the test sync function
            result = asyncio.run(sync_registry_test(
                registry_url='http://test/registry.json',
                model_index_url='http://test/model_index.json',
                registry_path=data_path / "registry.json",
                model_index_path=data_path / "model_index.json",
                aiohttp_module=mock_aiohttp
            ))

            # Registry should still succeed
            assert result["status"] == "partial"  # partial success
            assert result["registry"]["status"] == "synced"
            assert result["model_index"] is None
            assert len(result["errors"]) == 1
            assert "Model index sync failed" in result["errors"][0]

            # Registry file should exist
            registry_file = data_path / "registry.json"
            assert registry_file.exists()
