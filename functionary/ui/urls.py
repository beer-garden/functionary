from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    builds,
    environments,
    functions,
    home,
    packages,
    scheduling,
    tasks,
    teams,
    variables,
    workflows,
)

app_name = "ui"

"""
URL naming convention:

Sort the url patterns alphabetically.

For action based URLs, use the following verbs:
    - create
    - delete
    - list
    - detail
    - update

"""


urlpatterns = [
    path("", home.home, name="home"),
    path(
        "build_list/",
        (builds.BuildListView.as_view()),
        name="build-list",
    ),
    path(
        "build/<uuid:pk>",
        (builds.BuildDetailView.as_view()),
        name="build-detail",
    ),
    path(
        "function_list/",
        (functions.FunctionListView.as_view()),
        name="function-list",
    ),
    path(
        "function/<uuid:pk>",
        (functions.FunctionDetailView.as_view()),
        name="function-detail",
    ),
    path("function_execute/", (functions.execute), name="function-execute"),
    path(
        "package_list/",
        (packages.PackageListView.as_view()),
        name="package-list",
    ),
    path(
        "package/<uuid:pk>",
        (packages.PackageDetailView.as_view()),
        name="package-detail",
    ),
    path("task_list/", (tasks.TaskListView.as_view()), name="task-list"),
    path(
        "task/<uuid:pk>",
        (tasks.TaskDetailView.as_view()),
        name="task-detail",
    ),
    path("task/<pk>/log", (tasks.get_task_log), name="task-log"),
    path(
        "task/<uuid:pk>/results",
        (tasks.TaskResultsView.as_view()),
        name="task-results",
    ),
    path(
        "variables/<parent_id>",
        (variables.all_variables),
        name="all-variables",
    ),
    path(
        "add_variable/<parent_id>",
        (variables.VariableView.as_view()),
        name="add-variable",
    ),
    path(
        "update_variable/<pk>/<parent_id>",
        (variables.UpdateVariableView.as_view()),
        name="update-variable",
    ),
    path(
        "delete_variable/<pk>",
        (variables.delete_variable),
        name="delete-variable",
    ),
    path(
        "detail_variable/<pk>",
        (variables.VariableView.as_view()),
        name="detail-variable",
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

htmx_urlpatterns = [
    path(
        "crontab_minute_param/",
        (scheduling.crontab_minute_param),
        name="scheduled-minute-param",
    ),
    path(
        "crontab_hour_param/",
        (scheduling.crontab_hour_param),
        name="scheduled-hour-param",
    ),
    path(
        "crontab_day_of_week_param/",
        (scheduling.crontab_day_of_week_param),
        name="scheduled-day-of-week-param",
    ),
    path(
        "crontab_day_of_month_param/",
        (scheduling.crontab_day_of_month_param),
        name="scheduled-day-of-month-param",
    ),
    path(
        "crontab_month_of_year_param/",
        (scheduling.crontab_month_of_year_param),
        name="scheduled-month-of-year-param",
    ),
    path(
        "function_parameters/",
        (scheduling.function_parameters),
        name="function-parameters",
    ),
    path(
        "new_schedule/",
        (scheduling.ScheduledTaskCreateView.as_view()),
        name="new-schedule",
    ),
    path(
        "update_schedule/<uuid:pk>",
        (scheduling.update_scheduled_task),
        name="update-schedule",
    ),
    path(
        "schedule/<uuid:pk>",
        (scheduling.ScheduledTaskUpdateView.as_view()),
        name="schedule-detail",
    ),
    path(
        "schedule_list/",
        (scheduling.ScheduledTaskListView.as_view()),
        name="schedule-list",
    ),
]

environment_urlpatterns = [
    path(
        "environment/<uuid:pk>",
        (environments.EnvironmentDetailView.as_view()),
        name="environment-detail",
    ),
    path(
        "environment_list/",
        (environments.EnvironmentListView.as_view()),
        name="environment-list",
    ),
    path(
        "environment/set_environment",
        (environments.EnvironmentSelectView.as_view()),
        name="set-environment",
    ),
    path(
        "environment/<uuid:environment_id>/user_role/create",
        (environments.EnvironmentUserRoleCreateView.as_view()),
        name="create-environment-member",
    ),
    path(
        "environment/<uuid:environment_id>/user_role/<int:pk>/delete",
        (environments.EnvironmentUserRoleDeleteView.as_view()),
        name="delete-environment-member",
    ),
    path(
        "environment/<uuid:environment_id>/user_role/<int:pk>/update",
        (environments.EnvironmentUserRoleUpdateView.as_view()),
        name="update-environment-member",
    ),
]

team_urlpatterns = [
    path("team_list/", (teams.TeamListView.as_view()), name="team-list"),
    path(
        "team/<uuid:pk>",
        (teams.TeamDetailView.as_view()),
        name="team-detail",
    ),
    path(
        "team/<team_id>/create",
        (teams.TeamUserRoleCreateView.as_view()),
        name="create-team-member",
    ),
    path(
        "team/<team_id>/delete/<pk>",
        (teams.TeamUserRoleDeleteView.as_view()),
        name="delete-team-member",
    ),
    path(
        "team/<team_id>/update/<pk>",
        (teams.TeamUserRoleUpdateView.as_view()),
        name="update-team-member",
    ),
    path("users/", (teams.get_users), name="get-users"),
]


workflows_urlpatterns = [
    path(
        "workflow_list/",
        (workflows.WorkflowListView.as_view()),
        name="workflow-list",
    ),
    path(
        "workflow/create",
        (workflows.WorkflowCreateView.as_view()),
        name="workflow-create",
    ),
    path(
        "workflow/<uuid:pk>",
        (workflows.WorkflowDetailView.as_view()),
        name="workflow-detail",
    ),
    path(
        "workflow/<uuid:pk>/edit",
        (workflows.WorkflowUpdateView.as_view()),
        name="workflow-update",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/create",
        (workflows.WorkflowParameterCreateView.as_view()),
        name="workflowparameter-create",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/<int:pk>/delete",
        (workflows.WorkflowParameterDeleteView.as_view()),
        name="workflowparameter-delete",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/<int:pk>/edit",
        (workflows.WorkflowParameterUpdateView.as_view()),
        name="workflowparameter-edit",
    ),
]


"""
Append App URL patterns to a main urlpatterns list.

URL patterns should be grouped by the django app they represent.

For example, there should be a list for all the URLs related to
teams, environments, schedules, tasks, etc.

"""
urlpatterns += environment_urlpatterns
urlpatterns += team_urlpatterns
urlpatterns += htmx_urlpatterns + workflows_urlpatterns
