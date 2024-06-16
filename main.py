import requests
import json

BASE_URL = "https://api.hh.ru/vacancies"

params_all_time = {
    "text": "программист",
    "area": 1,
    "per_page": 20
}

params_last_month = {
    "text": "программист",
    "area": 1,
    "per_page": 20,
    "period": 30
}

popular_languages = ["Python", "Java", "Javascript", "C++", "C#", "PHP", "Ruby", "Go", "Swift", "Kotlin"]


def get_vacancies(params):
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            return response.json().get('items', []), response.json().get('found', 0)
        else:
            print(f"Ошибка запроса: {response.status_code}")
            return [], 0
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения: {e}")
        return [], 0


def get_vacancy_count(language):
    params = {
        "text": language,
        "area": 1,
        "per_page": 0,
        "search_field": "name"
    }
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            return response.json().get('found', 0)
        else:
            print(f"Ошибка запроса для {language}: {response.status_code}")
            return 0
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения для {language}: {e}")
        return 0


vacancies_all_time, total_all_time = get_vacancies(params_all_time)
print(f"Количество вакансий за всё время: {total_all_time}")

vacancies_last_month, total_last_month = get_vacancies(params_last_month)
print(f"Количество вакансий за последний месяц: {total_last_month}")

vacancy_counts = {language: get_vacancy_count(language) for language in popular_languages}
filtered_vacancy_counts = {lang: count for lang, count in vacancy_counts.items() if count > 100}

print("Количество вакансий для популярных языков программирования (больше 100):")
formatted_vacancy_counts = json.dumps(filtered_vacancy_counts, indent=4, ensure_ascii=False)
print(formatted_vacancy_counts)

print("\nПримеры вакансий за последний месяц:")
for item in vacancies_last_month[:5]:
    print(f"Название: {item['name']}")
    print(f"Компания: {item['employer']['name']}")
    print(f"Город: {item['area']['name']}")
    print(f"URL: {item['alternate_url']}")
    print("=" * 50)
