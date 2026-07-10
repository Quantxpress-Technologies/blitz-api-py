from setuptools import setup, find_packages

setup(
    name="blitzsdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "websocket-client>=1.7.0",
        "protobuf>=4.25.0",
    ],
    python_requires=">=3.10",
    description="BlitzConnect SDK for Interactive and Market Data APIs",
    author="BlitzConnect",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
