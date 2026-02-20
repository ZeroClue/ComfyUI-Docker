# Preset System Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the preset system with centralized management, version pinning, and enhanced UX for a reusable community-ready system.

**Architecture:** Separate GitHub repository (`zeroclue/comfyui-presets`) stores presets as individual YAML files with version pinning. A management bot (GitHub Actions) handles daily validation and version scanning. ComfyUI pods pull the registry read-only.

**Tech Stack:** Python 3.11+, YAML, JSON Schema, FastAPI, GitHub Actions, HuggingFace Hub API

---

## Phase 1: Core Infrastructure

### Task 1.1: Create Preset Registry Repository Structure

**Files:**
- Create: `presets/` directory structure
- Create: `schema.yaml`
- Create: `registry.json`
- Create: `README.md`
- Create: `.gitignore`

**Step 1: Initialize repository structure**

Create the following directory structure:

```
zeroclue/comfyui-presets/
├── presets/
│   ├── video/
│   ├── image/
│   └── audio/
├── scripts/
│   ├── validate.py
│   ├── scan_versions.py
│   └── generate_registry.py
├── schema.yaml
├── registry.json
├── README.md
└── .gitignore
```

**Step 2: Create schema.yaml**

```yaml
# JSON Schema for preset validation
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
  - id
  - version
  - name
  - category
  - type
  - files
properties:
  id:
    type: string
    pattern: "^[a-z0-9-]+$"
    description: "Unique preset identifier (lowercase, hyphens only)"
  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
    description: "Semantic version of preset schema"
  name:
    type: string
    minLength: 1
    maxLength: 100
  category:
    type: string
    enum: ["Video Generation", "Image Generation", "Audio Generation"]
  type:
    type: string
    enum: ["video", "image", "audio"]
  description:
    type: string
    maxLength: 500
  download_size:
    type: string
    pattern: "^\\d+(\\.\\d+)?(GB|MB)$"
  requirements:
    type: object
    properties:
      vram_gb:
        type: number
        minimum: 0
      disk_gb:
        type: number
        minimum: 0
      recommended_gpu:
        type: array
        items:
          type: string
      dependencies:
        type: array
        items:
          type: string
  files:
    type: array
    minItems: 1
    items:
      type: object
      required:
        - path
        - url
        - size
      properties:
        path:
          type: string
          description: "Relative path from /workspace/models/"
        url:
          type: string
          format: uri
        size:
          type: string
          pattern: "^\\d+(\\.\\d+)?(GB|MB)$"
        optional:
          type: boolean
          default: false
        source:
          type: object
          properties:
            type:
              type: string
              enum: ["huggingface", "civitai", "direct"]
            repo:
              type: string
            revision:
              type: string
              description: "Git commit SHA for version pinning"
        checksum:
          type: object
          properties:
            algorithm:
              type: string
              enum: ["sha256", "md5"]
            value:
              type: string
  tags:
    type: array
    items:
      type: string
    maxItems: 10
  use_case:
    type: string
    maxLength: 200
  created:
    type: string
    format: date-time
  updated:
    type: string
    format: date-time
```

**Step 3: Create initial registry.json**

```json
{
  "version": "1.0.0",
  "last_scan": null,
  "presets": {},
  "alerts": []
}
```

**Step 4: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
.env
.DS_Store
*.log
```

**Step 5: Create README.md**

```markdown
# ComfyUI Presets Registry

Centralized preset definitions for ComfyUI models.

## Structure

- `presets/` - Individual preset YAML files organized by category
- `schema.yaml` - JSON Schema for validation
- `registry.json` - Pre-computed metadata for fast loading

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Usage

```bash
# Fetch registry
curl -s https://raw.githubusercontent.com/zeroclue/comfyui-presets/main/registry.json

# Fetch specific preset
curl -s https://raw.githubusercontent.com/zeroclue/comfyui-presets/main/presets/video/wan-2-2-5-t2v/preset.yaml
```
```

**Step 6: Commit**

```bash
git add .
git commit -m "feat: initialize preset registry structure"
```

---

### Task 1.2: Create Preset Validation Script

**Files:**
- Create: `scripts/validate.py`

**Step 1: Write the validation script**

```python
#!/usr/bin/env python3
"""
Preset validation script
Validates preset YAML files against schema
"""

