"""
pyKis 패키지 설정 파일입니다.

이 파일은 pyKis 패키지의 설치 및 배포를 위한 설정을 포함합니다.
"""

from setuptools import setup, find_packages

setup(
    name="pyKis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "websockets>=12.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.0.0"
    ],
    author="unohee",
    author_email="unohee@github.com",
    description="한국투자증권 OpenAPI Python Wrapper",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unohee/pyKis",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 