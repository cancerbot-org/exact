"""
PatientInfo resolver — stateless (inline JSON) only.

The caller sends patient data as {"patient_info": {...}} in the request body.
No DB lookup is performed; PatientInfo is never persisted by this path.
"""
from trials.services.patient_info.normalize import normalize_patient_info


def resolve_patient_info(request):
    """
    Build an in-memory PatientInfo instance from the request body.

    Returns None if no patient_info payload is present (caller may proceed
    without patient context, e.g. for public trial browsing).
    """
    patient_info_data = request.data.get('patient_info')
    if not patient_info_data:
        return None
    return _build_in_memory(patient_info_data)


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