import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Installing jsonschema...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema
    from jsonschema import validate, ValidationError


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON Schema from YAML file"""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def load_preset(preset_path: Path) -> Dict[str, Any]:
    """Load preset YAML file"""
    with open(preset_path, 'r') as f:
        return yaml.safe_load(f)


def validate_preset(preset: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate preset against schema, return list of errors"""
    errors = []

    try:
        jsonschema.validate(instance=preset, schema=schema)
    except ValidationError as e:
        errors.append(f"Schema validation: {e.message}")

    # Additional validations
    if 'id' in preset:
        # Check ID matches directory name
        pass

    if 'files' in preset:
        for i, file in enumerate(preset['files']):
            if 'url' in file and 'huggingface.co' in file['url']:
                if 'source' not in file or 'revision' not in file.get('source', {}):
                    errors.append(f"File {i}: HuggingFace URLs should have revision pinning")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate preset YAML files")
    parser.add_argument("--preset", type=Path, help="Validate specific preset file")
    parser.add_argument("--all", action="store_true", help="Validate all presets")
    parser.add_argument("--schema", type=Path, default=Path("schema.yaml"), help="Schema file path")
    parser.add_argument("--presets-dir", type=Path, default=Path("presets"), help="Presets directory")
    args = parser.parse_args()

    # Load schema
    if not args.schema.exists():
        print(f"ERROR: Schema file not found: {args.schema}")
        sys.exit(1)

    schema = load_schema(args.schema)
    print(f"Loaded schema from {args.schema}")

    errors_found = 0
    presets_validated = 0

    if args.preset:
        # Validate single preset
        if not args.preset.exists():
            print(f"ERROR: Preset file not found: {args.preset}")
            sys.exit(1)

        preset = load_preset(args.preset)
        errors = validate_preset(preset, schema)

        if errors:
            print(f"❌ {args.preset}:")
            for error in errors:
                print(f"  - {error}")
            errors_found += 1
        else:
            print(f"✅ {args.preset}: Valid")
            presets_validated += 1

    elif args.all:
        # Validate all presets
        for category_dir in args.presets_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for preset_dir in category_dir.iterdir():
                if not preset_dir.is_dir():
                    continue

                preset_file = preset_dir / "preset.yaml"
                if not preset_file.exists():
                    print(f"⚠️  {preset_dir}: No preset.yaml found")
                    continue

                preset = load_preset(preset_file)
                errors = validate_preset(preset, schema)

                if errors:
                    print(f"❌ {preset_file}:")
                    for error in errors:
                        print(f"  - {error}")
                    errors_found += 1
                else:
                    presets_validated += 1

        print(f"\nValidated {presets_validated} presets, {errors_found} errors")

    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(1 if errors_found else 0)


if __name__ == "__main__":
    main()
```

**Step 2: Test validation script**

```bash
# Should show help
python scripts/validate.py --help
```

**Step 3: Make script executable**

```bash
chmod +x scripts/validate.py
```

**Step 4: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: add preset validation script"
```

---

### Task 1.3: Create Migration Script

**Files:**
- Create: `scripts/migrate.py`

**Step 1: Write migration script**

