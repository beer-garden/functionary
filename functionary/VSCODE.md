# Developing using VSCode

For users of VSCode, a variety of tooling is provided in the functionary
repository to help ease the development workflow.

## Workspaces

For organization purposes, treat each directory at the root of the repository as
its own workspace. That is, rather than opening the root folder in VSCode, open
one of the folders at that root level. For example:

- functionary
- runner
- cli

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
`.vscode/settings.json` folder of the workspace.

## Docker Compose

There are several processes and dependent services that are required to run in
order to use functionary. A docker-compose.yml is provided to start and stop all
of these processes with ease.

From within VSCode, there are tasks available to run docker compose up or down.
Press `Ctrl+p`, then type `task functionary`. You should see the following tasks
listed:

- "functionary: docker compose up"
- "functionary: docker compose down"

Run those as needed to start or stop the entire suite of containers.

## Debugging

To debug, a set of launch commands a provided. Specifically:

- For functionary folder
  - runserver
  - run_worker
  - build_worker
- For the runner folder
  - listener
  - worker

These will be available from the "RUN AND DEBUG" dropdown when you are in the
respective workspaces. When launching any of these, if there was already a
container running for that component it will be stopped. Then the process will
be run natively in debug mode through VSCode instead.

You can start more than one of the debug processes at a time, allowing you to
set breakpoints in code for the different processes as needed. To do this for
processes that run in separate workspaces (e.g. functionary and runner), you
will need to launch a separate instance of VSCode for each workspace.

**IMPORTANT NOTE**: When you exit debug mode, the container that was stopped is
not automatically restarted. If you wish to restart it, you can do so easily via
the docker extension tab in VSCode.
