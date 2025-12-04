from config.settings import HH_API_ACCESS_TOKEN, SUPERJOB_API_KEY


NOT_FOUND_DUTIES = "Отсутствует информация о задачах"
NOT_FOUND_REQS = "Отсутствует информация о требованиях"
NOT_FOUND_WORK_COND = "Отсутствует информация об условиях работы"

HH_API_HEADERS = {
    "Authorization": f"Bearer {HH_API_ACCESS_TOKEN}",
    "User-Agent": "TechHire/1.0"
}

SUPERJOB_API_HEADERS = {
    'X-Api-App-Id': SUPERJOB_API_KEY
}

NUMBER_OF_VACANCIES_TO_BE_FOUND = 35