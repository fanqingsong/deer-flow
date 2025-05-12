# Installation Guide

This guide will walk you through installing and setting up DeerFlow.

## Prerequisites

Ensure your system meets these minimum requirements:
- **[Python](https://www.python.org/downloads/):** Version `3.12+`
- **[Node.js](https://nodejs.org/en/download/):** Version `22+`

## Step 1: Clone the Repository

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
```

## Step 2: Install Python Dependencies

We use `uv` to manage Python dependencies:

```bash
# Install dependencies
uv sync
```

## Step 3: Configure Environment

1. Set up environment variables:
   ```bash
   # Copy example env file
   cp .env.example .env
   ```

2. Configure model settings:
   ```bash
   # Copy example config
   cp conf.yaml.example conf.yaml
   ```

   Edit these files with your API keys and preferences. See [Configuration Guide](configuration_guide.md) for details.

## Step 4: Install Web UI Dependencies

You can use either `pnpm` or `bun` as your Node.js package manager:

```bash
cd web

# Using pnpm
pnpm install

# OR using Bun
bun install
```

## Step 5: Install Additional Tools

```bash
# Install marp for PowerPoint generation
# On macOS:
brew install marp-cli
# On Windows (requires Node.js):
npm install -g @marp-team/marp-cli
```

## Running DeerFlow

### Option 1: Console UI

```bash
# Directly
uv run main.py
# OR

# On macOS/Linux
./bootstrap.sh --cli

# On Windows (Cmd)
.\bootstrap.bat --cli
```
### Option 2: Web UI

Run both backend and frontend in development mode:

#### Using pnpm:
```bash
# On macOS/Linux
./bootstrap.sh -d

# On Windows (PowerShell)
.\bootstrap.bat -d
```

#### Using Bun:
```bash
# On macOS/Linux
./bootstrap.sh -b

# On Windows (PowerShell)
.\bootstrap.bat -b
```

The web interface will be available at http://localhost:3000.

## Development Setup

### Running Tests
```bash
make test
```

### Code Quality
```bash
make lint    # Check code
make format  # Format code
```

## Troubleshooting

### Common Issues

1. Port in use
   - Make sure ports 3000 (frontend) and 8000 (backend) are available
   - Kill any processes using these ports

2. Node.js version mismatch
   - Use `nvm` to install Node.js 22+
   - Verify with `node --version`

3. Package manager issues
   - Update your package manager:
     ```bash
     # For pnpm
     npm install -g pnpm@latest     # For bun
     # On macOS/Linux:
     curl -fsSL https://bun.sh/install | bash
     # On Windows (PowerShell):
     irm https://bun.sh/install.ps1 | iex
     ```

4. Python environment issues
   - Verify Python version: `python --version`
   - Try removing and recreating the virtual environment
   - Make sure `uv` is installed and up to date

For more help, see:
- [Configuration Guide](configuration_guide.md) for settings
- [FAQ](FAQ.md) for common questions
