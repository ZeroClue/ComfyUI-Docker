#!/bin/bash

# ComfyUI Preset System Migration Script
# Updates schema and all necessary scripts for preset system compatibility
# Usage: curl -fsSL https://raw.githubusercontent.com/your-repo/ComfyUI-docker/main/scripts/migrate_schema.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect ComfyUI-docker directory
detect_comfyui_dir() {
    # Check if we're already in the ComfyUI-docker directory
    if [[ -f "config/presets-schema.json" && -f "config/presets.yaml" ]]; then
        echo "$(pwd)"
        return 0
    fi

    # Common locations to check
    local locations=(
        "$HOME/ComfyUI-docker"
        "$HOME/projects/ComfyUI-docker"
        "/opt/ComfyUI-docker"
        "$HOME/docker/ComfyUI-docker"
        "./ComfyUI-docker"
    )

    for location in "${locations[@]}"; do
        if [[ -d "$location" && -f "$location/config/presets-schema.json" ]]; then
            echo "$location"
            return 0
        fi
    done

    return 1
}

# Function to check if schema needs migration
check_schema_needs_migration() {
    local schema_file="$1"

    # Check if the schema contains the new metadata properties
    if grep -q "total_presets" "$schema_file" && grep -q "new_presets_from_docs" "$schema_file"; then
        return 1  # No migration needed
    else
        return 0  # Migration needed
    fi
}

# Function to create backup
create_backup() {
    local schema_file="$1"
    local backup_dir="$2"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/presets-schema_${timestamp}.json"

    cp "$schema_file" "$backup_file"
    print_success "Backup created: $backup_file"
}

# Function to migrate schema
migrate_schema() {
    local schema_file="$1"

    print_status "Migrating schema file: $schema_file"

    # Use Python to properly update the JSON schema
    python3 -c "
import json
import sys

def migrate_schema():
    try:
        with open('$schema_file', 'r') as f:
            schema = json.load(f)

        # Check if metadata properties need to be added
        metadata_props = schema['properties']['metadata']['properties']

        added_total_presets = False
        added_new_presets = False

        if 'total_presets' not in metadata_props:
            metadata_props['total_presets'] = {
                'type': 'number',
                'description': 'Total number of presets in configuration'
            }
            added_total_presets = True

        if 'new_presets_from_docs' not in metadata_props:
            metadata_props['new_presets_from_docs'] = {
                'type': 'number',
                'description': 'Number of new presets added from documentation'
            }
            added_new_presets = True

        # Write updated schema back to file
        with open('$schema_file', 'w') as f:
            json.dump(schema, f, indent=2)

        if added_total_presets:
            print('✓ Added total_presets property')
        if added_new_presets:
            print('✓ Added new_presets_from_docs property')

        if added_total_presets or added_new_presets:
            print('Schema migration completed successfully')
        else:
            print('Schema was already up to date')

    except Exception as e:
        print(f'Error migrating schema: {e}')
        sys.exit(1)

migrate_schema()
"
}

# Function to check prerequisites
check_prerequisites() {
    local comfyui_dir="$1"

    print_status "Checking prerequisites..."

    # Check network connectivity
    if ! curl -s --connect-timeout 10 "https://github.com" >/dev/null; then
        print_error "Cannot connect to GitHub. Check your network connection."
        return 1
    fi

    # Check write permissions in scripts directory
    local scripts_dir="${comfyui_dir}/scripts"
    if [[ -d "$scripts_dir" ]]; then
        if ! touch "${scripts_dir}/.test_write" 2>/dev/null; then
            print_error "No write permission in scripts directory: $scripts_dir"
            return 1
        fi
        rm -f "${scripts_dir}/.test_write" 2>/dev/null || true
    else
        # Create scripts directory if it doesn't exist
        if ! mkdir -p "$scripts_dir" 2>/dev/null; then
            print_error "Cannot create scripts directory: $scripts_dir"
            return 1
        fi
    fi

    # Check write permissions in config directory
    if ! touch "${comfyui_dir}/config/.test_write" 2>/dev/null; then
        print_error "No write permission in config directory: ${comfyui_dir}/config"
        return 1
    fi
    rm -f "${comfyui_dir}/config/.test_write" 2>/dev/null || true

    print_success "Prerequisites check passed"
    return 0
}

# Function to check if file exists on GitHub
check_file_exists() {
    local url="$1"

    # Use GitHub API to check if file exists
    local api_url="${url/\/raw\./\/api}"

    if curl -s -f -o /dev/null "$url"; then
        return 0  # File exists
    else
        return 1  # File doesn't exist
    fi
}

# Function to download file from GitHub
download_file() {
    local url="$1"
    local local_path="$2"
    local file_name="$3"
    local max_retries=3
    local retry_count=0

    print_status "Downloading $file_name..."

    # Create directory if it doesn't exist
    local dir_path
    dir_path="$(dirname "$local_path")"
    if ! mkdir -p "$dir_path" 2>/dev/null; then
        print_error "Cannot create directory: $dir_path"
        return 1
    fi

    # Check if file exists remotely first
    if ! check_file_exists "$url"; then
        print_warning "File not found on GitHub: $file_name"
        return 1
    fi

    # Download with retry logic
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -fsSL --connect-timeout 30 --max-time 300 "$url" -o "$local_path" 2>/dev/null; then
            print_success "Downloaded $file_name successfully"
            return 0
        else
            ((retry_count++))
            if [[ $retry_count -lt $max_retries ]]; then
                print_warning "Download attempt $retry_count failed, retrying..."
                sleep 2
            fi
        fi
    done

    print_error "Failed to download $file_name after $max_retries attempts"
    return 1
}

