from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    builds,
    environment_select,
    environments,
    functions,
    home,
    packages,
    schedules,
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
        "function_parameters/",
        (functions.function_parameters),
        name="function-parameters",
    ),
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
    path(
        "environment_select/",
        (environment_select.EnvironmentSelectView.as_view()),
        name="set-environment",
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

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

scheduling_urlpatterns = [
    path(
        "create_schedule/",
        (schedules.ScheduledTaskCreateView.as_view()),
        name="create-schedule",
    ),
    path(
        "schedule/<uuid:pk>",
        (schedules.ScheduledTaskDetailView.as_view()),
        name="detail-schedule",
    ),
    path(
        "schedule/<uuid:pk>/update",
        (schedules.ScheduledTaskUpdateView.as_view()),
        name="update-schedule",
    ),
    path(
        "schedule_list/",
        (schedules.ScheduledTaskListView.as_view()),
        name="schedule-list",
    ),
    path(
        "crontab_minute_param/",
        (schedules.crontab_minute_param),
        name="scheduled-minute-param",
    ),
    path(
        "crontab_hour_param/",
        (schedules.crontab_hour_param),
        name="scheduled-hour-param",
    ),
    path(
        "crontab_day_of_week_param/",
        (schedules.crontab_day_of_week_param),
        name="scheduled-day-of-week-param",
    ),
    path(
        "crontab_day_of_month_param/",
        (schedules.crontab_day_of_month_param),
        name="scheduled-day-of-month-param",
    ),
    path(
        "crontab_month_of_year_param/",
        (schedules.crontab_month_of_year_param),
        name="scheduled-month-of-year-param",
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
        "workflow/<uuid:pk>/delete",
        (workflows.WorkflowDeleteView.as_view()),
        name="workflow-delete",
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
    path(
        "workflow/<uuid:workflow_pk>/step/create",
        (workflows.WorkflowStepCreateView.as_view()),
        name="workflowstep-create",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/delete",
        (workflows.WorkflowStepDeleteView.as_view()),
        name="workflowstep-delete",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/edit",
        (workflows.WorkflowStepUpdateView.as_view()),
        name="workflowstep-edit",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/move",
        (workflows.move_workflow_step),
        name="workflowstep-move",
    ),
]


"""
Append App URL patterns to a main urlpatterns list.

URL patterns should be grouped by the django app they represent.

For example, there should be a list for all the URLs related to
teams, environments, schedules, tasks, etc.

"""
urlpatterns += environment_urlpatterns
urlpatterns += scheduling_urlpatterns
urlpatterns += team_urlpatterns
urlpatterns += workflows_urlpatterns
