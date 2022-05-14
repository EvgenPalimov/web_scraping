import re
import scrapy
from scrapy.http import TextResponse

from Lesson_6.jobparser.items import JobparserItem

TEMPLATE_URL = 'https://www.superjob.ru/vacancy/search/?keywords='


class SjruSpider(scrapy.Spider):
    name = 'sjru'
    allowed_domains = ['www.superjob.ru']

    def __init__(self, query, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [TEMPLATE_URL + query]
        self.site_for_vacancies = 'superjob.ru'

    def get_salary(self, salary):
        salary_min = 0
        salary_max = 0
        salary_currency = ''

        new_salary = ''.join(salary)

        if re.search('\d+', new_salary):
            get_salary_text = new_salary.replace(u'\xa0', u'')
            clear_salary_currency = re.sub(r'(\..*)', '', get_salary_text)
            salary_currency = re.sub(r'[дотДОТ\W0-9]', '', clear_salary_currency)
            salary_text = re.sub(r'[а-яА-Яa-zA-z.-]', '', get_salary_text)
            salaries = salary_text.split('\u2014')
            if len(salaries) > 1:
                salary_min = int(salaries[0])
                salary_max = int(salaries[1])
            elif 'от' in get_salary_text:
                salary_min = int(salary_text)
            elif 'до' in get_salary_text:
                salary_max = int(salary_text)

        return {'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency
                }

    def parse(self, response: TextResponse, *args, **kwargs):
        vacancies = response.xpath('//div[contains(@class, "f-test-vacancy-item")]')
        for vacancy in vacancies:
            new_title = vacancy.xpath('.//a[contains(@target, "_blank")]//text()').getall()
            url = vacancy.xpath('.//a[contains(@target, "_blank")]/@href')[0].get()
            salary = vacancy.xpath('.//span[contains(@class, "item-salary")]/span//text()').getall()
            salaries = self.get_salary(salary)

            item = JobparserItem()
            if len(new_title) > 1:
                title = ''.join(new_title)
                item['title'] = title
            else:
                item['title'] = new_title[0]
            item['salary_min'] = salaries['salary_min']
            item['salary_max'] = salaries['salary_max']
            item['salary_currency'] = salaries['salary_currency']
            item['url'] = f'{self.site_for_vacancies}{url}'
            item['vacancy_for_website'] = self.site_for_vacancies
            yield item

        next_url = response.xpath('//a[contains(@class, "f-test-button-dalshe")]/@href').get()
        if next_url:
            yield response.follow(f'{self.site_for_vacancies}{next_url}', callback=self.parse)
