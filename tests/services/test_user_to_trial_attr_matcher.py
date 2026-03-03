import pytest

from trials.services.user_to_trial_attr_matcher import UserToTrialAttrMatcher
from tests.factories import *


class TestUserToTrialAttrMatcher:
    @pytest.mark.django_db
    def test_potential_attrs_to_check(self):
        trial = TrialFactory()
        patient_info = PatientInfoFactory(disease='multiple myeloma')

        service = UserToTrialAttrMatcher(trial, patient_info)
        assert service.trial_match_status() == 'eligible'

        trial.age_low_limit = 18
        trial.save()
        assert service.trial_match_status() == 'potential'

        patient_info.patient_age = 16
        patient_info.save()
        assert service.trial_match_status() == 'not_eligible'

    @pytest.mark.django_db
    def test_therapy_related_things_mismatch_status(self):
        trial = TrialFactory()
        patient_info = PatientInfoFactory(disease='multiple myeloma')

        service = UserToTrialAttrMatcher(trial, patient_info)
        assert service.therapy_related_things_mismatch_status() == 'unknown'

        patient_info.prior_therapy = 'None'
        patient_info.save()

        assert service.therapy_related_things_mismatch_status() == 'not_matched'

        patient_info.prior_therapy = 'More than two lines of therapy'
        patient_info.save()

        assert service.therapy_related_things_mismatch_status() == 'unknown'

    @pytest.mark.django_db
    def test_therapy_related_things_match_status(self):
        patient_info = PatientInfoFactory(disease='multiple myeloma', prior_therapy='None')

        trial1 = TrialFactory(therapies_required=['vrd'])
        trial2 = TrialFactory(therapies_excluded=['vrd'])

        assert UserToTrialAttrMatcher(trial1, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'not_matched', 'values': []},
            'therapiesExcluded': {'status': 'matched', 'values': []},
            'therapyTypesRequired': {'status': 'matched', 'values': []},
            'therapyTypesExcluded': {'status': 'matched', 'values': []},
            'therapyComponentsRequired': {'status': 'matched', 'values': []},
            'therapyComponentsExcluded': {'status': 'matched', 'values': []}
        }

        assert UserToTrialAttrMatcher(trial2, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'matched', 'values': []},
            'therapiesExcluded': {'status': 'matched', 'values': []},
            'therapyTypesRequired': {'status': 'matched', 'values': []},
            'therapyTypesExcluded': {'status': 'matched', 'values': []},
            'therapyComponentsRequired': {'status': 'matched', 'values': []},
            'therapyComponentsExcluded': {'status': 'matched', 'values': []}
        }

        patient_info.prior_therapy = 'One line'
        patient_info.first_line_therapy = 'dara_vrd'
        patient_info.save()

        assert UserToTrialAttrMatcher(trial1, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'not_matched', 'values': ['Dara-VRd']},
            'therapiesExcluded': {'status': 'matched', 'values': ['Dara-VRd']},
            'therapyTypesRequired': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Monoclonal Antibody (Anti-CD38)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyTypesExcluded': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Monoclonal Antibody (Anti-CD38)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyComponentsRequired': {'status': 'matched', 'values': ['Bortezomib', 'Daratumumab', 'Dexamethasone', 'Lenalidomide']},
            'therapyComponentsExcluded': {'status': 'matched', 'values': ['Bortezomib', 'Daratumumab', 'Dexamethasone', 'Lenalidomide']}
        }

        assert UserToTrialAttrMatcher(trial2, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'matched', 'values': ['Dara-VRd']},
            'therapiesExcluded': {'status': 'matched', 'values': ['Dara-VRd']},
            'therapyTypesRequired': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Monoclonal Antibody (Anti-CD38)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyTypesExcluded': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Monoclonal Antibody (Anti-CD38)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyComponentsRequired': {'status': 'matched', 'values': ['Bortezomib', 'Daratumumab', 'Dexamethasone', 'Lenalidomide']},
            'therapyComponentsExcluded': {'status': 'matched', 'values': ['Bortezomib', 'Daratumumab', 'Dexamethasone', 'Lenalidomide']}
        }

        patient_info.first_line_therapy = 'vrd'
        patient_info.save()

        assert UserToTrialAttrMatcher(trial1, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'matched', 'values': ['**VRd**']},
            'therapiesExcluded': {'status': 'matched', 'values': ['VRd']},
            'therapyTypesRequired': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyTypesExcluded': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyComponentsRequired': {'status': 'matched', 'values': ['Bortezomib', 'Dexamethasone', 'Lenalidomide']},
            'therapyComponentsExcluded': {'status': 'matched', 'values': ['Bortezomib', 'Dexamethasone', 'Lenalidomide']}
        }

        assert UserToTrialAttrMatcher(trial2, patient_info).therapy_related_things_match_status() == {
            'therapiesRequired': {'status': 'matched', 'values': ['VRd']},
            'therapiesExcluded': {'status': 'not_matched', 'values': ['**VRd**']},
            'therapyTypesRequired': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyTypesExcluded': {'status': 'matched', 'values': ['Corticosteroid', 'Immunomodulatory Drug (IMiD)', 'Proteasome Inhibitor', 'Treatment for High-Risk Smoldering Multiple Myeloma']},
            'therapyComponentsRequired': {'status': 'matched', 'values': ['Bortezomib', 'Dexamethasone', 'Lenalidomide']},
            'therapyComponentsExcluded': {'status': 'matched', 'values': ['Bortezomib', 'Dexamethasone', 'Lenalidomide']}
        }
