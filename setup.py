"""Flexmock setup.py."""
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

setup(
    name="flexmock",
    version="0.11.0",
    author="Slavek Kabrda, Herman Sheremetyev",
    author_email="slavek@redhat.com",
    url="https://flexmock.readthedocs.io/",
    license="BSD-2-Clause",
    description="flexmock is a testing library for Python that makes it easy to create mocks,"
    "stubs and fakes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="flexmock mock stub test unittest pytest nose",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.6.2,<4.0.0",
    packages=["flexmock"],
    package_dir={"": "src"},
    include_package_data=True,
)
