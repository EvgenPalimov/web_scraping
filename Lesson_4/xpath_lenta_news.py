import os
import re
import requests
from lxml.html import fromstring
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")


class News_lenta:

    def __init__(self):
        self.URL = 'https://lenta.ru'
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/98.0.4758.80 Safari/537.36",
        }
        self.ITEMS_XPATH = '//div[@class="last24"]//a'
        self.TITLE_XPATH = 'Lenta.ru'
        self.NEWS_TITLE_XPATH = './/span[contains(@class, "__title")]//text()'
        self.LINK_TO_NEWS = './@href'
        self.DATE_OF_PUBLICATION_XPATH = '//time[contains(@class, "topic-header__item")]//text()'
        self.MONGO_HOST = os.getenv("MONGO_HOST", None)
        self.MONGO_PORT = int(os.getenv("MONGO_PORT", None))
        self.MONGO_DB = os.getenv("MONGO_DB", None)
        self.MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", None)
        self.link_news = ''
        self.news = {}

    def get_date(self):
        r = requests.get(self.link_news, headers=self.HEADERS)
        dom = fromstring(r.text)
        date = dom.xpath(self.DATE_OF_PUBLICATION_XPATH)[0]
        return re.sub(r'(\d.*),.', '', date)

    def get_data(self, items):
        for item in items:
            self.news['name_source'] = self.TITLE_XPATH
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            link = item.xpath(self.LINK_TO_NEWS)[0]
            self.link_news = f'{self.URL}{link}'
            self.news['link_news'] = self.link_news
            self.news['date'] = self.get_date()
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


start = News_lenta()
start.get_html()
