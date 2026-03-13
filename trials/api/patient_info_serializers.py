class PatientInfoSerializer:
    """
    Serializes an in-memory PatientInfo instance for API responses.

    PatientInfo is a plain Python class (not a Django model); this serializer
    is used purely for output — reading from the in-memory object built by
    resolve_patient_info().
    """

    def __init__(self, instance, **kwargs):
        self.instance = instance

    @property
    def data(self):
        return self.to_representation(self.instance)

    def to_representation(self, instance):
        d = {k: v for k, v in vars(instance).items() if not k.startswith('_')}
        if getattr(instance, 'no_pre_existing_conditions', False):
            d['preExistingConditionCategories'] = ['none']
        else:
            cats = getattr(instance, '_pre_existing_condition_categories', [])
            d['preExistingConditionCategories'] = [c.code for c in cats]
        return d


class GraphPatientInfoSerializer(PatientInfoSerializer):
    """Strip the heavy fields from PatientInfoSerializer for the graph endpoint."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('details', None)
        return data
