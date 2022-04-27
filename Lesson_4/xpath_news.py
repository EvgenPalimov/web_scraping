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
    'url': 'https://yandex.ru/news',
    'items_xpath': '//div[contains(@class, "news-top-flexible-stories")]/div',
    'name_source_xpath': './/a[contains(@class, "mg-card__source-link")]//text()',
    'news_title_xpath': './/a[contains(@class, "mg-card__link")]//text()',
    'link_to_news': './/a[contains(@class, "mg-card__link")]/@href',
    'date_of_publication_xpath': './/span[contains(@class, "mg-card-source__time")]//text()',
    're_value': r''
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
        # Сдела флаг, если нужна обработка строки, регулярным выражением
        if flag == 're':
            return re.sub(self.re_value, '', value)
        else:
            return value

    def get_data(self, items):
        '''Функция для извлечения данных с сайта'''
        for item in items:
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            link = item.xpath(self.LINK_TO_NEWS)[0]
            self.link_news = f'{self.URL}{link}'
            self.news['link_news'] = self.link_news
            self.news['name_source'] = self.NAME_SOURCE_XPATH
            self.news['date'] = self.get_value(self.link_news, self.DATE_OF_PUBLICATION_XPATH)
            self.write_news_to_db()

    def get_html(self):
        '''Функция для запроса к ресурсу и полачение страницы.
        Отправляем данные на изсвлечение.'''
        r = requests.get(self.URL, headers=self.HEADERS)
        dom = fromstring(r.text)
        items = dom.xpath(self.ITEMS_XPATH)
        self.get_data(items)

    def write_news_to_db(self):
        '''Функция для записи данных в базу данных.'''
        with MongoClient(self.MONGO_HOST, self.MONGO_PORT) as client:
            db = client[self.MONGO_DB]
            collection = db[self.MONGO_COLLECTION]
            collection.update_one(
                {'link_news': self.link_news},
                {'$set': self.news},
                upsert=True,
            )


class News_mail(News_lenta):
    def get_data(self, items):
        for item in items:
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            self.link_news = item.xpath(self.LINK_TO_NEWS)[0]
            self.news['link_news'] = self.link_news
            self.news['name_source'] = self.get_value(self.link_news, self.NAME_SOURCE_XPATH)
            self.news['date'] = self.get_value(self.link_news, self.DATE_OF_PUBLICATION_XPATH, 're')
            self.write_news_to_db()


class News_yandex(News_lenta):
    def get_data(self, items):
        for item in items:
            self.news['title_news'] = item.xpath(self.NEWS_TITLE_XPATH)[0]
            self.news['link_news'] = item.xpath(self.LINK_TO_NEWS)[0]
            self.news['name_source'] = item.xpath(self.NAME_SOURCE_XPATH)[0]
            self.news['date'] = item.xpath(self.DATE_OF_PUBLICATION_XPATH)[0]
            self.write_news_to_db()


lenta = News_lenta(LENTA_NEWS)
lenta.get_html()

mail = News_mail(MAIL_NEWS)
mail.get_html()

mail = News_yandex(YANDEX_NEWS)
mail.get_html()
