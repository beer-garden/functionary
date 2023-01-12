from enum import Enum, IntEnum, auto


class Permission(Enum):
    """Enum containing permissions, which consist of one for each of the CRUD
    operations per model. Examples:

        PACKAGE_CREATE = "package:create"
        PACKAGE_READ = "package:read"
        PACKAGE_UPDATE = "package:update"
        PACKAGE_DELETE = "package:delete"

    These are intended to be used with the User has_perm() method and can be provided
    as either the enum or its value:

        # both of these are valid
        user.has_perm(Permission.FUNCTION_READ, environment)
        user.has_perm(Permission.FUNCTION_READ.value, environment)
    """

    ENVIRONMENT_CREATE = "environment:create"
    ENVIRONMENT_READ = "environment:read"
    ENVIRONMENT_UPDATE = "environment:update"
    ENVIRONMENT_DELETE = "environment:delete"

    FUNCTION_CREATE = "function:create"
    FUNCTION_READ = "function:read"
    FUNCTION_UPDATE = "function:update"
    FUNCTION_DELETE = "function:delete"

    PACKAGE_CREATE = "package:create"
    PACKAGE_READ = "package:read"
    PACKAGE_UPDATE = "package:update"
    PACKAGE_DELETE = "package:delete"

    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"

    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"

    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    USERROLE_CREATE = "userrole:create"
    USERROLE_READ = "userrole:read"
    USERROLE_UPDATE = "userrole:update"
    USERROLE_DELETE = "userrole:delete"

    VARIABLE_CREATE = "variable:create"
    VARIABLE_READ = "variable:read"
    VARIABLE_UPDATE = "variable:update"
    VARIABLE_DELETE = "variable:delete"

    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"


class Role(Enum):
    """Enum containing assignable roles"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    READ_ONLY = "read_only"


class RoleHeirarchy(IntEnum):
    """Enum that sorts the role privileges in ascending order"""

    READ_ONLY = auto()
    OPERATOR = auto()
    DEVELOPER = auto()
    ADMIN = auto()


# ADMIN gets all permissions
_ADMIN_PERMISSIONS = [permission.value for permission in Permission]

# READ_ONLY gets read access to all models
_READ_ONLY_PERMISSIONS = [
    permission.value for permission in Permission if ":read" in permission.value
]

# Operators just handle tasking for a team and environment
_OPERATOR_PERMISSIONS = _READ_ONLY_PERMISSIONS + [
    Permission.TASK_CREATE.value,
    Permission.WORKFLOW_CREATE.value,
    Permission.WORKFLOW_UPDATE.value,
    Permission.WORKFLOW_DELETE.value,
]

# Developer role includes Operator roles plus some additional development roles
_DEVELOPER_PERMISSIONS = _OPERATOR_PERMISSIONS + [
    Permission.PACKAGE_CREATE.value,
    Permission.PACKAGE_UPDATE.value,
]

ROLE_PERMISSION_MAP = {
    Role.ADMIN.name: _ADMIN_PERMISSIONS,
    Role.DEVELOPER.name: _DEVELOPER_PERMISSIONS,
    Role.READ_ONLY.name: _READ_ONLY_PERMISSIONS,
    Role.OPERATOR.name: _OPERATOR_PERMISSIONS,
}

# To use this map, pass in the name of the role in uppercase form
ROLE_HEIRARCHY_MAP = {
    Role.READ_ONLY.name: RoleHeirarchy.READ_ONLY,
    Role.OPERATOR.name: RoleHeirarchy.OPERATOR,
    Role.DEVELOPER.name: RoleHeirarchy.DEVELOPER,
    Role.ADMIN.name: RoleHeirarchy.ADMIN,
}
