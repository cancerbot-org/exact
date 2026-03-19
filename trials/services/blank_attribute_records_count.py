from trials.models import *
from trials.services.user_to_trial_attrs_mapper import UserToTrialAttrsMapper


class BlankAttributeRecordsCount:
    def counts(self, scope=None, patient_info=None):
        if scope is None:
            scope = Trial.objects.all()

        if patient_info is None:
            return {}

        sql_conditions = UserToTrialAttrsMapper().potential_attrs_to_check(patient_info)
        if sql_conditions == {}:
            return {}

        sql_counts = {}
        for attr in sql_conditions.keys():
            sql_counts[attr] = f'SUM{sql_conditions[attr]}'

        out = scope.extra(select=sql_counts).values(*sql_counts.keys())

        out = out[0]
        out = {k: v for k, v in out.items() if v is not None}

        return out
