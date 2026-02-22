"""
ComfyUI REST API client
Handles communication with ComfyUI server for workflow execution and status monitoring
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin


class ComfyUIClient:
    """Async client for ComfyUI REST API"""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.client_id = "dashboard_client"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _get(self, endpoint: str, **kwargs) -> Dict:
        """Make GET request to ComfyUI API"""
        session = await self._get_session()
        url = urljoin(f"{self.base_url}/", endpoint)

        try:
            async with session.get(url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"ComfyUI API error: {str(e)}")

    async def _post(self, endpoint: str, **kwargs) -> Dict:
        """Make POST request to ComfyUI API"""
        session = await self._get_session()
        url = urljoin(f"{self.base_url}/", endpoint)

        try:
            async with session.post(url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"ComfyUI API error: {str(e)}")

    async def get_queue_status(self) -> Dict:
        """Get current queue status from ComfyUI"""
        return await self._get("queue")

    async def get_history(self, limit: Optional[int] = None) -> Dict:
        """Get execution history from ComfyUI"""
        history = await self._get("history")

        if limit and len(history) > limit:
            # Return only the most recent items
            history_items = sorted(history.items(), key=lambda x: x[0], reverse=True)[:limit]
            return dict(history_items)

        return history

    async def get_history_item(self, prompt_id: str) -> Dict:
        """Get specific execution history item"""
        history = await self._get("history")
        if prompt_id not in history:
            raise Exception(f"Prompt {prompt_id} not found in history")
        return history[prompt_id]

    async def queue_workflow(self, workflow: Dict) -> Dict:
        """
        Queue a workflow for execution in ComfyUI.

        Returns the prompt_id on success, or raises an exception on failure.
        """
        result = await self._post("prompt", json={
            "prompt": workflow,
            "client_id": self.client_id
        })

        # Check for errors in the response
        if "error" in result:
            error_info = result.get("error", {})
            if isinstance(error_info, dict):
                error_type = error_info.get("type", "unknown")
                error_msg = error_info.get("message", str(error_info))
                raise Exception(f"ComfyUI error ({error_type}): {error_msg}")
            else:
                raise Exception(f"ComfyUI error: {error_info}")

        if "node_errors" in result and result["node_errors"]:
            # Format node errors
            errors = []
            for node_id, node_error in result["node_errors"].items():
                errors.append(f"Node {node_id}: {node_error.get('errors', ['unknown error'])}")
            raise Exception(f"Workflow validation errors: {'; '.join(errors)}")

        return result

    async def interrupt_execution(self) -> Dict:
        """Interrupt current execution"""
        return await self._post("interrupt")

    async def clear_queue(self) -> Dict:
        """Clear all pending items from queue"""
        return await self._post("queue", json={"clear": True})

    async def get_outputs(self) -> List[Dict]:
        """Get list of generated outputs"""
        try:
            return await self._get("view")
        except Exception:
            return []

    async def get_system_metrics(self) -> Dict:
        """Get system metrics from ComfyUI"""
        try:
            return await self._get("system_stats")
        except Exception:
            return {"error": "Unable to fetch system metrics"}

    async def get_object_info(self) -> Dict:
        """Get information about available nodes and their inputs/outputs"""
        try:
            return await self._get("object_info")
        except Exception:
            return {}

    async def get_extensions(self) -> List[Dict]:
        """Get list of installed extensions"""
        try:
            return await self._get("extensions")
        except Exception:
            return []

    async def upload_image(self, image_data: bytes, overwrite: bool = True) -> Dict:
        """Upload an image to ComfyUI"""
        session = await self._get_session()
        url = urljoin(f"{self.base_url}/", "upload/image")

        data = aiohttp.FormData()
        data.add_field('image', image_data, filename='upload.png')
        data.add_field('overwrite', str(overwrite).lower())

        try:
            async with session.post(url, data=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Image upload error: {str(e)}")

    def inject_prompt(self, workflow: Dict, prompt_text: str) -> Dict:
        """
        Inject prompt text into workflow nodes.
        Finds the first positive prompt text encoder and replaces its content.
        Works with API format workflows (dict with node IDs as keys).
        """
        import copy
        workflow = copy.deepcopy(workflow)

        # Track if we've replaced a prompt already
        prompt_replaced = False

        # API format: {"1": {"class_type": "CLIPTextEncode", "inputs": {...}}, ...}
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                continue

            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})

            # Handle CLIPTextEncode nodes (most common for prompts)
            if class_type == "CLIPTextEncode" and "text" in inputs:
                node_title = node_data.get("_meta", {}).get("title", "").lower()

                # Skip negative prompt nodes
                if "negative" in node_title:
                    continue

                # Only replace the first positive prompt found
                if not prompt_replaced:
                    inputs["text"] = prompt_text
                    prompt_replaced = True

        return workflow

    async def validate_workflow(self, workflow: Dict) -> Dict:
        """
        Validate a workflow before execution
        Checks for missing nodes, invalid connections, etc.
        """
        object_info = await self.get_object_info()
        errors = []
        warnings = []

        # Check each node in workflow
        for node_id, node_data in workflow.items():
            class_type = node_data.get('class_type', '')
            if class_type and class_type not in object_info:
                errors.append(f"Node {node_id}: Unknown class type '{class_type}'")

            # Check inputs
            if 'inputs' in node_data:
                for input_key, input_value in node_data['inputs'].items():
                    if isinstance(input_value, list) and len(input_value) == 2:
                        # This is a connection to another node
                        connected_node_id = input_value[0]
                        if connected_node_id not in workflow:
                            errors.append(f"Node {node_id}: Invalid connection to node {connected_node_id}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def stream_execution(self, prompt_id: str):
        """
        Stream execution progress for a specific prompt
        Yields progress updates as they occur
        """
        last_history_len = 0

        while True:
            history = await self.get_history()

            if prompt_id in history:
                current_data = history[prompt_id]

                # Check if execution is complete
                if current_data.get('status', {}).get('completed', False):
                    yield {
                        "type": "complete",
                        "data": current_data
                    }
                    break

                # Send progress update
                yield {
                    "type": "progress",
                    "data": current_data
                }

            await asyncio.sleep(1)  # Poll every second


__all__ = ["ComfyUIClient"]
