from django.contrib import admin
from scheduler.models import Schedule

admin.site.register(Schedule, admin.ModelAdmin)
