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

### Config

```shell
functionary config <setting> <value>
```

The config command can be used to configure certain settings that the CLI uses,
such as API token and client certificate. Use `--help` to see the configurable
settings.

### Set Environment

```shell
functionary environment set
```

This will show you a list of available environments and allow you to choose
which one to operate on. Any subsequent commands (such as publishing a package)
will happen against the selected environment.

You can also see which environment is currently select by doing:

```shell
functionary environment list
```

### Package

#### Create

To create a new package:

```shell
functionary package create <package_name>
```

#### Publish

Once you have finished working on your functions and are ready to publish your
package:

```shell
functionary package publish <package_path>
```

#### Build Status

When you publish a package, it must be built before it is available for use. To
check the status of your package build, run:

```shell
# all builds
functionary package buildstatus

# specific build
functionary package buildstatus --id <build_id>
```

#### List Packages

To view the packages and their functions for the currently select environment:

```shell
functionary package list
```
