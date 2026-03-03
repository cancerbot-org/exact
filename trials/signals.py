import os

from django.db.models.signals import pre_save
from django.dispatch import receiver

from trials.models import PatientInfo
from trials.services.patient_info.normalize import normalize_patient_info


@receiver(pre_save, sender=PatientInfo, dispatch_uid='exact_normalize_patient_info')
def normalize_patient_info_on_save(sender, instance, update_fields, **kwargs):
    """Compute derived fields before saving an existing PatientInfo record."""
    if not instance.pk:
        return  # skip on create; caller should call normalize_patient_info() explicitly

    normalize_patient_info(instance)

    # Queue geolocation lookup if needed (handled separately via Celery)
    if instance.longitude and instance.latitude and not instance.geo_point:
        from trials.tasks import pull_country_and_postal_code
        if str(os.environ.get('PULL_COUNTRY_AND_POSTAL_CODE_INLINE', 'false')).lower() != 'true':
            # Task is dispatched after save in the view/service layer
            pass
