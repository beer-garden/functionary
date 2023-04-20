# Developing using VSCode

For users of VSCode, a variety of tooling is provided in the Functionary
repository to help ease the development workflow.

## Workspace

A workspace file, `functionary.code-workspace`, is provided that includes
settings, tasks, and debug launch configuration for the following components:

- cli
- functionary
- runner

Open this workspace file to take advantage of the features described in
throughout the remainder of this readme.

## Extensions

A list of recommended extensions is provided for the project. Once you have
loaded the workspace, navigate to the Extensions tab (`Ctrl+Shift+X`) and you
should see a "RECOMMENDED" section at the bottom. Installing those recommended
extensions is necessary to take advantage of the workflow described in this
document. It will also ensure that various formatting preferences for the
project are respected, as the workspace settings depend upon the various
extensions.

## Workspace Settings

As alluded to above, various settings are predefined for the workspaces. These
mostly include autoformatting settings, including format on save to ensure that
code always adheres to those standards. You can see the various settings in the
`functionary.code-workspace` file.

## Workspace Tasks

### Docker Compose

There are several processes and dependent services that are required to run in
order to use Functionary. A docker-compose.yml is provided to start and stop all
of these processes with ease.

From within VSCode, there are tasks available to run docker compose up or down.
Press `Ctrl+p`, then type `task functionary`. You should see the following tasks
listed:

- "functionary: docker compose up"
- "functionary: docker compose down"

Run those as needed to start or stop the entire suite of containers.

### Seed Database

A task is also provided for running migrations and seeding the database with
some initial data such as teams, environments, and users. This task is listed
as:

- "functionary: apply migrations and load fixtures"

Once this task is run, a superuser will be available with the username and
password both set to "admin". Some initial teams, environments, and users with
various roles are also created. For details on these, view the data in the
django admin pages, or see the
[bootstrap.yaml](../functionary/core/fixtures/bootstrap.yaml) containing the
seed data.

## Debugging

To debug, a set of launch commands is provided:

- runserver (functionary)
- run_listener (functionary)
- run_worker (functionary)
- run_builder (functionary)
- run_scheduler (functionary)
- shell (functionary)
- runner (runner)

These will be available from the dropdown in the "Run and Debug" panel
(`Ctrl+Shift+D`). When launching any of these, if there was already a container
running for that component it will be stopped. Then the process will be run
natively in debug mode through VSCode instead.

You can start more than one of the debug processes at a time, allowing you to
set breakpoints in code for the different processes as needed.

### IMPORTANT NOTES

- Be sure to have the correct Python interpreter / virtual environment selected
  before you start debugging. When you have a Python file open in VSCode, a menu
  item will appear on the far right of the bottom status bar that lets you
  choose which Python to use.
- When you exit debug mode, the container that was stopped is not automatically
  restarted. If you wish to restart it, you can do so easily via the docker
  extension tab in VSCode or by re-running the "functionary: docker compose up"
  task.
