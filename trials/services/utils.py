from glom import glom


def glom_or_none(data, key):
    try:
        return glom(data, key)
    except KeyError:
        return None


def to_date(value):
    if not value:
        return None
    parts = value.split('-')
    if len(parts) == 2:
        parts.append('01')
        return '-'.join(parts)
    else:
        return value


def get_overlap(a, b):
    def list_of_str(values):
        return [str(x) for x in values]

    return list(set(list_of_str(a)) & set(list_of_str(b)))
