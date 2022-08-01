from django.contrib import admin
from django.contrib.auth.models import Group

from core.models import Environment, Function, Package, Team, TeamMember, User

from .user import UserAdmin

admin.site.register(Environment, admin.ModelAdmin)
admin.site.register(Function, admin.ModelAdmin)
admin.site.register(Package, admin.ModelAdmin)
admin.site.register(Team, admin.ModelAdmin)
admin.site.register(TeamMember, admin.ModelAdmin)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
