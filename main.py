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


def extract_salaries(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy.get('salary')
        if salary:
            salaries.append(predict_rub_salary(salary))
        else:
            salaries.append(None)
    return salaries


def predict_rub_salary(salary):
    if salary.get('currency') != 'RUR':
        return None
    if salary.get('from') and salary.get('to'):
        return (salary.get('from') + salary.get('to')) / 2
    elif salary.get('from'):
        return salary.get('from') * 1.2
    elif salary.get('to'):
        return salary.get('to') * 0.8
    else:
        return None


vacancies_all_time, total_all_time = get_vacancies(params_all_time)
print(f"Количество вакансий за всё время: {total_all_time}")

vacancies_last_month, total_last_month = get_vacancies(params_last_month)
print(f"Количество вакансий за последний месяц: {total_last_month}")

vacancy_counts = {language: get_vacancy_count(language) for language in popular_languages}
filtered_vacancy_counts = {lang: count for lang, count in vacancy_counts.items() if count > 100}

print("Количество вакансий для популярных языков программирования (больше 100):")
formatted_vacancy_counts = json.dumps(filtered_vacancy_counts, indent=4, ensure_ascii=False)
print(formatted_vacancy_counts)

print("\nОжидаемые оклады по языку Python:")
python_params = {
    "text": "программист Python",
    "area": 1,
    "per_page": 20,
    "period": 30
}

python_vacancies, _ = get_vacancies(python_params)
python_salaries = extract_salaries(python_vacancies)

for salary in python_salaries[:20]:
    print(salary)
