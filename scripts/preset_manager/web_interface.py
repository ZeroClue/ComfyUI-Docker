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

# Import preset updater for GitHub integration
try:
    from preset_updater import PresetUpdater
    HAS_UPDATER = True
except ImportError:
    HAS_UPDATER = False
    print("Warning: preset_updater not available, update functionality disabled")

# Import download script generator for YAML-based downloads
try:
    from generate_download_scripts import DownloadScriptGenerator
    HAS_SCRIPT_GENERATOR = True
except ImportError:
    HAS_SCRIPT_GENERATOR = False
    print("Warning: download script generator not available, using fallback")


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
        self.preset_updater = PresetUpdater() if HAS_UPDATER else None
        self.script_generator = DownloadScriptGenerator() if HAS_SCRIPT_GENERATOR else None
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

            # Get preset version and update information
            preset_version = None
            update_available = False

            if self.preset_updater:
                try:
                    preset_version = self.preset_updater.get_current_version()
                    update_check = self.preset_updater.check_for_updates()
                    update_available = update_check.get('update_available', False)
                except Exception as e:
                    print(f"[WARNING] Error checking preset updates: {e}")

            # Add preset IDs to categories for template use
            categories_with_ids = {}
            for category_name, presets in self.model_manager.categories.items():
                categories_with_ids[category_name] = []
                for preset in presets:
                    preset_id = self.model_manager.get_preset_id_by_name(preset['name'])
                    preset_with_id = preset.copy()
                    preset_with_id['id'] = preset_id
                    categories_with_ids[category_name].append(preset_with_id)

            return render_template('index.html',
                                 storage_info=storage_info,
                                 categories=categories_with_ids,
                                 stats=stats,
                                 preset_version=preset_version,
                                 update_available=update_available,
                                 has_updater=HAS_UPDATER)

        @self.app.route('/presets')
        def presets():
            """Browse all presets"""
            # Add preset IDs to categories for template use
            categories_with_ids = {}
            for category_name, presets in self.model_manager.categories.items():
                categories_with_ids[category_name] = []
                for preset in presets:
                    preset_id = self.model_manager.get_preset_id_by_name(preset['name'])
                    preset_with_id = preset.copy()
                    preset_with_id['id'] = preset_id
                    categories_with_ids[category_name].append(preset_with_id)

            return render_template('presets.html', categories=categories_with_ids)

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

        @self.app.route('/api/unknown-models')
        def get_unknown_models():
            """Get unknown models not tracked by presets"""
            try:
                unknown_models = self.model_manager._get_unknown_models()
                return jsonify({
                    'success': True,
                    'unknown_models': unknown_models,
                    'count': len(unknown_models)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/report-model', methods=['POST'])
        def report_model():
            """Create GitHub issue data for reporting an unknown model"""
            try:
                data = request.get_json()
                if not data or 'model_path' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'model_path is required'
                    }), 400

                model_path = data['model_path']

                # Find the model in unknown models
                unknown_models = self.model_manager._get_unknown_models()
                model_info = None
                for model in unknown_models:
                    if model['relative_path'] == model_path or model['full_path'] == model_path:
                        model_info = model
                        break

                if not model_info:
                    return jsonify({
                        'success': False,
                        'error': 'Model not found in unknown models'
                    }), 404

                # Create GitHub issue data
                issue_data = self.model_manager.create_github_issue_data(model_info)

                return jsonify({
                    'success': True,
                    'issue_data': issue_data
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/presets/update/check', methods=['GET'])
        def check_preset_updates():
            """Check if preset updates are available"""
            if not self.preset_updater:
                return jsonify({
                    'success': False,
                    'error': 'Preset updater not available'
                }), 503

            try:
                update_check = self.preset_updater.check_for_updates()
                return jsonify(update_check)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/presets/update', methods=['POST'])
        def update_presets():
            """Update presets from GitHub"""
            if not self.preset_updater:
                return jsonify({
                    'success': False,
                    'error': 'Preset updater not available'
                }), 503

            try:
                force_update = request.json.get('force', False) if request.is_json else False

                # Initialize operation status
                operation_id = f"update_presets_{int(time.time())}"
                operation_status[operation_id] = {
                    'type': 'update',
                    'status': 'starting',
                    'progress': 0,
                    'message': 'Checking for updates...',
                    'start_time': datetime.now().isoformat()
                }

                # Start update in background thread
                thread = threading.Thread(target=self._update_presets_background, args=(operation_id, force_update))
                thread.daemon = True
                thread.start()

                return jsonify({'operation_id': operation_id})
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/presets/update/history', methods=['GET'])
        def get_update_history():
            """Get preset update history"""
            if not self.preset_updater:
                return jsonify({
                    'success': False,
                    'error': 'Preset updater not available'
                }), 503

            try:
                history = self.preset_updater.get_update_history()
                return jsonify(history)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @self.app.route('/api/presets/version', methods=['GET'])
        def get_preset_version():
            """Get current preset version information"""
            if not self.preset_updater:
                return jsonify({
                    'success': False,
                    'error': 'Preset updater not available'
                }), 503

            try:
                current_version = self.preset_updater.get_current_version()
                return jsonify({
                    'success': True,
                    'version': current_version
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    def _download_preset(self, operation_id: str, preset: Dict):
        """Download preset in background thread using YAML configuration"""
        try:
            # Get preset ID from the preset data
            preset_id = None
            for pid, pdata in self.model_manager.presets.items():
                if pdata.get('name') == preset.get('name'):
                    preset_id = pid
                    break

            if not preset_id:
                raise ValueError(f"Could not find preset ID for {preset.get('name')}")

            # Update status
            operation_status[operation_id]['status'] = 'downloading'
            operation_status[operation_id]['message'] = f'Downloading {preset["name"]}...'

            # Use YAML-based download if available
            if self.script_generator:
                self._download_preset_yaml(operation_id, preset_id, preset)
            else:
                # Fallback to script-based approach
                self._download_preset_script(operation_id, preset_id, preset)

        except Exception as e:
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'Download error: {str(e)}'

    def _download_preset_yaml(self, operation_id: str, preset_id: str, preset: Dict):
        """Download preset using YAML configuration"""
        try:
            # Load presets and get file URLs
            presets = self.script_generator.load_presets()
            files = self.script_generator.get_preset_urls(preset_id, presets)

            if not files:
                raise ValueError(f"No files found for preset {preset_id}")

            # Calculate total files for progress tracking
            total_files = len(files)
            completed_files = 0

            operation_status[operation_id]['message'] = f'Downloading {total_files} files for {preset["name"]}...'

            # Download each file
            for file_info in files:
                url = file_info['url']
                path = file_info['path']
                target_dir = f"/workspace/ComfyUI/models/{os.path.dirname(path)}"

                operation_status[operation_id]['message'] = f'Downloading {os.path.basename(path)}...'

                # Use the download function from generated script
                cmd = [
                    'bash', '-c',
                    f'''
source <(cat << 'EOF'
# download_if_missing function
download_if_missing() {{
    local url="$1"
    local dest_dir="$2"

    local filename
    filename=$(basename "$url")
    local filepath="$dest_dir/$filename"

    mkdir -p "$dest_dir"

    if [ -f "$filepath" ]; then
        echo "File already exists: $filepath"
        return 0
    fi

    echo "Downloading: $filename → $dest_dir"
    local tmpdir="/workspace/tmp"
    mkdir -p "$tmpdir"
    local tmpfile="$tmpdir/${{filename}}.part"

    if wget --show-progress -O "$tmpfile" "$url"; then
        mv -f "$tmpfile" "$filepath"
        echo "Download completed: $filepath"
        return 0
    else
        echo "Download failed: $url"
        rm -f "$tmpfile"
        return 1
    fi
}}
download_if_missing "{url}" "{target_dir}"
EOF
)
                    '''
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Monitor this download
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        operation_status[operation_id]['message'] = output.strip()

                # Check result
                if process.poll() == 0:
                    completed_files += 1
                    progress = int((completed_files / total_files) * 95)  # Leave 5% for finalization
                    operation_status[operation_id]['progress'] = progress
                else:
                    stderr_output = process.stderr.read()
                    operation_status[operation_id]['status'] = 'error'
                    operation_status[operation_id]['message'] = f'Download failed for {os.path.basename(path)}: {stderr_output}'
                    return

            # All downloads completed successfully
            operation_status[operation_id]['status'] = 'completed'
            operation_status[operation_id]['progress'] = 100
            operation_status[operation_id]['message'] = f'Download completed successfully! Downloaded {total_files} files.'

            # Rescan models to update status
            self.model_manager._scan_installed_models()

        except Exception as e:
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'YAML download error: {str(e)}'

    def _download_preset_script(self, operation_id: str, preset_id: str, preset: Dict):
        """Fallback: Download preset using traditional script approach"""
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

            # Run download command
            cmd = [script_path, preset_id]
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
                operation_status[operation_id]['message'] = f'Script download failed: {stderr_output}'

        except Exception as e:
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'Script download error: {str(e)}'

    def _update_presets_background(self, operation_id: str, force_update: bool = False):
        """Update presets in background thread"""
        try:
            # Update status
            operation_status[operation_id]['status'] = 'updating'
            operation_status[operation_id]['message'] = 'Updating presets from GitHub...'
            operation_status[operation_id]['progress'] = 10

            # Perform update
            update_result = self.preset_updater.update_presets(force=force_update)

            if update_result['success']:
                operation_status[operation_id]['status'] = 'completed'
                operation_status[operation_id]['progress'] = 100
                operation_status[operation_id]['message'] = update_result['message']

                # Reload presets to update the manager
                self.model_manager._parse_all_presets()
                self.model_manager._scan_installed_models()

                # Clear any related cache
                if hasattr(self.model_manager, 'presets_cache'):
                    self.model_manager.presets_cache.clear()

            else:
                operation_status[operation_id]['status'] = 'error'
                operation_status[operation_id]['message'] = update_result['message']

        except Exception as e:
            operation_status[operation_id]['status'] = 'error'
            operation_status[operation_id]['message'] = f'Update error: {str(e)}'

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