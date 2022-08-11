# Functionary CLI

The functionary CLI is a tool to help you build and publish packages. As it
develops, it will also grow to allow you to interact with Functionary to do
things such as execute tasking, view task results, and much more.

**NOTE:** This guide is written primarily for developers looking to work on the
CLI. Instructions for general users will be added as the tool becomes more
mature.

## Getting Started

To install the `functionary` command into your python environment:

```shell
pip install -e .
```

This will make the `functionary` command available and will link it to the
directory that you installed from so that any changes you make to the code will
be used without needing to re-run the `pip install` command.

## Usage

### Login

```shell
functionary login <functionary_url>
```

This will authenticate to the functionary server and store your api key in the
`~/.functionary` directory. This key will be used to authenticate you when
running any other commands.

### Package

#### Create

To create a new package:

```shell
functionary package create <package_name>
```

### Publish

Once you have finished working on your functions and are ready to publish your
package:

```shell
functionary package publish <package_path> <functionary_url>
```
