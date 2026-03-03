from django.contrib import admin

from trials.models import PatientInfo, Trial


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ('study_id', 'brief_title', 'disease', 'register')
    search_fields = ('study_id', 'brief_title', 'disease')
    list_filter = ('disease', 'register')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PatientInfo)
class PatientInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'disease', 'gender', 'patient_age')
    search_fields = ('external_id', 'disease')
    list_filter = ('disease', 'gender')
