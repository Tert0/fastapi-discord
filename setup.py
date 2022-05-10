from setuptools import find_packages, setup

readme = open("README.md", "r").read()

setup(
    name="fastapi_discord",
    packages=find_packages(),
    version="0.2.1",
    description="Discord OAuth FastAPI extension for APIs",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Tert0",
    license="MIT",
    install_requires=["fastapi==0.77.1", "aiohttp==3.8.1", "aiocache==0.11.1"],
    python_requires=">=3.5",
    url="https://github.com/Tert0/fastapi-discord",
)
