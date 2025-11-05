# Docker Deployment Guide

Quick guide to run SmartDeal using Docker.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose (included with Docker Desktop)
- Optional: NVIDIA GPU + nvidia-docker (for Ollama VLM)

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f smartdeal

# Stop services
docker-compose down
```

Visit http://localhost:8501

### Option 2: Docker Only

```bash
# Build image
docker build -t smartdeal .

# Run container
docker run -d \
  -p 8501:8501 \
  --name smartdeal-app \
  smartdeal

# View logs
docker logs -f smartdeal-app

# Stop container
docker stop smartdeal-app
```

## Configuration

### 1. Gemini API Key (Optional)

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your-actual-api-key
```

### 2. Ollama VLM (Optional)

To use local Ollama models:

```bash
# Start with Ollama service
docker-compose up -d

# Download a model (in Ollama container)
docker exec smartdeal-ollama ollama pull qwen2.5vl:7b

# Or download multiple models
docker exec smartdeal-ollama ollama pull llava:7b
docker exec smartdeal-ollama ollama pull llama3.2-vision:11b
```

**Note**: Ollama requires GPU support. Remove the GPU configuration in `docker-compose.yml` if you don't have NVIDIA GPU.

## Available Models

### Built-in (No Configuration)
- **Tesseract OCR**: Always available in Docker
- **PaddleOCR**: Always available in Docker

### Requires Configuration
- **Gemini AI**: Requires API key in `.env`
- **Ollama VLM**: Requires Ollama service + model download

## Advanced Usage

### Custom Port

```bash
# Change port mapping
docker run -d -p 8080:8501 --name smartdeal-app smartdeal
# Access at http://localhost:8080
```

### Volume Mounting

```bash
# Mount custom data directory
docker run -d \
  -p 8501:8501 \
  -v /path/to/brochures:/app/data/samples:ro \
  --name smartdeal-app \
  smartdeal
```

### Development Mode

```bash
# Mount source code for live updates
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/src:/app/src \
  --name smartdeal-dev \
  smartdeal
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs smartdeal-app

# Check container status
docker ps -a
```

### Port already in use

```bash
# Use different port
docker run -d -p 8502:8501 --name smartdeal-app smartdeal
```

### Ollama GPU not working

Remove GPU configuration from `docker-compose.yml`:

```yaml
# Remove this section:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Out of memory

Increase Docker memory limit in Docker Desktop settings (recommend 4GB+).

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi smartdeal

# Remove volumes (including Ollama models)
docker-compose down -v
```

## Production Deployment

### Using Docker Compose

```bash
# Production mode with restart policy
docker-compose up -d --scale smartdeal=1
```

### Behind Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name smartdeal.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  smartdeal:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Security Notes

1. **Never commit `.env` file** - Contains API keys
2. **Use secrets** - For production, use Docker secrets
3. **Update regularly** - Keep base images updated
4. **Network isolation** - Use custom networks

## Building for Different Architectures

```bash
# For ARM64 (Apple Silicon, Raspberry Pi)
docker buildx build --platform linux/arm64 -t smartdeal:arm64 .

# For AMD64
docker buildx build --platform linux/amd64 -t smartdeal:amd64 .

# Multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t smartdeal .
```

## Performance Tips

1. **Increase memory**: 4GB recommended for VLM models
2. **Use GPU**: For Ollama VLM performance
3. **Volume caching**: Use volumes for model storage
4. **Multi-stage builds**: Reduce image size (future improvement)

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- GitHub Issues: https://github.com/BufferHund/smart-deal-finder/issues
- Documentation: See README.md
