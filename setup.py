from setuptools import setup, find_packages
import os

# Read README.md if it exists
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="masumi",
    version="0.1.30",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.18.0"
    ],
    author="Patrick Tobler",
    author_email="patrick@nmkr.io",
    description="Masumi Payment Module for Cardano blockchain integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masumi-network/masumi",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 