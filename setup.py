from setuptools import setup, find_packages

setup(
    name="agent-coordinator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "redis>=5.0.1",
        "pydantic>=2.6.1",
        "aiohttp>=3.8.1",
        "fastapi>=0.109.2",
        "uvicorn>=0.27.1",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)