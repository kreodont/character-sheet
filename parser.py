import re
import xml.etree.ElementTree as ElementTree
from collections import namedtuple
import io
import pdfrw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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


def run_pdf_creation(character_name, template_filename='character_sheet.pdf'):
    character = Character(f'{character_name}.xml')
    print(f'Character "{character.xml.name}" loaded')
    canvas_data = get_overlay_canvas(character)
    form = merge(canvas_data, template_path=template_filename)
    with open(f'{character_name}.pdf', 'wb') as f:
        f.write(form.read())


def write_in_pdf(value, pdf, element_name):
    known_elements_dictionary = {
        'name': {'x': 150, 'y': 715, 'size': 26, 'limit': 10},
        'strength': {'x': 60, 'y': 615, 'size': 28, 'limit': 2, 'plus_minus': True},
        'strength.value': {'x': 59, 'y': 595, 'size': 14, 'limit': 2},
        'dexterity': {'x': 60, 'y': 543, 'size': 28, 'limit': 2, 'plus_minus': True},
        'dexterity.value': {'x': 59, 'y': 523, 'size': 14, 'limit': 2},
        'constitution': {'x': 60, 'y': 471, 'size': 28, 'limit': 2, 'plus_minus': True},
        'constitution.value': {'x': 59, 'y': 451, 'size': 14, 'limit': 2},
    }
    font_size = known_elements_dictionary[element_name]['size']
    if 'plus_minus' in known_elements_dictionary[element_name] and known_elements_dictionary[element_name]['plus_minus'] is True:
        if int(value) > 0:
            value = '+' + value

    if len(value) > known_elements_dictionary[element_name]['limit']:
        font_size = font_size // (len(value) / known_elements_dictionary[element_name]['limit'])

    if font_size < 5:
        font_size = 5

    known_elements_dictionary[element_name]['x'] -= len(value) * font_size // 3  # Centring

    print(f'Font size: {font_size}')
    pdf.setFont('FreeSans', font_size)
    pdf.drawString(x=known_elements_dictionary[element_name]['x'], y=known_elements_dictionary[element_name]['y'], text=value)


def get_overlay_canvas(character: "Character") -> io.BytesIO:
    data = io.BytesIO()
    pdf = canvas.Canvas(data)
    pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))
    write_in_pdf(character.xml.name, pdf, 'name')
    write_in_pdf(character.xml.abilities.strength.bonus, pdf, 'strength')
    write_in_pdf(character.xml.abilities.strength.score, pdf, 'strength.value')
    write_in_pdf(character.xml.abilities.dexterity.bonus, pdf, 'dexterity')
    write_in_pdf(character.xml.abilities.dexterity.score, pdf, 'dexterity.value')
    write_in_pdf(character.xml.abilities.constitution.bonus, pdf, 'constitution')
    write_in_pdf(character.xml.abilities.constitution.score, pdf, 'constitution.value')
    pdf.save()
    data.seek(0)
    return data


def merge(overlay_canvas: io.BytesIO, template_path: str) -> io.BytesIO:
    template_pdf = pdfrw.PdfReader(template_path)
    overlay_pdf = pdfrw.PdfReader(overlay_canvas)
    for page, data in zip(template_pdf.pages, overlay_pdf.pages):
        overlay = pdfrw.PageMerge().add(data)[0]
        pdfrw.PageMerge(page).add(overlay).render()
    form = io.BytesIO()
    pdfrw.PdfWriter().write(form, template_pdf)
    form.seek(0)
    return form


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
    # straight_translate('Leila1.xml')
    # character = Character('Leila1.xml')
    # print(character.xml.abilities.strength.score)
    run_pdf_creation('Leila')
