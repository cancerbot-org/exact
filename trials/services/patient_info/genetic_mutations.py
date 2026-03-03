class GeneticMutations:
    @staticmethod
    def mutation_genes(pi_genetic_mutations):
        items = [x['gene'] for x in pi_genetic_mutations if x['gene']]
        return sorted(list(set(items)))

    @staticmethod
    def mutation_variants(pi_genetic_mutations):
        items = [x['variant'] for x in pi_genetic_mutations if x['variant']]
        return sorted(list(set(items)))

    @staticmethod
    def mutation_origins(pi_genetic_mutations):
        out = []
        for item in pi_genetic_mutations:
            if item['origin']:
                if item['gene']:
                    out.append(f"{item['origin']}__{item['gene']}")
                if item['variant']:
                    out.append(f"{item['origin']}__{item['variant']}")
        return sorted(list(set(out)))

    @staticmethod
    def mutation_interpretations(pi_genetic_mutations):
        out = []
        for item in pi_genetic_mutations:
            if item['interpretation']:
                if item['gene']:
                    out.append(f"{item['gene']}__{item['interpretation']}")
        return sorted(list(set(out)))
