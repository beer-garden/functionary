# CLI

The Functionary CLI is used to perform operations in Functionary from the
commandline. It is used to create and publish packages as well as view the
status of the system.

## Installation

The CLI is available for most x86_64 linux operating systems
[here](/static/utils/functionary). Once downloaded, be sure to put the
executable somewhere in your PATH and to set the executable bit. For example, if
using the bash shell:

```shell
export FUNCTIONARY_BIN=$HOME/.functionary/bin
mkdir -p $FUNCTIONARY_BIN
curl -o $FUNCTIONARY_BIN/functionary <functionary_url>/static/utils/functionary
chmod +x $FUNCTIONARY_BIN/functionary
echo 'export PATH="$PATH:$HOME/.functionary/bin"' >> $HOME/.bashrc

# Optionally set PATH for the current shell so that you do not need to restart
export PATH="$PATH:$FUNCTIONARY_BIN"
```

!!! warning "SELinux Warning"

    On systems with SELinux enabled, the Functionary cli may fail to start due
    to the security restrictions on the /tmp directory. To work around this, set
    the `TMP` environment variable to an alternate location. For example:

    ```shell
    export TMP=$HOME/.functionary/tmp
    mkdir -p $TMP
    ```

    You can alternatively skip putting `$HOME/.functionary/bin` in your PATH and
    instead create an alias in your `.bashrc` that sets `TMP` for you when running
    the cli:

    ```shell
    alias functionary="TMP=$HOME/.functionary/tmp $HOME/.functionary/bin/functionary"
    ```

## Usage

### Login

```shell
functionary login <functionary_url>
```

This will authenticate to the Functionary server and store your api key in the
`~/.functionary` directory. This command must be run once to run commands on the
server. The key will be used to authenticate you when running any other
commands.

### Config

```shell
functionary config <setting> <value>
```

The config command can be used to configure certain settings that the CLI uses,
such as API token and client certificate. Use `--help` to see the configurable
settings.

### Environment

#### Set

`requires login`

Before running any other commands, you must first choose the environment to work
in. This can be done via:

```shell
functionary environment set
```

Any subsequent commands (such as publishing a package) will happen against the
selected environment. The `set` command only needs to be run again when you wish
to switch environments, not before every other command you run.

#### List

`requires login`

You can see the list of available environments and which one is currently active
by doing:

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

`requires login`

Once you have finished working on your functions and are ready to publish your
package:

```shell
functionary package publish <package_path>
```

#### Build Status

`requires login`

When you publish a package, it must be built before it is available for use. To
check the status of your package build, run:

```shell
# all builds
functionary package buildstatus

# specific build
functionary package buildstatus --id <build_id>
```

#### List Packages

`requires login`

To view the packages and their functions for the currently select environment:

```shell
functionary package list
```
