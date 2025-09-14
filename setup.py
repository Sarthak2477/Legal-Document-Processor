"""
Setup configuration for the contract processing pipeline.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="contract-processing-pipeline",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive pipeline for processing legal contracts using AI/ML",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/contract-processing-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "contract-pipeline=cli:app",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
            "coverage",
        ],
        "layoutlm": [
            "layoutparser[ocr]",
            "detectron2",
        ],
    },
)