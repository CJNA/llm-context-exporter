"""
Setup configuration for LLM Context Exporter.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "LLM Context Exporter - A tool for migrating context between LLM platforms"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
        return requirements

setup(
    name="llm-context-exporter",
    version="0.1.0",
    author="LLM Context Exporter Team",
    author_email="contact@llm-context-exporter.com",
    description="A tool for migrating context between LLM platforms",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/llm-context-exporter/llm-context-exporter",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.6.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "hypothesis>=6.88.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llm-context-export=llm_context_exporter.cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)