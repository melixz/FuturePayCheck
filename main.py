import requests
import datetime
import time
import os
from functools import partial
from operator import itemgetter
from dotenv import load_dotenv
from terminaltables import DoubleTable

LANGUAGES = [
    'JavaScript',
    'Python',
    'Java',
    'TypeScript',
    'C#',
    'PHP',
    'C++',
    'Shell',
    'C',
    'Ruby',
]

BASE_URL_HH = 'https://api.hh.ru/vacancies'
BASE_URL_SJ = 'https://api.superjob.ru/2.0/vacancies/'

AREA_RUSSIA = 1
PER_PAGE = 100
PERIOD_LAST_MONTH = 30
TOWN_MOSCOW = 4
CATALOGUES_PROGRAMMING = 48
NO_AGREEMENT = 1


def get_hh_vacancies(language):
    payload = {
        'text': f'Программист {language}',
        'area': AREA_RUSSIA,
        'only_with_salary': True,
        'period': PERIOD_LAST_MONTH,
    }
    while True:
        response = requests.get(BASE_URL_HH, params=payload)
        response.raise_for_status()
        response_data = response.json()
        page = response_data['page']
        pages = response_data['pages']
        if page >= pages:
            break
        payload['page'] = page + 1
        yield response_data['items'], response_data['found']


def get_sj_vacancies(language, api_key):
    headers = {
        'X-Api-App-Id': api_key,
    }
    search_from = datetime.datetime.now() - datetime.timedelta(days=PERIOD_LAST_MONTH)
    unix_time = int(time.mktime(search_from.timetuple()))
    payload = {
        'date_published_from': unix_time,
        'keyword': f'Программист {language}',
        'town': TOWN_MOSCOW,
        'no_agreement': NO_AGREEMENT,
        'page': 0,
    }
    total_vacancies = 0
    while True:
        response = requests.get(BASE_URL_SJ, headers=headers, params=payload)
        response.raise_for_status()
        page_content = response.json()
        if not payload['page']:
            total_vacancies = page_content['total']
        yield page_content['objects'], total_vacancies
        if not page_content['more']:
            break
        payload['page'] += 1


def predict_rub_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return int((salary_from + salary_to) / 2)
    elif salary_to:
        return int(salary_to * 0.8)
    elif salary_from:
        return int(salary_from * 1.2)


def get_salary_from_hh(vacancy):
    salary = vacancy['salary']
    return salary['from'], salary['to'], salary['currency'] == 'RUR'


def get_salary_from_sj(vacancy):
    sal_from = vacancy['payment_from']
    sal_to = vacancy['payment_to']
    return sal_from, sal_to, vacancy['currency'] == 'rub'


def get_found_vacancies(get_vacancies, get_salary, languages):
    vacancies_summary = {}
    for language in languages:
        average_salaries = []
        total_vacancies = 0
        for vacancies, found in get_vacancies(language):
            total_vacancies = found
            for vacancy in vacancies:
                if not isinstance(vacancy, dict):
                    continue
                salary_from, salary_to, currency_in_rub = get_salary(vacancy)
                if currency_in_rub:
                    salary = predict_rub_salary(salary_from, salary_to)
                    average_salaries.append(salary)

        vacancies_processed = len(average_salaries)
        average_salary = int(sum(average_salaries) / vacancies_processed) if vacancies_processed else 0

        vacancies_summary[language] = {
            'vacancies_found': total_vacancies,
            'average_salary': average_salary,
            'vacancies_processed': vacancies_processed
        }
    return vacancies_summary


def format_table(vacancy_statistics, table_name):
    data = []
    for key, value in vacancy_statistics.items():
        data_row = [key]
        data_row.extend(list(value.values()))
        data.append(data_row)
    data = sorted(data, key=itemgetter(2), reverse=True)
    data.insert(
        0,
        [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата',
        ],
    )
    table = DoubleTable(data, table_name)
    table.justify_columns = {
        0: 'left',
        1: 'center',
        2: 'center',
        3: 'right'
    }
    return table.table


if __name__ == '__main__':
    load_dotenv()
    sj_api_key = os.getenv('SJ_SECRET_KEY')
    sj_vacancies_finder = partial(get_sj_vacancies, api_key=sj_api_key)
    print('Сбор вакансий с HeadHunter...')
    hh_vacancies = get_found_vacancies(
        get_hh_vacancies,
        get_salary_from_hh,
        LANGUAGES,
    )
    print('Готово!')
    print('Сбор вакансий с SuperJob...')
    sj_vacancies = get_found_vacancies(
        sj_vacancies_finder,
        get_salary_from_sj,
        LANGUAGES,
    )
    print('Готово!')
    print(format_table(hh_vacancies, ' HeadHunter Moscow '))
    print(format_table(sj_vacancies, ' SuperJob Moscow '))
