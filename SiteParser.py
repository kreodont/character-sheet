from collections import namedtuple
import aiohttp
import asyncio
import typing
from bs4 import BeautifulSoup

Spell = namedtuple('Spell', ('name', 'level', 'school', 'cast_time', 'range', 'components', 'duration', 'classes', 'source', 'higher_levels', 'description'))
SpellAttribute = namedtuple('SpellAttribute', ('ru_name', 'ru_value', 'en_name', 'en_value'))


def spell_nice_print(s: Spell) -> str:
    output_string = f'{s.name.ru_value} ({s.name.en_value})'
    for value in sorted(s._asdict().values()):
        if value.ru_name == 'Имя':
            continue
        output_string += f'\n\t{value.ru_name.title():25}: {value.ru_value}'

    output_string += '\n'
    return output_string


Spell.__repr__ = spell_nice_print

attributes_translations_dict = {'уровень':            'level',
                                'школа':              'school',
                                'время накладывания': 'cast_time',
                                'дистанция':          'range',
                                'компоненты':         'components',
                                'длительность':       'duration',
                                'классы':             'classes',
                                'источник':           'source',
                                'на больших уровнях': 'higher_levels',
                                'имя':                'name',
                                'описание':           'description',
                                }


async def fetch_spell(*, eng_spell_name: str, session: aiohttp.client.ClientSession, debug: bool = False) -> typing.Optional[Spell]:
    searching_url = 'http://dungeon.su/spells/'
    # searching_url = f'http://dungeon.su/spells/{eng_spell_name}'
    async with session.get(searching_url, headers={'Accept':       'text/html,application/xhtml+xml,application/xml',
                                                   'Content-Type': 'text/html'}, params={'search': eng_spell_name}) as response:
        if debug:
            print(f'Fetching spell "{eng_spell_name}"')
            print(response.url)

        response_binary = await response.read()
        html = BeautifulSoup(response_binary.decode('utf-8'), 'html.parser')
        articles = html.find_all(name='div', attrs={'itemtype': "https://schema.org/Article"})  # type: typing.List[BeautifulSoup.element.Tag]
        if len(articles) != 1:
            print(f'Expected to get 1 spell block, {len(articles)} found: {articles}')
            return None

        spell_attributes_dict = {'level':         SpellAttribute(ru_name='уровень', ru_value=-1, en_name='level', en_value=-1),
                                 'school':        SpellAttribute(ru_name='школа', ru_value='нет', en_name='school', en_value='na'),
                                 'cast_time':     SpellAttribute(ru_name='время накладывания', ru_value='нет', en_name='cast_time', en_value='na'),
                                 'duration':      SpellAttribute(ru_name='длительность', ru_value='na', en_name='duration', en_value='na'),
                                 'range':         SpellAttribute(ru_name='дистанция', ru_value='na', en_name='range', en_value='na'),
                                 'components':    SpellAttribute(ru_name='компоненты', ru_value=[], en_name='components', en_value=[]),
                                 'classes':       SpellAttribute(ru_name='классы', ru_value=[], en_name='classes', en_value=[]),
                                 'source':        SpellAttribute(ru_name='источник', ru_value='na', en_name='source', en_value='na'),
                                 'higher_levels': SpellAttribute(ru_name='на больших уровнях', ru_value='', en_name='higher levels', en_value='na'),
                                 'name':          SpellAttribute(ru_name='имя', ru_value=eng_spell_name, en_name='name', en_value=''),
                                 'description':   SpellAttribute(ru_name='описание', ru_value='Нет описания', en_name='description', en_value='No description')}

        article = articles[0]  # type: BeautifulSoup.element.Tag
        name_tag = article.find('a', attrs={'class': 'item-link', 'itemprop': 'url'})
        if not name_tag:
            print(f'Name tag not found for {eng_spell_name}')
            return
        spell_attributes_dict['name'] = SpellAttribute(ru_name='имя',
                                                       ru_value=name_tag.text.split('(')[0].strip(),
                                                       en_name='name',
                                                       en_value=name_tag.text.split('(')[1].strip().replace(')', ''))

        article_body = article.find(name='div', attrs={"class": "card-body", "itemprop": "articleBody"})  # type: BeautifulSoup.element.Tag
        if not article_body:
            print(f'Cannot find any spell on html page')
            return None

        for attribute_tag in article_body('ul')[0]('li'):  # iterate over each <li> tag

            if attribute_tag.find(name='div', attrs={'itemprop': 'description'}):
                description_tag = attribute_tag.find(name='div', attrs={'itemprop': 'description'})
                if "На больших уровнях:" in description_tag.text:
                    spell_attributes_dict['description'] = SpellAttribute(ru_name='описание',
                                                                          ru_value=description_tag.text.split('На больших уровнях:')[0].strip(),
                                                                          en_name='description',
                                                                          en_value='')
                    spell_attributes_dict['higher_levels'] = SpellAttribute(ru_name='на больших уровнях',
                                                                            ru_value=description_tag.text.split('На больших уровнях:')[1].strip(),
                                                                            en_name='higher levels',
                                                                            en_value='')
                else:
                    spell_attributes_dict['description'] = SpellAttribute(ru_name='описание', ru_value=description_tag.text, en_name='description', en_value='')
            else:
                ru_name = attribute_tag('strong')[0].text.replace(':', '')
                if ru_name.lower() not in attributes_translations_dict:
                    continue

                ru_value = attribute_tag.text.replace(f'{ru_name}:', '').strip().replace('«', '').replace('»', '')
                spell_attributes_dict[attributes_translations_dict[ru_name.lower()]] = SpellAttribute(ru_name=ru_name,
                                                                                                      ru_value=ru_value,
                                                                                                      en_name=attributes_translations_dict[ru_name.lower()],
                                                                                                      en_value='')

    return Spell(name=spell_attributes_dict['name'],
                 level=spell_attributes_dict['level'],
                 cast_time=spell_attributes_dict['cast_time'],
                 classes=spell_attributes_dict['classes'],
                 components=spell_attributes_dict['components'],
                 duration=spell_attributes_dict['duration'],
                 higher_levels=spell_attributes_dict['higher_levels'],
                 range=spell_attributes_dict['range'],
                 school=spell_attributes_dict['school'],
                 source=spell_attributes_dict['source'],
                 description=spell_attributes_dict['description'],
                 )


async def open_connection_and_fetch_spells(spell_names_list: typing.List[str]):
    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(*[asyncio.create_task(fetch_spell(eng_spell_name=spell_name, session=session)) for spell_name in spell_names_list])
        print(responses)


if __name__ == '__main__':
    future = asyncio.ensure_future(open_connection_and_fetch_spells(['hellish rebuke']))
    asyncio.get_event_loop().run_until_complete(future)
