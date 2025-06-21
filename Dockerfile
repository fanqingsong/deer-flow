FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables for better network handling
ENV UV_CACHE_DIR=/root/.cache/uv
ENV UV_INDEX_URL=https://pypi.org/simple/
ENV UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
ENV UV_NATIVE_TLS=1
ENV UV_NO_PROGRESS=0

WORKDIR /app

# Pre-cache the application dependencies with better error handling
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the application into the container.
COPY . /app

# Install the application dependencies with better error handling
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

# Run the application.
CMD ["uv", "run", "python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
