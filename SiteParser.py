from collections import namedtuple

Spell = namedtuple('Spell', ('name', ))


def fetch_spell(spell_name: str) -> Spell:
    return Spell(name=spell_name)


if __name__ == '__main__':
    fetch_spell('hellish_rebuke')
