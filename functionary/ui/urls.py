from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    account,
    build,
    environment,
    environment_select,
    function,
    home,
    message,
    package,
    scheduled_task,
    task,
    taskable_objects,
    team,
    theme_select,
    userfile,
    variable,
    workflow,
)

app_name = "ui"

"""
URL naming convention:

Sort the url patterns alphabetically.

For action based URLs, use <model>-<verb> with the following verbs:
    - create
    - delete
    - list
    - detail
    - update

"""


urlpatterns = [
    # path("", task.list.TaskListView.as_view(), name="task-default"),
    path("", home.HomeView.as_view(), name="home"),
    path(
        "builds/",
        (build.BuildListView.as_view()),
        name="build-list",
    ),
    path(
        "builds/<uuid:pk>",
        (build.BuildDetailView.as_view()),
        name="build-detail",
    ),
    path(
        "functions/",
        (function.FunctionListView.as_view()),
        name="function-list",
    ),
    path(
        "functions/<uuid:pk>",
        (function.FunctionDetailView.as_view()),
        name="function-detail",
    ),
    path("function_execute/", (function.execute), name="function-execute"),
    path(
        "function_parameters/",
        (function.function_parameters),
        name="function-parameters",
    ),
    path(
        "packages/",
        (package.PackageListView.as_view()),
        name="package-list",
    ),
    path(
        "packages/<uuid:pk>",
        (package.PackageDetailView.as_view()),
        name="package-detail",
    ),
    path("tasks/", (task.list.TaskListView.as_view()), name="task-list"),
    path(
        "tasks/<uuid:pk>",
        (task.detail.TaskDetailView.as_view()),
        name="task-detail",
    ),
    path("task/<pk>/log", (task.detail.get_task_log), name="task-log"),
    path(
        "tasks/<uuid:pk>/results",
        (task.detail.TaskResultsView.as_view()),
        name="task-results",
    ),
    path(
        "taskable_objects/",
        (taskable_objects.TaskableObjectsView.as_view()),
        name="taskable-objects",
    ),
    path(
        "add_variable/<parent_id>",
        (variable.VariableView.as_view()),
        name="variable-create",
    ),
    path(
        "update_variable/<pk>/<parent_id>",
        (variable.UpdateVariableView.as_view()),
        name="variable-update",
    ),
    path(
        "delete_variable/<pk>",
        (variable.delete_variable),
        name="variable-delete",
    ),
    path(
        "environment_select/",
        (environment_select.EnvironmentSelectView.as_view()),
        name="set-environment",
    ),
    path(
        "theme_select/",
        (theme_select.ThemeSelectView.as_view()),
        name="set-theme",
    ),
    path(
        "messages/",
        (message.retrieve_messages),
        name="retrieve-messages",
    ),
    path(
        "errors/",
        (message.display_generic_error),
        name="display-error",
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

account_urlpatterns = [
    path("account/details", account.details, name="account-detail"),
    path(
        "account/disconnect_social",
        account.disconnect_social,
        name="account-disconnect-social",
    ),
    path("account/token/refresh", account.refresh_token, name="token-refresh"),
]

environment_urlpatterns = [
    path(
        "environments/<uuid:pk>",
        (environment.EnvironmentDetailView.as_view()),
        name="environment-detail",
    ),
    path(
        "environments/<uuid:environment_pk>/user_role/create",
        (environment.EnvironmentUserRoleCreateView.as_view()),
        name="environmentuserrole-create",
    ),
    path(
        "environments/<uuid:environment_pk>/user_role/<uuid:pk>/delete",
        (environment.EnvironmentUserRoleDeleteView.as_view()),
        name="environmentuserrole-delete",
    ),
    path(
        "environments/<uuid:environment_pk>/user_role/<uuid:pk>/update",
        (environment.EnvironmentUserRoleUpdateView.as_view()),
        name="environmentuserrole-update",
    ),
]

scheduling_urlpatterns = [
    path(
        "create_schedule/",
        (scheduled_task.ScheduledTaskCreateView.as_view()),
        name="scheduledtask-create",
    ),
    path(
        "schedules/create",
        (scheduled_task.ScheduleCreateView.as_view()),
        name="schedule-create",
    ),
    path(
        "schedules/<uuid:pk>",
        (scheduled_task.ScheduledTaskDetailView.as_view()),
        name="scheduledtask-detail",
    ),
    path(
        "schedules/<uuid:pk>/update",
        (scheduled_task.ScheduledTaskUpdateView.as_view()),
        name="scheduledtask-update",
    ),
    path(
        "schedules/<uuid:pk>/update_status",
        (scheduled_task.update_status),
        name="scheduledtask-update-status",
    ),
    path(
        "schedules/",
        (scheduled_task.ScheduledTaskListView.as_view()),
        name="scheduledtask-list",
    ),
    path(
        "schedules/archive",
        (scheduled_task.ScheduledTaskArchiveListView.as_view()),
        name="scheduledtask-archive-list",
    ),
    path(
        "crontab_minute_param/",
        (scheduled_task.crontab_minute_param),
        name="scheduled-minute-param",
    ),
    path(
        "crontab_hour_param/",
        (scheduled_task.crontab_hour_param),
        name="scheduled-hour-param",
    ),
    path(
        "crontab_day_of_month_param/",
        (scheduled_task.crontab_day_of_month_param),
        name="scheduled-day-of-month-param",
    ),
    path(
        "crontab_month_of_year_param/",
        (scheduled_task.crontab_month_of_year_param),
        name="scheduled-month-of-year-param",
    ),
    path(
        "crontab_day_of_week_param/",
        (scheduled_task.crontab_day_of_week_param),
        name="scheduled-day-of-week-param",
    ),
]

team_urlpatterns = [
    path(
        "teams/<uuid:pk>",
        (team.TeamDetailView.as_view()),
        name="team-detail",
    ),
    path(
        "teams/<uuid:team_pk>/create",
        (team.TeamUserRoleCreateView.as_view()),
        name="teamuserrole-create",
    ),
    path(
        "teams/<uuid:team_pk>/delete/<pk>",
        (team.TeamUserRoleDeleteView.as_view()),
        name="teamuserrole-delete",
    ),
    path(
        "teams/<uuid:team_pk>/update/<pk>",
        (team.TeamUserRoleUpdateView.as_view()),
        name="teamuserrole-update",
    ),
    path("users/", (team.get_users), name="get-users"),
]

workflows_urlpatterns = [
    path(
        "workflows/",
        (workflow.WorkflowListView.as_view()),
        name="workflow-list",
    ),
    path(
        "workflows/archive",
        (workflow.WorkflowArchiveListView.as_view()),
        name="workflow-archive-list",
    ),
    path(
        "workflows/create",
        (workflow.WorkflowCreateView.as_view()),
        name="workflow-create",
    ),
    path(
        "workflows/<uuid:pk>",
        (workflow.WorkflowDetailView.as_view()),
        name="workflow-detail",
    ),
    path(
        "workflows/<uuid:pk>/edit",
        (workflow.WorkflowUpdateView.as_view()),
        name="workflow-update",
    ),
    path(
        "workflows/<uuid:pk>/update_status",
        (workflow.update_status),
        name="workflow-update-status",
    ),
    path(
        "workflows/<uuid:pk>/delete",
        (workflow.WorkflowDeleteView.as_view()),
        name="workflow-delete",
    ),
    path(
        "workflows/<uuid:workflow_pk>/parameter/create",
        (workflow.WorkflowParameterCreateView.as_view()),
        name="workflowparameter-create",
    ),
    path(
        "workflows/<uuid:workflow_pk>/parameter/<uuid:pk>/delete",
        (workflow.WorkflowParameterDeleteView.as_view()),
        name="workflowparameter-delete",
    ),
    path(
        "workflows/<uuid:workflow_pk>/parameter/<uuid:pk>/edit",
        (workflow.WorkflowParameterUpdateView.as_view()),
        name="workflowparameter-update",
    ),
    path(
        "workflows/<uuid:workflow_pk>/step/create",
        (workflow.WorkflowStepCreateView.as_view()),
        name="workflowstep-create",
    ),
    path(
        "workflows/<uuid:workflow_pk>/step/<uuid:pk>/delete",
        (workflow.WorkflowStepDeleteView.as_view()),
        name="workflowstep-delete",
    ),
    path(
        "workflows/<uuid:workflow_pk>/step/<uuid:pk>/edit",
        (workflow.WorkflowStepUpdateView.as_view()),
        name="workflowstep-update",
    ),
    path(
        "workflows/<uuid:workflow_pk>/step/<uuid:pk>/move",
        (workflow.move_workflow_step),
        name="workflowstep-move",
    ),
    path(
        "workflows/<uuid:workflow_pk>/steps/reorder",
        (workflow.reorder_workflow_steps),
        name="workflowsteps-reorder",
    ),
]

files_urlpatterns = [
    path(
        "files/",
        (userfile.UserFileListView.as_view()),
        name="file-list",
    ),
    path(
        "files/create",
        (userfile.UserFileCreateView.as_view()),
        name="file-create",
    ),
    path(
        "files/<uuid:pk>/update/<str:action>",
        (userfile.UserFileUpdateView.as_view()),
        name="file-update",
    ),
    path(
        "files/<uuid:pk>/share",
        (userfile.update_share),
        name="file-share",
    ),
    path(
        "files/chooser",
        (userfile.UserFileChooserView.as_view()),
        name="file-chooser",
    ),
    path(
        "files/table",
        (userfile.UserFileChooserView.as_view()),
        name="file-table",
    ),
]

"""
Append App URL patterns to a main urlpatterns list.

URL patterns should be grouped by the django app they represent.

For example, there should be a list for all the URLs related to
teams, environments, schedules, tasks, etc.

"""
urlpatterns += account_urlpatterns
urlpatterns += environment_urlpatterns
urlpatterns += files_urlpatterns
urlpatterns += scheduling_urlpatterns
urlpatterns += team_urlpatterns
urlpatterns += workflows_urlpatterns
