import requests

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


vacancies_all_time, total_all_time = get_vacancies(params_all_time)
print(f"Количество вакансий за всё время: {total_all_time}")

vacancies_last_month, total_last_month = get_vacancies(params_last_month)
print(f"Количество вакансий за последний месяц: {total_last_month}")

print("\nПримеры вакансий за последний месяц:")
for item in vacancies_last_month[:5]:
    print(f"Название: {item['name']}")
    print(f"Компания: {item['employer']['name']}")
    print(f"Город: {item['area']['name']}")
    print(f"URL: {item['alternate_url']}")
    print("=" * 50)
