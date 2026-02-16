# Contributing to ComfyUI-Docker

Thank you for your interest in contributing to ComfyUI-Docker! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

---

## Getting Started

### Prerequisites

- Docker and Docker Buildx
- Git
- Python 3.13+ (for local development)
- NVIDIA GPU (for GPU-related development)
- Basic knowledge of ComfyUI

### First Steps

1. **Fork the repository**
   ```bash
   # Fork on GitHub and clone your fork
   git clone https://github.com/YOUR_USERNAME/ComfyUI-Docker.git
   cd ComfyUI-Docker
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ZeroClue/ComfyUI-Docker.git
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Local Development Environment

1. **Build the Docker image**
   ```bash
   # Build the base variant
   docker buildx bake base-12-6

   # Or build a specific variant
   docker buildx bake slim-12-6
   ```

2. **Run the container for development**
   ```bash
   docker run -d \
     --name comfyui-dev \
     --gpus all \
     -p 3000:3000 \
     -p 8080:8080 \
     -p 9000:9000 \
     -v $(pwd)/workspace:/workspace \
     -e ACCESS_PASSWORD=dev \
     zeroclue/comfyui:base-torch2.8.0-cu126
   ```

3. **Access the services**
   - ComfyUI: http://localhost:3000
   - Dashboard: http://localhost:8080
   - Preset Manager: http://localhost:9000

### Dashboard Development

1. **Install dependencies**
   ```bash
   cd app/dashboard
   pip install -r requirements.txt
   ```

2. **Run the dashboard in development mode**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8080
   ```

3. **Frontend development**
   - The frontend uses htmx + Alpine.js + Tailwind CSS
   - Edit files in `templates/` and `static/`
   - Changes are reflected immediately on reload

### ComfyUI Integration Development

1. **Test ComfyUI API**
   ```bash
   # Access ComfyUI shell
   docker exec -it comfyui-dev bash

   # Test API endpoint
   curl http://localhost:3000/system_stats
   ```

2. **Custom Nodes Development**
   - Add custom nodes to `config/custom_nodes.txt`
   - Rebuild the Docker image to include changes
   - Test nodes in ComfyUI interface

---

## Code Style Guidelines

### Python Code Style

- **PEP 8**: Follow PEP 8 style guide
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Include docstrings for all functions and classes
- **Line Length**: Maximum 100 characters per line
- **Imports**: Group imports: standard library, third-party, local

```python
"""
Module docstring describing the purpose of this module.
"""

from typing import Optional
from fastapi import APIRouter

from .core import config


async def example_function(param: str, optional_param: Optional[int] = None) -> dict:
    """
    Brief description of the function.

    Args:
        param: Description of param
        optional_param: Description of optional_param

    Returns:
        Description of return value
    """
    # Implementation
    pass
```

### Bash Script Style

- **Shebang**: Use `#!/bin/bash` for bash scripts
- **Error Handling**: Use `set -e` for error handling
- **Functions**: Use functions for reusable code
- **Comments**: Comment complex logic
- **Variable Names**: Use UPPER_CASE for environment variables

```bash
#!/bin/bash
set -e

# Function to perform a specific task
perform_task() {
    local param="$1"
    echo "Performing task with ${param}"
}

# Main execution
main() {
    perform_task "example"
}

main "$@"
```

### Dockerfile Style

- **Comments**: Document each stage and major steps
- **Layer Optimization**: Combine RUN commands where possible
- **Build Arguments**: Use ARG for configurable values
- **Multi-stage**: Use multi-stage builds for optimization

```dockerfile
# Stage 1: Builder
FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS builder

# Build arguments
ARG PYTHON_VERSION=3.13

# Install dependencies
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*
```

### Frontend Style (htmx + Alpine.js)

- **HTML**: Use semantic HTML5 elements
- **CSS**: Use Tailwind utility classes
- **JavaScript**: Use Alpine.js data components
- **Organization**: Keep templates modular

