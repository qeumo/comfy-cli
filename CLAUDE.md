# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

comfy-cli is a Python-based command-line interface tool for managing ComfyUI installations, custom nodes, models, and workflows. It provides cross-platform compatibility and supports various GPU configurations (NVIDIA, AMD, Intel Arc, Mac M-Series).

## Development Commands

### Setup and Installation
```bash
# Install in development mode
pip install -e .

# Set environment variable for development
export ENVIRONMENT=dev

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=comfy_cli --cov-report=xml .

# Run specific test files
pytest tests/comfy_cli/command/test_command.py
pytest tests/e2e/test_e2e.py
```

### Code Quality
```bash
# Lint check
ruff check

# Format check (show differences)
ruff format --diff

# Format files
ruff format
```

## Code Architecture

### Entry Points
- **Main CLI entry**: `comfy_cli/cmdline.py` - Contains the main Typer app and all command definitions
- **Module entry**: `comfy_cli/__main__.py` - Simple wrapper that calls main()

### Core Components

#### Command Structure
Commands are organized under `comfy_cli/command/` with submodule structure:
- `custom_nodes/` - Custom node management (install, update, bisect, snapshots)
- `models/` - Model downloading and management
- `github/` - PR information and handling
- `install.py` - ComfyUI installation logic
- `launch.py` - ComfyUI launching with background support and frontend PR testing
- `run.py` - API workflow execution
- `pr_command.py` - PR cache management

#### Key Managers
- **WorkspaceManager** (`workspace_manager.py`) - Handles ComfyUI workspace detection and path management
- **ConfigManager** (`config_manager.py`) - Configuration file management
- **EnvChecker** (`env_checker.py`) - Environment validation (Python version, system info)

#### Utilities
- `uv.py` - Dependency compilation and fast dependency management
- `git_utils.py` - Git operations for ComfyUI and custom nodes
- `file_utils.py` - File system operations
- `tracking.py` - Analytics tracking with Mixpanel
- `ui.py` - Rich-based console UI components

### Command Registration
All commands are registered in `comfy_cli/cmdline.py` using Typer:
- Main commands defined as functions with `@app.command()` decorator
- Subcommands added via `app.add_typer()` for organized command groups
- Mutual exclusivity validation for workspace selection options (`--workspace`, `--recent`, `--here`)

### Workspace Resolution Priority
1. Explicit `--workspace` path
2. `--recent` - most recently used ComfyUI installation
3. `--here` - ComfyUI in current directory
4. Default workspace set via `comfy set-default`
5. Fallback to recent installation
6. Fallback to current directory detection

### PR and Frontend Testing
- Backend PR testing: Install and checkout specific ComfyUI PRs via `--pr` flag
- Frontend PR testing: `--frontend-pr` flag builds and caches frontend PRs from ComfyUI_frontend repo
- PR cache management with automatic expiration (7 days) and size limits (10 builds)

### GPU Platform Detection
Automatic GPU detection with manual override options:
- NVIDIA (with CUDA version selection)
- AMD (ROCm)
- Intel Arc (beta support, requires conda)
- Mac M-Series vs Intel

### Testing Structure
- Unit tests in `tests/comfy_cli/` mirror source structure
- E2E tests in `tests/e2e/`
- Mock data in `tests/uv/mock_*/` for dependency testing
- Test fixtures for UV dependency compilation scenarios

### Configuration Files
- `pyproject.toml` - Project metadata, dependencies, and Ruff configuration
- `pyrightconfig.json` - TypeScript-style Python type checking
- Pre-commit hooks enforce Ruff formatting and linting

### Key Dependencies
- **typer** - CLI framework with rich help and autocompletion
- **rich** - Terminal formatting and progress bars
- **questionary** - Interactive prompts
- **gitpython** - Git operations
- **uv** - Fast Python dependency resolution
- **httpx/requests** - HTTP operations for downloads
- **pyyaml** - Configuration file parsing

### Background Process Management
- Launch ComfyUI in background with `comfy launch --background`
- Process tracking via ConfigManager
- Stop background instances with `comfy stop`
- Background info displayed in `comfy env`

### Model and Custom Node Management
- Integration with ComfyUI-Manager (cm-cli) for custom nodes
- Direct model downloading from CivitAI, Hugging Face
- Snapshot functionality for custom node states
- Bisect tool for debugging custom node conflicts