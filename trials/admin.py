from django.contrib import admin

from trials.models import Trial


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ('study_id', 'brief_title', 'disease', 'register')
    search_fields = ('study_id', 'brief_title', 'disease')
    list_filter = ('disease', 'register')
    readonly_fields = ('created_at', 'updated_at')
