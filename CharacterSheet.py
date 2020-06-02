from dataclasses import dataclass
import io
import pdfrw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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


@dataclass
class Value:
    name: str  # How it is called on PDF page (ex: СПАСБРОСКИ - Сила)
    font_size: int = 0  # zero, if use Field default
    value: str = ""  # Value, numeric or string
    explaination: str = ""  # Why this field has this value
    english_name: str = ""  # Name translated into English


@dataclass
class Field:
    value: Value  # can be left empty
    center_x: int  # x coordinates of center
    center_y: int  # y coordinates of center
    length: int  # to calculate if text fits
    height: int  # row high
    default_font_size: int
    rows_coordinates: tuple = ()  # if more that one row
    alignment: str = 'center'  # left, right or center
    auto_fit_font_size: bool = True  # Should change font size to fit

    def calculate_y(self, font_size):
        return self.center_y - font_size // 4

    def calculate_x(self, font_size):
        return self.center_x - (font_size // 4) * len(str(self.value.value))

    def render(self, pdf):
        font_size = self.default_font_size
        if self.value.font_size:
            font_size = self.value.font_size
        length_in_coordinates = font_size // 2 * len(str(self.value.value))
        if length_in_coordinates > self.length and self.auto_fit_font_size:
            font_size = font_size * (self.length / length_in_coordinates)
        # must have FreeSans.ttf in the same folder
        pdf.setFont('FreeSans', font_size)
        if self.alignment == 'center':
            x = self.calculate_x(font_size)
        else:
            x = self.center_x
        pdf.drawString(
            x=x,
            y=self.calculate_y(font_size),
            text=self.value.value,
        )


@dataclass()
class CharacterSheet:
    result_file_name: str
    template_file = 'character_sheet_light.pdf'
    # bottom left corner coords are 0, 0
    # upper left corner coords are 0, 790
    # upper righ corner coords are 593 ,790
    character_name: Field = Field(
        value=Value("Имя персонажа"),
        default_font_size=20,
        alignment='center',
        auto_fit_font_size=True,
        height=20,
        length=170,
        center_x=128,
        center_y=720,
    )

    class_and_level: Field = Field(
        value=Value("КЛАСС И УРОВЕНЬ"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=310,
        center_y=735,
    )

    backstory: Field = Field(
        value=Value("Предыстория"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=400,
        center_y=735,
    )

    player_name: Field = Field(
        value=Value("Имя игрока"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=510,
        center_y=735,
    )

    race: Field = Field(
        value=Value("Раса"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=310,
        center_y=708,
    )

    alignment: Field = Field(
        value=Value("Мировоззрение"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=400,
        center_y=708,
    )

    experience: Field = Field(
        value=Value("Опыт"),
        default_font_size=8,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=80,
        center_x=510,
        center_y=708,
    )

    strength: Field = Field(
        value=Value("Сила"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=597,
    )

    dexterity: Field = Field(
        value=Value("Ловкость"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=525,
    )

    constitution: Field = Field(
        value=Value("Телосложение"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=454,
    )

    intelligence: Field = Field(
        value=Value("Интеллект"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=382,
    )
    wisdom: Field = Field(
        value=Value("Мудрость"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=310,
    )
    charisma: Field = Field(
        value=Value("Харизма"),
        default_font_size=10,
        alignment='center',
        auto_fit_font_size=True,
        height=5,
        length=15,
        center_x=55,
        center_y=238,
    )

    def set_field(self, *, field_name: str, value, override_font_size: int = 0):
        for prop_name in self.__dict__:
            field = self.__dict__[prop_name]
            if not isinstance(field, Field):
                continue
            if field.value.name.lower() == field_name.lower():  # first match
                break
        else:
            raise ValueError(f'Field with name "{field_name}" not found')
        field.value.value = value
        if override_font_size:
            field.value.font_size = override_font_size

    def render(self):
        data = io.BytesIO()
        pdf = canvas.Canvas(data)
        pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))

        for field in self.__dict__.values():
            if not isinstance(field, Field):
                continue
            print(f'Rendering "{field}"')
            field.render(pdf)

        pdf.save()
        data.seek(0)
        form = merge(data, template_path=self.template_file)
        with open(f'{self.result_file_name}', 'wb') as f:
            f.write(form.read())


if __name__ == '__main__':
    empty_sheet = CharacterSheet('empty.pdf')
    empty_sheet.set_field(
        field_name="Имя персонажа",
        value='Чебурашка',
    )
    empty_sheet.set_field(
        field_name="Класс и уровень",
        value='Колдун 1',
    )

    empty_sheet.set_field(
        field_name="Предыстория",
        value='Отшельник',
    )

    empty_sheet.set_field(
        field_name="Имя игрока",
        value='Губка Боб',
    )

    empty_sheet.set_field(
        field_name="Раса",
        value='Полурослик',
    )

    empty_sheet.set_field(
        field_name="Мировоззрение",
        value='Законно добрый',
    )

    empty_sheet.set_field(
        field_name="Опыт",
        value='',
    )

    empty_sheet.set_field(
        field_name="Сила",
        value='16',
    )

    empty_sheet.set_field(
        field_name="Ловкость",
        value='20',
    )

    empty_sheet.set_field(
        field_name="Телосложение",
        value='0',
    )

    empty_sheet.set_field(
        field_name="Интеллект",
        value='100',
    )

    empty_sheet.set_field(
        field_name="Мудрость",
        value='-5',
    )

    empty_sheet.set_field(
        field_name="Харизма",
        value='6',
    )

    empty_sheet.render()
