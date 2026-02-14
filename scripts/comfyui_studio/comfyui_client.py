"""
ComfyUI API and WebSocket client
"""
import os
import json
import uuid
import time
import logging
import threading
from queue import Queue
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests

# Check for correct websocket package
try:
    import websocket
    if not hasattr(websocket, 'WebSocketApp'):
        raise ImportError("Wrong websocket package")
except ImportError:
    print("\nERROR: websocket-client not installed!")
    print("Please run: pip install websocket-client==1.7.0\n")
    raise

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class GenerationJob:
    """Represents a generation job"""
    id: str
    workflow: Dict[str, Any]
    status: str = "queued"
    progress: float = 0.0
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    current_node: Optional[str] = None


class ComfyUIWebSocketClient:
    """WebSocket client for ComfyUI real-time updates"""

    def __init__(self, server_address: str):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.messages = Queue()
        self.jobs: Dict[str, GenerationJob] = {}
        self.running = False
        self.thread = None

    def connect(self):
        """Connect to ComfyUI WebSocket"""
        # Strip any protocol prefix from server_address
        server_addr = self.server_address
        if server_addr.startswith('http://'):
            server_addr = server_addr[7:]
        elif server_addr.startswith('https://'):
            server_addr = server_addr[8:]

        ws_url = f"ws://{server_addr}/ws?clientId={self.client_id}"

        def on_message(ws, message):
            try:
                if isinstance(message, bytes):
                    return
                data = json.loads(message)
                self.process_message(data)
            except json.JSONDecodeError:
                logger.error("Failed to parse WebSocket message")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")

        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
            if "codec" not in str(error):
                self.running = False

        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self.running = False

        def on_open(ws):
            logger.info("WebSocket connection established")
            self.running = True

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)

    def process_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message"""
        msg_type = data.get('type')
        msg_data = data.get('data', {})

        if msg_type == 'status':
            logger.debug(f"Queue status: {msg_data.get('status', {})}")

        elif msg_type == 'execution_start':
            prompt_id = msg_data.get('prompt_id')
            if prompt_id and prompt_id in self.jobs:
                self.jobs[prompt_id].status = 'running'
                logger.info(f"Execution started: {prompt_id}")

        elif msg_type == 'executing':
            prompt_id = msg_data.get('prompt_id')
            node = msg_data.get('node')
            if prompt_id and prompt_id in self.jobs:
                self.jobs[prompt_id].current_node = node
                logger.info(f"Executing node {node} for prompt {prompt_id}")

        elif msg_type == 'progress':
            prompt_id = msg_data.get('prompt_id')
            if prompt_id and prompt_id in self.jobs:
                value = msg_data.get('value', 0)
                max_value = msg_data.get('max', 100)
                self.jobs[prompt_id].progress = (value / max_value) if max_value > 0 else 0

        elif msg_type == 'executed':
            prompt_id = msg_data.get('prompt_id')
            logger.info(f"Node executed for prompt {prompt_id}")

        elif msg_type == 'execution_error':
            prompt_id = msg_data.get('prompt_id')
            if prompt_id and prompt_id in self.jobs:
                error = msg_data.get('exception_message', 'Unknown error')
                self.jobs[prompt_id].status = 'failed'
                self.jobs[prompt_id].error = error
                logger.error(f"Execution error for {prompt_id}: {error}")


class ComfyUIClient:
    """Client for interacting with ComfyUI API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.ws_client = ComfyUIWebSocketClient(base_url.replace('http://', ''))
        self.ws_client.connect()

    def queue_prompt(self, prompt: Dict[str, Any]) -> str:
        """Queue a prompt in ComfyUI"""
        p = {"prompt": prompt, "client_id": self.ws_client.client_id}
        response = requests.post(f"{self.base_url}/prompt", json=p)
        response.raise_for_status()
        result = response.json()
        prompt_id = result['prompt_id']

        job = GenerationJob(id=prompt_id, workflow=prompt)
        self.ws_client.jobs[prompt_id] = job
        logger.info(f"Queued prompt: {prompt_id}")
        return prompt_id

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt"""
        try:
            response = requests.get(f"{self.base_url}/history/{prompt_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {}

    def get_queue_status(self) -> Dict[str, Any]:
        """Get ComfyUI queue status"""
        try:
            response = requests.get(f"{self.base_url}/queue")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {}

    def interrupt_execution(self) -> bool:
        """Interrupt current execution"""
        try:
            response = requests.post(f"{self.base_url}/interrupt")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to interrupt execution: {e}")
            return False

    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """Download an image from ComfyUI"""
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        try:
            response = requests.get(f"{self.base_url}/view", params=params)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to get image {filename}: {e}")
            return None

    def upload_image(self, filepath: str, name: Optional[str] = None, overwrite: bool = True) -> str:
        """Upload an image to ComfyUI"""
        if name is None:
            name = os.path.basename(filepath)

        with open(filepath, 'rb') as f:
            files = {'image': (name, f, 'image/png')}
            data = {'overwrite': str(overwrite).lower()}
            response = requests.post(f"{self.base_url}/upload/image", files=files, data=data)
            response.raise_for_status()
            result = response.json()
            return result.get('name', name)

    def wait_for_job(self, prompt_id: str, timeout: int = 300) -> GenerationJob:
        """Wait for a job to complete"""
        start_time = time.time()
        job = self.ws_client.jobs.get(prompt_id)

        if not job:
            job = GenerationJob(id=prompt_id, workflow={})
            self.ws_client.jobs[prompt_id] = job

        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)

            if prompt_id in history:
                hist_data = history[prompt_id]
                outputs = hist_data.get('outputs', {})

                if outputs:
                    for node_id, node_output in outputs.items():
                        if 'images' in node_output:
                            for img in node_output['images']:
                                existing = any(
                                    o['node_id'] == node_id and
                                    o.get('original_filename') == img['filename']
                                    for o in job.outputs
                                )
                                if existing:
                                    continue

                                img_data = self.get_image(
                                    img['filename'],
                                    img.get('subfolder', ''),
                                    img.get('type', 'output')
                                )

                                if img_data:
                                    output_filename = f"{prompt_id}_{img['filename']}"
                                    output_path = os.path.join(config.OUTPUT_FOLDER, output_filename)

                                    with open(output_path, 'wb') as f:
                                        f.write(img_data)

                                    job.outputs.append({
                                        'filename': output_filename,
                                        'node_id': node_id,
                                        'path': output_path,
                                        'original_filename': img['filename']
                                    })
                                    logger.info(f"Saved output image: {output_filename}")

                    if job.outputs:
                        job.status = 'completed'
                        job.completed_at = datetime.now()
                        return job

            if job.status == 'failed':
                raise Exception(f"Job failed: {job.error}")

            time.sleep(0.5)

        raise TimeoutError(f"Job {prompt_id} timed out after {timeout} seconds")
