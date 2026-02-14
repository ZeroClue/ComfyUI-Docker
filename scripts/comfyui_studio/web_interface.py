"""
Flask web interface for ComfyUI Studio
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import requests
from flask import (
    Flask, render_template_string, request,
    jsonify, session, redirect, url_for, send_file
)

try:
    from flask_session import Session
    HAS_SESSION = True
except ImportError:
    HAS_SESSION = False

from .config import config
from .core import WorkflowManager
from .comfyui_client import ComfyUIClient

logger = logging.getLogger(__name__)


class StudioWeb:
    """Flask web interface for ComfyUI Studio"""

    def __init__(self):
        self.app = Flask(__name__)
        self.workflow_manager = WorkflowManager()
        self.comfy_client = ComfyUIClient(config.comfyui_url)
        self._setup_flask_config()
        self._setup_routes()

    def _setup_flask_config(self):
        """Configure Flask application"""
        self.app.config['SECRET_KEY'] = config.SECRET_KEY
        self.app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

        if HAS_SESSION:
            self.app.config['SESSION_TYPE'] = 'filesystem'
            self.app.config['SESSION_PERMANENT'] = False
            self.app.config['SESSION_USE_SIGNER'] = True
            self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
            self.app.config['SESSION_FILE_DIR'] = '/tmp/studio_sessions'
            os.makedirs('/tmp/studio_sessions', exist_ok=True)
            Session(self.app)

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.before_request
        def require_auth():
            """Require authentication for all routes except login and static"""
            if request.endpoint in ['login', 'static'] or request.path.startswith('/static/'):
                return
            if not session.get('authenticated'):
                return redirect(url_for('login'))

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page"""
            if request.method == 'POST':
                password = request.form.get('password')
                if password == config.ACCESS_PASSWORD:
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    return render_template_string(
                        LOGIN_TEMPLATE,
                        error='Invalid password',
                        using_default_password=(config.ACCESS_PASSWORD == 'password')
                    )

            return render_template_string(
                LOGIN_TEMPLATE,
                password_required=True,
                using_default_password=(config.ACCESS_PASSWORD == 'password')
            )

        @self.app.route('/logout')
        def logout():
            """Logout"""
            session.pop('authenticated', None)
            return redirect(url_for('login'))

        @self.app.route('/')
        def index():
            """Main dashboard"""
            workflows = self.workflow_manager.list_workflows()
            storage_info = self.workflow_manager.get_storage_info()
            return render_template_string(
                INDEX_TEMPLATE,
                workflows=workflows,
                storage_info=storage_info
            )

        @self.app.route('/workflow/<workflow_id>')
        def workflow_detail(workflow_id):
            """Workflow detail and execution page"""
            workflow = self.workflow_manager.get_workflow(workflow_id)
            if not workflow:
                return "Workflow not found", 404

            inputs = self.workflow_manager.analyze_workflow(workflow['workflow'])
            return render_template_string(
                WORKFLOW_TEMPLATE,
                workflow=workflow,
                inputs=inputs
            )

        # API Routes

        @self.app.route('/api/workflows')
        def api_workflows():
            """List all workflows"""
            workflows = self.workflow_manager.list_workflows()
            return jsonify(workflows)

        @self.app.route('/api/workflows/<workflow_id>')
        def api_workflow_detail(workflow_id):
            """Get workflow details and inputs"""
            workflow = self.workflow_manager.get_workflow(workflow_id)
            if not workflow:
                return jsonify({'error': 'Workflow not found'}), 404

            inputs = self.workflow_manager.analyze_workflow(workflow['workflow'])
            return jsonify({
                'id': workflow_id,
                'name': workflow['name'],
                'description': workflow['description'],
                'inputs': inputs
            })

        @self.app.route('/api/generate', methods=['POST'])
        def api_generate():
            """Generate images using a workflow"""
            try:
                data = request.get_json()
                workflow_id = data.get('workflow_id')
                if not workflow_id:
                    return jsonify({'success': False, 'error': 'No workflow specified'}), 400

                workflow = self.workflow_manager.get_workflow(workflow_id)
                if not workflow:
                    return jsonify({'success': False, 'error': 'Workflow not found'}), 404

                inputs = data.get('inputs', {})

                # Handle image URLs
                sha256_hash = hashlib.sha256()
                for key, img_url in data.items():
                    if key.startswith('file_image_'):
                        input_id = key[11:]
                        try:
                            response = requests.get(img_url, stream=True)
                            response.raise_for_status()
                            sha256_hash.update(img_url.encode('utf-8'))
                            fname = sha256_hash.hexdigest()
                            fpath = os.path.join(config.UPLOAD_FOLDER, fname)

                            with open(fpath, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)

                            comfy_filename = self.comfy_client.upload_image(fpath, fname)
                            inputs[f"image_{input_id}"] = comfy_filename
                            logger.info(f"Uploaded image for input {input_id}")

                        except Exception as e:
                            logger.error(f"Failed to upload image: {e}")

                # Apply inputs to workflow
                workflow_copy = self.workflow_manager.apply_inputs(
                    workflow['workflow'], inputs
                )

                # Queue the prompt
                prompt_id = self.comfy_client.queue_prompt(workflow_copy)

                return jsonify({
                    'success': True,
                    'job_id': prompt_id
                })

            except Exception as e:
                logger.error(f"Generation error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/jobs/<job_id>')
        def api_job_status(job_id):
            """Get job status"""
            try:
                job = self.comfy_client.ws_client.jobs.get(job_id)

                if not job:
                    history = self.comfy_client.get_history(job_id)
                    if job_id in history:
                        return jsonify({
                            'id': job_id,
                            'status': 'completed',
                            'outputs': []
                        })
                    return jsonify({'error': 'Job not found'}), 404

                return jsonify({
                    'id': job.id,
                    'status': job.status,
                    'progress': job.progress,
                    'outputs': job.outputs,
                    'error': job.error,
                    'current_node': job.current_node
                })

            except Exception as e:
                logger.error(f"Error getting job status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/sync', methods=['POST'])
        def api_sync():
            """Sync workflows from ComfyUI"""
            result = self.workflow_manager.sync_from_comfyui()
            return jsonify(result)

        @self.app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
        def api_delete_workflow(workflow_id):
            """Delete a workflow"""
            success = self.workflow_manager.delete_workflow(workflow_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Workflow not found'}), 404

        @self.app.route('/api/storage')
        def api_storage():
            """Get storage info"""
            return jsonify(self.workflow_manager.get_storage_info())

        @self.app.route('/outputs/<filename>')
        def serve_output(filename):
            """Serve output images"""
            filepath = os.path.join(config.OUTPUT_FOLDER, filename)
            if os.path.exists(filepath):
                return send_file(filepath, mimetype='image/png')
            return "Image not found", 404

    def run(self, host=None, port=None, debug=False):
        """Run the Flask application"""
        host = host or config.STUDIO_HOST
        port = port or config.STUDIO_PORT

        print(f"\n{'='*60}")
        print("ComfyUI Studio")
        print(f"{'='*60}")
        print(f"  Studio URL: http://{host}:{port}")
        print(f"  ComfyUI URL: {config.comfyui_url}")
        print(f"  Workflows: {config.WORKFLOWS_FOLDER}")
        print(f"  Loaded: {len(self.workflow_manager.workflows)} workflows")
        print(f"{'='*60}\n")

        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """Create and configure the Flask application"""
    studio = StudioWeb()
    return studio.app


# HTML Templates (using safer DOM methods in JavaScript)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ComfyUI Studio - Login</title>
    <style>
        body { font-family: system-ui; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #1a1a2e; color: #eee; }
        .login-box { background: #16213e; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        h1 { margin-top: 0; }
        input { width: 100%; padding: 0.75rem; margin: 0.5rem 0; border: 1px solid #333; border-radius: 4px; background: #1a1a2e; color: #eee; }
        button { width: 100%; padding: 0.75rem; background: #e94560; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        button:hover { background: #ff6b6b; }
        .error { color: #e94560; margin-bottom: 1rem; }
        .warning { color: #ffc107; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>ComfyUI Studio</h1>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        {% if using_default_password %}<p class="warning">Using default password</p>{% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ComfyUI Studio</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui; margin: 0; background: #1a1a2e; color: #eee; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        h1 { margin-bottom: 0.5rem; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; color: white; }
        .btn-primary { background: #e94560; }
        .btn-secondary { background: #0f3460; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: #16213e; padding: 1rem; border-radius: 8px; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #e94560; }
        .workflows { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
        .workflow-card { background: #16213e; padding: 1.5rem; border-radius: 8px; transition: transform 0.2s; }
        .workflow-card:hover { transform: translateY(-2px); }
        .workflow-card h3 { margin-top: 0; }
        .workflow-card p { color: #aaa; margin-bottom: 1rem; }
        .workflow-actions { display: flex; gap: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>ComfyUI Studio</h1>
                <p>Workflow execution made simple</p>
            </div>
            <div>
                <a href="/logout" class="btn btn-secondary">Logout</a>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ workflows|length }}</div>
                <div>Workflows</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ storage_info.total_size_mb }} MB</div>
                <div>Storage Used</div>
            </div>
        </div>

        <div class="header">
            <h2>Workflows</h2>
            <button class="btn btn-primary" onclick="syncWorkflows()">Sync from ComfyUI</button>
        </div>

        <div class="workflows" id="workflows-grid">
            {% for workflow in workflows %}
            <div class="workflow-card">
                <h3>{{ workflow.name }}</h3>
                <p>{{ workflow.description }}</p>
                <div class="workflow-actions">
                    <a href="/workflow/{{ workflow.id }}" class="btn btn-primary">Run</a>
                    <button class="btn btn-secondary" onclick="deleteWorkflow('{{ workflow.id }}')">Delete</button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        async function syncWorkflows() {
            const response = await fetch('/api/sync', { method: 'POST' });
            const result = await response.json();
            alert(result.message);
            location.reload();
        }

        async function deleteWorkflow(id) {
            if (!confirm('Delete this workflow?')) return;
            const response = await fetch('/api/workflows/' + id, { method: 'DELETE' });
            const result = await response.json();
            if (result.success) location.reload();
            else alert('Failed to delete workflow');
        }
    </script>
</body>
</html>
"""

WORKFLOW_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ workflow.name }} - ComfyUI Studio</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui; margin: 0; background: #1a1a2e; color: #eee; }
        .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
        h1 { margin-bottom: 0.5rem; }
        .back { color: #e94560; text-decoration: none; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #333; border-radius: 4px; background: #16213e; color: #eee; }
        .form-group textarea { min-height: 100px; resize: vertical; }
        .btn { padding: 1rem 2rem; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .btn-primary { background: #e94560; color: white; }
        .btn:hover { opacity: 0.9; }
        .progress { margin-top: 2rem; display: none; }
        .progress-bar { height: 20px; background: #16213e; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #e94560; width: 0%; transition: width 0.3s; }
        .outputs { margin-top: 2rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
        .output img { width: 100%; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">&larr; Back to workflows</a>
        <h1>{{ workflow.name }}</h1>
        <p>{{ workflow.description }}</p>

        <form id="generateForm">
            <input type="hidden" name="workflow_id" value="{{ workflow.id }}">

            {% for input_id, input in inputs.items() %}
            <div class="form-group">
                <label>{{ input.title }}</label>
                {% if input.type == 'text' %}
                <textarea name="input_{{ input_id }}" {% if input.required %}required{% endif %}>{{ input.value or '' }}</textarea>
                {% elif input.type == 'image' %}
                <input type="file" name="file_{{ input_id }}" accept="image/*" {% if input.required %}required{% endif %}>
                {% elif input.type == 'number' %}
                <input type="number" name="input_{{ input_id }}" value="{{ input.value }}" min="{{ input.min }}" max="{{ input.max }}" step="{{ input.step or 1 }}">
                {% endif %}
            </div>
            {% endfor %}

            <button type="submit" class="btn btn-primary">Generate</button>
        </form>

        <div class="progress" id="progress">
            <p id="status">Queued...</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>

        <div class="outputs" id="outputs"></div>
    </div>

    <script>
        document.getElementById('generateForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(e.target);
            const inputs = {};
            for (let [key, value] of formData.entries()) {
                if (key.startsWith('input_')) {
                    inputs[key.substring(6)] = value;
                }
            }

            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workflow_id: formData.get('workflow_id'),
                    inputs: inputs
                })
            });

            const result = await response.json();
            if (result.success) {
                pollJob(result.job_id);
            } else {
                alert('Error: ' + result.error);
            }
        });

        async function pollJob(jobId) {
            document.getElementById('progress').style.display = 'block';

            const poll = async () => {
                const response = await fetch('/api/jobs/' + jobId);
                const job = await response.json();

                document.getElementById('status').textContent = job.status;
                document.getElementById('progressFill').style.width = (job.progress * 100) + '%';

                if (job.status === 'completed') {
                    const outputsDiv = document.getElementById('outputs');
                    outputsDiv.textContent = '';
                    for (const output of job.outputs) {
                        const div = document.createElement('div');
                        div.className = 'output';
                        const img = document.createElement('img');
                        img.src = '/outputs/' + encodeURIComponent(output.filename);
                        div.appendChild(img);
                        outputsDiv.appendChild(div);
                    }
                } else if (job.status === 'failed') {
                    alert('Generation failed: ' + job.error);
                } else {
                    setTimeout(poll, 1000);
                }
            };

            poll();
        }
    </script>
</body>
</html>
"""
