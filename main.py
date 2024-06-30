import requests
import json
import os
import datetime
import time
from dotenv import load_dotenv

BASE_URL_HH = "https://api.hh.ru/vacancies"
BASE_URL_SJ = "https://api.superjob.ru/2.0/vacancies/"

LANGUAGES = ["JavaScript", "Python", "Java", "TypeScript", "C#", "PHP", "C++", "Shell", "C", "Ruby"]

params_all_time = {"text": "программист", "area": 1, "per_page": 100}
params_last_month = {"text": "программист", "area": 1, "per_page": 100, "period": 30}


def get_vacancies_hh(params):
    try:
        response = requests.get(BASE_URL_HH, params=params)
        response.raise_for_status()
        return response.json().get('items', []), response.json().get('found', 0)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения: {e}")
        return [], 0


def get_vacancy_count_hh(language):
    params = {"text": language, "area": 1, "per_page": 0, "search_field": "name"}
    try:
        response = requests.get(BASE_URL_HH, params=params)
        response.raise_for_status()
        return response.json().get('found', 0)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения для {language}: {e}")
        return 0


def extract_salaries_hh(vacancies):
    salaries = []
    for vacancy in vacancies:
        salary = vacancy.get('salary')
        if salary:
            salaries.append(predict_rub_salary_hh(salary))
        else:
            salaries.append(None)
    return salaries


def predict_rub_salary_hh(salary):
    if salary.get('currency') != 'RUR':
        return None
    return predict_salary(salary.get('from'), salary.get('to'))


def get_vacancies_sj(language, api_key):
    headers = {"X-Api-App-Id": api_key}
    search_from = datetime.datetime.now() - datetime.timedelta(days=30)
    unix_time = int(time.mktime(search_from.timetuple()))
    payload = {
        "date_published_from": unix_time,
        "keyword": language,
        "town": 4,
        "catalogues": 48,
        "no_agreement": 1,
        "page": 0,
    }
    vacancies = []
    while True:
        response = requests.get(BASE_URL_SJ, headers=headers, params=payload)
        response.raise_for_status()
        page_data = response.json()
        for vacancy in page_data["objects"]:
            profession = vacancy["profession"].lower()
            if "программист" in profession or "разработчик" in profession:
                salary = predict_rub_salary_sj(vacancy)
                vacancies.append(f"{vacancy['profession']}, Москва, {salary}")
        if not page_data["more"]:
            break
        payload["page"] += 1
    return vacancies


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')
    currency = vacancy.get('currency')
    if currency != 'rub':
        return None
    return predict_salary(salary_from, salary_to)


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    else:
        return None


def calculate_average_salaries(get_vacancies_func, extract_salaries_func):
    average_salaries = {}
    for language in LANGUAGES:
        language_params = {"text": f"программист {language}", "area": 1, "per_page": 100, "period": 30}
        language_vacancies, total_found = get_vacancies_func(language_params)
        language_salaries = extract_salaries_func(language_vacancies)
        language_salaries = [salary for salary in language_salaries if salary is not None]

        pages_to_process = (1000 - len(language_salaries)) // 100 + 1
        for page in range(2, pages_to_process + 1):
            language_params["page"] = page
            page_vacancies, _ = get_vacancies_func(language_params)
            page_salaries = extract_salaries_func(page_vacancies)
            language_salaries.extend([salary for salary in page_salaries if salary is not None])
            if len(language_salaries) >= 1000:
                break

        if language_salaries:
            average_salary = int(sum(language_salaries) / len(language_salaries))
            average_salaries[language] = {
                "vacancies_found": total_found,
                "vacancies_processed": len(language_salaries),
                "average_salary": average_salary
            }
    return average_salaries


def calculate_average_salaries_sj(api_key):
    average_salaries = {}
    for language in LANGUAGES:
        vacancies = get_vacancies_sj(language, api_key)
        salaries = []
        for vacancy in vacancies:
            parts = vacancy.split(', ')
            if len(parts) == 3:
                salary = parts[2]
                if salary != 'None':
                    salaries.append(float(salary))

        if salaries:
            average_salary = int(sum(salaries) / len(salaries))
            average_salaries[language] = {
                "vacancies_processed": len(salaries),
                "average_salary": average_salary
            }
    return average_salaries


def main():
    load_dotenv()
    sj_api_key = os.getenv("SJ_SECRET_KEY")

    vacancies_all_time, total_all_time = get_vacancies_hh(params_all_time)
    print(f"Количество вакансий за всё время: {total_all_time}")

    vacancies_last_month, total_last_month = get_vacancies_hh(params_last_month)
    print(f"Количество вакансий за последний месяц: {total_last_month}")

    vacancy_counts = {language: get_vacancy_count_hh(language) for language in LANGUAGES}
    filtered_vacancy_counts = {lang: count for lang, count in vacancy_counts.items() if count > 100}

    print("Количество вакансий для популярных языков программирования (больше 100):")
    formatted_vacancy_counts = json.dumps(filtered_vacancy_counts, indent=4, ensure_ascii=False)
    print(formatted_vacancy_counts)

    print("\nОжидаемые оклады по языку Python:")
    python_params = {"text": "программист Python", "area": 1, "per_page": 100, "period": 30}
    python_vacancies, _ = get_vacancies_hh(python_params)
    python_salaries = extract_salaries_hh(python_vacancies)

    for salary in python_salaries[:20]:
        print(salary)

    average_salaries_hh = calculate_average_salaries(get_vacancies_hh, extract_salaries_hh)
    print("\nСредние зарплаты по языкам программирования (HeadHunter):")
    formatted_average_salaries_hh = json.dumps(average_salaries_hh, indent=4, ensure_ascii=False)
    print(formatted_average_salaries_hh)

    print("\nСредние зарплаты по языкам программирования (SuperJob):")
    average_salaries_sj = calculate_average_salaries_sj(sj_api_key)
    formatted_average_salaries_sj = json.dumps(average_salaries_sj, indent=4, ensure_ascii=False)
    print(formatted_average_salaries_sj)

    print("\nПолучение названий вакансий для популярных языков с SuperJob...")
    all_titles = []
    for language in LANGUAGES:
        titles = get_vacancies_sj(language, sj_api_key)
        all_titles.extend(titles)
    print("Названия вакансий с SuperJob:")
    for title in all_titles:
        print(title)


if __name__ == "__main__":
    main()
