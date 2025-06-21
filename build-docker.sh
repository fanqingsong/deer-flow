#!/bin/bash

# Docker build script for DeerFlow with better error handling and network configuration

set -e

echo "🚀 Starting Docker build for DeerFlow..."

# Set Docker build arguments for better network handling
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Build arguments
BUILD_ARGS=""
TAG="deer-flow:latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            BUILD_ARGS="$BUILD_ARGS --no-cache"
            shift
            ;;
        --optimized)
            DOCKERFILE="Dockerfile.optimized"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --tag TAG        Set image tag (default: deer-flow:latest)"
            echo "  --no-cache       Build without cache"
            echo "  --optimized      Use optimized Dockerfile"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set default Dockerfile if not specified
DOCKERFILE=${DOCKERFILE:-"Dockerfile"}

echo "📋 Build configuration:"
echo "  Dockerfile: $DOCKERFILE"
echo "  Tag: $TAG"
echo "  Build args: $BUILD_ARGS"

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ Error: Dockerfile '$DOCKERFILE' not found!"
    exit 1
fi

# Function to retry Docker build
retry_build() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "🔄 Build attempt $attempt/$max_attempts..."
        
        if docker build \
            --file "$DOCKERFILE" \
            --tag "$TAG" \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --build-arg UV_NATIVE_TLS=1 \
            --build-arg UV_NO_PROGRESS=0 \
            $BUILD_ARGS \
            .; then
            echo "✅ Build successful!"
            return 0
        else
            echo "❌ Build attempt $attempt failed"
            if [ $attempt -lt $max_attempts ]; then
                echo "⏳ Waiting 10 seconds before retry..."
                sleep 10
            fi
            attempt=$((attempt + 1))
        fi
    done
    
    echo "❌ All build attempts failed"
    return 1
}

# Start the build process
echo "🔨 Starting Docker build..."
if retry_build; then
    echo "🎉 Docker image built successfully!"
    echo "📦 Image: $TAG"
    echo ""
    echo "To run the container:"
    echo "  docker run -p 8000:8000 $TAG"
    echo ""
    echo "To run with environment variables:"
    echo "  docker run -p 8000:8000 -e BASIC_MODEL__api_key=your_key $TAG"
else
    echo "💥 Build failed after all attempts"
    exit 1
fi 