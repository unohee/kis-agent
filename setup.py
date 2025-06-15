"""
pyKis 패키지 설정 파일입니다.

이 파일은 pyKis 패키지의 설치 및 배포를 위한 설정을 포함합니다.
"""

from setuptools import setup, find_packages

setup(
    name="pykis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "pandas",
        "numpy",
        "pytest",
        "pytest-cov",
    ],
    author="Heewon Oh",
    author_email="heewon@earwire.kr",
    description="KIS API를 사용한 자동매매 에이전트",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unohee/KIS_AGENT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 