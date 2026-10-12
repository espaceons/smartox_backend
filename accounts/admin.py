from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PatientProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'phone_number', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations IoT', {'fields': ('role', 'phone_number')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(PatientProfile)