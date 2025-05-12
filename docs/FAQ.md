# FAQ

## Table of Contents

- [General Questions](#general-questions)
  - [Where's the name DeerFlow come from?](#wheres-the-name-deerflow-come-from)
  - [Which models does DeerFlow support?](#which-models-does-deerflow-support)
- [Installation & Setup](#installation--setup)
  - [What's the difference between pnpm and bun?](#whats-the-difference-between-pnpm-and-bun)
  - [Do I need both Python and Node.js?](#do-i-need-both-python-and-nodejs)
  - [Which package manager should I choose?](#which-package-manager-should-i-choose)
- [Running the Application](#running-the-application)  - [What's the difference between CLI and Web UI modes?](#whats-the-difference-between-cli-and-web-ui-modes)
  - [What's the difference between development and production mode?](#whats-the-difference-between-development-and-production-mode)
  - [How do I restart the application?](#how-do-i-restart-the-application)

## General Questions

### Where's the name DeerFlow come from?

DeerFlow is short for **D**eep **E**xploration and **E**fficient **R**esearch **Flow**. It is named after the deer, which is a symbol of gentleness and elegance. We hope DeerFlow can bring a gentle and elegant deep research experience to you.

### Which models does DeerFlow support?

Please refer to the [Configuration Guide](configuration_guide.md) for more details.

## Installation & Setup

### What's the difference between pnpm and bun?

- **pnpm** is a fast, disk space-efficient package manager that creates a non-flat node_modules directory structure.
- **bun** is an all-in-one JavaScript runtime and package manager that offers faster installation and execution speeds.

Both are supported in DeerFlow, and you can choose either based on your preference.

### Do I need both Python and Node.js?

Yes, DeerFlow requires both:
- **Python** (3.12+) for the backend server and research functionality
- **Node.js** (22+) for the web interface

### Which package manager should I choose?

If you're not sure, we recommend:
- **pnpm** for better compatibility and stable performance
- **bun** for faster installation and development experience

Both are fully supported, so you can switch between them at any time.

## Running the Application

### What's the difference between development and production mode?

- **Development Mode** (`-d` or `-b` flag):
  - Hot-reloading for both frontend and backend
  - Detailed error messages
  - Development-specific features enabled

- **Production Mode**:
  - Optimized performance
  - Minimized code
  - Production-ready setup

### How do I restart the application?

1. Stop the current instance:
   - Press Ctrl+C in the terminal
   - Or use Task Manager/Activity Monitor to end the processes

2. Start again using:
   ```bash
   # For pnpm
   ./bootstrap.sh -d    # macOS/Linux
   .\bootstrap.bat -d   # Windows (PowerShell)

   # For bun
   ./bootstrap.sh -b    # macOS/Linux
   .\bootstrap.bat -b   # Windows (PowerShell)
   ```

For more detailed setup instructions, refer to the [Installation Guide](installation_guide.md).

### What's the difference between CLI and Web UI modes?

- **CLI Mode** (`--cli` flag):
  - Simple command-line interface
  - Lightweight, doesn't require web server
  - Perfect for quick research tasks
  - Can be used in scripts
  ```bash
  # Direct method
  uv run main.py
    # Or using bootstrap scripts
  # On macOS/Linux:
  ./bootstrap.sh --cli
  # On Windows (PowerShell):
  .\bootstrap.bat --cli
  ```

- **Web UI Mode** (`-d` or `-b` flag):
  - Rich graphical interface
  - Interactive research experience
  - Real-time updates
  - Better for complex research tasks

Choose CLI mode when you want a simple, straightforward interface, and Web UI mode when you need the full interactive experience.