```python
#!/usr/bin/env python3
"""
Migrate presets from old monolithic YAML to new structure
"""

import sys
import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import re


def sanitize_id(old_id: str) -> str:
    """Convert old preset ID to new format (lowercase, hyphens)"""
    # Convert SNAKE_CASE to kebab-case
    return old_id.lower().replace('_', '-')


def convert_preset(old_preset: Dict[str, Any], preset_id: str, category: str) -> Dict[str, Any]:
    """Convert old preset format to new format"""
    now = datetime.utcnow().isoformat() + "Z"

    # Map category to directory
    category_map = {
        "Video Generation": "video",
        "Image Generation": "image",
        "Audio Generation": "audio"
    }
    category_dir = category_map.get(category, "other")

    new_preset = {
        "id": preset_id,
        "version": "1.0.0",
        "name": old_preset.get("name", preset_id),
        "category": category,
        "type": old_preset.get("type", category_dir),
        "description": old_preset.get("description", ""),
        "download_size": old_preset.get("download_size", "0GB"),
        "files": [],
        "tags": old_preset.get("tags", []),
        "use_case": old_preset.get("use_case", ""),
        "created": now,
        "updated": now
    }

    # Add requirements if we can infer them
    requirements = {}
    if "download_size" in old_preset:
        size_str = old_preset["download_size"]
        if "GB" in size_str:
            requirements["disk_gb"] = float(size_str.replace("GB", "").strip())
    if requirements:
        new_preset["requirements"] = requirements

    # Convert files
    for old_file in old_preset.get("files", []):
        new_file = {
            "path": old_file["path"],
            "url": old_file["url"],
            "size": old_file.get("size", "0GB"),
            "optional": old_file.get("optional", False)
        }

        # Detect source type from URL
        if "huggingface.co" in old_file["url"]:
            new_file["source"] = {
                "type": "huggingface",
                "repo": extract_hf_repo(old_file["url"]),
                "revision": None  # Will be filled by version scanner
            }

        new_preset["files"].append(new_file)

    return new_preset


def extract_hf_repo(url: str) -> str:
    """Extract HuggingFace repo from URL"""
    # URL format: https://huggingface.co/{repo}/resolve/main/{file}
    match = re.search(r'huggingface\.co/([^/]+/[^/]+)', url)
    if match:
        return match.group(1)
    return ""


def main():
    parser = argparse.ArgumentParser(description="Migrate presets from old format")
    parser.add_argument("--source", type=Path, required=True, help="Source presets.yaml file")
    parser.add_argument("--output", type=Path, default=Path("presets"), help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"ERROR: Source file not found: {args.source}")
        sys.exit(1)

    with open(args.source, 'r') as f:
        old_config = yaml.safe_load(f)

    presets = old_config.get("presets", {})
    categories = old_config.get("categories", {})

    print(f"Found {len(presets)} presets to migrate")

    # Create output directories
    for category in categories.keys():
        category_dir = args.output / category.lower().replace(" ", "-").replace("/", "-")
        if not args.dry_run:
            category_dir.mkdir(parents=True, exist_ok=True)

    # Convert each preset
    for old_id, old_preset in presets.items():
        new_id = sanitize_id(old_id)
        category = old_preset.get("category", "Other")

        # Determine category directory
        category_map = {
            "Video Generation": "video",
            "Image Generation": "image",
            "Audio Generation": "audio"
        }
        category_dir = category_map.get(category, "other")

        new_preset = convert_preset(old_preset, new_id, category)

        # Write preset file
        preset_dir = args.output / category_dir / new_id
        preset_file = preset_dir / "preset.yaml"

        print(f"  {old_id} -> {category_dir}/{new_id}")

        if not args.dry_run:
            preset_dir.mkdir(parents=True, exist_ok=True)
            with open(preset_file, 'w') as f:
                yaml.dump(new_preset, f, default_flow_style=False, sort_keys=False)

    print(f"\nMigration {'previewed' if args.dry_run else 'complete'}!")


if __name__ == "__main__":
    main()
```

**Step 2: Test migration (dry run)**

```bash
# From comfyui-presets repo
python scripts/migrate.py --source /path/to/comfyui-docker/config/presets.yaml --dry-run
```

**Step 3: Commit**

```bash
git add scripts/migrate.py
git commit -m "feat: add preset migration script"
```

---

### Task 1.4: Create Registry Generator Script

**Files:**
- Create: `scripts/generate_registry.py`

**Step 1: Write registry generator**

