import os
import re
import requests
from lxml.html import fromstring
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")

MAIL_NEWS = {
    'url': 'https://news.mail.ru',
    'items_xpath': '//ul[contains(@class, "list_half")]//li',
    'name_source_xpath': '//a[contains(@class, "breadcrumbs__link")]/span//text()',
    'news_title_xpath': './a//text()',
    'link_to_news': './a/@href',
    'date_of_publication_xpath': '//span[contains(@class, "breadcrumbs__text")]/@datetime',
    're_value': r'T(\d.*)'
}

YANDEX_NEWS = {
    'url': 'https://news.mail.ru',
    'items_xpath': '//div[contains(@class, "news-top-flexible-stories")]',
    'name_source_xpath': '//span[contains(@class, "news-story__subtitle-text")]//text()',
    'news_title_xpath': './/a[contains(@class, "mg-card__link")]//text()',
    'link_to_news': './/a[contains(@class, "mg-card__link")]/@href',
    'date_of_publication_xpath': '//span[contains(@class, "breadcrumbs__text")]/@datetime',
    're_value': r'T(\d.*)'
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

    def get_value(self, link, xpath_str, flag=None):
        r = requests.get(link, headers=self.HEADERS)
        dom = fromstring(r.text)
        value = dom.xpath(xpath_str)[0]
        # Сдела флаг, если нужна обработка строик, регулярным выражением
        if flag == 're':
            return re.sub(self.re_value, '', value)
        else:
            return value

    def get_data(self, items):
        for item in items:
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            self.link_news = item.xpath(self.LINK_TO_NEWS)[0]
            self.news['link_news'] = self.link_news
            self.news['name_source'] = self.get_value(self.link_news, self.NAME_SOURCE_XPATH)
            self.news['date'] = self.get_value(self.link_news, self.DATE_OF_PUBLICATION_XPATH, 're')
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


start = News_lenta(MAIL_NEWS)
start.get_html()
