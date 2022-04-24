from bs4 import BeautifulSoup as bs
import json
import re
import requests
import time

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


def hh(main_link: str, search_value: str, page_count: int):
    html = requests.get(f'{main_link}/search/vacancy?clusters=true&area=3&ored_clusters=true'
                        f'&enable_snippets=true&salary=&text={search_value}', headers=HEADERS)
    if html.ok:
        parsed_html = bs(html.text, 'lxml')
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

                    job_data['site'] = main_link
                    jobs.append(job_data)
            time.sleep(3)
            next_btn_block = parsed_html.find('a', attrs={'class': 'bloko-button', 'data-qa': 'pager-next'})
            next_btn_link = next_btn_block.get('href')
            if next_btn_link is None:
                return jobs
            else:
                html = requests.get(f'{main_link}{next_btn_link}', headers=HEADERS).text
                parsed_html = bs(html, 'lxml')
        return jobs


def write_jbos_to_json(name_file: str, list: list):
    with open(name_file, 'r', encoding='utf-8') as f_r:
        data = json.load(f_r)

    with open(name_file, 'w', encoding='utf-8') as f_w:
        data_list = data['vacancy']
        data_list.append(list)
        json.dump(data, f_w, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    job_name = input('Пожалуйста введите, имя интересующей вакансии: ')
    try:
        page_count = int(input('Введите желаемое количество страниц для просмотра'
                               '(на одной странице 20 вакансий): '))
    except ValueError:
        print('Количество страниц - должно указано только цифрой')

    head_hunter = hh('https://hh.ru', job_name, page_count)
    write_jbos_to_json('vacancy.json', head_hunter)
