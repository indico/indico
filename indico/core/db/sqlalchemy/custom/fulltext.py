import re


TS_REGEX = re.compile(r'([@\<\>!\(\)\&\|])')


def preprocess_ts_string(text, prefix=True):
    atoms = [TS_REGEX.sub(r'\\\1', atom.strip()) for atom in text.split()]
    return ' & '.join('{}:*'.format(atom) if prefix else atom for atom in atoms)
