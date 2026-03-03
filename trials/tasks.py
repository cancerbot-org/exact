from celery import shared_task


@shared_task
def pull_country_and_postal_code(pi_id, longitude, latitude):
    from trials.models import PatientInfo
    from trials.services.patient_info.patient_info_geo_point import PatientInfoGeoPoint

    try:
        patient_info = PatientInfo.objects.get(id=pi_id)
    except PatientInfo.DoesNotExist:
        return
    PatientInfoGeoPoint.update_country_and_postal_code_by_geolocation(longitude, latitude, pi_id)
