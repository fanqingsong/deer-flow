# Docker 构建指南

## 问题描述

在构建 Docker 镜像时，可能会遇到以下问题：
- 构建过程卡在下载依赖包（如 `tiktoken`、`aiohttp`）时
- 网络超时导致构建失败
- uv 包管理器下载速度慢

## 解决方案

### 方案 1: 使用优化的 Dockerfile（推荐）

```bash
# 使用优化的 Dockerfile
./build-docker.sh --optimized

# 或者直接使用 docker build
docker build -f Dockerfile.optimized -t deer-flow:latest .
```

### 方案 2: 使用简化的 Dockerfile（避免 uv 问题）

```bash
# 使用简化的 Dockerfile（使用 pip 而不是 uv）
docker build -f Dockerfile.simple -t deer-flow:latest .
```

### 方案 3: 修改原始 Dockerfile

如果问题仍然存在，可以尝试以下修改：

1. **增加超时时间**：
```dockerfile
ENV UV_TIMEOUT=600
ENV UV_RETRIES=5
```

2. **使用国内镜像源**：
```dockerfile
ENV UV_INDEX_URL=https://pypi.org/simple/
ENV UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
```

3. **添加重试机制**：
```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --timeout 600 --retries 5
```

### 方案 4: 使用构建脚本

```bash
# 使用提供的构建脚本
./build-docker.sh

# 使用不同的选项
./build-docker.sh --optimized --no-cache
./build-docker.sh --tag my-deer-flow:v1.0
```

## 网络配置建议

### 1. 配置 Docker 镜像源

在 `/etc/docker/daemon.json` 中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

然后重启 Docker：
```bash
sudo systemctl restart docker
```

### 2. 配置 pip 镜像源

在 Dockerfile 中设置：

```dockerfile
ENV PIP_INDEX_URL=https://pypi.org/simple/
ENV PIP_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 使用代理（如果需要）

```bash
# 设置代理环境变量
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 构建时传递代理
docker build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTPS_PROXY=$HTTPS_PROXY .
```

## 故障排除

### 1. 检查网络连接

```bash
# 测试网络连接
curl -I https://pypi.org/simple/
curl -I https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. 清理 Docker 缓存

```bash
# 清理构建缓存
docker builder prune -f

# 清理所有未使用的资源
docker system prune -a
```

### 3. 使用不同的基础镜像

如果问题持续，可以尝试使用不同的基础镜像：

```dockerfile
# 使用 Ubuntu 而不是 Debian
FROM python:3.12-ubuntu

# 或者使用 Alpine
FROM python:3.12-alpine
```

### 4. 分步构建

```bash
# 先构建基础镜像
docker build --target dependencies -t deer-flow-deps .

# 然后构建完整镜像
docker build --target application -t deer-flow:latest .
```

## 验证构建

构建成功后，可以运行以下命令验证：

```bash
# 运行容器
docker run -p 8000:8000 deer-flow:latest

# 检查健康状态
docker ps
curl http://localhost:8000/health

# 查看日志
docker logs <container_id>
```

## 常见错误及解决方案

### 错误 1: 网络超时
```
ERROR: Could not find a version that satisfies the requirement tiktoken
```

**解决方案**：
- 增加超时时间
- 使用国内镜像源
- 检查网络连接

### 错误 2: 权限问题
```
ERROR: Could not install packages due to an OSError
```

**解决方案**：
- 确保 Docker 有足够权限
- 检查磁盘空间
- 清理 Docker 缓存

### 错误 3: 依赖冲突
```
ERROR: Cannot uninstall 'package'. It is a distutils installed project
```

**解决方案**：
- 使用 `--no-cache-dir` 选项
- 强制重新安装依赖
- 检查版本兼容性

## 性能优化建议

1. **使用多阶段构建**：减少最终镜像大小
2. **合理使用缓存**：避免重复下载依赖
3. **并行构建**：使用 BuildKit 的并行特性
4. **镜像优化**：移除不必要的文件和依赖

## 联系支持

如果问题仍然存在，请：
1. 检查网络环境
2. 尝试不同的构建方案
3. 查看详细的构建日志
4. 在 GitHub Issues 中报告问题 