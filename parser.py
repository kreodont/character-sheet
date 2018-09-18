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


def run_pdf_creation(character_name, template_filename='character_sheet_light.pdf'):
    character = Character(f'{character_name}.xml')
    print(f'Character "{character.xml.name}" loaded')
    canvas_data = get_overlay_canvas(character)
    form = merge(canvas_data, template_path=template_filename)
    with open(f'{character_name}.pdf', 'wb') as f:
        f.write(form.read())


def write_in_pdf(value, pdf, element_name):
    known_elements_dictionary = {
        'name':                  {'x': 150, 'y': 715, 'size': 26, 'limit': 10},
        'strength':              {'x': 60, 'y': 615, 'size': 28, 'limit': 2, 'plus_minus': True},
        'strength.value':        {'x': 59, 'y': 595, 'size': 14, 'limit': 2},
        'dexterity':             {'x': 60, 'y': 543, 'size': 28, 'limit': 2, 'plus_minus': True},
        'dexterity.value':       {'x': 59, 'y': 523, 'size': 14, 'limit': 2},
        'constitution':          {'x': 60, 'y': 471, 'size': 28, 'limit': 2, 'plus_minus': True},
        'constitution.value':    {'x': 59, 'y': 451, 'size': 14, 'limit': 2},
        'intellect':             {'x': 60, 'y': 399, 'size': 28, 'limit': 2, 'plus_minus': True},
        'intellect.value':       {'x': 59, 'y': 379, 'size': 14, 'limit': 2},
        'wisdom':                {'x': 60, 'y': 327, 'size': 28, 'limit': 2, 'plus_minus': True},
        'wisdom.value':          {'x': 59, 'y': 307, 'size': 14, 'limit': 2},
        'charisma':              {'x': 60, 'y': 255, 'size': 28, 'limit': 2, 'plus_minus': True},
        'charisma.value':        {'x': 59, 'y': 235, 'size': 14, 'limit': 2},
        'passive_perception':    {'x': 45, 'y': 187, 'size': 16, 'limit': 2},
        'profbonus':             {'x': 110, 'y': 610, 'size': 16, 'limit': 2},
        'strength.saveprof':     {'x': 105, 'y': 578, 'size': 14, 'limit': 1},
        'dexterity.saveprof':    {'x': 105, 'y': 564, 'size': 14, 'limit': 1},
        'constitution.saveprof': {'x': 105, 'y': 550, 'size': 14, 'limit': 1},
        'intellect.saveprof':    {'x': 105, 'y': 537, 'size': 14, 'limit': 1},
        'wisdom.saveprof':       {'x': 105, 'y': 523, 'size': 14, 'limit': 1, },
        'charisma.saveprof':     {'x': 105, 'y': 509, 'size': 14, 'limit': 1},
        'strength.save':         {'x': 120, 'y': 578, 'size': 14, 'limit': 2, 'plus_minus': True},
        'dexterity.save':        {'x': 120, 'y': 564, 'size': 14, 'limit': 2, 'plus_minus': True},
        'constitution.save':     {'x': 120, 'y': 550, 'size': 14, 'limit': 2, 'plus_minus': True},
        'intellect.save':        {'x': 120, 'y': 537, 'size': 14, 'limit': 2, 'plus_minus': True},
        'wisdom.save':           {'x': 120, 'y': 523, 'size': 14, 'limit': 2, 'plus_minus': True},
        'charisma.save':         {'x': 120, 'y': 509, 'size': 14, 'limit': 2, 'plus_minus': True},

        'acrobatics.prof':       {'x': 105, 'y': 463, 'size': 14, 'limit': 2},
        'investigation.prof':    {'x': 105, 'y': 449, 'size': 14, 'limit': 2},
        'athletic.prof':         {'x': 105, 'y': 436, 'size': 14, 'limit': 2},
        'perception.prof':       {'x': 105, 'y': 422, 'size': 14, 'limit': 2},
        'survival.prof':         {'x': 105, 'y': 409, 'size': 14, 'limit': 2},
        'performance.prof':      {'x': 105, 'y': 395, 'size': 14, 'limit': 2},
        'intimidation.prof':     {'x': 105, 'y': 382, 'size': 14, 'limit': 2},
        'history.prof':          {'x': 105, 'y': 368, 'size': 14, 'limit': 2},
        'sleight_of_hand.prof':  {'x': 105, 'y': 355, 'size': 14, 'limit': 2},
        'arcana.prof':           {'x': 105, 'y': 341, 'size': 14, 'limit': 2},
        'medicine.prof':         {'x': 105, 'y': 328, 'size': 14, 'limit': 2},
        'deception.prof':        {'x': 105, 'y': 314, 'size': 14, 'limit': 2},
        'nature.prof':           {'x': 105, 'y': 301, 'size': 14, 'limit': 2},
        'insight.prof':          {'x': 105, 'y': 287, 'size': 14, 'limit': 2},
        'religion.prof':         {'x': 105, 'y': 274, 'size': 14, 'limit': 2},
        'stealth.prof':          {'x': 105, 'y': 260, 'size': 14, 'limit': 2},
        'persuasion.prof':       {'x': 105, 'y': 247, 'size': 14, 'limit': 2},
        'animal_handling.prof':  {'x': 105, 'y': 233, 'size': 14, 'limit': 2},

        'acrobatics':            {'x': 120, 'y': 463, 'size': 14, 'limit': 2, 'plus_minus': True},
        'investigation':         {'x': 120, 'y': 449, 'size': 14, 'limit': 2, 'plus_minus': True},
        'athletic':              {'x': 120, 'y': 436, 'size': 14, 'limit': 2, 'plus_minus': True},
        'perception':            {'x': 120, 'y': 422, 'size': 14, 'limit': 2, 'plus_minus': True},
        'survival':              {'x': 120, 'y': 409, 'size': 14, 'limit': 2, 'plus_minus': True},
        'performance':           {'x': 120, 'y': 395, 'size': 14, 'limit': 2, 'plus_minus': True},
        'intimidation':          {'x': 120, 'y': 382, 'size': 14, 'limit': 2, 'plus_minus': True},
        'history':               {'x': 120, 'y': 368, 'size': 14, 'limit': 2, 'plus_minus': True},
        'sleight_of_hand':       {'x': 120, 'y': 355, 'size': 14, 'limit': 2, 'plus_minus': True},
        'arcana':                {'x': 120, 'y': 341, 'size': 14, 'limit': 2, 'plus_minus': True},
        'medicine':              {'x': 120, 'y': 328, 'size': 14, 'limit': 2, 'plus_minus': True},
        'deception':             {'x': 120, 'y': 314, 'size': 14, 'limit': 2, 'plus_minus': True},
        'nature':                {'x': 120, 'y': 301, 'size': 14, 'limit': 2, 'plus_minus': True},
        'insight':               {'x': 120, 'y': 287, 'size': 14, 'limit': 2, 'plus_minus': True},
        'religion':              {'x': 120, 'y': 274, 'size': 14, 'limit': 2, 'plus_minus': True},
        'stealth':               {'x': 120, 'y': 260, 'size': 14, 'limit': 2, 'plus_minus': True},
        'persuasion':            {'x': 120, 'y': 247, 'size': 14, 'limit': 2, 'plus_minus': True},
        'animal_handling':       {'x': 120, 'y': 233, 'size': 14, 'limit': 2, 'plus_minus': True},

        'armor':                 {'x': 248, 'y': 640, 'size': 14, 'limit': 2},
        'initiative':            {'x': 301, 'y': 640, 'size': 14, 'limit': 2, 'plus_minus': True},
        'speed':                 {'x': 361, 'y': 640, 'size': 14, 'limit': 2},
        'class_level':           {'x': 270, 'y': 730, 'size': 10, 'limit': 15, 'dont_center': True},
        'race':                  {'x': 270, 'y': 704, 'size': 10, 'limit': 20, 'dont_center': True},
        'alignment':             {'x': 380, 'y': 704, 'size': 10, 'limit': 20, 'dont_center': True},
        'background':            {'x': 380, 'y': 730, 'size': 10, 'limit': 20, 'dont_center': True},
        'hp_max':                {'x': 300, 'y': 587, 'size': 10, 'limit': 3},
        'total_dice':            {'x': 255, 'y': 466, 'size': 10, 'limit': 2},
        'dice':                  {'x': 230, 'y': 450, 'size': 10, 'limit': 15, 'dont_center': True},
        'magic1':                {'x': 220, 'y': 335, 'size': 10, 'limit': 40, 'dont_center': True},
        'magic2':                {'x': 220, 'y': 323, 'size': 7, 'limit': 60, 'dont_center': True},
        'magic3':                {'x': 220, 'y': 312, 'size': 10, 'limit': 40, 'dont_center': True},
        'magic4':                {'x': 220, 'y': 302, 'size': 7, 'limit': 60, 'dont_center': True},
        'magic5':                {'x': 220, 'y': 290, 'size': 6, 'limit': 60, 'dont_center': True},
        'magic6':                {'x': 220, 'y': 279, 'size': 6, 'limit': 60, 'dont_center': True},
        'magic7':                {'x': 220, 'y': 268, 'size': 6, 'limit': 60, 'dont_center': True},
        'magic8':                {'x': 220, 'y': 258, 'size': 8, 'limit': 60, 'dont_center': True},
        'magic9':                {'x': 220, 'y': 246, 'size': 10, 'limit': 40, 'dont_center': True},
        'magic10':               {'x': 220, 'y': 234, 'size': 10, 'limit': 40, 'dont_center': True},
        'magic11':               {'x': 220, 'y': 222, 'size': 10, 'limit': 40, 'dont_center': True},

        'weapon0.name':          {'x': 260, 'y': 390, 'size': 10, 'limit': 12},
        'weapon1.name':          {'x': 260, 'y': 370, 'size': 10, 'limit': 12},
        'weapon2.name':          {'x': 260, 'y': 350, 'size': 10, 'limit': 12},
        'weapon0.attack':        {'x': 305, 'y': 390, 'size': 10, 'limit': 12, 'plus_minus': True},
        'weapon1.attack':        {'x': 305, 'y': 370, 'size': 10, 'limit': 12, 'plus_minus': True},
        'weapon2.attack':        {'x': 305, 'y': 350, 'size': 10, 'limit': 12, 'plus_minus': True},
        'weapon0.damage':        {'x': 370, 'y': 390, 'size': 10, 'limit': 12},
        'weapon1.damage':        {'x': 370, 'y': 370, 'size': 10, 'limit': 12},
        'weapon2.damage':        {'x': 370, 'y': 350, 'size': 10, 'limit': 12},

        'feature1':              {'x': 410, 'y': 400, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature2':              {'x': 410, 'y': 390, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature3':              {'x': 410, 'y': 378, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature4':              {'x': 410, 'y': 368, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature5':              {'x': 410, 'y': 357, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature6':              {'x': 410, 'y': 346, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature7':              {'x': 410, 'y': 335, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature8':              {'x': 410, 'y': 324, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature9':              {'x': 410, 'y': 313, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature10':             {'x': 410, 'y': 302, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature11':             {'x': 410, 'y': 291, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature12':             {'x': 410, 'y': 280, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature13':             {'x': 410, 'y': 269, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature14':             {'x': 410, 'y': 258, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature15':             {'x': 410, 'y': 247, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature16':             {'x': 410, 'y': 236, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature17':             {'x': 410, 'y': 225, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature18':             {'x': 410, 'y': 214, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature19':             {'x': 410, 'y': 203, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature20':             {'x': 410, 'y': 192, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature21':             {'x': 410, 'y': 181, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature22':             {'x': 410, 'y': 170, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature23':             {'x': 410, 'y': 159, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature24':             {'x': 410, 'y': 148, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature25':             {'x': 410, 'y': 137, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature26':             {'x': 410, 'y': 126, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature27':             {'x': 410, 'y': 115, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature28':             {'x': 410, 'y': 104, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature29':             {'x': 410, 'y': 93, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature30':             {'x': 410, 'y': 82, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature31':             {'x': 410, 'y': 71, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature32':             {'x': 410, 'y': 60, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature33':             {'x': 410, 'y': 49, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature34':             {'x': 410, 'y': 38, 'size': 10, 'limit': 30, 'dont_center': True},
        'feature35':             {'x': 410, 'y': 27, 'size': 10, 'limit': 30, 'dont_center': True},

        'language1':             {'x': 35, 'y': 160, 'size': 10, 'limit': 30, 'dont_center': True},
        'language2':             {'x': 35, 'y': 149, 'size': 10, 'limit': 30, 'dont_center': True},
        'language3':             {'x': 35, 'y': 138, 'size': 10, 'limit': 30, 'dont_center': True},
        'language4':             {'x': 35, 'y': 127, 'size': 10, 'limit': 30, 'dont_center': True},
        'language5':             {'x': 35, 'y': 116, 'size': 10, 'limit': 30, 'dont_center': True},
        'language6':             {'x': 35, 'y': 95, 'size': 10, 'limit': 30, 'dont_center': True},
        'language7':             {'x': 35, 'y': 84, 'size': 10, 'limit': 30, 'dont_center': True},
        'language8':             {'x': 35, 'y': 73, 'size': 10, 'limit': 30, 'dont_center': True},
        'language9':             {'x': 35, 'y': 62, 'size': 10, 'limit': 30, 'dont_center': True},
        'language10':            {'x': 35, 'y': 51, 'size': 10, 'limit': 30, 'dont_center': True},
        'language11':            {'x': 35, 'y': 30, 'size': 10, 'limit': 30, 'dont_center': True},
        'language12':            {'x': 35, 'y': 19, 'size': 10, 'limit': 30, 'dont_center': True},

    }
    font_size = known_elements_dictionary[element_name]['size']
    if 'plus_minus' in known_elements_dictionary[element_name] and known_elements_dictionary[element_name]['plus_minus'] is True:
        if int(value) > 0:
            value = '+' + value

    if len(value) > known_elements_dictionary[element_name]['limit']:
        font_size = font_size // (len(value) / known_elements_dictionary[element_name]['limit'])

    if font_size < 5:
        font_size = 5

    if not ('dont_center' in known_elements_dictionary[element_name] and known_elements_dictionary[element_name]['dont_center'] is True):
        known_elements_dictionary[element_name]['x'] -= len(value) * font_size // 3  # Centring

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
    write_in_pdf(character.xml.abilities.intelligence.bonus, pdf, 'intellect')
    write_in_pdf(character.xml.abilities.intelligence.score, pdf, 'intellect.value')
    write_in_pdf(character.xml.abilities.wisdom.bonus, pdf, 'wisdom')
    write_in_pdf(character.xml.abilities.wisdom.score, pdf, 'wisdom.value')
    write_in_pdf(character.xml.abilities.charisma.bonus, pdf, 'charisma')
    write_in_pdf(character.xml.abilities.charisma.score, pdf, 'charisma.value')
    write_in_pdf(character.xml.perception, pdf, 'passive_perception')
    write_in_pdf(character.xml.profbonus, pdf, 'profbonus')
    if character.xml.abilities.strength.saveprof == '1':
        write_in_pdf('v', pdf, 'strength.saveprof')
    if character.xml.abilities.dexterity.saveprof == '1':
        write_in_pdf('v', pdf, 'dexterity.saveprof')
    if character.xml.abilities.constitution.saveprof == '1':
        write_in_pdf('v', pdf, 'constitution.saveprof')
    if character.xml.abilities.intelligence.saveprof == '1':
        write_in_pdf('v', pdf, 'intellect.saveprof')
    if character.xml.abilities.wisdom.saveprof == '1':
        write_in_pdf('v', pdf, 'wisdom.saveprof')
    if character.xml.abilities.charisma.saveprof == '1':
        write_in_pdf('v', pdf, 'charisma.saveprof')
    write_in_pdf(character.xml.abilities.strength.save, pdf, 'strength.save')
    write_in_pdf(character.xml.abilities.dexterity.save, pdf, 'dexterity.save')
    write_in_pdf(character.xml.abilities.constitution.save, pdf, 'constitution.save')
    write_in_pdf(character.xml.abilities.intelligence.save, pdf, 'intellect.save')
    write_in_pdf(character.xml.abilities.wisdom.save, pdf, 'wisdom.save')
    write_in_pdf(character.xml.abilities.charisma.save, pdf, 'charisma.save')

    if character.xml.skilllist.acrobatics.prof == '1':
        write_in_pdf('v', pdf, 'acrobatics.prof')
    if character.xml.skilllist.investigation.prof == '1':
        write_in_pdf('v', pdf, 'investigation.prof')
    if character.xml.skilllist.athletics.prof == '1':
        write_in_pdf('v', pdf, 'athletic.prof')
    if character.xml.skilllist.perception.prof == '1':
        write_in_pdf('v', pdf, 'perception.prof')
    if character.xml.skilllist.survival.prof == '1':
        write_in_pdf('v', pdf, 'survival.prof')
    if character.xml.skilllist.performance.prof == '1':
        write_in_pdf('v', pdf, 'performance.prof')
    if character.xml.skilllist.intimidation.prof == '1':
        write_in_pdf('v', pdf, 'intimidation.prof')
    if character.xml.skilllist.history.prof == '1':
        write_in_pdf('v', pdf, 'history.prof')
    if character.xml.skilllist.sleight_of_hand.prof == '1':
        write_in_pdf('v', pdf, 'sleight_of_hand.prof')
    if character.xml.skilllist.arcana.prof == '1':
        write_in_pdf('v', pdf, 'arcana.prof')
    if character.xml.skilllist.medicine.prof == '1':
        write_in_pdf('v', pdf, 'medicine.prof')
    if character.xml.skilllist.deception.prof == '1':
        write_in_pdf('v', pdf, 'deception.prof')
    if character.xml.skilllist.nature.prof == '1':
        write_in_pdf('v', pdf, 'nature.prof')
    if character.xml.skilllist.insight.prof == '1':
        write_in_pdf('v', pdf, 'insight.prof')
    if character.xml.skilllist.religion.prof == '1':
        write_in_pdf('v', pdf, 'religion.prof')
    if character.xml.skilllist.stealth.prof == '1':
        write_in_pdf('v', pdf, 'stealth.prof')
    if character.xml.skilllist.persuasion.prof == '1':
        write_in_pdf('v', pdf, 'persuasion.prof')
    if character.xml.skilllist.animal_handling.prof == '1':
        write_in_pdf('v', pdf, 'animal_handling.prof')

    write_in_pdf(character.xml.skilllist.acrobatics.total, pdf, 'acrobatics')
    write_in_pdf(character.xml.skilllist.investigation.total, pdf, 'investigation')
    write_in_pdf(character.xml.skilllist.athletics.total, pdf, 'athletic')
    write_in_pdf(character.xml.skilllist.perception.total, pdf, 'perception')
    write_in_pdf(character.xml.skilllist.survival.total, pdf, 'survival')
    write_in_pdf(character.xml.skilllist.performance.total, pdf, 'performance')
    write_in_pdf(character.xml.skilllist.intimidation.total, pdf, 'intimidation')
    write_in_pdf(character.xml.skilllist.history.total, pdf, 'history')
    write_in_pdf(character.xml.skilllist.sleight_of_hand.total, pdf, 'sleight_of_hand')
    write_in_pdf(character.xml.skilllist.arcana.total, pdf, 'arcana')
    write_in_pdf(character.xml.skilllist.medicine.total, pdf, 'medicine')
    write_in_pdf(character.xml.skilllist.deception.total, pdf, 'deception')
    write_in_pdf(character.xml.skilllist.nature.total, pdf, 'nature')
    write_in_pdf(character.xml.skilllist.insight.total, pdf, 'insight')
    write_in_pdf(character.xml.skilllist.religion.total, pdf, 'religion')
    write_in_pdf(character.xml.skilllist.stealth.total, pdf, 'stealth')
    write_in_pdf(character.xml.skilllist.persuasion.total, pdf, 'persuasion')
    write_in_pdf(character.xml.skilllist.animal_handling.total, pdf, 'animal_handling')

    write_in_pdf(character.xml.defenses.ac.total, pdf, 'armor')
    write_in_pdf(character.xml.initiative.total, pdf, 'initiative')
    write_in_pdf(str(int(character.xml.speed.total) // 5), pdf, 'speed')
    class_level_string = ''
    dice = []
    for class_ in character.xml.classes:
        class_level_string += f', {class_.name} {class_.level}'
        dice.extend(str((class_.hddie + ' ') * int(class_.level)).split())

    class_level_string = class_level_string[2:]
    write_in_pdf(class_level_string, pdf, 'class_level')
    write_in_pdf(character.xml.race, pdf, 'race')
    try:
        write_in_pdf(character.xml.alignment, pdf, 'alignment')
    except AttributeError:
        pass
    write_in_pdf(character.xml.background, pdf, 'background')
    write_in_pdf(character.xml.hp.total, pdf, 'hp_max')
    write_in_pdf(str(len(dice)), pdf, 'total_dice')
    write_in_pdf(' '.join(dice), pdf, 'dice')
    magic_attacks_modifier = int(character.xml.profbonus) + int(character.xml.abilities.intelligence.bonus)
    if magic_attacks_modifier > 0:
        magic_attacks_modifier = '+' + str(magic_attacks_modifier)

    write_in_pdf(f'Модификатор магических атак: {magic_attacks_modifier}', pdf, 'magic1')
    write_in_pdf(f'Бонус мастерства ({character.xml.profbonus}) + Модификатор Интеллекта ({character.xml.abilities.intelligence.bonus})', pdf, 'magic2')
    write_in_pdf(f'Сложность спасброска: {10 + int(character.xml.abilities.intelligence.bonus)}', pdf, 'magic3')
    write_in_pdf(f'10 + Модификатор Интеллекта ({character.xml.abilities.intelligence.bonus})', pdf, 'magic4')
    write_in_pdf(f'Атака: Бонус мастерства ({character.xml.profbonus}), если проф. владение+', pdf, 'magic5')
    write_in_pdf(f'Модификатор Силы({character.xml.abilities.strength.bonus}) или Ловкости({character.xml.abilities.dexterity.bonus}), если фехтовальное', pdf, 'magic6')
    write_in_pdf(f'Урон: Модификатор Силы ({character.xml.abilities.strength.bonus}) или Ловкости({character.xml.abilities.dexterity.bonus}), если фехтовальное', pdf, 'magic7')

    dexterity_included = character.xml.abilities.dexterity.bonus
    try:
        if character.xml.defenses.ac.dexbonus == 'no':
            dexterity_included = 'no'
    except AttributeError:
        pass

    write_in_pdf(f'КД: Осн(10) + Броня({character.xml.defenses.ac.armor}) + Ловк({dexterity_included}) + Щит({character.xml.defenses.ac.shield})', pdf, 'magic8')

    damage_translations_dict = {'slashing':    'рубящий',
                                'piercing':    'колющий',
                                'bludgeoning': 'дробящий',
                                'cold':        'холод',
                                'acid':        'кислота',
                                'fire':        'огонь',
                                'magic':       'магический',
                                'poison':      'яд',
                                'force':       'сил. поле',
                                'necrotic':    'некротика',
                                'lightning':   'молния',
                                'psychic':     'психический',
                                'radiant':     'излучение',
                                'thunder':     'звук',
                                }
    weapons = character.xml.weaponlist

    for number, weapon in enumerate(weapons):
        if number > 2:
            break
        damage_type = damage_translations_dict[weapon.damagelist[0].type.lower()] if weapon.damagelist[0].type.lower() in damage_translations_dict else weapon.damagelist[0].type.lower()

        attack_bonus = 0
        damage_bonus = 0
        if hasattr(weapon, 'prof') and weapon.prof == '1':
            attack_bonus += int(character.xml.profbonus)

        if 'finesse' in weapon.properties.lower():
            attack_bonus += max(int(character.xml.abilities.strength.bonus), int(character.xml.abilities.dexterity.bonus))
            damage_bonus += max(int(character.xml.abilities.strength.bonus), int(character.xml.abilities.dexterity.bonus))
        else:
            attack_bonus += int(character.xml.abilities.strength.bonus)
            damage_bonus += int(character.xml.abilities.strength.bonus)
        if damage_bonus > 0:
            damage_bonus = '+' + str(damage_bonus)
        elif damage_bonus == 0:
            damage_bonus = ''
        damage_dice_string = ''
        damage_dice_list = weapon.damagelist[0].dice.split(',')  # type:list
        for unique_dice in set(damage_dice_list):
            if damage_dice_list.count(unique_dice) == 1:
                damage_dice_string += f'{unique_dice} + '
            else:
                damage_dice_string += f'{damage_dice_list.count(unique_dice)}{unique_dice} + '

        damage_dice_string = damage_dice_string[:-2]  # to cut plus and space in the end

        write_in_pdf(weapon.name, pdf, f'weapon{number}.name')
        write_in_pdf(str(attack_bonus), pdf, f'weapon{number}.attack')
        write_in_pdf(f'{damage_dice_string}{damage_bonus} {damage_type}', pdf, f'weapon{number}.damage')

    feature_list_position = 0
    for number, feature in enumerate(character.xml.featurelist, 1):
        feature_list_position += 1
        try:
            level = feature.level
        except AttributeError:
            level = ''
        write_in_pdf(f'{feature.name} (от {feature.source} {level})', pdf, f'feature{number * 2 - 1}')

    for number, feature in enumerate(character.xml.featlist, feature_list_position + 1):
        write_in_pdf(f'{feature.name} (черта)', pdf, f'feature{number * 2 - 1}')

    language_translation_dict = {'Common':      'Общий',
                                 'Dwarvish':    'Дворфский',
                                 'Elvish':      'Эльфийский',
                                 'Abyssal':     'Бездны',
                                 'Aquan':       'Водный',
                                 'Celestial':   'Небесный',
                                 'Deep Speech': 'Глубинный',
                                 'Draconic':    'Драконий',
                                 'Giant':       'Великаний',
                                 'Gnomish':     'Гномий',
                                 'Goblin':      'Гоблинский',
                                 'Halfling':    'Полуросликов',
                                 'Ingan':       'Огненный',
                                 'Infernal':    'Инфернальный',
                                 'Orc':         'Орочий',
                                 'Primordal':   'Первородный',
                                 'Sylvan':      'Лесной',
                                 'Terran':      'Земной',
                                 'UnderCommon': 'Глубинный Общий'}
    for number, language in enumerate(character.xml.languagelist, 1):
        language_name = language.name.strip()
        if language_name in language_translation_dict:
            language_name = language_translation_dict[language_name]
        write_in_pdf(f'{language_name} язык', pdf, f'language{number}')

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

        if element.tag.startswith('id-'):
            name_child = [e for e in element if e.tag == 'name']
            if name_child:
                element.tag = translate_from_iso_codes(name_child[0].text). \
                    lower(). \
                    replace(' ', '_'). \
                    replace('-', '_'). \
                    replace('(', ''). \
                    replace(')', ''). \
                    replace(':', ''). \
                    replace(',', ''). \
                    replace('.', '')
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
    # print(translate_to_iso_codes('Божественное Чувство'))
    run_pdf_creation('Leila')
    # straight_translate('Satar.xml')