```python
#!/usr/bin/env python3
"""
Generate registry.json from preset files
"""

import sys
import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def parse_size_to_gb(size_str: str) -> float:
    """Convert size string to GB float"""
    size_str = size_str.upper().strip()
    if "GB" in size_str:
        return float(size_str.replace("GB", "").strip())
    elif "MB" in size_str:
        return float(size_str.replace("MB", "").strip()) / 1024
    return 0.0


def generate_registry(presets_dir: Path) -> Dict[str, Any]:
    """Generate registry.json from all presets"""
    registry = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "presets": {},
        "stats": {
            "total": 0,
            "by_category": {}
        }
    }

    for category_dir in presets_dir.iterdir():
        if not category_dir.is_dir():
            continue

        category = category_dir.name
        registry["stats"]["by_category"][category] = 0

        for preset_dir in category_dir.iterdir():
            if not preset_dir.is_dir():
                continue

            preset_file = preset_dir / "preset.yaml"
            if not preset_file.exists():
                continue

            with open(preset_file, 'r') as f:
                preset = yaml.safe_load(f)

            preset_id = preset.get("id", preset_dir.name)

            # Create registry entry (lightweight)
            registry["presets"][preset_id] = {
                "name": preset.get("name", preset_id),
                "category": preset.get("category", category),
                "type": preset.get("type", category),
                "download_size": preset.get("download_size", "0GB"),
                "vram_gb": preset.get("requirements", {}).get("vram_gb", 0),
                "disk_gb": preset.get("requirements", {}).get("disk_gb", 0),
                "tags": preset.get("tags", []),
                "update_available": False,
                "last_verified": preset.get("updated"),
                "file_count": len(preset.get("files", [])),
                "path": f"presets/{category}/{preset_id}/preset.yaml"
            }

            registry["stats"]["total"] += 1
            registry["stats"]["by_category"][category] += 1

    return registry


def main():
    parser = argparse.ArgumentParser(description="Generate registry.json")
    parser.add_argument("--presets-dir", type=Path, default=Path("presets"), help="Presets directory")
    parser.add_argument("--output", type=Path, default=Path("registry.json"), help="Output file")
    args = parser.parse_args()

    if not args.presets_dir.exists():
        print(f"ERROR: Presets directory not found: {args.presets_dir}")
        sys.exit(1)

    registry = generate_registry(args.presets_dir)

    with open(args.output, 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"Generated registry.json with {registry['stats']['total']} presets")
    print(f"By category: {registry['stats']['by_category']}")


if __name__ == "__main__":
    main()
```

**Step 2: Test registry generator**

```bash
python scripts/generate_registry.py --presets-dir presets --output registry.json
```

**Step 3: Commit**

```bash
git add scripts/generate_registry.py
git commit -m "feat: add registry generator script"
```

---

### Task 1.5: Set Up GitHub Actions CI

**Files:**
- Create: `.github/workflows/validate.yml`

**Step 1: Create CI workflow**

```yaml
name: Validate Presets

on:
  push:
    branches: [main]
    paths:
      - 'presets/**'
      - 'schema.yaml'
  pull_request:
    branches: [main]
    paths:
      - 'presets/**'
      - 'schema.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema

      - name: Validate all presets
        run: |
          python scripts/validate.py --all

      - name: Generate registry
        run: |
          python scripts/generate_registry.py

      - name: Upload registry artifact
        uses: actions/upload-artifact@v4
        with:
          name: registry
          path: registry.json

  commit-registry:
    needs: validate
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Generate registry
        run: python scripts/generate_registry.py

      - name: Commit registry
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add registry.json
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: update registry.json"
          git push
```

**Step 2: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "feat: add GitHub Actions CI for preset validation"
```

---

## Phase 2: Management Bot

### Task 2.1: Create HuggingFace Version Scanner

**Files:**
- Create: `scripts/scan_versions.py`

**Step 1: Write version scanner**

```python
#!/usr/bin/env python3
"""
Scan HuggingFace repos for version updates
"""

import sys
import yaml
import json
import argparse
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class HuggingFaceScanner:
    """Scan HuggingFace repos for updates"""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.api_base = "https://huggingface.co/api"
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def get_commit_info(self, session: aiohttp.ClientSession, repo: str, revision: str) -> Optional[Dict]:
        """Get commit info for a specific revision"""
        url = f"{self.api_base}/models/{repo}/commit/{revision}"
        try:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            print(f"  Error fetching commit {revision[:8]}: {e}")
        return None

    async def get_main_branch_head(self, session: aiohttp.ClientSession, repo: str) -> Optional[str]:
        """Get the latest commit SHA on main branch"""
        url = f"{self.api_base}/models/{repo}/tree/main"
        try:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    # The API returns file listing, we need the commit SHA
                    # Alternative: use git API
                    pass
        except Exception as e:
            print(f"  Error fetching main branch: {e}")

        # Fallback: use git ls-remote
        return None

    async def check_for_updates(self, session: aiohttp.ClientSession, repo: str, tracked_revision: Optional[str]) -> Dict[str, Any]:
        """Check if repo has updates since tracked revision"""
        result = {
            "repo": repo,
            "tracked_revision": tracked_revision,
            "latest_revision": None,
            "update_available": False,
            "error": None
        }

        if not tracked_revision:
            result["error"] = "No revision tracked"
            result["update_available"] = True  # Needs to be pinned
            return result

        # For now, use a simple HEAD request to check if URL still works
        # Full implementation would compare commits
        try:
            url = f"https://huggingface.co/{repo}"
            async with session.head(url, headers=self.headers) as resp:
                if resp.status == 200:
                    result["latest_revision"] = "main"  # Placeholder
                    # In production, compare actual commits
                    result["update_available"] = False
                else:
                    result["error"] = f"HTTP {resp.status}"
        except Exception as e:
            result["error"] = str(e)

        return result


