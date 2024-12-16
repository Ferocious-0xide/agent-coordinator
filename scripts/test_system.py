import asyncio
import logging
from datetime import datetime
from typing import Dict

from coordinator.core.coordinator import CoordinatorService
from coordinator.workers.worker import Worker
from common.models.task import Task, TaskPriority
from common.integrations.heroku_ai import HerokuAIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_workflow():
    """Test basic system workflow"""
    try:
        # Initialize services
        config = {
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'worker': {
                'max_concurrent_tasks': 3,
                'task_timeout': 300
            },
            'monitoring': {
                'health_check_interval': 60,
                'metrics_interval': 30
            }
        }

        # Start coordinator
        coordinator = CoordinatorService(config)
        await coordinator.start()
        logger.info("Coordinator started")

        # Start worker
        worker = Worker("test_worker_1", config)
        await worker.start()
        logger.info("Worker started")

        # Create test task
        test_task = Task(
            id="test_task_1",
            type="test",
            priority=TaskPriority.MEDIUM,
            payload={
                "prompt": "Tell me a joke about programming"
            },
            agent_requirements=["gpt-4"]
        )

        # Submit task
        task_id = await coordinator.submit_task(test_task)
        logger.info(f"Task submitted with ID: {task_id}")

        # Monitor task status
        for _ in range(10):  # Poll for 10 seconds
            status = await coordinator.get_task_status(task_id)
            logger.info(f"Task status: {status}")
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # Cleanup
        await worker.stop()
        await coordinator.stop()
        logger.info("Test completed")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

async def test_ai_integration():
    """Test Heroku AI integration"""
    async with HerokuAIClient() as client:
        try:
            response = await client.generate_completion(
                prompt="Write a hello world program in Python",
                max_tokens=100
            )
            logger.info(f"AI Response: {response}")
        except Exception as e:
            logger.error(f"AI test failed: {e}")
            raise

def run_tests():
    """Run all tests"""
    asyncio.run(test_basic_workflow())
    asyncio.run(test_ai_integration())

if __name__ == "__main__":
    run_tests()