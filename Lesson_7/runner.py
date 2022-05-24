from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from chitai_gorod import settings
from chitai_gorod.spiders.chitai_gorod_ru import ChitaiGorodRuSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)

    # Для запуска из консоли необходимо использовать параметр
    # "-a QUERY=VALUE" VALUE - название вакансии

    name_vacancy = input('Введите название желаемой вакансии или нажмите клавишу "Ввод": ')
    if name_vacancy:
        search_kwargs = {'query': name_vacancy.replace(' ', '+')}
    else:
        search_kwargs = {'query': ''}

    process.crawl(ChitaiGorodRuSpider, **search_kwargs)

    process.start()
