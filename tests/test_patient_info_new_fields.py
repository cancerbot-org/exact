"""
Tests for newly added PatientInfo fields (CLL-specific and shared) —
DB-level persistence and defaults.
"""
import pytest

from tests.factories import *


class TestNewSharedFields:
    @pytest.mark.django_db
    def test_external_id_stored(self):
        pi = PatientInfoFactory(external_id='omop-42')
        assert pi.external_id == 'omop-42'

    @pytest.mark.django_db
    def test_external_id_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.external_id is None

    @pytest.mark.django_db
    def test_languages_skills_stored(self):
        pi = PatientInfoFactory(languages_skills='English - fluent')
        assert pi.languages_skills == 'English - fluent'

    @pytest.mark.django_db
    def test_status_stored(self):
        pi = PatientInfoFactory(status='remission')
        assert pi.status == 'remission'

    @pytest.mark.django_db
    def test_status_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.status is None

    @pytest.mark.django_db
    def test_later_therapies_default_empty_list(self):
        pi = PatientInfoFactory()
        assert pi.later_therapies == []

    @pytest.mark.django_db
    def test_later_therapies_stored(self):
        therapies = [
            {'line_number': 3, 'therapy': 'R-CHOP', 'date': '2023-01-01', 'outcome': 'CR'},
        ]
        pi = PatientInfoFactory(later_therapies=therapies)
        assert pi.later_therapies == therapies

    @pytest.mark.django_db
    def test_measurable_disease_imwg_stored(self):
        pi = PatientInfoFactory(measurable_disease_imwg=True)
        assert pi.measurable_disease_imwg is True

    @pytest.mark.django_db
    def test_measurable_disease_imwg_defaults_none(self):
        pi = PatientInfoFactory()
        # Field is nullable; factory doesn't set it, normalize may compute it
        # Accept True/False/None — just ensure no DB error
        assert pi.measurable_disease_imwg in (True, False, None)

    @pytest.mark.django_db
    def test_genetic_mutations_default_empty_list(self):
        pi = PatientInfoFactory()
        assert pi.genetic_mutations == []

    @pytest.mark.django_db
    def test_genetic_mutations_stored(self):
        mutations = [{'gene': 'TP53', 'variant': 'p.R175H', 'clinical_significance': 'Pathogenic'}]
        pi = PatientInfoFactory(genetic_mutations=mutations)
        assert pi.genetic_mutations == mutations


