#!/bin/bash

# Create test environment
python -m venv test_venv
source test_venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Redis for testing
docker run -d --name test-redis -p 6379:6379 redis:alpine

# Set up test environment variables
export ENVIRONMENT=test
export REDIS_URL=redis://localhost:6379
export HEROKU_AI_API_KEY=your_test_key  # Replace with actual test key

# Run tests
python scripts/test_system.py

# Cleanup
docker stop test-redis
docker rm test-redis
deactivate