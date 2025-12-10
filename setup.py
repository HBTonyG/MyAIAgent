"""
Setup configuration for MyAIAgent package.
"""

from setuptools import setup
import os
import glob

# Read requirements from requirements.txt
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(req_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
        return requirements

# Collect config files for data_files
config_files = glob.glob('config/*.yaml')

setup(
    name="myaiagent",
    version="0.1.0",
    description="Self-improving AI agent for code improvement and automation",
    author="Tony G",
    py_modules=[
        "main",
        "agent",
        "api_client",
        "browser_automation",
        "config_parser",
        "cursor_integration",
        "database",
        "improvement_engine",
        "project_analyzer",
        "quality_analyzer",
        "self_improvement",
        "website_tester",
    ],
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "myaiagent=main:main",
        ],
    },
    data_files=[
        ('config', config_files),
    ],
    python_requires=">=3.10",
)

