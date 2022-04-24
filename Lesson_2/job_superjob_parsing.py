import json
import re
import requests
from bs4 import BeautifulSoup as bs


def parser_superjob(vacancy, page_count):
    vacancy_date = []
    params = {
        'keywords': vacancy,
        'page': ''
    }
    headers = {
        'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Ubuntu Chromium/80.0.3987.87 Chrome/80.0.3987.87 Safari/537.36'
    }
    link = 'https://www.superjob.ru/vacancy/search/'
    html = requests.get(link, params=params, headers=headers)

    if html.ok:
        parsed_html = bs(html.text, 'lxml')
        page_block = parsed_html.find('a', {'class': 'f-test-button-1'})
        if not page_block:
            last_page = 1
        else:
            last_page = page_count

        for page in range(last_page):
            params['page'] = page
            html = requests.get(link, params=params, headers=headers)
            if html.ok:
                parsed_html = bs(html.text, 'html.parser')
                vacancy_items = parsed_html.find_all('div', {'class': 'f-test-vacancy-item'})
                for item in vacancy_items:
                    vacancy_date.append(parser_item_superjob(item))

        return vacancy_date


def get_salary(salary, is_check_salary):
    salary_min = 0
    salary_max = 0
    by_agreement = False
    salary_currency = ''

    if salary:
        if is_check_salary == 'По':
            # Заговтовка для базы данных, признак что выбрана зарплата по договоренности
            by_agreement = True
        else:
            get_salary_text = salary[0].getText().replace(u'\xa0', u'')
            salary_text = re.sub(r'[а-яА-Яa-zA-z.-]', '', get_salary_text)
            salary_currency = re.sub(r'[дотДОТ\W0-9]', '', get_salary_text)
            salaries = salary_text.split('—')
            if is_check_salary == 'до':
                salary_max = int(salaries[0])
            elif is_check_salary == 'от':
                salary_min = int(salaries[0])
            else:
                salary_min = int(salaries[0])
                if len(salaries) <= 1:
                    salary_max = 0
                else:
                    salary_max = int(salaries[1])
        return {'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency,
                'by_agreement': by_agreement}
    else:
        return None


def parser_item_superjob(item):
    vacancy_date = {}

    # Vacancy name, Company name, Vacancy link
    vacancy = item.find_all('a')
    vacancy_name = vacancy[0].getText()
    vacancy_link = vacancy[0]['href']
    company_name = vacancy[1].getText()

    vacancy_date['vacancy_name'] = vacancy_name
    vacancy_date['company_name'] = company_name
    vacancy_date['vacancy_link'] = f'https://www.superjob.ru{vacancy_link}'

    # salary
    salary = item.find('span', {'class': 'f-test-text-company-item-salary'}).findChildren()
    is_check_salary = \
        item.find('span', {'class': 'f-test-text-company-item-salary'}).getText().replace(u'\xa0', u' ').split(' ', 1)[
            0]
    salaries = get_salary(salary, is_check_salary)

    vacancy_date['salary_min'] = salaries['salary_min']
    vacancy_date['salary_max'] = salaries['salary_max']

    # Salary currency
    vacancy_date['salary_currency'] = salaries['salary_currency']

    # By agreement
    vacancy_date['by_agreement'] = salaries['by_agreement']

    # site
    vacancy_date['site'] = 'www.superjob.ru'
    return vacancy_date


def write_jbos_to_json(name_file, list):
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

    super_job = parser_superjob(job_name, page_count)
    write_jbos_to_json('vacancy.json', super_job)
