import os
import re

from lxml import html
from dotenv import load_dotenv
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv("../.env")

VK_POSTS_DATA = {
    'url': 'https://vk.com/tokyofashion',
    # Возникла проблема с selenium, он почему-то в Windows не воспринмал папку "Users"
    # поэтому пришлось закинуть файл с драйвером в корень диска.
    'driver_path': 'C:\chromedriver.exe',
    'items_xpath': '//div[contains(@id, "page_wall_posts")]/div[contains(@id, "post")]',
    'likes_xpath': './/div[contains(@class, "_counter_anim_container")]//text()',
    'share_xpath': './/div[contains(@class, "_share")]/span[contains(@class, "_counter_anim_container")]//text()',
    'like_views': './/div[contains(@class, "like_views")]/@title',
    'text_xpath': './/div[contains(@class, "wall_post_text")]//text()',
    'link_to_post': './/a[contains(@class, "post_link")]/@href',
    'date_of_publication_xpath': './/a[contains(@class, "post_link")]/span//text()'
}



class Posts:

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
        self.DRIVER_PATH = Service(params['driver_path'])
        self.ITEMS_XPATH = params['items_xpath']
        self.LIKES_XPATH = params['likes_xpath']
        self.SHARE_XPATH = params['share_xpath']
        self.LIKE_VIEWS_XPATH = params['like_views']
        self.TEXT_XPATH = params['text_xpath']
        self.LINK_TO_POST_XPATH = params["link_to_post"]
        self.DATE_OF_PUBLICATION_XPATH = params['date_of_publication_xpath']
        self.html = ''
        self.link_to_post = ''
        self.posts = {}


    def get_data(self, items: list):
        '''
        Функция для извлечения данных с сайта и передача на запись в БД
        :param items: Список постов для извлечения информации
        '''
        for item in items:
            self.posts['text'] = item.xpath(self.TEXT_XPATH)[0]
            new_link_to_post = item.xpath(self.LINK_TO_POST_XPATH)[0]
            self.link_to_post = f'https://vk.com{new_link_to_post}/'
            self.posts['link_to_post'] = self.link_to_post
            self.posts['date'] = item.xpath(self.DATE_OF_PUBLICATION_XPATH)[0]
            self.posts['likes'] = 0 if not bool(item.xpath(self.LIKES_XPATH)) else item.xpath(self.LIKES_XPATH)[0]
            self.posts['share'] = 0 if not bool(item.xpath(self.SHARE_XPATH)) else item.xpath(self.SHARE_XPATH)[0]
            new_like_views = 0 if not bool(item.xpath(self.LIKE_VIEWS_XPATH)) else item.xpath(self.LIKE_VIEWS_XPATH)[0]
            self.posts['like_views'] = re.sub(r'\s\w*', '', new_like_views)
            self.write_news_to_db()


    def search_for_posts(self, driver: webdriver.Chrome):
        '''
        Функция - для фильтрации постов. Вводится значение через консоль, если пустая строка -
        то поиск осуществляться не будет, посты будут выведены как есть.

        :param driver: Получаем переменную - webdriver, для осуществления поиска
        '''
        search_answer = input('Введите значение для поисак или оставьте поле пустым: ')
        if search_answer == '':
            print('Фильтрация не была использована, выводится по умолчанию.')
        else:
            search_click = driver.find_element(by=By.CLASS_NAME, value='ui_tab_search')
            search_click.click()
            search_input = driver.find_element(by=By.CLASS_NAME, value='ui_search_field')
            search_input.send_keys(search_answer + Keys.ENTER)


    def get_html(self):
        '''
        Главная функция запуска парсинга сайта:
          - устанавливаем параметры webdriver
          - передаем данные в функцию фильтрации
          - запускается обход сайта для получения нужной информации.
        Затем передаем данные в функцию get_data, для извлечения нужной информации.
        '''
        MAX_PAGE_NUMBER = 5
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=self.DRIVER_PATH, options=options)
        driver.get(self.URL)
        self.search_for_posts(driver)

        for i in range(MAX_PAGE_NUMBER):
            # Проверка на всплывающий баннер аутификации
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'UnauthActionBox__close'))).click()
                print('Окно с аутификацией было закрыто.')
            except Exception:
                # Думал сделать просто заглушку "pass", но решил оставить так
               print('Окна с аутификацией - не было.')
            data_posts = driver.find_elements(by=By.CLASS_NAME, value='_post')
            webdriver.ActionChains(driver).move_to_element(data_posts[-1]).perform()
            self.html_data = driver.page_source

        dom = html.fromstring(self.html_data)
        items = dom.xpath(self.ITEMS_XPATH)
        self.get_data(items)

        driver.quit()

    def write_news_to_db(self):
        '''Функция для записи данных в базу данных.'''
        with MongoClient(self.MONGO_HOST, self.MONGO_PORT) as client:
            db = client[self.MONGO_DB]
            collection = db[self.MONGO_COLLECTION]
            collection.update_one(
                {'link_to_post': self.link_to_post},
                {'$set': self.posts},
                upsert=True,
            )


start = Posts(VK_POSTS_DATA)
start.get_html()
