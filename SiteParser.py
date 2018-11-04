from collections import namedtuple
import aiohttp
import asyncio
import typing
from bs4 import BeautifulSoup

Spell = namedtuple('Spell', ('name', ))


async def fetch_spell(spell_name: str, session: aiohttp.client.ClientSession, debug: bool=False) -> typing.Optional[Spell]:
    async with session.get(f'http://dungeon.su/spells/{spell_name}', headers={
                                         'Accept':            'text/html,application/xhtml+xml,application/xml',
                                         'Content-Type':      'text/html'}) as response:
        if debug:
            print(f'Fetching spell "{spell_name}"')
        response_binary = await response.read()
        html = BeautifulSoup(response_binary.decode('utf-8'), 'html.parser')
        articles = html.find_all(name='div', attrs={'itemtype': "https://schema.org/Article"})  # type: typing.List[BeautifulSoup.element.Tag]
        if len(articles) != 1:
            print(f'Expected to get 1 spell block, {len(articles)} found: {articles}')
            return None

        article = articles[0]  # type: BeautifulSoup.element.Tag
        article_body = article.find(name='div', attrs={"class": "card-body",  "itemprop": "articleBody"}) # type: BeautifulSoup.element.Tag
        if not article_body:
            print(f'Cannot find any spell on html page')
            return None

        print(article_body.prettify())
    return Spell(name=spell_name)


async def open_connection_and_fetch_spells(spell_names_list: typing.List[str]):
    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(*[asyncio.create_task(fetch_spell(spell_name, session)) for spell_name in spell_names_list])
        print(responses)

if __name__ == '__main__':
    future = asyncio.ensure_future(open_connection_and_fetch_spells(['1-hellish_rebuke', ]))
    asyncio.get_event_loop().run_until_complete(future)  # Fetching users from Jira API