async def scan_presets(presets_dir: Path, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scan all presets for HuggingFace updates"""
    scanner = HuggingFaceScanner(token)
    results = []

    async with aiohttp.ClientSession() as session:
        for category_dir in presets_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for preset_dir in category_dir.iterdir():
                if not preset_dir.is_dir():
                    continue

                preset_file = preset_dir / "preset.yaml"
                if not preset_file.exists():
                    continue

                with open(preset_file, 'r') as f:
                    preset = yaml.safe_load(f)

                # Check each file's HuggingFace source
                for file_info in preset.get("files", []):
                    source = file_info.get("source", {})
                    if source.get("type") == "huggingface" and source.get("repo"):
                        print(f"Checking {preset.get('id')}: {source['repo']}")

                        update = await scanner.check_for_updates(
                            session,
                            source["repo"],
                            source.get("revision")
                        )

                        results.append({
                            "preset_id": preset.get("id"),
                            "file_path": file_info.get("path"),
                            **update
                        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Scan for HuggingFace updates")
    parser.add_argument("--presets-dir", type=Path, default=Path("presets"))
    parser.add_argument("--token", type=str, help="HuggingFace API token")
    parser.add_argument("--output", type=Path, default=Path("version_scan.json"))
    args = parser.parse_args()

    results = asyncio.run(scan_presets(args.presets_dir, args.token))

    with open(args.output, 'w') as f:
        json.dump({
            "scanned_at": datetime.utcnow().isoformat() + "Z",
            "results": results
        }, f, indent=2)

    # Summary
    updates_available = sum(1 for r in results if r.get("update_available"))
    errors = sum(1 for r in results if r.get("error"))

    print(f"\nScan complete:")
    print(f"  Total scanned: {len(results)}")
    print(f"  Updates available: {updates_available}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add scripts/scan_versions.py
git commit -m "feat: add HuggingFace version scanner"
```

---

### Task 2.2: Create URL Health Checker

**Files:**
- Create: `scripts/check_urls.py`

**Step 1: Write URL health checker**

```python
#!/usr/bin/env python3
"""
Check URL health for all preset files
"""

import sys
import yaml
import json
import argparse
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


async def check_url(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Dict[str, Any]:
    """Check if URL is accessible"""
    result = {
        "url": url,
        "status": "unknown",
        "status_code": None,
        "error": None,
        "response_time_ms": None
    }

    try:
        import time
        start = time.time()
        async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as resp:
            result["status_code"] = resp.status
            result["response_time_ms"] = int((time.time() - start) * 1000)

            if resp.status == 200:
                result["status"] = "ok"
            elif resp.status == 401:
                result["status"] = "auth_required"
            elif resp.status == 403:
                result["status"] = "forbidden"
            elif resp.status == 404:
                result["status"] = "not_found"
            else:
                result["status"] = f"http_{resp.status}"

    except asyncio.TimeoutError:
        result["status"] = "timeout"
        result["error"] = "Request timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def check_all_urls(presets_dir: Path, concurrency: int = 5) -> List[Dict[str, Any]]:
    """Check all URLs in all presets"""
    results = []
    semaphore = asyncio.Semaphore(concurrency)

    # Collect all URLs first
    urls_to_check = []
    for category_dir in presets_dir.iterdir():
        if not category_dir.is_dir():
            continue

        for preset_dir in category_dir.iterdir():
            if not preset_dir.is_dir():
                continue

            preset_file = preset_dir / "preset.yaml"
            if not preset_file.exists():
                continue

            with open(preset_file, 'r') as f:
                preset = yaml.safe_load(f)

            for file_info in preset.get("files", []):
                url = file_info.get("url")
                if url:
                    urls_to_check.append({
                        "preset_id": preset.get("id"),
                        "file_path": file_info.get("path"),
                        "url": url
                    })

    print(f"Checking {len(urls_to_check)} URLs...")

    async with aiohttp.ClientSession() as session:
        async def check_with_semaphore(item):
            async with semaphore:
                result = await check_url(session, item["url"])
                result["preset_id"] = item["preset_id"]
                result["file_path"] = item["file_path"]
                print(f"  {result['status']:15} {item['url'][:60]}...")
                return result

        tasks = [check_with_semaphore(item) for item in urls_to_check]
        results = await asyncio.gather(*tasks)

    return results


def main():
    parser = argparse.ArgumentParser(description="Check URL health")
    parser.add_argument("--presets-dir", type=Path, default=Path("presets"))
    parser.add_argument("--output", type=Path, default=Path("url_check.json"))
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent requests")
    args = parser.parse_args()

    results = asyncio.run(check_all_urls(args.presets_dir, args.concurrency))

    with open(args.output, 'w') as f:
        json.dump({
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "results": results
        }, f, indent=2)

    # Summary
    by_status = {}
    for r in results:
        status = r["status"]
        by_status[status] = by_status.get(status, 0) + 1

    print(f"\nURL Health Summary:")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add scripts/check_urls.py
git commit -m "feat: add URL health checker"
```

---

### Task 2.3: Create Scheduled Workflow

**Files:**
- Create: `.github/workflows/scheduled-scan.yml`

**Step 1: Create scheduled workflow**

```yaml
name: Scheduled Preset Scan

on:
  schedule:
    # Run daily at 6 AM UTC
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml aiohttp

      - name: Check URL health
        run: |
          python scripts/check_urls.py --output url_check.json
        continue-on-error: true

      - name: Scan for version updates
        run: |
          python scripts/scan_versions.py --output version_scan.json
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        continue-on-error: true

      - name: Generate registry
        run: |
          python scripts/generate_registry.py

      - name: Create issue for broken URLs
        if: always()
        run: |
          python scripts/create_alert_issue.py --url-check url_check.json --version-scan version_scan.json
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

      - name: Commit updates
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add registry.json url_check.json version_scan.json
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: scheduled scan update"
          git push
```

**Step 2: Commit**

```bash
git add .github/workflows/scheduled-scan.yml
git commit -m "feat: add scheduled scan workflow"
```

---

## Phase 3: Dashboard Integration

### Task 3.1: Add Registry Sync Endpoint

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Add registry sync endpoint**

Add to `dashboard/api/presets.py`:

```python
# Add to imports
import httpx
from datetime import datetime

# Add new endpoint
@router.get("/registry/sync")
async def sync_registry():
    """Sync preset registry from remote source"""
    registry_url = "https://raw.githubusercontent.com/zeroclue/comfyui-presets/main/registry.json"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(registry_url, timeout=30.0)
            resp.raise_for_status()
            registry = resp.json()

            # Update local cache
            preset_cache.set_config({"registry": registry})

            return {
                "status": "synced",
                "timestamp": datetime.utcnow().isoformat(),
                "presets_count": registry.get("stats", {}).get("total", 0)
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch registry: {e}")


@router.get("/registry/status")
async def registry_status():
    """Get current registry status"""
    config = preset_cache.get_config()
    if config and "registry" in config:
        registry = config["registry"]
        return {
            "version": registry.get("version"),
            "generated_at": registry.get("generated_at"),
            "total_presets": registry.get("stats", {}).get("total", 0),
            "categories": registry.get("stats", {}).get("by_category", {})
        }
    return {"status": "not_loaded"}
```

**Step 2: Add httpx dependency**

Add to requirements or Dockerfile if not present.

**Step 3: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat: add registry sync endpoint"
```

---

### Task 3.2: Update Preset Loader for Dual Format

**Files:**
- Modify: `dashboard/api/presets.py`

**Step 1: Update get_presets_from_config**

```python
async def get_presets_from_config() -> Dict:
    """Load presets from configuration file with caching
    Supports both old monolithic YAML and new registry format
    """
    import yaml

    # Check cache first
    cached = preset_cache.get_config()
    if cached:
        return cached

    # Try new registry format first
    registry_path = Path(settings.PRESET_CONFIG_PATH).parent / "registry.json"
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)

        # Convert registry to expected format
        config = {
            "metadata": {
                "version": registry.get("version", "1.0.0"),
                "source": "registry"
            },
            "categories": {
                "Video Generation": {"type": "video"},
                "Image Generation": {"type": "image"},
                "Audio Generation": {"type": "audio"}
            },
            "presets": {}
        }

        # Load each preset file
        for preset_id, preset_meta in registry.get("presets", {}).items():
            preset_path = preset_meta.get("path")
            if preset_path:
                full_path = Path(settings.PRESET_CONFIG_PATH).parent.parent / preset_path
                if full_path.exists():
                    with open(full_path, 'r') as f:
                        preset_data = yaml.safe_load(f)
                        preset_data["installed"] = False  # Will be checked separately
                        config["presets"][preset_id] = preset_data

        preset_cache.set_config(config)
        return config

    # Fallback to old monolithic format
    config_path = Path(settings.PRESET_CONFIG_PATH)
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Preset configuration not found")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    preset_cache.set_config(config)
    return config
```

**Step 2: Commit**

```bash
git add dashboard/api/presets.py
git commit -m "feat: add dual format support for preset loader"
```

---

### Task 3.3: Add Requirements Display to Models Page

**Files:**
- Modify: `dashboard/templates/models.html`

**Step 1: Add VRAM display to preset cards**

Find the preset card template and add:

```html
<!-- Add after download_size display -->
{% if preset.requirements %}
<div class="flex items-center gap-2 text-sm text-gray-500">
    {% if preset.requirements.vram_gb %}
    <span class="flex items-center gap-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"/>
        </svg>
        {{ preset.requirements.vram_gb }}GB VRAM
    </span>
    {% endif %}
</div>
{% endif %}
```

**Step 2: Commit**

```bash
git add dashboard/templates/models.html
git commit -m "feat: add VRAM requirements display to preset cards"
```

---

### Task 3.4: Add Storage Management UI

**Files:**
- Create: `dashboard/templates/storage.html`
- Modify: `dashboard/main.py`

**Step 1: Create storage management page**

```html
{% extends "base.html" %}

{% block title %}Storage Management{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6">Storage Management</h1>

    <!-- Disk Usage -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-lg font-semibold mb-4">Disk Usage</h2>
        <div class="mb-4">
            <div class="flex justify-between mb-1">
                <span class="text-sm text-gray-600">Used</span>
                <span class="text-sm font-medium" id="disk-used">--</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-4">
                <div class="bg-blue-600 h-4 rounded-full" id="disk-bar" style="width: 0%"></div>
            </div>
            <div class="flex justify-between mt-1">
                <span class="text-xs text-gray-500" id="disk-percent">0%</span>
                <span class="text-xs text-gray-500" id="disk-total">-- total</span>
            </div>
        </div>

        <!-- By Category -->
        <div class="space-y-2" id="category-breakdown">
            <!-- Filled by JS -->
        </div>
    </div>

    <!-- Cleanup Suggestions -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">Cleanup Suggestions</h2>
        <div id="cleanup-suggestions" class="space-y-4">
            <!-- Filled by JS -->
        </div>
    </div>
</div>

<script>
async function loadStorageData() {
    try {
        const resp = await fetch('/api/system/resources');
        const data = await resp.json();

        // Update disk usage
        const disk = data.disk;
        document.getElementById('disk-used').textContent = disk.used_formatted;
        document.getElementById('disk-total').textContent = disk.total_formatted;
        document.getElementById('disk-percent').textContent = disk.percent + '%';
        document.getElementById('disk-bar').style.width = disk.percent + '%';
    } catch (e) {
        console.error('Failed to load storage data:', e);
    }
}

loadStorageData();
setInterval(loadStorageData, 30000);
</script>
{% endblock %}
```

**Step 2: Add route to main.py**

```python
@app.get("/storage", response_class=HTMLResponse)
async def storage_page(request: Request):
    return templates.TemplateResponse("storage.html", {"request": request})
```

**Step 3: Commit**

```bash
git add dashboard/templates/storage.html dashboard/main.py
git commit -m "feat: add storage management page"
```

---

## Summary

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Phase 1: Core Infrastructure | 5 tasks | Foundation |
| Phase 2: Management Bot | 3 tasks | Validation |
| Phase 3: Dashboard Integration | 4 tasks | UX |

**Total: 12 bite-sized tasks**

Each task follows TDD principles with:
- Write the code
- Test it
- Commit

---

## Execution Options

After saving the plan:

1. **Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints
