import os
import re
import requests
from lxml.html import fromstring
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")
MONGO_HOST = os.getenv("MONGO_HOST", None)
MONGO_PORT = int(os.getenv("MONGO_PORT", None))
MONGO_DB = os.getenv("MONGO_DB", None)
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", None)

URL = 'https://lenta.ru'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/98.0.4758.80 Safari/537.36",
}

ITEMS_XPATH = '//div[@class="last24"]//a'
TITLE_XPATH = 'Lenta.ru'
NEWS_TITLE_XPATH = './/span[contains(@class, "__title")]//text()'
LINK_TO_NEWS = './@href'
DATE_OF_PUBLICATION_XPATH = '//time[contains(@class, "topic-header__item")]//text()'


def get_date(href: str):
    r = requests.get(href, headers=HEADERS)
    dom = fromstring(r.text)
    date = dom.xpath(DATE_OF_PUBLICATION_XPATH)[0]
    return re.sub(r'(\d.*),.', '', date)


def write_jbos_to_db(link: str, news: dict):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        collection.update_one(
            {'link_news': link},
            {'$set': news},
            upsert=True,
        )


def get_data(items):
    news = {}
    for item in items:
        news['name_source'] = TITLE_XPATH
        news['title_news'] = item.xpath(NEWS_TITLE_XPATH)[0]
        link = item.xpath(LINK_TO_NEWS)[0]
        link_news = f'{URL}{link}'
        news['link_news'] = link_news
        news['date'] = get_date(link_news)
        write_jbos_to_db(link_news, news)


r = requests.get(URL, headers=HEADERS)
dom = fromstring(r.text)
items = dom.xpath(ITEMS_XPATH)
get_data(items)
