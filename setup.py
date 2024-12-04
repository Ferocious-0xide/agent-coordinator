from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-coordinator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A distributed system for coordinating AI agents using AgentLite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agent-coordinator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "redis>=5.0.1",
        "pydantic>=2.6.1",
        "python-dotenv>=1.0.0",
        
        # Machine Learning
        "torch==2.2.0+cpu",
        "tensorflow-cpu>=2.15.0",
        
        # Async support
        "aioredis>=2.0.1",
        "asyncio>=3.4.3",
        
        # Monitoring and metrics
        "prometheus_client>=0.19.0",
        "psutil>=5.9.8",
        
        # API and web
        "fastapi>=0.109.2",
        "uvicorn>=0.27.1",
        
        # Existing AgentLite dependencies
        "wolframalpha>=5.0.0",
        "wikipedia>=1.4.0",
        "matplotlib>=3.8.2",
        "langchain>=0.1.0",
        "langchain-community>=0.0.16",
    ],
    extras_require={
        'dev': [
            # Testing
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            
            # Development tools
            "black>=24.1.1",
            "isort>=5.13.2",
            "flake8>=7.0.0",
            
            # Documentation
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=2.0.0",
        ],
        'test': [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ],
        'docs': [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.2",
        ]
    },
    entry_points={
        'console_scripts': [
            'coordinator=coordinator.core.coordinator:main',
            'worker=coordinator.workers.worker:main',
        ],
    },
    package_data={
        'agent_coordinator': [
            'config/*.yaml',
            'config/*.json',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/agent-coordinator/issues",
        "Documentation": "https://agent-coordinator.readthedocs.io/",
        "Source Code": "https://github.com/yourusername/agent-coordinator",
    }
)