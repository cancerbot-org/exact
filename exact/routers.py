class PatientInfoRouter:
    """
    Routes PatientInfo (and its related models) to the 'patients' database
    when PATIENT_DB_URL is configured. Falls back to 'default' otherwise.
    """
    _patient_models = {
        'patientinfo',
        'patientinfopreexistingconditioncategory',
        'studyinfo',
    }

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self._patient_models:
            return 'patients'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self._patient_models:
            return 'patients'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self._patient_models:
            return db == 'patients'
        if db == 'patients':
            return False
        return None
