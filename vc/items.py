# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class VcItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    subscription = scrapy.Field()
    subscriber = scrapy.Field()
    subs_type = scrapy.Field()
