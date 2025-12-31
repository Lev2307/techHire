import requests
from django.core.cache import cache

from config.settings import RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS
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
        try:
            response = requests.get(f"https://api.hh.ru/vacancies/{external_id}/", headers=headers, timeout=30)
            if response.status_code == 200:
                vac = response.json()
                cache.set(f"HH_VACANCY_ID_{external_id}", vac, timeout=3600*24)
                return vac["description"] if get_only_desc else vac
            return {}
        except requests.ConnectionError:
            return {}
    else:
        vac_from_cache = cache.get(f"HH_VACANCY_ID_{external_id}")
        return vac_from_cache["description"] if get_only_desc else vac_from_cache