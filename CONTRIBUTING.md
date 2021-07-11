# Setting up the development environment

The easiest way to setup your development environment and install the needed dependendecies is to use Poetry. For instructions, see [Poetry Docs - Installation](https://python-poetry.org/docs/#installation).

After installing Poetry you can use the following command to install all the needed dependencies:

```sh
poetry install
```

After installing the dependencies, you can enter the Python virtual environment that Poetry created with the following command:
```sh
poetry shell
```

# Running tests and linters

Tests and code linters are executed in CI pipeline when you open a new pull request, but you can also execute them locally. This project contains a Makefile that allows you to easily run all tests and linters with one command:

```sh
# Run tests and linters
make
# Run only tests
make test
# Run only linters
make lint
```

## Running tests with multiple Python versions using Tox

CI pipeline also runs tests using all the supported Python versions. You can use Tox if you want to run these tests yourself, but first you need to have all different Python versions available in your local system.

One option is to use [Pyenv](https://github.com/pyenv/pyenv) to manage different Python versions. For example, if you would want to run the test suite using Python versions 3.6 and 3.7, you can install the needed Python versions with the following commands:

```sh
pyenv install 3.6.14
pyenv install 3.7.11
```

After the installation, you can make the installed Python versions available globally:

```sh
pyenv global 3.6.14 3.7.11
```

Finally, you can run Tox and it should discover the installed Python version automatically:

```sh
tox -e py36,py37
```

You can omit the `-e` argument if you want to run the tests against all supported Python versions. If everything works, the output should be something similar to this:

```sh
...
__________ summary __________
  py36: commands succeeded
  py37: commands succeeded
  congratulations :)
```

# How to build the documentation

The documentation is built using [Sphinx](https://www.sphinx-doc.org). Follow
their documentation for a full introduction. We will see the steps to create the
HTML documentation.

1. Make sure you have installed the dev dependencies, as they include Sphinx.

2. You can build the documentation using the following command. The `docs` folder
   contains the templates, and the `docs-html` is the output directory, which
   you can change. The `-b html` option tells to build the documentation in HTML
   format, which is the default, so it can be omitted, but other options include
   `man` for man pages and `text` for raw text format.
   
```sh
sphinx-build -b html  docs docs-html
```

3. Alternatively the `docs` folder includes a makefile to build in different
   formats into the `docs/_build` folder.
   
```sh
cd docs
make epub
```
