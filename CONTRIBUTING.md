# How to build the documentation

The documentation is built using [Sphinx](https://www.sphinx-doc.org). Follow
their documentation for a full introduction. We will see the steps to create the
HTML documentation.

1. Make sure you have installed the dev dependencies, as they include Sphinx.

```sh
poetry install
```

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
