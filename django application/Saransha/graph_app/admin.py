from django.contrib import admin
from .models import Users_Publication, Publication, FacultyProfile

# Register your models here.

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'designation', 'department', 'created_at')
    list_filter = ('department', 'designation', 'created_at')
    search_fields = ('full_name', 'user__user_name', 'user__user_email', 'department')
    readonly_fields = ('created_at', 'updated_at')
