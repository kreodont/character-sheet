import re
import xml.etree.ElementTree as ElementTree
from collections import namedtuple


def straight_translate(filename: str) -> None:
    """
    For using https://www.alonlinetools.net/FGCharacterSheet.aspx
    Doesn't work for now
    :param filename: xml file exported from Fantasy Grounds
    :return: New xml file created
    """
    with open(f'translated_{filename}', 'w', encoding='utf-8') as output_file:
        with open(filename) as input_file:
            text = input_file.read()
            text = text.replace('<?', '<\!').replace('?>', '\!>')  # to save xml tags
            # text = text.replace('iso-8859-1', 'utf-8')
            text = translate_from_iso_codes(text)
            print(text)
            text = text.replace('<\!', '<?').replace('\!>', '?>')  # restoring xml tags
            output_file.write(text)


def translate_to_iso_codes(text: str) -> str:
    first_letter_code = 192
    all_letters = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя'
    result_text = ''

    for char in text:
        if char == 'ё':
            result_text += '&#184;'
        elif char == 'Ё':
            result_text += '&#168;'
        elif char in all_letters:
            char_position = all_letters.index(char)
            code = first_letter_code + char_position
            result_text += '&#%s;' % code
        else:
            result_text += char

    return result_text


def translate_from_iso_codes(text: str) -> str:
    if isinstance(text, int):
        return str(text)

    if not text:
        return ''

    russian_letters = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя'
    for letter in text:
        try:
            letter_code = int.from_bytes(letter.encode('latin-1'), 'big')  # this is decoding from FG format
        except UnicodeEncodeError:
            # print('Error: %s' % e)
            continue

        if 192 <= letter_code <= 256:
            text = text.replace(letter, russian_letters[letter_code - 192])
        elif letter_code == 184 or letter == '?':
            text = text.replace(letter, 'ё')
        elif letter_code == 168:
            text = text.replace(letter, 'Ё')
    output_text = text
    letters = re.findall('&#.+?;', text)
    for letter in letters:
        if letter == '&#8226;':
            ru_letter = '•'
        elif letter == '&#8212;':
            ru_letter = '—'
        elif letter == '&#8722;':
            ru_letter = '−'
        elif letter == '&#8217;':
            ru_letter = '’'
        elif letter == '&#8211;':
            ru_letter = '–'
        elif letter == '&#184;':
            ru_letter = 'ё'
        elif letter == '&#184;':
            ru_letter = 'Ё'
        else:
            letter_number = int(letter[2:-1]) - 192
            ru_letter = russian_letters[letter_number]

        output_text = output_text.replace(letter, ru_letter)

    return output_text


class Character:
    @staticmethod
    def element_to_dict(element: ElementTree.Element) -> dict:
        dict_to_return = {}
        if element.tag == 'class':
            element.tag = 'class_'

        element.tag = element.tag.replace('-', '_')

        if list(element):  # if it has children
            for e in list(element):
                dict_to_return[e.tag] = Character.element_to_dict(e)
        else:
            dict_to_return[element.tag] = translate_from_iso_codes(element.text)
        return dict_to_return

    def __init__(self, filename: str):
        self.xml = Character.convert(Character.element_to_dict(ElementTree.parse(filename).getroot())['character'])

    @staticmethod
    def convert(dictionary: dict):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = Character.convert(value)
            else:
                return value

        return namedtuple('GenericDict', dictionary.keys())(**dictionary)


if __name__ == '__main__':
    straight_translate('Leila1.xml')
    # character = Character('Leila1.xml')
    # print(character.xml.abilities.strength.score)
