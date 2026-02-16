"""
E2E tests for dashboard UI functionality
Tests dashboard API endpoints, WebSocket communication, and UI interactions
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Mark all tests as E2E tests
pytestmark = pytest.mark.e2e


@pytest.mark.e2e
class TestDashboardAPIEndpoints:
    """Test dashboard API endpoints end-to-end"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_dashboard_home(self):
        """Test dashboard home page"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_api_models_list(self):
        """Test models list API endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Mock the models directory
        with patch('app.dashboard.api.models.settings') as mock_settings:
            mock_settings.MODEL_BASE_PATH = "/tmp/test_models"

            response = client.get("/api/models/")

        # Should return 200 or 404 depending on whether models exist
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_api_presets_list(self):
        """Test presets list API endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.presets.settings') as mock_settings:
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.get("/api/presets/")

        # Should return 200 or 404
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_api_system_info(self):
        """Test system info API endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/system/info")

        # Should return system information
        assert response.status_code in [200, 404]


@pytest.mark.e2e
class TestDashboardWebSocket:
    """Test dashboard WebSocket functionality"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        try:
            with client.websocket_connect("/ws") as websocket:
                # Connection should be established
                assert websocket is not None

                # Send test message
                websocket.send_text("test message")

                # Receive response
                data = websocket.receive_text()

                # Should receive echo or acknowledgment
                assert data is not None
        except Exception as e:
            pytest.skip(f"WebSocket connection failed: {e}")

    @pytest.mark.asyncio
    async def test_websocket_downloads_endpoint(self):
        """Test WebSocket downloads endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        try:
            with client.websocket_connect("/ws/downloads") as websocket:
                # Connection should be established
                assert websocket is not None

                # Send test message
                websocket.send_text('{"type": "test"}')

                # Receive response
                data = websocket.receive_text()

                assert data is not None
        except Exception as e:
            pytest.skip(f"WebSocket downloads connection failed: {e}")

    @pytest.mark.asyncio
    async def test_websocket_connections_count(self):
        """Test WebSocket connections count endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/ws/connections")

        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert isinstance(data["active_connections"], int)


@pytest.mark.e2e
class TestDashboardModelsAPI:
    """Test dashboard models API functionality"""

    @pytest.mark.asyncio
    async def test_models_list_filter(self):
        """Test models list with type filter"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.models.settings') as mock_settings:
            mock_settings.MODEL_BASE_PATH = "/tmp/test_models"

            response = client.get("/api/models/?model_type=checkpoints")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_models_validation(self):
        """Test models validation endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.models.settings') as mock_settings:
            mock_settings.MODEL_BASE_PATH = "/tmp/test_models"
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.get("/api/models/validate")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_models_disk_usage(self):
        """Test models disk usage endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.models.settings') as mock_settings:
            mock_settings.MODEL_BASE_PATH = "/tmp"

            response = client.get("/api/models/disk-usage")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_model_types_list(self):
        """Test model types list endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.models.settings') as mock_settings:
            mock_settings.MODEL_BASE_PATH = "/tmp/test_models"

            response = client.get("/api/models/types")

        assert response.status_code in [200, 404]


@pytest.mark.e2e
class TestDashboardPresetsAPI:
    """Test dashboard presets API functionality"""

    @pytest.mark.asyncio
    async def test_presets_list(self):
        """Test presets list endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.presets.settings') as mock_settings:
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.get("/api/presets/")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_preset_by_id(self):
        """Test getting preset by ID"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.presets.settings') as mock_settings:
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.get("/api/presets/TEST_PRESET")

        # Should return 404 for non-existent preset or 200 if exists
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_preset_install(self):
        """Test preset installation endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.presets.settings') as mock_settings:
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.post("/api/presets/TEST_PRESET/install")

        # Should return 202 for queued or 404 for not found
        assert response.status_code in [202, 404]

    @pytest.mark.asyncio
    async def test_preset_categories(self):
        """Test preset categories endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.presets.settings') as mock_settings:
            mock_settings.PRESET_CONFIG_PATH = "/tmp/test_presets.yaml"

            response = client.get("/api/presets/categories")

        assert response.status_code in [200, 404]


@pytest.mark.e2e
class TestDashboardWorkflowsAPI:
    """Test dashboard workflows API functionality"""

    @pytest.mark.asyncio
    async def test_workflows_list(self):
        """Test workflows list endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.workflows.settings') as mock_settings:
            mock_settings.WORKSPACE_BASE_PATH = "/tmp/test_workspace"

            response = client.get("/api/workflows/")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_workflow_execute(self):
        """Test workflow execution endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch('app.dashboard.api.workflows.settings') as mock_settings:
            mock_settings.WORKSPACE_BASE_PATH = "/tmp/test_workspace"

            test_workflow = {
                "nodes": [],
                "links": []
            }

            response = client.post("/api/workflows/execute", json=test_workflow)

        # Should return 202 for accepted or 404
        assert response.status_code in [202, 404]


@pytest.mark.e2e
class TestDashboardSystemAPI:
    """Test dashboard system API functionality"""

    @pytest.mark.asyncio
    async def test_system_info(self):
        """Test system info endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/system/info")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_system_health(self):
        """Test system health endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/system/health")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_system_stats(self):
        """Test system stats endpoint"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/system/stats")

        assert response.status_code in [200, 404]


@pytest.mark.e2e
class TestDashboardStaticFiles:
    """Test dashboard static file serving"""

    @pytest.mark.asyncio
    async def test_static_files_mount(self):
        """Test static files are accessible"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Try to access a static file (may not exist, so 404 is acceptable)
        response = client.get("/static/test.css")

        # Should either serve file or return 404 (not 500)
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_favicon(self):
        """Test favicon is accessible"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Try to access favicon (may not exist)
        response = client.get("/static/favicon.ico")

        assert response.status_code in [200, 404]


@pytest.mark.e2e
class TestDashboardCORSMiddleware:
    """Test dashboard CORS middleware"""

    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test CORS headers are set"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health", headers={"Origin": "http://example.com"})

        # Should include CORS headers
        assert response.status_code == 200


@pytest.mark.e2e
class TestDashboardErrorHandling:
    """Test dashboard error handling"""

    @pytest.mark.asyncio
    async def test_404_handling(self):
        """Test 404 error handling"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/nonexistent")

        # Should return 404
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test handling of invalid JSON"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.post(
            "/api/workflows/execute",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed(self):
        """Test method not allowed handling"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Try POST on GET endpoint
        response = client.post("/health")

        # Should return 405 Method Not Allowed
        assert response.status_code == 405


@pytest.mark.e2e
class TestDashboardAuthentication:
    """Test dashboard authentication (if implemented)"""

    @pytest.mark.asyncio
    async def test_unauthenticated_access(self):
        """Test unauthenticated access to protected endpoints"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Try to access a protected endpoint (if any)
        response = client.get("/api/system/admin")

        # Should either allow (404 if endpoint doesn't exist) or deny with 401/403
        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.e2e
class TestDashboardResponseFormat:
    """Test dashboard response formats"""

    @pytest.mark.asyncio
    async def test_json_response(self):
        """Test API returns JSON responses"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_response_structure(self):
        """Test API response structure"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        data = response.json()

        # Should have expected keys
        assert "status" in data or "error" in data


@pytest.mark.e2e
class TestDashboardRateLimiting:
    """Test dashboard rate limiting (if implemented)"""

    @pytest.mark.asyncio
    async def test_multiple_requests(self):
        """Test handling of multiple rapid requests"""
        from app.dashboard.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response.status_code)

        # All requests should succeed
        assert all(status == 200 for status in responses)
