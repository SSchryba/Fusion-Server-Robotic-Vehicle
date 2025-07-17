#!/usr/bin/env python3
"""
Setup script for Fusion Tools Suite
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fusion-tools",
    version="1.0.0",
    author="Fusion AI Community",
    author_email="support@fusionai.dev",
    description="Tools for hybrid LLM fusion server management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fusion-ai/fusion-tools",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fusion-monitor=fusion_tools.run_monitor:main",
            "fusion-controller=fusion_tools.run_controller:main",
            "fusion-chat=fusion_tools.run_chat:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fusion_tools": [
            "config/*.yaml",
            "chat/frontend/*.html",
            "chat/frontend/*.css",
            "chat/frontend/*.js",
        ],
    },
    zip_safe=False,
) 