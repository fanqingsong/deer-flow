#!/bin/bash

# Function to install uv
install_uv() {
  echo "Checking if uv is installed..."
  if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    pip install uv || { echo "Failed to install uv. Please check your Python and pip installation."; exit 1; }
    echo "uv installed successfully."
  else
    echo "uv is already installed."
  fi
}

# Function to install pnpm
install_pnpm() {
  echo "Checking if pnpm is installed..."
  if ! command -v pnpm &> /dev/null; then
    echo "pnpm is not installed. Installing pnpm..."
    npm install -g pnpm || { echo "Failed to install pnpm. Please check your Node.js and npm installation."; exit 1; }
    echo "pnpm installed successfully."
  else
    echo "pnpm is already installed."
  fi
}

# Function to install bun
install_bun() {
  echo "Checking if bun is installed..."
  if ! command -v bun &> /dev/null; then
    echo "bun is not installed. Installing bun..."
    curl -fsSL https://bun.sh/install | bash || { echo "Failed to install bun. Please check your internet connection."; exit 1; }
    echo "bun installed successfully."
  else
    echo "bun is already installed."
  fi
}

# Function to handle development mode with pnpm
dev_mode() {
  echo "Starting DeerFlow in [DEVELOPMENT] mode with pnpm..."
  uv run server.py --reload & SERVER_PID=$!
  cd web && pnpm dev & WEB_PID=$!
  trap "kill $SERVER_PID $WEB_PID" SIGINT SIGTERM
  wait
}

# Function to handle development mode with bun
bun_dev_mode() {
  echo "Starting DeerFlow in [DEVELOPMENT] mode with bun..."
  uv run server.py --reload & SERVER_PID=$!
  cd web && bun dev & WEB_PID=$!
  trap "kill $SERVER_PID $WEB_PID" SIGINT SIGTERM
  wait
}

# Function to handle production mode
prod_mode() {
  echo "Starting DeerFlow in [PRODUCTION] mode..."
  uv run server.py
  cd web && pnpm start
}

# Main logic
case "$1" in  --cli)
    echo "Running DeerFlow CLI..."
    install_uv
    uv run main.py
    ;;
  --install|-i|install)
    echo "Installing dependencies..."
    install_uv
    uv sync
    install_pnpm
    pnpm install
    ;;
  --install-bun|--i-bun)
    echo "Installing bun..."
    install_bun
    ;;
  --install-pnpm|--i-pnpm)
    echo "Installing pnpm..."
    install_pnpm
    ;;
  --install-uv|--i-uv)
    echo "Installing uv..."
    install_uv
    ;;
  --dev|-d|dev|development|--development)
    dev_mode
    ;;
  --bun-dev|-b|bundev|bun-development|--bun-development)
    bun_dev_mode
    ;;
  --prod|-p|prod|production|--production)
    prod_mode
    ;;
  --install-dev)
    echo "Installing dependencies for development mode..."
    install_uv
    uv sync
    install_pnpm
    pnpm install
    dev_mode
    ;;
  --install-bun-dev)
    echo "Installing dependencies for development mode with bun..."
    install_uv
    uv sync
    install_bun
    bun install
    bun_dev_mode
    ;;
  --install-prod)
    echo "Installing dependencies for production mode..."
    install_uv
    uv sync
    install_pnpm
    pnpm install
    prod_mode
    ;;
  "")
    echo "No argument provided. Defaulting to Install and Development mode with bun."
    install_uv
    uv sync
    install_bun
    bun install
    bun_dev_mode
    ;;
  *)
    echo "Invalid argument. Usage: bootstrap.sh [--dev | --prod | --install | --install-bun | --install-pnpm | --install-uv | --bun-dev]"
    exit 1
    ;;
esac
