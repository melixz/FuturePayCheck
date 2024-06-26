import datetime
import os
import time
import requests
from dotenv import load_dotenv

LANGUAGES = [
    'JavaScript', 'Python', 'Java', 'TypeScript', 'C#', 'PHP', 'C++', 'Shell', 'C', 'Ruby'
]


def get_sj_vacancies_titles(language, api_key):
    sj_api_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': api_key}
    search_from = datetime.datetime.now() - datetime.timedelta(days=30)
    unix_time = int(time.mktime(search_from.timetuple()))
    payload = {
        'date_published_from': unix_time,
        'keyword': language,
        'town': 4,  # ID Москвы
        'catalogues': 48,  # ID каталога "Разработка, программирование"
        'no_agreement': 1,
        'page': 0,
    }
    titles = []
    while True:
        response = requests.get(sj_api_url, headers=headers, params=payload)
        response.raise_for_status()
        page_data = response.json()
        for vacancy in page_data['objects']:
            profession = vacancy['profession'].lower()
            if 'программист' in profession or 'разработчик' in profession:
                titles.append(f"{vacancy['profession']}, Москва")
        if not page_data['more']:
            break
        payload['page'] += 1
    return titles


if __name__ == '__main__':
    load_dotenv()
    sj_api_key = os.getenv('SJ_SECRET_KEY')
    all_titles = []
    for language in LANGUAGES:
        print(f'Получение названий вакансий для {language} с SuperJob...')
        titles = get_sj_vacancies_titles(language, sj_api_key)
        all_titles.extend(titles)
    print('Названия вакансий с SuperJob:')
    for title in all_titles:
        print(title)
