"""
Unified PatientInfo resolver.

Supports two modes:
  - Stateful:   ?patient_info_id=<pk>  — loads PatientInfo from DB
  - Stateless:  body key "patient_info": {...} — builds an in-memory instance
                (no DB write; M2M via _pre_existing_condition_categories attribute)
"""
from rest_framework.exceptions import ValidationError

from trials.services.patient_info.normalize import normalize_patient_info


def resolve_patient_info(request):
    """
    Return a PatientInfo instance (saved or in-memory) from the request.

    Raises ValidationError if neither source is found.
    """
    patient_info_id = request.query_params.get('patient_info_id') or request.data.get('patient_info_id')
    patient_info_data = request.data.get('patient_info')

    if patient_info_id:
        return _load_from_db(patient_info_id)
    elif patient_info_data:
        return _build_in_memory(patient_info_data)
    else:
        raise ValidationError(
            'Provide either "patient_info_id" query param or "patient_info" object in request body.'
        )


def _load_from_db(patient_info_id):
    from trials.models import PatientInfo
    try:
        return PatientInfo.objects.get(pk=patient_info_id)
    except (PatientInfo.DoesNotExist, ValueError, TypeError):
        raise ValidationError(f'PatientInfo with id={patient_info_id} not found.')


def _build_in_memory(data: dict):
    """Build an unsaved PatientInfo from a dict, compute derived fields."""
    from trials.models import PatientInfo, PreExistingConditionCategory

    # Extract M2M fields that can't be set on an unsaved instance
    pre_existing_ids = data.pop('pre_existing_condition_categories', None) or []
    concomitant_ids = data.pop('concomitant_medications', None) or []

    # Convert camelCase keys to snake_case if needed
    snake_data = _to_snake_case(data)

    # Filter to known model fields only
    model_fields = {f.name for f in PatientInfo._meta.get_fields() if hasattr(f, 'column')}
    filtered = {k: v for k, v in snake_data.items() if k in model_fields}

    pi = PatientInfo(**filtered)

    # Attach M2M as synthetic attributes so matchers can read them
    if pre_existing_ids:
        categories = list(PreExistingConditionCategory.objects.filter(pk__in=pre_existing_ids))
    else:
        categories = []
    pi._pre_existing_condition_categories = categories
    pi._concomitant_medications = concomitant_ids

    normalize_patient_info(pi)
    return pi


def _to_snake_case(data: dict) -> dict:
    """Convert camelCase dict keys to snake_case."""
    import re
    def camel_to_snake(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    return {camel_to_snake(k): v for k, v in data.items()}
