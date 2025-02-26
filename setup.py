from setuptools import setup, find_packages

setup(
    name="masumi_crewai",
    version="0.1.20",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.19.0"
    ],
    author="Patrick Tobler",
    author_email="patrick@nmkr.io",
    description="A package for easily interacting with remote crews via the Masumi protocol.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/masumi-network",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
