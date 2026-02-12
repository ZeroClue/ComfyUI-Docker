"""
Preset Manager Error Classes with User-Facing Messages

Provides structured error handling for the Preset Manager system.
Each error class includes actionable guidance for users.
"""


class PresetManagerError(Exception):
    """Base exception for Preset Manager errors"""

    def __init__(self, message: str, details: str = ""):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def to_dict(self):
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


class ScriptNotFoundError(PresetManagerError):
    """Raised when a required download script is not found"""

    def __init__(self, script_path: str):
        self.script_path = script_path
        message = f"Download script not found: {script_path}"
        details = (
            f"The required download script '{script_path}' is missing from your Docker image. "
            f"This may indicate an outdated or incomplete image.\n\n"
            f"Solutions:\n"
            f"1. Pull the latest image: docker pull zeroclue/comfyui:<tag>\n"
            f"2. Rebuild your Docker image from the latest source\n"
            f"3. Check the image is properly built: docker image inspect zeroclue/comfyui:<tag>\n\n"
            f"For more information, visit: https://github.com/zeroclue/comfyui-docker"
        )
        super().__init__(message, details)


class ComponentValidationError(PresetManagerError):
    """Raised when a required preset manager component is missing"""

    def __init__(self, component_name: str, component_path: str):
        self.component_name = component_name
        self.component_path = component_path
        message = f"Required component missing: {component_name}"
        details = (
            f"The preset manager component '{component_name}' is missing from '{component_path}'. "
            f"This prevents the Preset Manager web interface from functioning properly.\n\n"
            f"Solutions:\n"
            f"1. Pull the latest Docker image: docker pull zeroclue/comfyui:<tag>\n"
            f"2. Rebuild your Docker image from source\n"
            f"3. Verify the image was built successfully (check build logs)\n\n"
            f"For troubleshooting, visit: https://github.com/zeroclue/comfyui-docker/issues"
        )
        super().__init__(message, details)


class ImportFailureError(PresetManagerError):
    """Raised when a required Python import fails"""

    def __init__(self, module_name: str, import_error: str):
        self.module_name = module_name
        self.import_error = import_error
        message = f"Failed to import required module: {module_name}"
        details = (
            f"The Python module '{module_name}' could not be imported. "
            f"Error: {import_error}\n\n"
            f"This usually indicates a problem with the Docker image build or Python environment.\n\n"
            f"Solutions:\n"
            f"1. Pull the latest Docker image: docker pull zeroclue/comfyui:<tag>\n"
            f"2. Rebuild the image with fresh dependencies\n"
            f"3. Check the container logs: docker logs <container_id>\n"
            f"4. Verify Python dependencies are installed correctly\n\n"
            f"For build instructions, visit: https://github.com/zeroclue/comfyui-docker"
        )
        super().__init__(message, details)


class DownloadFailureError(PresetManagerError):
    """Raised when a preset download fails"""

    def __init__(self, preset_id: str, reason: str):
        self.preset_id = preset_id
        self.reason = reason
        message = f"Download failed for preset: {preset_id}"
        details = (
            f"The preset '{preset_id}' could not be downloaded. Reason: {reason}\n\n"
            f"Common causes:\n"
            f"1. Network connectivity issues\n"
            f"2. Invalid or expired download URLs\n"
            f"3. Insufficient disk space\n"
            f"4. Permission issues\n\n"
            f"Solutions:\n"
            f"1. Check your internet connection\n"
            f"2. Verify you have sufficient disk space (df -h)\n"
            f"3. Check the preset manager logs at /workspace/logs/preset_manager.log\n"
            f"4. Try downloading a different preset to test the system\n\n"
            f"If the issue persists, please report it at: "
            f"https://github.com/zeroclue/comfyui-docker/issues"
        )
        super().__init__(message, details)


class HealthCheckError(PresetManagerError):
    """Raised when a health check fails"""

    def __init__(self, service_name: str, check_result: str):
        self.service_name = service_name
        self.check_result = check_result
        message = f"Health check failed for: {service_name}"
        details = (
            f"The health check for '{service_name}' failed. Result: {check_result}\n\n"
            f"Diagnostic steps:\n"
            f"1. Check if the service is running: ps aux | grep {service_name}\n"
            f"2. Check the service logs at /workspace/logs/\n"
            f"3. Verify port availability: netstat -tuln | grep <port>\n"
            f"4. Restart the container if necessary\n\n"
            f"Common solutions:\n"
            f"- Restart the preset manager: pkill -f preset_manager.py && /start.sh\n"
            f"- Rebuild the Docker image if components are missing\n"
            f"- Pull the latest image from Docker Hub\n\n"
            f"For more help: https://github.com/zeroclue/comfyui-docker/issues"
        )
        super().__init__(message, details)


def get_user_friendly_message(error: Exception) -> str:
    """
    Convert an exception to a user-friendly error message with actionable guidance.

    Args:
        error: The exception to convert

    Returns:
        A user-friendly error message with solutions
    """
    if isinstance(error, PresetManagerError):
        return f"{error.message}\n\n{error.details}"

    # Handle standard Python exceptions
    error_messages = {
        FileNotFoundError: "File not found",
        PermissionError: "Permission denied",
        ConnectionError: "Network connection error",
        TimeoutError: "Operation timed out",
    }

    error_type = type(error)
    if error_type in error_messages:
        return (
            f"{error_messages[error_type]}: {str(error)}\n\n"
            f"If you need help, please visit:\n"
            f"https://github.com/zeroclue/comfyui-docker/issues"
        )

    # Fallback for unknown errors
    return (
        f"An unexpected error occurred: {str(error)}\n"
        f"Error type: {error_type.__name__}\n\n"
        f"For assistance, please visit:\n"
        f"https://github.com/zeroclue/comfyui-docker/issues"
    )