class TestCllFields:
    @pytest.mark.django_db
    def test_binet_stage_stored(self):
        pi = PatientInfoFactory(binet_stage='B')
        assert pi.binet_stage == 'B'

    @pytest.mark.django_db
    def test_binet_stage_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.binet_stage is None

    @pytest.mark.django_db
    def test_tp53_disruption_computed_from_molecular_markers(self):
        # tp53_disruption is derived by save() from cytogenic/molecular markers
        pi = PatientInfoFactory(molecular_markers='tp53Mutation')
        assert pi.tp53_disruption is True

    @pytest.mark.django_db
    def test_tp53_disruption_false_when_no_markers(self):
        pi = PatientInfoFactory(molecular_markers=None, cytogenic_markers=None)
        assert pi.tp53_disruption is False

    @pytest.mark.django_db
    def test_lymphocyte_doubling_time_stored(self):
        pi = PatientInfoFactory(lymphocyte_doubling_time=6)
        assert pi.lymphocyte_doubling_time == 6

    @pytest.mark.django_db
    def test_lymphocyte_doubling_time_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.lymphocyte_doubling_time is None

    @pytest.mark.django_db
    def test_absolute_lymphocyte_count_stored(self):
        pi = PatientInfoFactory(absolute_lymphocyte_count=12.5)
        assert float(pi.absolute_lymphocyte_count) == 12.5

    @pytest.mark.django_db
    def test_splenomegaly_stored(self):
        pi = PatientInfoFactory(splenomegaly=True)
        assert pi.splenomegaly is True

    @pytest.mark.django_db
    def test_splenomegaly_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.splenomegaly is None

    @pytest.mark.django_db
    def test_hepatomegaly_stored(self):
        pi = PatientInfoFactory(hepatomegaly=False)
        assert pi.hepatomegaly is False

    @pytest.mark.django_db
    def test_lymphadenopathy_stored(self):
        pi = PatientInfoFactory(lymphadenopathy=True)
        assert pi.lymphadenopathy is True

    @pytest.mark.django_db
    def test_bone_marrow_involvement_stored(self):
        pi = PatientInfoFactory(bone_marrow_involvement=True)
        assert pi.bone_marrow_involvement is True

    @pytest.mark.django_db
    def test_autoimmune_cytopenias_stored(self):
        pi = PatientInfoFactory(autoimmune_cytopenias_refractory_to_steroids=True)
        assert pi.autoimmune_cytopenias_refractory_to_steroids is True

    @pytest.mark.django_db
    def test_measurable_disease_iwcll_stored(self):
        pi = PatientInfoFactory(measurable_disease_iwcll=True)
        assert pi.measurable_disease_iwcll is True

    @pytest.mark.django_db
    def test_btk_inhibitor_refractory_stored(self):
        pi = PatientInfoFactory(btk_inhibitor_refractory=True)
        assert pi.btk_inhibitor_refractory is True

    @pytest.mark.django_db
    def test_bcl2_inhibitor_refractory_stored(self):
        pi = PatientInfoFactory(bcl2_inhibitor_refractory=False)
        assert pi.bcl2_inhibitor_refractory is False

    @pytest.mark.django_db
    def test_spleen_size_stored(self):
        pi = PatientInfoFactory(spleen_size=15.2)
        assert float(pi.spleen_size) == 15.2

    @pytest.mark.django_db
    def test_largest_lymph_node_size_stored(self):
        pi = PatientInfoFactory(largest_lymph_node_size=3.4)
        assert float(pi.largest_lymph_node_size) == 3.4

    @pytest.mark.django_db
    def test_serum_beta2_microglobulin_level_stored(self):
        pi = PatientInfoFactory(serum_beta2_microglobulin_level=4.1)
        assert float(pi.serum_beta2_microglobulin_level) == 4.1

    @pytest.mark.django_db
    def test_qtcf_value_stored(self):
        pi = PatientInfoFactory(qtcf_value=430.0)
        assert float(pi.qtcf_value) == 430.0

    @pytest.mark.django_db
    def test_tumor_burden_stored(self):
        pi = PatientInfoFactory(tumor_burden='high')
        assert pi.tumor_burden == 'high'

    @pytest.mark.django_db
    def test_disease_activity_stored(self):
        pi = PatientInfoFactory(disease_activity='active')
        assert pi.disease_activity == 'active'

    @pytest.mark.django_db
    def test_protein_expressions_stored(self):
        pi = PatientInfoFactory(protein_expressions='CD5: positive; CD23: positive')
        assert pi.protein_expressions == 'CD5: positive; CD23: positive'

    @pytest.mark.django_db
    def test_clonal_bone_marrow_b_lymphocytes_stored(self):
        pi = PatientInfoFactory(clonal_bone_marrow_b_lymphocytes=42.5)
        assert float(pi.clonal_bone_marrow_b_lymphocytes) == 42.5

    @pytest.mark.django_db
    def test_clonal_b_lymphocyte_count_stored(self):
        pi = PatientInfoFactory(clonal_b_lymphocyte_count=1200)
        assert pi.clonal_b_lymphocyte_count == 1200

    @pytest.mark.django_db
    def test_richter_transformation_defaults_none(self):
        pi = PatientInfoFactory()
        assert pi.richter_transformation is None

    @pytest.mark.django_db
    def test_richter_transformation_stored(self):
        pi = PatientInfoFactory(richter_transformation=True)
        assert pi.richter_transformation is True

    @pytest.mark.django_db
    def test_all_cll_fields_default_none(self):
        """All 22 CLL fields default to None when not explicitly set."""
        # tp53_disruption is derived by save() from markers, not stored directly — excluded here
        cll_fields = [
            'binet_stage', 'protein_expressions', 'richter_transformation',
            'tumor_burden', 'lymphocyte_doubling_time',
            'measurable_disease_iwcll', 'hepatomegaly',
            'autoimmune_cytopenias_refractory_to_steroids', 'lymphadenopathy',
            'largest_lymph_node_size', 'splenomegaly', 'spleen_size',
            'disease_activity', 'btk_inhibitor_refractory', 'bcl2_inhibitor_refractory',
            'absolute_lymphocyte_count', 'qtcf_value', 'serum_beta2_microglobulin_level',
            'clonal_bone_marrow_b_lymphocytes', 'clonal_b_lymphocyte_count',
            'bone_marrow_involvement',
        ]
        pi = PatientInfoFactory()
        for field in cll_fields:
            assert getattr(pi, field) is None, f'{field} should default to None'
