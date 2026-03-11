from trials.models import *
from trials.services.attribute_names import AttributeNames
from trials.services.therapies_mapper import *


class LoadTherapies:
    def load_all(self):
        # print("\n\n>>>>LoadTherapies.load_all")
        self.load_diseases()
        self.load_therapy_rounds()
        self.load_therapies()
        self.connect_therapies_to_rounds()
        self.load_components_and_categories()

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
            'first_line_therapy': 'First Line Therapy',
            'second_line_therapy': 'Second Line Therapy',
            'later_therapy': 'Later Therapy'
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
                code = AttributeNames.get_by_camel_case(component_name.lower()).replace(' ', '_')
                component, _ = TherapyComponent.objects.update_or_create(code=code, defaults={'title': component_name})
                all_components.append(component.code)
                components.append(component)

            therapy.components.set(components)
        components2delete = TherapyComponent.objects.exclude(code__in=all_components)
        components2delete.delete()

    def connect_therapies_to_rounds(self):
        rounds = {x.code: x for x in TherapyRound.objects.all()}
        diseases = {x.code.lower(): x for x in Disease.objects.all()}

        first_line_therapy_mm = TherapiesMapper().first_line_mm()
        first_line_therapy_fl = TherapiesMapper().first_line_fl()
        first_line_therapy_bc = TherapiesMapper().first_line_bc()
        second_line_therapy_mm = TherapiesMapper().second_line_mm()
        second_line_therapy_fl = TherapiesMapper().second_line_fl()
        second_line_therapy_bc = TherapiesMapper().second_line_bc()
        later_therapy_mm = TherapiesMapper().later_therapy_mm()
        later_therapy_fl = TherapiesMapper().later_therapy_fl()
        later_therapy_bc = TherapiesMapper().later_therapy_bc()

        items = []

        for therapy in Therapy.objects.iterator():
            if therapy.code in first_line_therapy_mm:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['mm'], round=rounds['first_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in first_line_therapy_fl:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['fl'], round=rounds['first_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in first_line_therapy_bc:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['bc'], round=rounds['first_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in second_line_therapy_mm:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['mm'], round=rounds['second_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in second_line_therapy_fl:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['fl'], round=rounds['second_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in second_line_therapy_bc:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['bc'], round=rounds['second_line_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in later_therapy_mm:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['mm'], round=rounds['later_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in later_therapy_fl:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['fl'], round=rounds['later_therapy'], therapy=therapy)
                items.append(item.id)
            if therapy.code in later_therapy_bc:
                item, _ = DiseaseRoundTherapyConnection.objects.get_or_create(
                    disease=diseases['bc'], round=rounds['later_therapy'], therapy=therapy)
                items.append(item.id)

        # cleanup
        DiseaseRoundTherapyConnection.objects.exclude(id__in=items).delete()

    def load_components_and_categories(self):
        items = []
        for item in TherapiesMapper().category_mapping():
            comp, _ = TherapyComponent.objects.update_or_create(code=item['code'], defaults={'title': item['name']})
            code = AttributeNames.get_by_camel_case(item['type'].lower()).replace(' ', '_')
            cat = TherapyComponentCategory.objects.filter(title=item['type']).first()
            if cat:
                cat.code = code
                cat.save()
            else:
                cat, _ = TherapyComponentCategory.objects.update_or_create(code=code, defaults={'title': item['type']})

            rec, _ = TherapyComponentCategoryConnection.objects.get_or_create(component=comp, category=cat)
            items.append(rec.id)

        # cleanup
        TherapyComponentCategoryConnection.objects.exclude(id__in=items).delete()

    def fix_all(self):
        # therapy_codes = [x.code for x in Therapy.objects.all()]
        # therapy_type_codes = [x.code for x in TherapyComponentCategory.objects.all()]
        therapy_component_codes = [x.code for x in TherapyComponent.objects.all()]
        for trial in Trial.objects.iterator():
            # if trial.therapies_required:
            #     trial.therapies_required = list(set(trial.therapies_required).intersection(therapy_codes))
            # if trial.therapies_excluded:
            #     trial.therapies_excluded = list(set(trial.therapies_excluded).intersection(therapy_codes))
            #
            # if trial.therapy_types_required:
            #     trial.therapy_types_required = list(set(trial.therapy_types_required).intersection(therapy_type_codes))
            # if trial.therapy_types_excluded:
            #     trial.therapy_types_excluded = list(set(trial.therapy_types_excluded).intersection(therapy_type_codes))

            if trial.therapy_components_required:
                trial.therapy_components_required = list(set(trial.therapy_components_required).intersection(therapy_component_codes))
            if trial.therapy_components_excluded:
                trial.therapy_components_excluded = list(set(trial.therapy_components_excluded).intersection(therapy_component_codes))
            trial.save()
