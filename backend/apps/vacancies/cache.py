import requests
from django.core.cache import cache

from apps.accounts.models import Applicant

def get_user_city_info_from_cache_superjob(city: str, headers: dict) -> dict:
    if not cache.get(f"SUPERJOB_CITY_INFO_{city}"):
        url = f"https://api.superjob.ru/2.0/towns"
        response = requests.get(url, headers=headers)
        cities = response.json().get("objects", [])
        for j in cities:
            if j["title"] == city:
                cache.set(f"SUPERJOB_CITY_INFO_{city}", j)
                return j["id"]
    else:
        return cache.get(f"SUPERJOB_CITY_INFO_{city}")["id"]

def get_user_city_info_from_cache_hh(city: str, headers: dict):
    if not cache.get(f"HH_CITY_INFO_{city}"):
        url = f"https://api.hh.ru/areas"
        response = requests.get(url, headers=headers)
        russian_cities = []
        for j in response.json():
            if j['name'] == 'Россия':
                russian_cities.append(j["areas"])
                break
        for c in russian_cities:
            for i in c:
                if i["name"] == city:
                    cache.set(f"HH_CITY_INFO_{city}", i)
                    return i["id"]
    else:
        return cache.get(f"HH_CITY_INFO_{city}")["id"]
    
def get_superjob_vacancy_from_cache(external_id: str, headers: dict):
    if not cache.get(f"SUPERJOB_VACANCY_ID_{external_id}"):
        response = requests.get(f"https://api.superjob.ru/2.0/vacancies/{external_id}/", headers=headers)
        if response.status_code == 200:
            cache.set(f"SUPERJOB_VACANCY_ID_{external_id}", response.json(), timeout=3600*24)
            return response.json()
        return {}
    else:
        return cache.get(f"SUPERJOB_VACANCY_ID_{external_id}")

def get_hh_vacancy_from_cache(external_id: str, headers: dict, get_only_desc=False):
    if not cache.get(f"HH_VACANCY_ID_{external_id}"):
        response = requests.get(f"https://api.hh.ru/vacancies/{external_id}/", headers=headers)
        if response.status_code == 200:
            vac = response.json()
            cache.set(f"HH_VACANCY_ID_{external_id}", vac, timeout=3600*24)
            return vac["description"] if get_only_desc else vac
        return {}
    else:
        vac_from_cache = cache.get(f"HH_VACANCY_ID_{external_id}")
        return vac_from_cache["description"] if get_only_desc else vac_from_cache

def store_in_cache_vacancies_gathered_from_api_for_recommendations(user: Applicant, lifetime: int):
    '''
        Для блока рекомендаций сторит в кэш вакансии, полученные из апи на определённый промежуток времени (lifetime)
    '''
    cache.clear()
    from .api_utils import get_vacancies_from_combined_api_sources
    if not cache.get(f"STORED_VACANCIES_FOR_RECOMMENDATIONS_USER_{user.email}"):
        vacancies = get_vacancies_from_combined_api_sources(user, number_of_vacancies=100, pages_count=4)
        cache.set(f"STORED_VACANCIES_FOR_RECOMMENDATIONS_USER_{user.email}", vacancies, timeout=1)
        return vacancies
    else:
        return cache.get(f"STORED_VACANCIES_FOR_RECOMMENDATIONS_USER_{user.email}")
    