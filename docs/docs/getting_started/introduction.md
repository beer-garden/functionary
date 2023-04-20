# Introduction

## Terminology

Before you get started using Functionary, it's helpful to be aware of the
following concepts and terminology.

### Function

An individual unit of code that can be executed. Put simply, it maps directly to
a function written in the language of your choice.

### Package

Packages are groups of related functions. When deploying code to Functionary, it
is deployed as a package containing one or more functions. This logical grouping
makes it easier for developers to manage their function definitions and for
users to find the functions they need to execute.

### Task

A specific execution of a function or workflow is referred to as a task. Viewing
a task lets you see the status, results, and logs of a function or workflow that
has been run.

### Environment

Functionary allows for users and data to be segmented into separate namespaces
called environments. All packages, functions, tasks, etc. belong to a specific
environment. When using Functionary, you select the environment to work in from
those that you have access to and see only the data for that environment.

### Team

Each environment belongs to a team. A team provides a point of access control
and configuration for all of the environments it contains. For instance, a user
can be given a role on a team, which would grant them that role for all
environments within that team. Similarly, variables and secrets can be created
at the team level to be shared with all of the team's environments. Environments
always belong to one and only one team, but a team can contain any number of
environments.

## Next Steps

Now that you are familiar with the basic concepts, check out how to
[create a package of your own](create_a_package.md).
