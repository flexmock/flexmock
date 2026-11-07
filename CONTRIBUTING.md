# Contributing

## Setting up the development environment

The easiest way to setup your development environment and install the needed dependendecies is to use Poetry. For instructions, see [Poetry Docs - Installation](https://python-poetry.org/docs/#installation).

After installing Poetry you can use the following command to install all the needed dependencies:

```
poetry install
```

After installing the dependencies, you can enter the Python virtual environment that Poetry created with the following command:

```
poetry shell
```

## Running tests and linters

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

One option is to use [Pyenv](https://github.com/pyenv/pyenv) to manage different Python versions. For example, if you would want to run the test suite using Python versions 3.12 and 3.13, you can install the needed Python versions with the following commands:

```
pyenv install 3.12
pyenv install 3.13
```

After the installation, you can make the installed Python versions available globally:

```
pyenv global 3.12 3.13
```

Finally, you can run Tox and it should discover the installed Python version automatically:

```
tox -e py312,py313
```

You can omit the `-e` argument if you want to run the tests against all supported Python versions. If everything works, the output should be something similar to this:

```
...
__________ summary __________
  py312: commands succeeded
  py313: commands succeeded
  congratulations :)
```

## Updating documentation

The documentation is built using [Mkdocs](https://www.mkdocs.org/). After
installing the development dependencies, you can simply run the following
command to serve the documentation on your local machine:

```
mkdocs serve
```

For more details, see [Mkdocs - User guide](https://www.mkdocs.org/user-guide/)
and [Mkdocs Material theme documentation](https://squidfunk.github.io/mkdocs-material/).

The documentation is automatically deployed to Read the Docs service on every
new commit to the default branch.

## Releasing a new version

Releases are made with `scripts/release.py`. It needs [GitHub CLI](https://cli.github.com/)
and a clean, up-to-date `master` branch.

1. Bump the version in `pyproject.toml` and `setup.py`, move the entries in the
   `Unreleased` section of `CHANGELOG.md` under the new version, and open a pull
   request. Choose `major`, `minor` or `patch` following semantic versioning. The
   script shows the changes and asks for confirmation before it commits them to a new
   branch, pushes the branch and opens the pull request:

   ```
   poetry run python scripts/release.py prepare minor
   ```

2. Merge the pull request after it has been approved and CI passes. Do not create
   the release before the pull request is merged.

3. Update your local `master` branch and create the GitHub release. The script
   shows the release notes and asks for confirmation before it creates the release
   and its `v`-prefixed tag at the current commit:

   ```
   git switch master
   git pull --ff-only
   poetry run python scripts/release.py release
   ```

4. The release starts the publish workflow, which first runs the CI workflow. After
   the tests and linters pass and the release checks succeed, the workflow waits for
   approval to deploy to the `pypi` environment. Before approving, check that the
   commit of the run is on the default branch and that its `.github/workflows/`
   directory is the same as on the default branch.

Saving a draft or publishing a pre-release does not publish anything to PyPI, but
changing a pre-release to a release does start the workflow.

If the workflow fails before the deployment, nothing has been uploaded to PyPI. Fix
the problem in a pull request, remove the failed release with
`gh release delete v1.2.3 --cleanup-tag` and create it again. If the tag cannot be
reused, release a new version instead.

### Release infrastructure

PyPI trusted publishing is tied to the workflow file `publish.yml` and the `pypi`
environment. The manual approval exists only if the `pypi` environment has required
reviewers: GitHub creates a missing environment without any protection when a
workflow references it. Do not delete or rename the environment, and do not leave
the environment name blank in the PyPI trusted publisher.
