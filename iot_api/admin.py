from django.contrib import admin
from .models import DoseLog

@admin.register(DoseLog)
class DoseLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'compartment_number', 'status', 'taken_at')
    list_filter = ('status', 'taken_at', 'compartment_number')
    search_fields = ('patient__username', 'patient__email', 'patient__first_name', 'patient__last_name')
    readonly_fields = ('taken_at',)
    ordering = ('-taken_at',)