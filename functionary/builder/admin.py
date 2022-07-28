from django.contrib import admin

from builder.models import Build

admin.site.register(Build, admin.ModelAdmin)
