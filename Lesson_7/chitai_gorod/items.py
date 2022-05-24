# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import re

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join


def clear_string(s):
    return s.strip()


def get_price(price):
    return int(re.sub(r'(\D)', '', price))


class ChitaiGorodItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field(input_processor=MapCompose(clear_string),
                         output_processor=Join(separator=" "))
    url = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=TakeFirst(),
                         output_processor=MapCompose(get_price))
    img_urls = scrapy.Field()
    img_info = scrapy.Field()
    features_books = scrapy.Field(output_processor=TakeFirst())
