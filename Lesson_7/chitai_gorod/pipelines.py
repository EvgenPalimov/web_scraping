# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
from urllib.parse import urlparse

import pymongo
from slugify import slugify
from itemadapter import ItemAdapter
from scrapy.http import Request
from scrapy.pipelines.images import ImagesPipeline


class ChitaiGorodPipeline:
    collection_name = 'scrapy_books'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].update_one(
            {'url': item['url']},
            {'$set': ItemAdapter(item).asdict()},
            upsert=True,
        )
        return item


class ChitaiGorodImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        img_urls = []
        img_urls.extend(item["img_urls"])
        img_urls = set(img_urls)

        if img_urls:
            for img_url in img_urls:
                try:
                    yield Request(img_url)
                except Exception as e:
                    print(e)

    def file_path(self, request, response=None, info=None, *, item=None):
        # Взял имя для папки - Title перевел в латиницу
        slug = slugify(item['title'])
        return f'full/{slug}/' + os.path.basename(urlparse(request.url).path)

    def item_completed(self, results, item, info):
        if results:
            item["img_info"] = [r[1]['path'] for r in results if r[0]]
            del item["img_urls"]
        return item
