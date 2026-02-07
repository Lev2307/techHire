import os
import httpx

TELEGRAM_HEADERS = {
    "X-Internal-Token": os.environ.get("TELEGRAM_BOT_TOKEN"),
}

async def toggle_specialization_name(spec_id: str):
    '''Получение названия специализации через её id'''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/specializations/{spec_id}", headers=TELEGRAM_HEADERS)
            if response.status_code == 200:
                return response.json()["name"]
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def toggle_technology_name(tech_id: str):
    '''Получение названия технологии через её id'''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/technologies/{tech_id}", headers=TELEGRAM_HEADERS)
            if response.status_code == 200:
                return response.json()["name"]
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_applicant_auth_token(user_id: int):
    '''Получает токен пользователя для использования api экшенов, требующих авторизацию'''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
            if response.status_code == 200:
                auth_token_data = response.json()
                return auth_token_data.get('auth_token')
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_applicant_info_by_telegram_id(token_key: str, user_id: int):
    '''Получение информации о соискателе, исходя из привязанного тг, в человекочитаемом формате (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/by-telegram", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS) # стираю токен с бд
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")
        
async def edit_applicant_profile(data: dict, token_key: str, user_id: int):
    '''Частичное редактирование профиля пользователя, используя данные data (PATCH)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(f"http://backend:8000/api/accounts/me", json=data, headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS) # стираю токен с бд
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_available_cities_with_applicant_option(token_key: str, user_id: int):
    '''Получение всех использующихся городов в сервисе + помечание города, который выбрал пользователь (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/all-available-cities-info", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_available_experience_choices_with_applicant_option(token_key: str, user_id: int):
    '''Получение всех использующихся видов опыта работы + помечание опыта, который выбрал пользователь (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/all-available-experience-info", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_available_work_formats_with_applicant_options(token_key: str, user_id: int):
    '''Получение всех использующихся видов формата работы + помечание формата(-ов), который выбрал пользователь (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/all-available-work-formats-info", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_applicant_selected_work_formats_ids(token_key: str, user_id: int):
    '''Получение списка айдишек всех выбранных форматов работы пользователем (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/list-applicant-work-formats-ids", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_available_specializations_with_applicant_options(token_key: str, user_id: int):
    '''Получение всех использующихся видов специализаций + помечание специализаций, выбранных пользователем'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/all-available-specializations-info", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_applicant_selected_specializations_ids(token_key: str, user_id: int):
    '''Получение списка айдишек всех выбранных специализаций пользователем (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/list-applicant-specializations-ids", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_technologies_by_query(data: dict, token_key: str, user_id: int):
    '''Получение списка технологий, исходя из параметра query - пользовательского ввода (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/technologies-list-by-query", params=data, headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_all_applicant_selected_technologies_ids(token_key: str, user_id: int):
    '''Получение списка айдишек всех выбранных технологий пользователем (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/accounts/list-applicant-technologies-ids", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def login(data: dict):
    '''Вход в аккаунт Techhire через телеграм-бота (POST)'''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://backend:8000/api/accounts/telegram-auth", json=data)
            response_data = response.json()
            if response.status_code == 200:
                if response_data.get('token', ''):
                    return True, response_data
            return False, response_data
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def logout(token_key: str):
    '''Выход из аккаунта Techhire через телеграм-бота (POST)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://backend:8000/api/accounts/logout", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_applicant_favourite_vacancies_list(token_key: str, user_id: int):
    '''Получение списка избранных вакансий пользователя (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://backend:8000/api/vacancies/favourites", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_favourite_vacancy_work_formats_names(vac_id: str, token_key: str, user_id: int):
    '''Получение списка названий форматов работы избранной вакансии (GET)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/vacancies/{vac_id}/work-formats-names", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

#remove-from-favourites
async def remove_vacancy_from_favourites(vac_id: str, token_key: str, user_id: int):
    '''Удаление избранной вакансии (DELETE)'''
    auth_headers = {
        "Authorization": f"Token {token_key}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"http://backend:8000/api/vacancies/{vac_id}/remove-from-favourites", headers=auth_headers)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                await client.put(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
                return False, {"error": "unauthorized", "detail": response.json()["detail"]}
            return False, response.json()
        except Exception as e:
            print(f"Ошибка связи с API: {e}")