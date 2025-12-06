from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.accounts.models import Applicant
from ..api_utils.api_base import get_vacancies_from_combined_api_sources_with_requirements_and_duties_fullfilled_both
from ..api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from ..models import Vacancy
from ..helpers import (
    extract_keywords_from_lists,
    get_applicant_criterias_for_filtering_vacancies, 
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,

)
from .applicant_profile import calculate_total_similarity_between_appilicant_profile_and_vacancy
from .favourites import calculate_total_similarity_between_vacancy_and_applicant_favourites 

def filter_vacancies_by_similarity_between_applicant_favourite_vacancies_with_profile_and_vacancies_gathered_from_api(
    vacancies: list, 
    applicant_data: dict, 
    applicant_favourites_vacancies_data: dict, 
    threshold=0.7
    ) -> list:
    '''Фильтрует вакансии, используя косинусное сходство векторов вакансий (строк) и профиля пользователя с избранными вакансиями. Возвращает список отсортированных вакансий по убыванию сходства'''
    applicant_text_techs = (
        applicant_data['specializations'] + " " + applicant_data['technologies'] + " "
    )
    applicant_text_techs = applicant_text_techs.lower()

    vacancies_texts_keywords = []
    for vac in vacancies:
        duties = vac.get('duties') if vac.get('duties') != NOT_FOUND_DUTIES else []
        reqs = vac.get('requirements') if vac.get('requirements') != NOT_FOUND_REQS else []
        keywords = extract_keywords_from_lists(" ".join(duties + reqs))
        vacancies_texts_keywords.append(keywords)

    vectorizer = TfidfVectorizer()

    tfidf_matrix = vectorizer.fit_transform(
        [applicant_text_techs] + vacancies_texts_keywords
    )

    applicant_vector = tfidf_matrix[0]
    vacancies_vector = tfidf_matrix[1:]
    similarities = cosine_similarity(applicant_vector, vacancies_vector)

    filtered_vacancies = []
    for idx, vacancy in enumerate(vacancies):
        similarity_with_applicant_profile_ratio = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data, 
            vacancy=vacancy,
            tech_similarity=similarities[0][idx]
        )
        total_similarity = similarity_with_applicant_profile_ratio
        if len(applicant_favourites_vacancies_data.keys()) > 0:
            similarity_with_favourites_ratio = calculate_total_similarity_between_vacancy_and_applicant_favourites(
                vacancy=vacancy,
                vacancy_text_only_keywords=vacancies_texts_keywords[idx], 
                favourites=applicant_favourites_vacancies_data
            )
            total_similarity += similarity_with_favourites_ratio
        print(similarities[0][idx], similarity_with_applicant_profile_ratio, total_similarity)
        if total_similarity >= threshold:
            filtered_vacancies.append((vacancy, similarities[0][idx]))
    filtered_vacancies.sort(key=lambda x: x[1], reverse=True)
    return [i[0] for i in filtered_vacancies]


def get_recommended_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    # applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))
    all_latest_it_vacancies = get_vacancies_from_combined_api_sources_with_requirements_and_duties_fullfilled_both(user, 100)
    filtered_vacancies = filter_vacancies_by_similarity_between_applicant_favourite_vacancies_with_profile_and_vacancies_gathered_from_api(
        all_latest_it_vacancies, 
        applicant_data, 
        applicant_fav_vacancies_data
    )
    return filtered_vacancies