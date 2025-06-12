"""
KIS_AGENT 패키지 설정 파일입니다.

이 파일은 KIS_AGENT 패키지의 설치 및 배포를 위한 설정을 포함합니다.
"""

from setuptools import setup, find_packages

setup(
    name="kis_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.8",
    author="unohee",
    author_email="unohee@example.com",
    description="한국투자증권 OpenAPI를 활용한 자동매매 에이전트",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unohee/KIS_AGENT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 