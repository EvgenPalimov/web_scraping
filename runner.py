from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from vc import settings
from vc.spiders.vcru import VcruSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)

    process.crawl(VcruSpider,)

    process.start()
