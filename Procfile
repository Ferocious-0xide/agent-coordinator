# Coordinator Process
web: gunicorn coordinator.core.coordinator:app --workers=2 --threads=4 --worker-class=uvicorn.workers.UvicornWorker --bind=0.0.0.0:$PORT --timeout=120 --keep-alive=5 --access-logfile=- --error-logfile=- --log-level=info

# Worker Processes
worker: python -m coordinator.workers.worker --concurrency=4 --max-tasks=100

# Monitoring Processes
monitor: python -m coordinator.core.monitor
health: python -m coordinator.core.health_check
metrics: python -m coordinator.utils.metrics

# Cleanup Process
cleanup: python -m coordinator.core.cleanup --interval=300

# Release Tasks
release: python -m coordinator.core.db_migrations