```html
<div x-data="componentName()" class="container mx-auto p-4">
    <h1 class="text-2xl font-bold" x-text="title"></h1>
    <button @click="handleClick" class="bg-blue-500 text-white px-4 py-2 rounded">
        Click Me
    </button>
</div>

<script>
function componentName() {
    return {
        title: 'Example Component',
        handleClick() {
            // Handle click
        }
    }
}
</script>
```

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if you've changed functionality
2. **Add tests** for new features or bug fixes
3. **Ensure all tests pass** locally
4. **Update CHANGELOG.md** if applicable

### Submitting a Pull Request

1. **Update your branch** with the latest upstream changes
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a pull request**
   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Provide a clear description of your changes
   - Link related issues

### Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain the what and why
- **Related Issues**: Link to related issues
- **Screenshots**: Include screenshots for UI changes
- **Testing**: Describe how you tested your changes

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update

## Testing
Describe how you tested these changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests passing
```

---

## Testing Guidelines

### Unit Tests

- **Location**: `tests/unit/`
- **Framework**: pytest
- **Coverage**: Aim for >80% coverage

```python
import pytest
from app.dashboard.api.presets import list_presets

def test_list_presets():
    """Test listing all presets"""
    result = list_presets()
    assert isinstance(result, dict)
    assert 'presets' in result
```

### Integration Tests

- **Location**: `tests/integration/`
- **Framework**: pytest with testcontainers
- **Focus**: Component interactions

```python
import pytest
from testcontainers.docker import DockerContainer

def test_preset_installation():
    """Test preset installation flow"""
    with DockerContainer("zeroclue/comfyui:base-torch2.8.0-cu126") as container:
        # Test installation
        pass
```

### End-to-End Tests

- **Location**: `tests/e2e/`
- **Framework**: Playwright or Selenium
- **Focus**: User workflows

```python
from playwright.sync_api import Page, expect

def test_preset_installation_ui(page: Page):
    """Test preset installation through UI"""
    page.goto("http://localhost:8080")
    page.click("text=Models")
    page.click("text=Install Preset")
    expect(page).to_have_selector("text=Installation Complete")
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_presets.py::test_list_presets
```

---

## Documentation

### Documentation Standards

- **Clear and Concise**: Use simple language
- **Examples**: Include code examples
- **Diagrams**: Use ASCII diagrams for architecture
- **Up-to-date**: Keep documentation current with code changes

### Documentation Files

- **README.md**: Project overview and quick start
- **docs/ARCHITECTURE.md**: System architecture
- **docs/API.md**: API reference
- **docs/DEPLOYMENT.md**: Deployment guide
- **docs/MIGRATION.md**: Migration guide
- **CONTRIBUTING.md**: This file

### Writing Documentation

- **Use Markdown**: All documentation in Markdown
- **Code Blocks**: Use triple backticks with language
- **Links**: Use relative links for internal docs
- **Sections**: Use proper heading hierarchy

```markdown
## Section Title

Description of the section.

### Subsection

More details.

```python
# Code example
def example():
    pass
```
```

---

## Reporting Issues

### Before Reporting

1. **Search existing issues**: Check if the issue already exists
2. **Check documentation**: Review relevant documentation
3. **Test latest version**: Ensure issue exists in latest version

### Issue Report Template

```markdown
## Description
Clear description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g. Ubuntu 24.04]
- Docker Version: [e.g. 24.0.0]
- Image: [e.g. zeroclue/comfyui:base-torch2.8.0-cu126]
- GPU: [e.g. RTX 4090]

## Logs
Relevant log output

## Additional Context
Any other relevant information
```

### Feature Requests

For feature requests, include:

- **Use Case**: Describe the problem you're trying to solve
- **Proposed Solution**: How you envision the feature
- **Alternatives**: Other approaches considered
- **Impact**: Who would benefit and how

---

## Getting Help

### Community Resources

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and discuss ideas
- **Documentation**: Check docs/ for detailed guides
- **Wiki**: Community-contributed guides

### Contact

- **Maintainers**: Tag maintainers in issues for urgent matters
- **Security**: Report security vulnerabilities privately

---

## Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Credits for each release
- **Documentation**: Special contributors section

---

## License

By contributing to ComfyUI-Docker, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ComfyUI-Docker! Your contributions help make this project better for everyone.
