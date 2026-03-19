from trials.models import *
from trials.services.concomitant_medications_mapper import ConcomitantMedicationsMapper


class LoadConcomitantMedications:
    def load_all(self):
        self.load_diseases()
        self.load_items()

    def load_diseases(self):
        data = ConcomitantMedicationsMapper().diseases()

        for code, title in data.items():
            Disease.objects.update_or_create(code=code, defaults={'title': title})

    def load_items(self):
        data = ConcomitantMedicationsMapper().data()

        for code in data.keys():
            obj = data[code]
            title = obj['name']

            item, _ = ConcomitantMedication.objects.update_or_create(code=code.lower(), defaults={'title': title})

            diseases = Disease.objects.filter(code__in=obj['diseases'])
            item.diseases.set(diseases)
