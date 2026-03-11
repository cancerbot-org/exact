from trials.models import *


class LoadPlannedTherapyOptions:
    def load_all(self, skip_diseases=True):
        self.load_diseases()
        self.load_data(skip_diseases=skip_diseases)

    def load_data(self, skip_diseases=True):
        data = self.get_data()

        for code, val in data.items():
            obj, _ = PlannedTherapy.objects.update_or_create(code=code, defaults={'title': val['title']})
            if not skip_diseases:
                obj.diseases.set(val.get('diseases', []))

    def load_diseases(self):
        data = {
            'mm': 'Multiple Myeloma',
            'fl': 'Follicular Lymphoma',
            'bc': 'Breast Cancer'
        }

        for code, title in data.items():
            Disease.objects.get_or_create(title=title, defaults={'code': code})

    def get_data(self):
        diseases = {x.code.lower(): x for x in Disease.objects.all()}
        out = {}
        chunks = [
            [self.mm_data(), diseases['mm']],
            [self.fl_data(), diseases['fl']],
            [self.bc_data(), diseases['bc']]]
        for chunk in chunks:
            codes = chunk[0]
            disease = chunk[1]
            for code, title in codes.items():
                new_code = code.lower().replace(' ', '_')
                if new_code not in out:
                    out[new_code] = {
                        'title': title,
                        'diseases': []
                    }
                out[new_code]['diseases'].append(disease)

        return out

    def mm_data(self):
        return {
            "Smoldering MM monitoring": "Smoldering MM monitoring",
            "Induction chemotherapy": "Induction chemotherapy",
            "Lenalidomide-based therapy": "Lenalidomide-based therapy (e.g., VRd: bortezomib, lenalidomide, dexamethasone)",
            "Bortezomib-based therapy": "Bortezomib-based therapy (e.g., VCD, VTD)",
            "Thalidomide-based therapy": "Thalidomide-based therapy",
            "Daratumumab-based therapy": "Daratumumab-based therapy (e.g., Dara-Rd, Dara-VTd)",
            "Carfilzomib-based therapy": "Carfilzomib-based therapy",
            "Ixazomib-based therapy": "Ixazomib-based therapy",
            "Pomalidomide-based therapy": "Pomalidomide-based therapy",
            "Autologous Stem cell transplant": "Autologous Stem cell transplant",
            "Allogeneic Stem cell transplant": "Allogeneic Stem cell transplant",
            "Consolidation therapy": "Consolidation therapy",
            "Maintenance therapy": "Maintenance therapy (e.g., lenalidomide)",
            "High-dose melphalan": "High-dose melphalan",
            "Corticosteroids": "Corticosteroids (e.g., dexamethasone, prednisone)",
            "Proteasome inhibitors": "Proteasome inhibitors",
            "Immunomodulatory drugs": "Immunomodulatory drugs (IMiDs)",
            "Monoclonal antibodies": "Monoclonal antibodies (e.g., daratumumab, elotuzumab, isatuximab)",
            "BCMA-targeted therapy": "BCMA-targeted therapy",
            "CAR-T cell therapy": "CAR-T cell therapy",
            "Bispecific antibodies": "Bispecific antibodies (e.g., mosunetuzumab, glofitamab)",
            "Bispecific T-cell engagers": "Bispecific T-cell engagers (e.g., teclistamab)",
            "Radiotherapy": "Radiotherapy (for plasmacytomas or bone lesions)",
            "Bisphosphonates": "Bisphosphonates (e.g., zoledronic acid)",
            "Denosumab": "Denosumab",
            "Checkpoint inhibitors": "Checkpoint inhibitors (experimental)",
            "Vaccines": "Vaccines (experimental)"
        }

    def fl_data(self):
        return {
            "Radiotherapy": "Radiotherapy",
            "Chemotherapy": "Chemotherapy",
            "Alkylating agents": "Alkylating agents (e.g., bendamustine, cyclophosphamide)",
            "Purine analogs": "Purine analogs (e.g., fludarabine)",
            "R-CHOP": "R-CHOP (rituximab + cyclophosphamide, doxorubicin, vincristine, prednisone)",
            "R-CVP": "R-CVP (rituximab + cyclophosphamide, vincristine, prednisone)",
            "R-Bendamustine": "R-Bendamustine",
            "Rituximab monotherapy": "Rituximab monotherapy",
            "Obinutuzumab": "Obinutuzumab",
            "Targeted therapy": "Targeted therapy",
            "PI3K inhibitors": "PI3K inhibitors (e.g., idelalisib, copanlisib, duvelisib)",
            "BTK inhibitors": "BTK inhibitors (e.g., zanubrutinib, ibrutinib)",
            "Immunotherapy": "Immunotherapy",
            "Checkpoint inhibitors": "Checkpoint inhibitors (e.g., nivolumab, pembrolizumab)",
            "CAR-T cell therapy": "CAR-T cell therapy",
            "Stem cell transplant": "Stem cell transplant",
            "Autologous Stem cell transplant": "Autologous Stem cell transplant",
            "Allogeneic Stem cell transplant": "Allogeneic Stem cell transplant",
            "Maintenance therapy with anti-CD20 antibodies": "Maintenance therapy with anti-CD20 antibodies (e.g., rituximab)",
            "Radioimmunotherapy": "Radioimmunotherapy (e.g., 90Y-ibritumomab tiuxetan)",
            "Bispecific antibodies": "Bispecific antibodies (e.g., mosunetuzumab, glofitamab)"
        }

    def bc_data(self):
        return {
            "Surgery": "Surgery",
            "lumpectomy": "breast-conserving surgery (lumpectomy)",
            "mastectomy": "mastectomy",
            "axillary lymph node dissection": "axillary lymph node dissection",
            "Neoadjuvant Chemotherapy": "Neoadjuvant Chemotherapy",
            "Neoadjuvant Anthracycline-based Chemotherapy": "Neoadjuvant Anthracycline-based Chemotherapy",
            "Neoadjuvant Taxane-based Chemotherapy": "Neoadjuvant Taxane-based Chemotherapy",
            "Neoadjuvant Platinum-based Chemotherapy": "Neoadjuvant Platinum-based Chemotherapy",
            "Neoadjuvant Endocrine/Hormonal Therapy": "Neoadjuvant Endocrine/Hormonal Therapy",
            "Neoadjuvant Aromatase inhibitors": "Neoadjuvant Aromatase inhibitors (e.g., letrozole, anastrozole)",
            "Neoadjuvant Tamoxifen": "Neoadjuvant Tamoxifen",
            "Neoadjuvant Ovarian suppression": "Neoadjuvant Ovarian suppression (e.g., goserelin)",
            "Neoadjuvant HER2-Targeted Therapy": "Neoadjuvant HER2-Targeted Therapy",
            "Neoadjuvant Trastuzumab": "Neoadjuvant Trastuzumab (Herceptin)",
            "Neoadjuvant Pertuzumab": "Neoadjuvant Pertuzumab (Perjeta)",
            "Neoadjuvant Trastuzumab emtansine": "Neoadjuvant Trastuzumab emtansine (T-DM1)",
            "Neoadjuvant Immunotherapy": "Neoadjuvant Immunotherapy",
            "Neoadjuvant Checkpoint inhibitors": "Neoadjuvant Checkpoint inhibitors (e.g., pembrolizumab, atezolizumab)",
            "Neoadjuvant Radiotherapy": "Neoadjuvant Radiotherapy",
            "Neoadjuvant External beam radiation therapy": "Neoadjuvant External beam radiation therapy",
            "Neoadjuvant Targeted intraoperative radiotherapy": "Neoadjuvant Targeted intraoperative radiotherapy",
            "Adjuvant Chemotherapy": "Adjuvant Chemotherapy",
            "Adjuvant Endocrine_Hormonal Therapy": "Adjuvant Endocrine/Hormonal Therapy",
            "Adjuvant HER2-Targeted Therapy": "Adjuvant HER2-Targeted Therapy",
            "Adjuvant trastuzumab": "Adjuvant trastuzumab",
            "Adjuvant Radiotherapy": "Adjuvant Radiotherapy",
            "Chemotherapy": "Chemotherapy",
            "Anthracycline-based Chemotherapy": "Anthracycline-based Chemotherapy",
            "Taxane-based Chemotherapy": "Taxane-based Chemotherapy",
            "Platinum-based Chemotherapy": "Platinum-based Chemotherapy",
            "Endocrine_Hormonal Therapy": "Endocrine/Hormonal Therapy",
            "Aromatase inhibitors": "Aromatase inhibitors (e.g., letrozole, anastrozole)",
            "Tamoxifen": "Tamoxifen",
            "Ovarian suppression": "Ovarian suppression (e.g., goserelin)",
            "HER2-Targeted Therapy": "HER2-Targeted Therapy",
            "Trastuzumab": "Trastuzumab (Herceptin)",
            "Pertuzumab": "Pertuzumab (Perjeta)",
            "Trastuzumab emtansine": "Trastuzumab emtansine (T-DM1)",
            "Immunotherapy": "Immunotherapy",
            "Checkpoint inhibitors": "Checkpoint inhibitors (e.g., pembrolizumab, atezolizumab)",
            "Radiotherapy": "Radiotherapy",
            "External beam radiation therapy": "External beam radiation therapy",
            "Targeted intraoperative radiotherapy": "Targeted intraoperative radiotherapy",
            "Bone-Modifying Agents": "Bone-Modifying Agents",
            "Bisphosphonates": "Bisphosphonates (e.g., zoledronic acid)",
            "Denosumab": "Denosumab"
        }
