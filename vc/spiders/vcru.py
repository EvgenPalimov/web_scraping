import scrapy
from scrapy.http import TextResponse

from vc.items import VcItem


class VcruSpider(scrapy.Spider):
    name = "vcru"
    allowed_domains = ["vc.ru"]
    start_urls = ["https://vc.ru/"]
    login_url = "https://vc.ru/auth/simple/login"
    users = [{'id':'700', 'name': 'Роман Горбачёв'},
             {'id':'566775', 'name': 'grafdesigna'},
             {'id':'55537', 'name': 'Евгений Яровой'}]  # id пользователей
    subscribers = "https://vc.ru/subsite/subscribers/"
    subscriptions = "https://vc.ru/subsite/subscriptions/"

    def parse(self, response: TextResponse, **kwargs):
        for user in self.users:
            yield response.follow(self.subscribers + user['id'],
                                  callback=self.parse_subscribers,
                                  cb_kwargs={'user': user})
            yield response.follow(self.subscriptions + user['id'],
                                  callback=self.parse_subscriptions,
                                  cb_kwargs={'user': user})

    def parse_subscribers(self, response: TextResponse, user):
        print("SUBSCRIBERS")
        if response.json()['rc'] == 200:
            subscribers = response.json()['data']
            if 'lastId' in subscribers and 'lastSortingValue' in subscribers:
                lastId = subscribers['lastId']
                lastSortingValue = subscribers['lastSortingValue']
            else:
                # Если нету lastId и lastSortingValue - значит все значения,
                # уместились в одном json-файле и пагинация не требуется,
                # ставим значения по умолчанию.
                lastId = 1
                lastSortingValue = 1
            if lastId > 0 and lastSortingValue:
                for data in subscribers['items']:
                    item = VcItem()
                    subscriber = {}
                    item['user_id'] = user['id']
                    item['user_name'] = user['name']
                    subscriber['id'] = data['id']
                    subscriber['name'] = data['label']
                    subscriber['url'] = data['url']
                    subscriber['image_url'] = data['image']
                    item['subscriber'] = subscriber
                    item['subs_type'] = 'subscriber'
                    yield item
                if lastId != 1 and lastSortingValue != 1:
                    # Если не прошла проверку значит пагинация не требуется
                    yield response.follow(f'https://vc.ru/subsite/'
                                          f'subscribers/700?lastId={lastId}&'
                                          f'lastSortingValue={lastSortingValue}'
                                          f'&mode=raw',
                                          callback=self.parse_subscribers,
                                          cb_kwargs={'user': user})

    def parse_subscriptions(self, response: TextResponse, user):
        print('SUBSCRIPTIONS')
        if response.json()['rc'] == 200:
            subscriptions = response.json()['data']
            if 'lastId' in subscriptions and \
                    'lastSortingValue' in subscriptions:
                lastId = subscriptions['lastId']
                lastSortingValue = subscriptions['lastSortingValue']
            else:
                # Если нету lastId и lastSortingValue - значит все значения,
                # уместились в одном json-файле и пагинация не требуется,
                # ставим значения по умолчанию.
                lastId = 1
                lastSortingValue = 1
            if lastId > 0 and lastSortingValue:
                for data in subscriptions['items']:
                    item = VcItem()
                    subscription = {}
                    item['user_id'] = user['id']
                    item['user_name'] = user['name']
                    subscription['id'] = data['id']
                    subscription['name'] = data['label']
                    subscription['url'] = data['url']
                    subscription['image_url'] = data['image']
                    item['subscription'] = subscription
                    item['subs_type'] = 'subscription'
                    yield item
                if lastId != 1 and lastSortingValue != 1:
                    # Если не прошла проверку значит пагинация не требуется
                    yield response.follow(f'https://vc.ru/subsite/'
                                          f'subscriptions/700?lastId={lastId}&'
                                          f'lastSortingValue={lastSortingValue}'
                                          f'&mode=raw',
                                          callback=self.parse_subscribers,
                                          cb_kwargs={'user': user})
