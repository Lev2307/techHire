from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.accounts.models import Applicant
from config.settings import TECHNOLOGIES_LIST, SPECIALIZATIONS_LIST
from .api_utils.api_base import get_vacancies_from_combined_api_sources_with_requirements_or_duties_filled
from .api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from .helpers import (
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies
)
from .models import Vacancy, SearchHistory


def extract_keywords_from_lists(text: str) -> str:
    text_lower = text.lower()
    keywords = set()
    techs = [i.lower() for i in TECHNOLOGIES_LIST]
    specs = [i.lower() for i in SPECIALIZATIONS_LIST]

    for tech in techs:
        if tech in text_lower:
            keywords.add(tech)

    for spec in specs:
        if spec in text_lower:
            keywords.add(spec)

    return " ".join(list(keywords))

def filter_vacancies_by_similarity(vacancies: list, applicant_data: dict, threshold=0.15) -> list:
    '''Фильтрует вакансии, используя косинусное сходство векторов вакансий (строк). Возвращает список отсортированных вакансий по убыванию сходства'''
    applicant_text = (
        applicant_data['specializations'] + " " + applicant_data['technologies'] + " " +
        f"{applicant_data['experience']}" + " " +
        applicant_data['preferred_work_format']
    )
    applicant_text = applicant_text.lower()

    vacancies_texts = []
    for vac in vacancies:
        duties = vac.get('duties') if vac.get('duties') != NOT_FOUND_DUTIES else []
        reqs = vac.get('requirements') if vac.get('requirements') != NOT_FOUND_REQS else []
        exp_text = vac.get('experience_ru', '')
        text = " ".join(duties + reqs + [exp_text])
        keywords = extract_keywords_from_lists(text)
        vacancies_texts.append(keywords)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(
        [applicant_text] + vacancies_texts
    )

    applicant_vector = tfidf_matrix[0]
    vacancies_vector = tfidf_matrix[1:]
    similarities = cosine_similarity(applicant_vector, vacancies_vector)

    filtered_vacancies = []
    mx = 0
    for idx, vacancy in enumerate(vacancies):
        print(similarities[0][idx], vacancies_texts[idx])
        mx = max(mx, similarities[0][idx])
        if similarities[0][idx] >= threshold:
            filtered_vacancies.append((vacancy, similarities[0][idx]))
    print(mx)
    filtered_vacancies.sort(key=lambda x: x[1], reverse=True)
    return filtered_vacancies


def get_recommended_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))
    all_latest_it_vacancies = get_vacancies_from_combined_api_sources_with_requirements_or_duties_filled(user)
    filtered_vacancies = filter_vacancies_by_similarity(all_latest_it_vacancies, applicant_data)
    return filtered_vacancies