# Function to update scripts from GitHub
update_scripts() {
    local comfyui_dir="$1"

    print_status "Updating necessary scripts from GitHub..."

    # GitHub repository details
    local github_repo="ZeroClue/ComfyUI-Docker"
    local github_branch="main"
    local base_url="https://raw.githubusercontent.com/${github_repo}/${github_branch}"

    # List of scripts to update
    local scripts=(
        "scripts/preset_updater.py:Preset Updater"
        "scripts/preset_validator.py:Preset Validator"
        "scripts/generate_download_scripts.py:Download Scripts Generator"
        "scripts/unified_preset_downloader.py:Unified Preset Downloader"
    )

    local updated_count=0
    local total_count=${#scripts[@]}

    for script_info in "${scripts[@]}"; do
        IFS=':' read -r script_path script_name <<< "$script_info"

        local local_file="${comfyui_dir}/${script_path}"
        local remote_url="${base_url}/${script_path}"

        # Create backup of existing script if it exists
        if [[ -f "$local_file" ]]; then
            cp "$local_file" "${local_file}.backup.$(date +%Y%m%d_%H%M%S)"
            print_status "Backed up existing $script_name"
        fi

        # Download updated script
        if download_file "$remote_url" "$local_file" "$script_name"; then
            chmod +x "$local_file" 2>/dev/null || true  # Make executable if possible
            ((updated_count++))
            print_success "Updated $script_name"
        else
            print_warning "Failed to update $script_name, continuing with others..."
        fi
    done

    print_status "Updated $updated_count/$total_count scripts"
    return $((total_count - updated_count))
}

# Function to validate migrated schema
validate_schema() {
    local schema_file="$1"

    print_status "Validating migrated schema..."

    python3 -c "
import json
import sys

try:
    with open('$schema_file', 'r') as f:
        schema = json.load(f)

    # Basic validation - check if it's valid JSON and has required structure
    required_sections = ['metadata', 'categories', 'presets']
    for section in required_sections:
        if section not in schema['properties']:
            print(f'Missing required section: {section}')
            sys.exit(1)

    # Check new properties exist
    metadata_props = schema['properties']['metadata']['properties']
    required_new_props = ['total_presets', 'new_presets_from_docs']

    for prop in required_new_props:
        if prop not in metadata_props:
            print(f'Missing required property: {prop}')
            sys.exit(1)

    print('✓ Schema validation passed')

except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Validation error: {e}')
    sys.exit(1)
"
}

# Main execution
main() {
    print_status "ComfyUI Preset System Migration Script"
    print_status "====================================="

    # Detect ComfyUI-docker directory
    COMFYUI_DIR=$(detect_comfyui_dir)
    if [[ $? -ne 0 ]]; then
        print_error "ComfyUI-docker directory not found!"
        print_error "Please run this script from within ComfyUI-docker or ensure it's in a standard location."
        exit 1
    fi

    print_status "Found ComfyUI-docker directory: $COMFYUI_DIR"

    # Define file paths
    SCHEMA_FILE="$COMFYUI_DIR/config/presets-schema.json"
    BACKUP_DIR="$COMFYUI_DIR/config/backups"

    # Check if schema file exists
    if [[ ! -f "$SCHEMA_FILE" ]]; then
        print_error "Schema file not found: $SCHEMA_FILE"
        exit 1
    fi

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Run pre-flight checks
    if ! check_prerequisites "$COMFYUI_DIR"; then
        print_error "Pre-flight checks failed. Cannot proceed with migration."
        exit 1
    fi

    # Update scripts first (always update to ensure compatibility)
    print_status "Updating migration and preset management scripts..."
    update_scripts "$COMFYUI_DIR"
    script_update_result=$?

    # Check if schema migration is needed
    if check_schema_needs_migration "$SCHEMA_FILE"; then
        print_status "Schema needs migration"

        # Create backup
        create_backup "$SCHEMA_FILE" "$BACKUP_DIR"

        # Migrate schema
        migrate_schema "$SCHEMA_FILE"

        # Validate migrated schema
        if validate_schema "$SCHEMA_FILE"; then
            print_success "Schema migration completed successfully!"
            print_status "You can now run the preset update process again."
            print_status "The backup was saved to: $BACKUP_DIR/presets-schema_*.json"
        else
            print_error "Schema migration failed! Please check the backup and try manually."
            exit 1
        fi
    else
        print_success "Schema is already up to date."
    fi

    # Report final status
    if [[ $script_update_result -eq 0 ]]; then
        print_success "All scripts updated successfully!"
    else
        print_warning "Some script updates failed. Check the logs above."
    fi

    print_status "Migration process completed. You can now run preset updates normally."
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Run main function
main "$@"