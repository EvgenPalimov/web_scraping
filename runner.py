from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from jobparser import settings
from jobparser.spiders.hhru import HhruSpider
from jobparser.spiders.sjru import SjruSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)

    name_vacancy = input('Введите название желаемой вакансии в формате "-a query=Название вакансии"'
                         ' или нажмите клавишу "Ввод": ')
    if name_vacancy:
        search_kwargs = {'query': name_vacancy}
    else:
        search_kwargs = {'query': ''}

    process.crawl(HhruSpider, **search_kwargs)
    process.crawl(SjruSpider, **search_kwargs)

    process.start()
