from dataclasses import dataclass, field as dataclass_field
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
    value: dataclass_field() = None
    font_size: int = 0  # zero, if use Field default
    explaination: str = ""  # Why this field has this value
    english_name: str = ""  # Name translated into English

    @property
    def repr_value(self):
        return str(self.value)


class IntegerValue(Value):
    value: int = 0


class IntegerValueWithSign(IntegerValue):
    @property
    def repr_value(self):
        if int(self.value) > 0:
            return '+' + str(int(self.value))
        if int(self.value) < 0:
            return str(int(self.value))
        return self.value


class StringValue(Value):
    pass


class BooleanValue(Value):
    pass


@dataclass
class Field:
    center_x: int  # x coordinates of center
    center_y: int  # y coordinates of center
    length: int  # to calculate if text fits
    height: int  # row high
    default_font_size: int
    value: Value = Value('Empty')
    rows_coordinates: tuple = ()  # if more that one row
    alignment: str = 'center'  # left, right or center
    auto_fit_font_size: bool = True  # Should change font size to fit

    def set_value(self, value):
        self.value.value = value

    def calculate_y(self, font_size):
        return self.center_y - font_size // 4

    def calculate_x(self, font_size, string_length):
        if string_length == 1:
            return self.center_x - font_size // 8
        return self.center_x - (font_size // 4) * len(str(
            self.value.repr_value))

    def render(self, pdf):
        font_size = self.default_font_size
        if self.value.font_size:
            font_size = self.value.font_size
        length_in_coordinates = font_size // 2 * len(str(self.value.repr_value))
        if length_in_coordinates > self.length and self.auto_fit_font_size:
            font_size = font_size * (self.length / length_in_coordinates)
        # must have FreeSans.ttf in the same folder
        pdf.setFont('FreeSans', font_size)
        if self.alignment == 'center':
            x = self.calculate_x(font_size, len(self.value.repr_value))
        else:
            x = self.center_x
        pdf.drawString(
            x=x,
            y=self.calculate_y(font_size),
            text=self.value.repr_value,
        )


class CharacterSheet:
    # bottom left corner coords are 0, 0
    # upper left corner coords are 0, 790
    # upper righ corner coords are 593 ,790
    result_file_name: str
    character_name: Field
    class_and_level: Field
    backstory: Field
    player_name: Field
    race: Field
    alignment: Field
    experience: Field
    strength: Field
    strength_modifier: Field
    dexterity: Field
    dexterity_modifier: Field
    constitution: Field
    constitution_modifier: Field
    intelligence: Field
    intelligence_modifier: Field
    wisdom: Field
    wisdom_modifier: Field
    charisma: Field
    charisma_modifier: Field
    template_file = 'character_sheet_light.pdf'

    def __init__(
            self,
            *,
            result_file_name: str,
            abilities_modifiers_bigger: bool = True,  # what numbers are
            # main, attributes values or their modifiers
            template_file_name: str = 'character_sheet_light.pdf',
    ):
        self.result_file_name = result_file_name
        self.template_file = template_file_name
        self.character_name = Field(
            value=StringValue("Имя персонажа"),
            default_font_size=20,
            alignment='center',
            auto_fit_font_size=True,
            height=20,
            length=170,
            center_x=128,
            center_y=720,
        )
        self.class_and_level = Field(
            value=StringValue("КЛАСС И УРОВЕНЬ"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=310,
            center_y=735,
        )

        self.backstory: Field = Field(
            value=StringValue("Предыстория"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=400,
            center_y=735,
        )

        self.player_name: Field = Field(
            value=StringValue("Имя игрока"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=510,
            center_y=735,
        )

        self.race: Field = Field(
            value=StringValue("Раса"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=310,
            center_y=708,
        )

        self.alignment: Field = Field(
            value=StringValue("Мировоззрение"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=400,
            center_y=708,
        )

        self.experience: Field = Field(
            value=IntegerValue("Опыт"),
            default_font_size=8,
            alignment='center',
            auto_fit_font_size=True,
            height=5,
            length=80,
            center_x=510,
            center_y=708,
        )

        if abilities_modifiers_bigger:
            self.strength: Field = Field(
                value=StringValue("Сила"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=597,
            )
            self.strength_modifier: Field = Field(
                value=StringValue("Модификатор силы"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=620,
            )
        else:
            self.strength: Field = Field(
                value=IntegerValue("Сила"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=620,
            )
            self.strength_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор силы"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=597,
            )

        if abilities_modifiers_bigger:
            self.dexterity: Field = Field(
                value=IntegerValue("Ловкость"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=525,
            )

            self.dexterity_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор ловкости"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=548,
            )
        else:
            self.dexterity: Field = Field(
                value=IntegerValue("Ловкость"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=548,
            )

            self.dexterity_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор ловкости"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=525,
            )

        if abilities_modifiers_bigger:
            self.constitution: Field = Field(
                value=IntegerValue("Телосложение"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=454,
            )

            self.constitution_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор телосложения"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=476,
            )
        else:
            self.constitution: Field = Field(
                value=IntegerValue("Телосложение"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=476,
            )

            self.constitution_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор телосложения"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=454,
            )

        if abilities_modifiers_bigger:
            self.intelligence: Field = Field(
                value=IntegerValue("Интеллект"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=382,
            )

            self.intelligence_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор интеллекта"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=404,
            )
        else:
            self.intelligence: Field = Field(
                value=IntegerValue("Интеллект"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=404,
            )

            self.intelligence_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор интеллекта"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=382,
            )
        if abilities_modifiers_bigger:
            self.wisdom: Field = Field(
                value=IntegerValue("Мудрость"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=310,
            )
            self.wisdom_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор мудрости"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=335,
            )
        else:
            self.wisdom: Field = Field(
                value=IntegerValue("Мудрость"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=335,
            )
            self.wisdom_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор мудрости"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=25,
                center_x=55,
                center_y=310,
            )

        if abilities_modifiers_bigger:
            self.charisma: Field = Field(
                value=IntegerValue("Харизма"),
                default_font_size=10,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=238,
            )
            self.charisma_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор Харизмы"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=263,
            )
        else:
            self.charisma: Field = Field(
                value=IntegerValue("Харизма"),
                default_font_size=24,
                alignment='center',
                auto_fit_font_size=True,
                height=5,
                length=15,
                center_x=55,
                center_y=263,
            )
            self.charisma_modifier: Field = Field(
                value=IntegerValueWithSign("Модификатор Харизмы"),
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
    empty_sheet = CharacterSheet(
        result_file_name='empty.pdf',
        abilities_modifiers_bigger=True,
    )
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
        field_name="Модификатор силы",
        value='+3',
    )

    empty_sheet.set_field(
        field_name="Ловкость",
        value='20',
    )

    empty_sheet.set_field(
        field_name="Модификатор ловкости",
        value='-90',
    )

    empty_sheet.set_field(
        field_name="Телосложение",
        value='0',
    )

    empty_sheet.set_field(
        field_name="Модификатор телосложения",
        value='-3',
    )

    empty_sheet.set_field(
        field_name="Интеллект",
        value='100',
    )

    empty_sheet.set_field(
        field_name="Модификатор интеллекта",
        value='+3',
    )

    empty_sheet.set_field(
        field_name="Мудрость",
        value='-5',
    )
    empty_sheet.set_field(
        field_name="Модификатор Мудрости",
        value='2',
    )

    empty_sheet.set_field(
        field_name="Харизма",
        value='60',
    )

    empty_sheet.set_field(
        field_name="Модификатор Харизмы",
        value='12',
    )

    empty_sheet.render()
