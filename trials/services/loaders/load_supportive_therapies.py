from trials.models import *
from trials.services.attribute_names import AttributeNames
from trials.services.therapies_mapper import *


class LoadSupportiveTherapies:
    def load_all(self):
        self.load_diseases()
        self.load_therapy_rounds()
        self.load_therapies()
        self.connect_therapies_to_supportive_therapy()

    def load_diseases(self):
        data = {
            'mm': 'Multiple Myeloma',
            'fl': 'Follicular Lymphoma',
            'bc': 'Breast Cancer'
        }

        for code, title in data.items():
            Disease.objects.get_or_create(title=title, defaults={'code': code})

    def load_therapy_rounds(self):
        data = {
            'supportive_therapy': 'Supportive Therapy'
        }

        for code in data.keys():
            TherapyRound.objects.update_or_create(code=code, defaults={'title': data[code]})

    def load_therapies(self):
        data = TherapiesMapper().data()

        all_components = []

        for code in data.keys():
            obj = data[code]
            if 'short_name' in obj:
                title = obj['short_name']
            else:
                title = obj['name']

            descr = obj['descr']

            therapy = Therapy.objects.filter(title=title).first()
            if therapy:
                therapy.code = code
                therapy.save()
            else:
                therapy, _ = Therapy.objects.update_or_create(code=code, defaults={'title': title, 'description': descr})

            components = []
            for component_name in obj['drugs']:
                code = AttributeNames.get_by_camel_case(component_name.lower()).replace(' ', '_').replace('/', '_').replace("'", '_')
                component, _ = TherapyComponent.objects.update_or_create(code=code, defaults={'title': component_name})
                all_components.append(component.code)
                components.append(component)

            therapy.components.set(components)

    def connect_therapies_to_supportive_therapy(self):
        supportive_therapy = TherapyRound.objects.get(code='supportive_therapy')
        diseases = {x.code.lower(): x for x in Disease.objects.all()}

        supportive_mm = TherapiesMapper().supportive_mm()
        supportive_fl = TherapiesMapper().supportive_fl()
        supportive_bc = TherapiesMapper().supportive_bc()

        items = []

        for therapy in Therapy.objects.iterator():
            if therapy.code in supportive_mm:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['mm'], round=supportive_therapy, therapy=therapy)
                items.append(item.id)
            if therapy.code in supportive_fl:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['fl'], round=supportive_therapy, therapy=therapy)
                items.append(item.id)
            if therapy.code in supportive_bc:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['bc'], round=supportive_therapy, therapy=therapy)
                items.append(item.id)

        # cleanup
        DiseaseRoundTherapyConnection.objects.filter(round=supportive_therapy).exclude(id__in=items).delete()
