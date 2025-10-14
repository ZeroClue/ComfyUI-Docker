"""
Flask web interface for the ComfyUI Preset Manager
Contains all HTTP routes and web-related functionality
"""

import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import Dict

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory

# Try to import optional dependencies
try:
    from flask_session import Session
    HAS_SESSION = True
except ImportError:
    HAS_SESSION = False
    print("Warning: flask-session not available, using default session handling")

from .core import ModelManager
from .config import DEFAULT_HOST, DEFAULT_PORT, SECRET_KEY


# Global variables for operation tracking
operation_status = {}
operation_progress = {}


class PresetManagerWeb:
    """Flask web interface for preset management"""

    def __init__(self):
        # Explicitly specify template and static folders to resolve path issues
        self.app = Flask(__name__,
                        template_folder='/app/templates',
                        static_folder='/app/static')
        self.model_manager = ModelManager()
        self.access_password = os.environ.get('ACCESS_PASSWORD', 'password')
        self._setup_flask_config()
        self._setup_routes()

    def _setup_flask_config(self):
        """Configure Flask application"""
        self.app.config['SECRET_KEY'] = SECRET_KEY

        # Initialize session if available
        if HAS_SESSION:
            self.app.config['SESSION_TYPE'] = 'filesystem'
            self.app.config['SESSION_PERMANENT'] = False
            self.app.config['SESSION_USE_SIGNER'] = True
            self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
            self.app.config['SESSION_FILE_DIR'] = '/tmp/flask_sessions'
            os.makedirs('/tmp/flask_sessions', exist_ok=True)
            Session(self.app)
        else:
            print("Using default Flask session handling")

    def _setup_routes(self):
        """Setup Flask routes"""

        def check_auth():
            """Check if user is authenticated"""
            if 'authenticated' not in session:
                return False
            return session.get('authenticated') == True

        @self.app.before_request
        def require_auth():
            """Require authentication for all routes except login and static"""
            if request.endpoint in ['login', 'static'] or request.path.startswith('/static/'):
                return

            if not check_auth():
                return redirect(url_for('login'))

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Login page"""
            if request.method == 'POST':
                password = request.form.get('password')
                if password == self.access_password:
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html',
                                         error='Invalid password',
                                         using_default_password=(self.access_password == 'password'))

            # Check if using default password
            using_default_password = (self.access_password == 'password')

            return render_template('login.html',
                                 password_required=True,
                                 using_default_password=using_default_password)

        @self.app.route('/logout')
        def logout():
            """Logout"""
            session.pop('authenticated', None)
            return redirect(url_for('login'))

        @self.app.route('/')
        def index():
            """Main dashboard with storage overview"""
            storage_info = self.model_manager.get_storage_info()

            # Calculate installation statistics
            total_presets = len(self.model_manager.presets)
            installed_presets = len([p for p in self.model_manager.presets.values() if p['is_installed']])
            partial_presets = len([p for p in self.model_manager.presets.values() if p['is_partial']])

            stats = {
                'total_presets': total_presets,
                'installed_presets': installed_presets,
                'partial_presets': partial_presets,
                'installation_rate': round((installed_presets / total_presets) * 100, 1) if total_presets > 0 else 0
            }

            return render_template('index.html',
                                 storage_info=storage_info,
                                 categories=self.model_manager.categories,
                                 stats=stats)

        @self.app.route('/presets')
        def presets():
            """Browse all presets"""
            return render_template('presets.html', categories=self.model_manager.categories)

        @self.app.route('/preset/<preset_id>')
        def preset_detail(preset_id):
            """Preset detail page"""
            preset = self.model_manager.get_preset(preset_id)
            if not preset:
                return "Preset not found", 404

            readme_content = self.model_manager.get_preset_readme(preset_id)
            readme_html = self.model_manager.render_readme(readme_content) if readme_content else None

            return render_template('preset_detail.html',
                                 preset=preset,
                                 preset_id=preset_id,
                                 readme_html=readme_html)

        @self.app.route('/storage')
        def storage():
            """Storage management page"""
            storage_info = self.model_manager.get_storage_info()
            return render_template('storage.html', storage_info=storage_info)

        @self.app.route('/api/download/<preset_id>', methods=['POST'])
        def start_download(preset_id):
            """Start downloading a preset"""
            preset = self.model_manager.get_preset(preset_id)
            if not preset:
                return jsonify({'error': 'Preset not found'}), 404

            # Initialize operation status
            operation_id = f"download_{preset_id}_{int(time.time())}"
            operation_status[operation_id] = {
                'type': 'download',
                'preset_id': preset_id,
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing download...',
                'start_time': datetime.now().isoformat()
            }

            # Start download in background thread
            thread = threading.Thread(target=self._download_preset, args=(operation_id, preset))
            thread.daemon = True
            thread.start()

            return jsonify({'operation_id': operation_id})

        @self.app.route('/api/delete/<preset_id>', methods=['DELETE'])
        def delete_preset(preset_id):
            """Delete preset files"""
            try:
                success, message = self.model_manager.delete_preset_files(preset_id)
                if success:
                    return jsonify({'success': True, 'message': message})
                else:
                    return jsonify({'success': False, 'message': message}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/cleanup', methods=['POST'])
        def cleanup_models():
            """Cleanup unused models"""
            try:
                cleanup_type = request.json.get('type', 'unused')

                if cleanup_type == 'unused':
                    success, message = self.model_manager.cleanup_unused_models()
                else:
                    return jsonify({'success': False, 'message': 'Unknown cleanup type'}), 400

                if success:
                    return jsonify({'success': True, 'message': message})
                else:
                    return jsonify({'success': False, 'message': message}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/operation/status/<operation_id>')
        def get_operation_status(operation_id):
            """Get operation status"""
            if operation_id not in operation_status:
                return jsonify({'error': 'Operation not found'}), 404

            return jsonify(operation_status[operation_id])

        @self.app.route('/api/storage/status')
        def get_storage_status():
            """Get current storage information"""
            storage_info = self.model_manager.get_storage_info()
            return jsonify(storage_info)

    def _download_preset(self, operation_id: str, preset: Dict):
        """Download preset in background thread"""
        try:
            # Determine script path based on preset type
            if preset['type'] == 'video':
                script_path = "/scripts/download_presets.sh"
            elif preset['type'] == 'image':
                script_path = "/scripts/download_image_presets.sh"
            elif preset['type'] == 'audio':
                script_path = "/scripts/download_audio_presets.sh"
            else:
                raise ValueError(f"Unknown preset type: {preset['type']}")

            # Update status
            operation_status[operation_id]['status'] = 'downloading'
            operation_status[operation_id]['message'] = f'Downloading {preset["name"]}...'

            # Run download command
            cmd = [script_path, preset['name'].split()[0]]  # Use first part of name
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Parse progress from output
                    if 'Downloading' in output or 'downloading' in output.lower():
                        operation_status[operation_id]['progress'] = min(
                            operation_status[operation_id]['progress'] + 5, 90
                        )
                        operation_status[operation_id]['message'] = output.strip()

            # Check result
            return_code = process.poll()
            if return_code == 0:
                operation_status[operation_id]['status'] = 'completed'
                operation_status[operation_id]['progress'] = 100
                operation_status[operation_id]['message'] = 'Download completed successfully!'

                # Rescan models to update status
                self.model_manager._scan_installed_models()
            else:
                stderr_output = process.stderr.read()
                operation_status[operation_id]['status'] = 'error'
                operation_status[operation_id]['message'] = f'Download failed: {stderr_output}'

        except Exception as e:
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'Download error: {str(e)}'

    def run(self, host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False):
        """Run the Flask application"""
        # Create required directories
        os.makedirs('/app/templates', exist_ok=True)
        os.makedirs('/app/static', exist_ok=True)

        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """Create and configure the Flask application"""
    web_interface = PresetManagerWeb()
    return web_interface.app