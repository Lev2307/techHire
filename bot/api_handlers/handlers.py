import os
import httpx

TELEGRAM_HEADERS = {
    "X-Internal-Token": os.environ.get("TELEGRAM_BOT_TOKEN"),
}

async def get_applicant_info_by_telegram_id(user_id: int):
    '''Получение информации о соискателе, исходя из привязанного тг, в человекочитаемом формате (GET)'''
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/by-telegram/{user_id}", headers=TELEGRAM_HEADERS)
            if response.status_code == 200:
                applicant_data = response.json()
                return applicant_data
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

async def get_applicant_auth_token(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://backend:8000/api/accounts/linked-telegram-info/{user_id}", headers=TELEGRAM_HEADERS)
            if response.status_code == 200:
                token = response.json()
                return token
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