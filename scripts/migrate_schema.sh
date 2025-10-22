#!/bin/bash

# ComfyUI Preset Schema Migration Script
# Fixes schema validation issues for preset updates
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
    print_status "ComfyUI Preset Schema Migration Script"
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

    # Check if migration is needed
    if check_schema_needs_migration "$SCHEMA_FILE"; then
        print_status "Schema needs migration"
    else
        print_success "Schema is already up to date. No migration needed."
        exit 0
    fi

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
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

# Run main function
main "$@"