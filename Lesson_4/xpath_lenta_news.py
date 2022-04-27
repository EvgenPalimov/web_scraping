import os
import re
import requests
from lxml.html import fromstring
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")

LENTA_NEWS = {
    'url': 'https://lenta.ru',
    'items_xpath': '//div[@class="last24"]//a',
    'name_source_xpath': 'Lenta.ru',
    'news_title_xpath': './/span[contains(@class, "__title")]//text()',
    'link_to_news': './@href',
    'date_of_publication_xpath': '//time[contains(@class, "topic-header__item")]//text()',
    're_value': r'(\d.*),.'
}

class News_lenta:

    def __init__(self, params):
        self.MONGO_HOST = os.getenv("MONGO_HOST", None)
        self.MONGO_PORT = int(os.getenv("MONGO_PORT", None))
        self.MONGO_DB = os.getenv("MONGO_DB", None)
        self.MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", None)
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/98.0.4758.80 Safari/537.36",
        }
        self.URL = params['url']
        self.ITEMS_XPATH = params['items_xpath']
        self.NAME_SOURCE_XPATH = params['name_source_xpath']
        self.NEWS_TITLE_XPATH = params['news_title_xpath']
        self.LINK_TO_NEWS = params['link_to_news']
        self.DATE_OF_PUBLICATION_XPATH = params['date_of_publication_xpath']
        self.re_value = params['re_value']
        self.link_news = ''
        self.news = {}

    def get_value(self, link, xpath_str):
        r = requests.get(link, headers=self.HEADERS)
        dom = fromstring(r.text)
        date = dom.xpath(xpath_str)[0]
        return re.sub(self.re_value, '', date)

    def get_data(self, items):
        for item in items:
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            link = item.xpath(self.LINK_TO_NEWS)[0]
            self.link_news = f'{self.URL}{link}'
            self.news['link_news'] = self.link_news
            self.news['name_source'] = self.NAME_SOURCE_XPATH
            self.news['date'] = self.get_value(self.link_news, self.DATE_OF_PUBLICATION_XPATH)
            self.write_news_to_db()

    def get_html(self):
        r = requests.get(self.URL, headers=self.HEADERS)
        dom = fromstring(r.text)
        items = dom.xpath(self.ITEMS_XPATH)
        self.get_data(items)

    def write_news_to_db(self):
        with MongoClient(self.MONGO_HOST, self.MONGO_PORT) as client:
            db = client[self.MONGO_DB]
            collection = db[self.MONGO_COLLECTION]
            collection.update_one(
                {'link_news': self.link_news},
                {'$set': self.news},
                upsert=True,
            )


start = News_lenta(LENTA_NEWS)
start.get_html()
