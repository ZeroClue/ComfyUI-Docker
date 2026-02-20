"""
System status and health check API endpoints
Handles system monitoring, resource usage, and service status
"""

from typing import Dict, List, Optional
from pathlib import Path
import shutil
import sys
import psutil
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.config import settings
from ..core.comfyui_client import ComfyUIClient


# Request/Response Models
class SystemStatusResponse(BaseModel):
    """Response for system status endpoint"""
    status: str
    timestamp: str
    services: Dict[str, Dict]
    system: Dict
    errors: List[str]


class ServiceStatus(BaseModel):
    """Individual service status"""
    name: str
    status: str
    url: str
    response_time: Optional[float] = None
    error: Optional[str] = None


class ResourceUsage(BaseModel):
    """System resource usage information"""
    cpu_percent: float
    memory: Dict
    disk: Dict
    gpu: Optional[Dict] = None


# Initialize router and dependencies
router = APIRouter()
comfyui_client = ComfyUIClient(base_url=f"http://localhost:{settings.COMFYUI_PORT}")


async def check_service_health(name: str, url: str) -> ServiceStatus:
    """Check health of a specific service"""
    import time
    import aiohttp

    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    return ServiceStatus(
                        name=name,
                        status="healthy",
                        url=url,
                        response_time=response_time
                    )
                else:
                    return ServiceStatus(
                        name=name,
                        status="unhealthy",
                        url=url,
                        response_time=response_time,
                        error=f"HTTP {response.status}"
                    )
    except Exception as e:
        return ServiceStatus(
            name=name,
            status="down",
            url=url,
            error=str(e)
        )


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Get overall system status including all services"""
    services = {}
    errors = []

    # Check ComfyUI service
    comfyui_status = await check_service_health(
        "ComfyUI",
        f"http://localhost:{settings.COMFYUI_PORT}/system_stats"
    )
    services["comfyui"] = comfyui_status.dict()

    # Check Dashboard service
    dashboard_status = ServiceStatus(
        name="Dashboard",
        status="healthy",
        url=f"http://localhost:{settings.DASHBOARD_PORT}"
    )
    services["dashboard"] = dashboard_status.dict()

    # Get system resource usage
    system_info = get_system_info()

    # Determine overall status
    overall_status = "healthy"
    for service_data in services.values():
        if service_data["status"] in ["down", "unhealthy"]:
            overall_status = "degraded"
            errors.append(f"{service_data['name']}: {service_data.get('error', 'Unknown error')}")

    return SystemStatusResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services=services,
        system=system_info,
        errors=errors
    )


@router.get("/resources")
async def get_resource_usage() -> ResourceUsage:
    """Get detailed system resource usage"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory usage
    memory = psutil.virtual_memory()
    memory_info = {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "percent": memory.percent
    }

    # Disk usage - prefer /workspace (network volume) if available
    workspace_path = '/workspace'
    if Path(workspace_path).exists():
        disk = psutil.disk_usage(workspace_path)
    else:
        disk = psutil.disk_usage('/')
    disk_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
        "path": workspace_path if Path(workspace_path).exists() else '/'
    }

    # GPU information (if available)
    gpu_info = None
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            gpu_info = {"devices": []}
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 4:
                        gpu_info["devices"].append({
                            "name": parts[0],
                            "memory_used": int(parts[1]),
                            "memory_total": int(parts[2]),
                            "utilization": int(parts[3])
                        })
    except Exception:
        pass

    return ResourceUsage(
        cpu_percent=cpu_percent,
        memory=memory_info,
        disk=disk_info,
        gpu=gpu_info
    )


@router.get("/logs")
async def get_system_logs(
    service: str = "all",
    lines: int = 100
) -> Dict:
    """
    Get system logs from various services

    - **service**: Filter logs by service (comfyui, dashboard, all)
    - **lines**: Number of log lines to return
    """
    logs = {}

    if service in ["all", "comfyui"]:
        # Get ComfyUI logs if available
        comfyui_log_path = "/workspace/logs/comfyui.log"
        try:
            with open(comfyui_log_path, 'r') as f:
                comfyui_logs = f.readlines()[-lines:]
                logs["comfyui"] = [line.strip() for line in comfyui_logs]
        except Exception:
            logs["comfyui"] = ["Log file not available"]

    if service in ["all", "dashboard"]:
        # Get dashboard logs if available
        dashboard_log_path = "/workspace/logs/dashboard.log"
        try:
            with open(dashboard_log_path, 'r') as f:
                dashboard_logs = f.readlines()[-lines:]
                logs["dashboard"] = [line.strip() for line in dashboard_logs]
        except Exception:
            logs["dashboard"] = ["Log file not available"]

    return {"service": service, "lines": lines, "logs": logs}


@router.post("/restart")
async def restart_service(service: str):
    """
    Restart a specific service

    - **service**: Service to restart (comfyui, dashboard)
    """
    if service not in ["comfyui", "dashboard"]:
        raise HTTPException(status_code=400, detail="Invalid service name")

    # This would integrate with your service orchestration
    # For now, return a placeholder response
    return {
        "status": "not_implemented",
        "message": f"Service restart for {service} not yet implemented",
        "service": service
    }


@router.get("/config")
async def get_system_config():
    """Get current system configuration"""
    return {
        "model_base_path": settings.MODEL_BASE_PATH,
        "comfyui_port": settings.COMFYUI_PORT,
        "dashboard_port": settings.DASHBOARD_PORT,
        "preset_config_path": settings.PRESET_CONFIG_PATH,
        "workflow_base_path": settings.WORKFLOW_BASE_PATH
    }


@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard statistics for the home page"""
    from pathlib import Path
    import yaml

    # Count models installed
    model_base = Path(settings.MODEL_BASE_PATH)
    models_installed = 0
    if model_base.exists():
        for model_dir in model_base.iterdir():
            if model_dir.is_dir() and not model_dir.name.startswith('.'):
                models_installed += len(list(model_dir.glob('*.safetensors'))) + \
                                   len(list(model_dir.glob('*.ckpt'))) + \
                                   len(list(model_dir.glob('*.pt')))

    # Count workflows
    workflow_base = Path(settings.WORKFLOW_BASE_PATH)
    active_workflows = 0
    if workflow_base.exists():
        active_workflows = len(list(workflow_base.glob('*.json')))

    # Get storage used
    storage_used = "0 GB"
    try:
        if model_base.exists():
            total_size = sum(f.stat().st_size for f in model_base.rglob('*') if f.is_file())
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if total_size < 1024.0:
                    storage_used = f"{total_size:.1f} {unit}"
                    break
                total_size /= 1024.0
    except Exception:
        pass

    # Get generations from ComfyUI history
    total_generations = 0
    try:
        history = await comfyui_client.get_history()
        total_generations = len(history)
    except Exception:
        pass

    return {
        "totalGenerations": total_generations,
        "modelsInstalled": models_installed,
        "storageUsed": storage_used,
        "activeWorkflows": active_workflows
    }


def get_system_info() -> Dict:
    """Get basic system information"""
    uname_result = psutil.os.uname()
    return {
        "hostname": uname_result.nodename,
        "platform": uname_result.sysname,
        "release": uname_result.release,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "uptime": get_uptime()
    }


def get_uptime() -> str:
    """Get system uptime in human readable format"""
    boot_time = psutil.boot_time()
    uptime_seconds = psutil.time.time() - boot_time

    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    return f"{days}d {hours}h {minutes}m"
