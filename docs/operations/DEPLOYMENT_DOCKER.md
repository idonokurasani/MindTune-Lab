# Docker Deployment

```bash
docker build -f deploy/docker/Dockerfile.clm -t mindtune/clm:0.9.0 .
docker compose -f deploy/compose/docker-compose.yml up -d
```

The image is non-root, has no baked secrets, mounts `data/` and an external environment file.

Health checks and restart policy are configured in `docker-compose.yml`.
