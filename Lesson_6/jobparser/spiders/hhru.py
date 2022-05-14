import re
import scrapy
from scrapy.http import TextResponse

from Lesson_6.jobparser.items import JobparserItem

TEMPLATE_URL = 'https://hh.ru/search/vacancy?text='


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['www.hh.ru']

    def __init__(self, query, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [TEMPLATE_URL + query]
        self.site_for_vacancies = 'hh.ru'

    def get_salary(self, salary):
        salary_min = 0
        salary_max = 0
        salary_currency = ''

        new_salary = ''.join(salary)

        if re.search('\d+', new_salary):
            get_salary_text = new_salary.replace('\xa0', '')
            clear_salary_currency = re.sub(r'(\..*)', '', get_salary_text)
            salary_currency = re.sub(r'[дотДОТ\W0-9]', '', clear_salary_currency)
            salary_text = re.sub(r'\b\D*\B\D*', ' ', get_salary_text)
            salaries = salary_text.split(' ')
            if len(salaries) > 3:
                salary_min = int(salaries[1])
                salary_max = int(salaries[2])
            elif 'от' in get_salary_text:
                salary_min = int(salaries[1])
            elif 'до' in get_salary_text:
                salary_max = int(salaries[1])

        return {'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency
                }

    def parse_item(self, response: TextResponse, title: str):
        salary = response.xpath('//div[@data-qa="vacancy-salary"]/span//text()').getall()
        salaries = self.get_salary(salary)

        item = JobparserItem()
        item['title'] = title
        item['salary_min'] = salaries['salary_min']
        item['salary_max'] = salaries['salary_max']
        item['salary_currency'] = salaries['salary_currency']
        item['url'] = response.url
        item['vacancy_for_website'] = self.site_for_vacancies
        yield item

    def parse(self, response: TextResponse, *args, **kwargs):
        items = response.xpath('//a[contains(@data-qa, "__vacancy-title")]')
        for item in items:
            url = item.xpath('./@href').get()
            title = item.xpath('.//text()').get()
            data_kwargs = {'title': title}
            yield response.follow(url, callback=self.parse_item, cb_kwargs=data_kwargs)

        next_url = response.xpath('//a[contains(@data-qa, "pager-next")]/@href').get()
        if next_url:
            yield response.follow(next_url, callback=self.parse)
