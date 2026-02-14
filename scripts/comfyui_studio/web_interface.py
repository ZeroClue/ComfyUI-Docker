"""
Flask web interface for ComfyUI Studio
"""
import os
import json
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from urllib.parse import urlparse

import requests
from flask import (
    Flask, render_template_string, request,
    jsonify, session, redirect, url_for, send_file
)

# Security: Blocked hosts for SSRF protection
BLOCKED_HOSTS = {'localhost', '127.0.0.1', '169.254.169.254'}
BLOCKED_PREFIXES = ('10.', '172.', '192.168.', '169.254.')

try:
    from flask_session import Session
    HAS_SESSION = True
except ImportError:
    HAS_SESSION = False

from .config import config
from .core import WorkflowManager
from .comfyui_client import ComfyUIClient

logger = logging.getLogger(__name__)


def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        # Only allow http/https schemes
        if parsed.scheme not in {'http', 'https'}:
            return False
        # Block internal network access
        hostname = parsed.hostname
        if not hostname:
            return False
        # Check blocked hosts
        if hostname in BLOCKED_HOSTS:
            return False
        # Check blocked prefixes (private networks)
        for prefix in BLOCKED_PREFIXES:
            if hostname.startswith(prefix):
                return False
        return True
    except Exception:
        return False


def safe_join_path(base_dir: str, filename: str) -> str:
    """Safely join paths and prevent path traversal."""
    # Get basename to remove any path components
    safe_name = os.path.basename(filename)
    if safe_name != filename or '..' in filename:
        return None
    # Build full path
    full_path = os.path.join(base_dir, safe_name)
    # Resolve to absolute path
    full_path = os.path.abspath(full_path)
    base_dir = os.path.abspath(base_dir)
    # Ensure resolved path is within base directory
    if not full_path.startswith(base_dir + os.sep):
        return None
    return full_path


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

                # Handle image URLs with SSRF protection
                sha256_hash = hashlib.sha256()
                for key, img_url in data.items():
                    if key.startswith('file_image_'):
                        input_id = key[11:]
                        try:
                            # Security: Validate URL to prevent SSRF
                            if not is_safe_url(img_url):
                                logger.error(f"Blocked unsafe URL: {img_url}")
                                return jsonify({
                                    'success': False,
                                    'error': f'Unsafe URL provided for image input'
                                }), 400

                            response = requests.get(img_url, stream=True, timeout=30)
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
                            return jsonify({
                                'success': False,
                                'error': f'Failed to upload image: {str(e)}'
                            }), 400

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
            """Serve output images with path traversal protection"""
            # Security: Use safe path joining to prevent path traversal
            filepath = safe_join_path(config.OUTPUT_FOLDER, filename)
            if filepath is None:
                return "Invalid filename", 400
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

