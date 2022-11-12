"""Flexmock setup.py."""
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

VERSION = "0.11.3"

setup(
    name="flexmock",
    version=VERSION,
    author="Slavek Kabrda, Herman Sheremetyev",
    author_email="slavek@redhat.com",
    url="https://flexmock.readthedocs.io/",
    project_urls={
        "Documentation": "https://flexmock.readthedocs.io/",
        "Changes": "https://flexmock.readthedocs.io/en/latest/changelog/",
        "Source Code": "https://github.com/flexmock/flexmock",
        "Issue Tracker": "https://github.com/flexmock/flexmock/issues",
    },
    license="BSD-2-Clause",
    description="flexmock is a testing library for Python that makes it easy to create mocks,"
    "stubs and fakes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mock testing test unittest pytest",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Mocking",
        "Topic :: Software Development :: Testing :: Unit",
        "Typing :: Typed",
    ],
    python_requires=">=3.7.1,<4.0.0",
    packages=["flexmock"],
    package_dir={"": "src"},
    include_package_data=True,
    command_options={
        "build_sphinx": {
            "version": ("setup.py", VERSION),
            "release": ("setup.py", VERSION),
        }
    },
)
