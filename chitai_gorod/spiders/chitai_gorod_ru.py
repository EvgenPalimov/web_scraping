import scrapy
from scrapy_selenium import SeleniumRequest
from scrapy.loader import ItemLoader
from scrapy.http import TextResponse

from chitai_gorod.items import ChitaiGorodItem
from selenium.webdriver.chrome.service import Service

SEARCH_URL = 'https://www.chitai-gorod.ru/search/result/?q='
DRIVER_CHROME = Service('C:\chromedriver.exe')


class ChitaiGorodRuSpider(scrapy.Spider):
    name = 'chitai_gorod_ru'
    allowed_domains = ['chitai-gorod.ru']

    def __init__(self, query, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if query:
            self.start_urls = f'https://www.chitai-gorod.ru/search/result/?q={query}'
        else:
            self.start_urls = 'http://chitai-gorod.ru/'

    def start_requests(self):
        # Не работал поиск через стандартные свойства Scrapy, поэтому пришлось подключить Selenium
        # Работает поиск как на Английском так и на Русском(без кодировки, поддерживает сайт)
        yield SeleniumRequest(
            url=self.start_urls,
            wait_time=3,
            screenshot=True,
            callback=self.parse,
            dont_filter=True
        )

    def parse_item(self, response: TextResponse, title: str):
        features_books = {}
        features_value_list = []

        loader = ItemLoader(item=ChitaiGorodItem(), response=response)
        loader.add_value('title', title)
        loader.add_value('url', response.url)
        loader.add_xpath('price', '//div[@class="price"]/text()')
        if response.xpath('//div[@class="product-media__icon"]/img/@data-src'):
            loader.add_xpath('img_urls', '//div[@class="product-media__icon"]/img/@data-src')
        else:
            loader.add_xpath('img_urls', '//div[contains(@class, "product__image")]/img/@data-src')
        # Получилось извлечь данные только таким способом для параметров товара.
        features_keys = response.xpath('//div[@class="product-prop"]/div[contains(@class, "__title")]/text()').getall()
        features_value = response.xpath('//div[@class="product-prop"]/div[contains(@class, "__value")]')
        for value in features_value:
            if value.xpath('./text()').get().strip():
                features_value_list.append(value.xpath('./text()').get().strip())
            else:
                # На некоторых объектах вылетает ошибка при проверке, поэтому просто пропускаем
                # так как оно пустое
                try:
                    if value.xpath('./a/text()').get().strip():
                        features_value_list.append(value.xpath('./a/text()').get().strip())
                except AttributeError:
                    pass
                if value.xpath('./a/span/text()').get():
                    features_value_list.append(value.xpath('./a/span/text()').get())
                elif value.xpath('./div/span/text()').get():
                    features_value_list.append(value.xpath('./div/span/text()')[0].get())
        for i in range(0, len(features_keys)):
            features_books[features_keys[i]] = features_value_list[i]
        loader.add_value('features_books', features_books)
        yield loader.load_item()

    def parse(self, response: TextResponse, *args, **kwargs):
        items = response.xpath('//div[contains(@class, "js_product")]')
        for item in items:
            url = item.xpath('.//a[contains(@class, "__link")]/@href').get()
            title = item.xpath('.//div[contains(@class, "__title")]//text()').get()
            data_kwargs = {'title': title}
            yield response.follow(url, callback=self.parse_item, cb_kwargs=data_kwargs)

        try:
            next_url = response.xpath('//div[contains(@class, "pagination")]/a//@href').getall()
            if next_url:
                yield SeleniumRequest(
                    url=f'http://chitai-gorod.ru{next_url[-1]}',
                    wait_time=3,
                    screenshot=True,
                    callback=self.parse,
                    dont_filter=True
                )
        except Exception:
            print('Пагинация отсутствует на странице')
