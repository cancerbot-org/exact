from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from trials.api.patient_info_serializers import PatientInfoSerializer
from trials.models import PatientInfo, PatientInfoPreExistingConditionCategory, PreExistingConditionCategory
from trials.services.patient_info.normalize import normalize_patient_info


def _apply_pre_existing_conditions(data, patient_info):
    """Handle the preExistingConditionCategories field update."""
    raw = data.pop('preExistingConditionCategories', None)
    if raw is None:
        return

    if isinstance(raw, (list, tuple)):
        codes = list(raw)
    else:
        codes = [x.strip() for x in str(raw).split(',') if x.strip()]

    patient_info.no_pre_existing_conditions = codes == ['none']
    patient_info.save(update_fields=['no_pre_existing_conditions'])

    patient_info.pre_existing_condition_categories.all().delete()
    if codes and codes != ['none']:
        cat_map = {
            c.code: c for c in PreExistingConditionCategory.objects.filter(code__in=codes)
        }
        for code in codes:
            if code in cat_map:
                PatientInfoPreExistingConditionCategory.objects.create(
                    patient_info=patient_info, category=cat_map[code]
                )


def _apply_geolocation(data):
    """Unpack geolocation object into longitude/latitude."""
    geo = data.pop('geolocation', None)
    if isinstance(geo, dict):
        data['longitude'] = geo.get('longitude', data.get('longitude'))
        data['latitude'] = geo.get('latitude', data.get('latitude'))


class PatientInfoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientInfoSerializer
    queryset = PatientInfo.objects.all()

    def get_queryset(self):
        qs = PatientInfo.objects.all()
        external_id = self.request.query_params.get('external_id')
        if external_id:
            qs = qs.filter(external_id=external_id)
        return qs

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        _apply_geolocation(data)
        pre_existing = data.pop('preExistingConditionCategories', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        patient_info = serializer.save()

        if pre_existing is not None:
            _apply_pre_existing_conditions({'preExistingConditionCategories': pre_existing}, patient_info)

        normalize_patient_info(patient_info)
        patient_info.save()

        return Response(self.get_serializer(patient_info).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = dict(request.data)
        _apply_geolocation(data)
        pre_existing = data.pop('preExistingConditionCategories', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        patient_info = serializer.save()

        if pre_existing is not None:
            _apply_pre_existing_conditions({'preExistingConditionCategories': pre_existing}, patient_info)

        normalize_patient_info(patient_info)
        patient_info.save()

        return Response(self.get_serializer(patient_info).data)

    @action(methods=['get', 'patch'], detail=True, url_path='study-info')
    def study_info(self, request, pk=None):
        from trials.models import StudyInfo
        from rest_framework import serializers as drf_serializers

        patient_info = self.get_object()

        if request.method == 'GET':
            si = StudyInfo.objects.filter(patient_info=patient_info).first()
            if not si:
                return Response({})

            class StudyInfoSerializer(drf_serializers.ModelSerializer):
                class Meta:
                    model = StudyInfo
                    exclude = ['patient_info']
            return Response(StudyInfoSerializer(si).data)

        # PATCH
        si, _ = StudyInfo.objects.get_or_create(patient_info=patient_info)
        data = request.data

        simple_fields = [
            'search_title', 'search_disease', 'search_treatment', 'sponsor',
            'recruitment_status', 'register', 'country', 'region', 'postal_code',
            'distance', 'distance_units', 'validated_only', 'trial_type',
        ]
        changed = []
        for field in simple_fields:
            camel = _snake_to_camel(field)
            if camel in data:
                setattr(si, field, data[camel])
                changed.append(field)
            elif field in data:
                setattr(si, field, data[field])
                changed.append(field)
        if changed:
            si.save(update_fields=changed)

        return Response({'status': 'ok'})


def _snake_to_camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])
