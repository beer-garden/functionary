# Functionary Documentation

The documentation for Functionary is built using
[material-mkdocs](https://squidfunk.github.io/mkdocs-material/getting-started/).

## Installing mkdocs

To install mkdocs and other dependencies:

```shell
pip install -r requirements.txt
```

## Previewing Docs

To start a live preview of the documentation as you work on, simply run:

```shell
./devserver.sh
```

Then navigate to [http://localhost:7000](http://localhost:7000) in your browser.

## Build

To build the docs for hosting:

```shell
./build.sh /path/to/output
```

This will run the mkdocs build command and place the documentation in the
specified directory.