# Shared theme variables - High Contrast accessibility theme
_THEME_VARS = """
    :root {
        --bg-color: #0d0d0d;
        --card-color: #1a1a1a;
        --accent-color: #ffb819;
        --accent-hover: #ffc940;
        --secondary-color: #333333;
        --text-primary: #ffffff;
        --text-secondary: #b3b3b3;
        --border-color: rgba(255,255,255,0.15);
        --border-radius: 4px;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
    }
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ComfyUI Studio - Login</title>
    <style>
        """ + _THEME_VARS + """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 17px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: var(--bg-color);
            color: var(--text-primary);
        }
        .login-box {
            background: var(--card-color);
            padding: var(--spacing-xl);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            min-width: 320px;
        }
        h1 {
            margin-bottom: var(--spacing-md);
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        input {
            width: 100%;
            padding: var(--spacing-md);
            margin: var(--spacing-sm) 0 var(--spacing-md);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            background: var(--bg-color);
            color: var(--text-primary);
            font-size: 1rem;
        }
        input:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
        button {
            width: 100%;
            padding: var(--spacing-md);
            background: var(--accent-color);
            color: #000;
            border: none;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: background 0.15s ease;
        }
        button:hover { background: var(--accent-hover); }
        button:focus {
            outline: 2px solid var(--text-primary);
            outline-offset: 2px;
        }
        .error {
            color: var(--accent-color);
            margin-bottom: var(--spacing-md);
            font-weight: 500;
        }
        .warning {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: var(--spacing-md);
            padding: var(--spacing-sm);
            background: var(--secondary-color);
            border-radius: var(--border-radius);
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>ComfyUI Studio</h1>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        {% if using_default_password %}<p class="warning">Using default password</p>{% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="Password" required autofocus>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ComfyUI Studio</title>
    <style>
        """ + _THEME_VARS + """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 17px;
            background: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: var(--spacing-xl); }
        h1, h2 { margin-bottom: var(--spacing-sm); font-weight: 700; letter-spacing: -0.02em; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-xl);
            flex-wrap: wrap;
            gap: var(--spacing-md);
        }
        .header p { color: var(--text-secondary); }
        .btn {
            padding: var(--spacing-sm) var(--spacing-md);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9375rem;
            font-weight: 500;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-sm);
        }
        .btn-primary {
            background: var(--accent-color);
            color: #000;
            border-color: var(--accent-color);
        }
        .btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
        .btn-secondary {
            background: var(--secondary-color);
            color: var(--text-primary);
        }
        .btn-secondary:hover { background: #444; }
        .btn:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: var(--spacing-md);
            margin-bottom: var(--spacing-xl);
        }
        .stat-card {
            background: var(--card-color);
            padding: var(--spacing-lg);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
            letter-spacing: -0.03em;
        }
        .stat-label { color: var(--text-secondary); margin-top: var(--spacing-xs); }
        .section-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-md);
            flex-wrap: wrap;
            gap: var(--spacing-md);
        }
        .workflows {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: var(--spacing-md);
        }
        .workflow-card {
            background: var(--card-color);
            padding: var(--spacing-lg);
            border-radius: var(--border-radius);
            border: 1px solid var(--border-color);
            transition: border-color 0.15s ease, transform 0.15s ease;
        }
        .workflow-card:hover {
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }
        .workflow-card h3 { margin-top: 0; font-weight: 600; }
        .workflow-card p {
            color: var(--text-secondary);
            margin-bottom: var(--spacing-md);
            font-size: 0.9375rem;
        }
        .workflow-actions { display: flex; gap: var(--spacing-sm); }
        .workflow-actions .btn { flex: 1; justify-content: center; }
        .empty-state {
            text-align: center;
            padding: var(--spacing-xl) * 2;
            color: var(--text-secondary);
        }
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
                <div class="stat-label">Workflows</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ storage_info.total_size_mb }} MB</div>
                <div class="stat-label">Storage Used</div>
            </div>
        </div>

        <div class="section-title">
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
            const btn = event.target;
            btn.textContent = 'Syncing...';
            btn.disabled = true;
            try {
                const response = await fetch('/api/sync', { method: 'POST' });
                const result = await response.json();
                alert(result.message);
                location.reload();
            } catch (e) {
                alert('Sync failed: ' + e.message);
                btn.textContent = 'Sync from ComfyUI';
                btn.disabled = false;
            }
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ workflow.name }} - ComfyUI Studio</title>
    <style>
        """ + _THEME_VARS + """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 17px;
            background: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
        }
        .container { max-width: 800px; margin: 0 auto; padding: var(--spacing-xl); }
        h1 { margin-bottom: var(--spacing-sm); font-weight: 700; letter-spacing: -0.02em; }
        .description {
            color: var(--text-secondary);
            margin-bottom: var(--spacing-xl);
            font-size: 1.0625rem;
        }
        .back {
            color: var(--accent-color);
            text-decoration: none;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-sm);
            margin-bottom: var(--spacing-lg);
            transition: color 0.15s ease;
        }
        .back:hover { color: var(--accent-hover); }
        .form-group { margin-bottom: var(--spacing-lg); }
        .form-group label {
            display: block;
            margin-bottom: var(--spacing-sm);
            font-weight: 500;
        }
        .form-group input[type="text"],
        .form-group input[type="number"],
        .form-group input[type="file"],
        .form-group textarea {
            width: 100%;
            padding: var(--spacing-md);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            background: var(--card-color);
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
        }
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        .form-group input:focus,
        .form-group textarea:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
        .form-group input[type="file"] {
            cursor: pointer;
        }
        .form-group input[type="file"]::file-selector-button {
            background: var(--secondary-color);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--border-radius);
            cursor: pointer;
            margin-right: var(--spacing-md);
        }
        .btn {
            padding: var(--spacing-md) var(--spacing-xl);
            border: 1px solid var(--accent-color);
            border-radius: var(--border-radius);
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        .btn-primary {
            background: var(--accent-color);
            color: #000;
        }
        .btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
        .btn-primary:disabled {
            background: var(--secondary-color);
            border-color: var(--secondary-color);
            color: var(--text-secondary);
            cursor: not-allowed;
        }
        .btn:focus {
            outline: 2px solid var(--text-primary);
            outline-offset: 2px;
        }
        .progress {
            margin-top: var(--spacing-xl);
            padding: var(--spacing-lg);
            background: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            display: none;
        }
        .progress-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-sm);
        }
        .progress-status span { font-weight: 500; }
        .progress-percent {
            color: var(--accent-color);
            font-weight: 600;
        }
        .progress-bar {
            height: 8px;
            background: var(--secondary-color);
            border-radius: var(--border-radius);
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: var(--accent-color);
            width: 0%;
            transition: width 0.3s ease;
        }
        .outputs {
            margin-top: var(--spacing-xl);
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: var(--spacing-md);
        }
        .output {
            background: var(--card-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            overflow: hidden;
        }
        .output img {
            width: 100%;
            display: block;
        }
        .outputs-title {
            margin-bottom: var(--spacing-md);
            font-weight: 600;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">&larr; Back to workflows</a>
        <h1>{{ workflow.name }}</h1>
        <p class="description">{{ workflow.description }}</p>

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

            <button type="submit" class="btn btn-primary" id="submitBtn">Generate</button>
        </form>

        <div class="progress" id="progress">
            <div class="progress-status">
                <span id="status">Queued...</span>
                <span class="progress-percent" id="progressPercent">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>

        <div id="outputsContainer" style="display: none;">
            <h3 class="outputs-title">Generated Images</h3>
            <div class="outputs" id="outputs"></div>
        </div>
    </div>

    <script>
        document.getElementById('generateForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.textContent = 'Starting...';

            const formData = new FormData(e.target);
            const inputs = {};
            for (let [key, value] of formData.entries()) {
                if (key.startsWith('input_')) {
                    inputs[key.substring(6)] = value;
                }
            }

            try {
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
                    btn.disabled = false;
                    btn.textContent = 'Generate';
                }
            } catch (e) {
                alert('Request failed: ' + e.message);
                btn.disabled = false;
                btn.textContent = 'Generate';
            }
        });

        async function pollJob(jobId) {
            const progress = document.getElementById('progress');
            const progressFill = document.getElementById('progressFill');
            const progressPercent = document.getElementById('progressPercent');
            const status = document.getElementById('status');
            const btn = document.getElementById('submitBtn');

            progress.style.display = 'block';
            btn.textContent = 'Generating...';

            const poll = async () => {
                const response = await fetch('/api/jobs/' + jobId);
                const job = await response.json();

                const pct = Math.round(job.progress * 100);
                status.textContent = job.current_node || job.status;
                progressFill.style.width = pct + '%';
                progressPercent.textContent = pct + '%';

                if (job.status === 'completed') {
                    btn.disabled = false;
                    btn.textContent = 'Generate';

                    const container = document.getElementById('outputsContainer');
                    const outputsDiv = document.getElementById('outputs');
                    outputsDiv.textContent = '';
                    container.style.display = 'block';

                    for (const output of job.outputs) {
                        const div = document.createElement('div');
                        div.className = 'output';
                        const img = document.createElement('img');
                        img.src = '/outputs/' + encodeURIComponent(output.filename);
                        img.alt = 'Generated image';
                        div.appendChild(img);
                        outputsDiv.appendChild(div);
                    }
                } else if (job.status === 'failed') {
                    alert('Generation failed: ' + job.error);
                    btn.disabled = false;
                    btn.textContent = 'Generate';
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
