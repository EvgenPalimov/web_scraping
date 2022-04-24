import os
from bs4 import BeautifulSoup as bs
import json
import re
import requests
import time
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv("../.env")
MONGO_HOST = os.getenv("MONGO_HOST", None)
MONGO_PORT = int(os.getenv("MONGO_PORT", None))
MONGO_DB = os.getenv("MONGO_DB", None)
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", None)

HEADERS = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Ubuntu Chromium/80.0.3987.87 Chrome/80.0.3987.87 Safari/537.36'}


def get_salary(salary):
    salary_min = 0
    salary_max = 0
    salary_currency = ''
    by_agreement = False

    if salary:
        get_salary_text = salary.getText().replace('\u202f', '')
        salary_currency = re.sub(r'[дотДОТ\W0-9.]', '', get_salary_text)
        salary_text = re.sub(r'[а-яА-Яa-zA-z.-]', '', get_salary_text)
        salaries = salary_text.split('–')
        if len(salaries) > 1:
            salary_min = int(salaries[0])
            salary_max = int(salaries[1])
        elif 'от' in get_salary_text:
            salary_min = int(salaries[0])
        elif 'до' in get_salary_text:
            salary_max = int(salaries[0])

    else:
        # Заговтовка для базы данных, признак что выбрана зарплата по договоренности
        by_agreement = True

    return {'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': salary_currency,
            'by_agreement': by_agreement
            }


def hh(search_value: str, page_count: int, new = None):
    MAIN_LINK = 'https://hh.ru'

    if new:
        # Не стал множить код и нарушать правило Do Not Repeat
        # Добавил флаг - который будет выводить обычные вакансии или только новые
        HTML = requests.get(f'{MAIN_LINK}/search/vacancy?clusters=true&area=3&ored_clusters=true'
                        f'&enable_snippets=true&salary=&text={search_value}', headers=HEADERS)
    else:
        HTML = requests.get(f'https://ekaterinburg.hh.ru/search/vacancy?text={search_value}&area=3&salary='
                            f'&currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=1'
                            f'&items_on_page=20&no_magic=true&L_save_area=true')

    if HTML.ok:
        parsed_html = bs(HTML.text, 'lxml')
        jobs = []
        for i in range(page_count):
            jobs_block = parsed_html.find('div', {'id': 'a11y-main-content'})
            jobs_list = jobs_block.findChildren(recursive=False)
            for job in jobs_list:
                job_data = {}
                req = job.find('span', {'class': 'g-user-content'})
                if req != None:
                    main_info = req.findChild()
                    job_name = main_info.getText()
                    job_link = main_info['href']
                    salary = job.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                    company = job.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
                    company_name = company.getText().replace('\xa0', ' ')
                    salaries = get_salary(salary)

                    job_data['vacancy_name'] = job_name
                    job_data['company_name'] = company_name
                    job_data['vacancy_link'] = job_link
                    job_data['salary_min'] = salaries['salary_min']
                    job_data['salary_max'] = salaries['salary_max']
                    job_data['salary_currency'] = salaries['salary_currency']
                    job_data['by_agreement'] = salaries['by_agreement']

                    job_data['site'] = MAIN_LINK
                    jobs.append(job_data)
            time.sleep(3)
            next_btn_block = parsed_html.find('a', attrs={'class': 'bloko-button', 'data-qa': 'pager-next'})
            next_btn_link = next_btn_block.get('href')
            if next_btn_link is None:
                return jobs
            else:
                HTML = requests.get(f'{MAIN_LINK}{next_btn_link}', headers=HEADERS).text
                parsed_html = bs(HTML, 'lxml')
        write_jbos_to_db(jobs)


def write_jbos_to_json(name_file: str, list: list):
    with open(name_file, 'r', encoding='utf-8') as f_r:
        data = json.load(f_r)

    with open(name_file, 'w', encoding='utf-8') as f_w:
        data_list = data['vacancy']
        data_list.append(list)
        json.dump(data, f_w, indent=4, ensure_ascii=False)


def write_jbos_to_db(list):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        collection.insert_many(list)




if __name__ == '__main__':
    job_name = input('Пожалуйста введите, имя интересующей вакансии: ')
    new_vacansy = input('Пожалуйста, набирите "1" - если хотите увидеть новые вакансии, '
                        'в ином случае оставьте это поле пустым.')
    try:
        page_count = int(input('Введите желаемое количество страниц для просмотра'
                               '(на одной странице 20 вакансий): '))
    except ValueError:
        print('Количество страниц - должно указано только цифрой')

    hh(job_name, page_count, new_vacansy)
