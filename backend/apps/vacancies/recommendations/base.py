from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.accounts.models import Applicant
from ..api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from ..cache import store_in_cache_vacancies_gathered_from_api_for_recommendations
from ..models import Vacancy, SearchHistory
from ..helpers import (
    extract_keywords_from_lists,
    get_applicant_criterias_for_filtering_vacancies, 
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies
)
from .applicant_profile import calculate_total_similarity_between_appilicant_profile_and_vacancy
from .favourites import calculate_total_similarity_between_vacancy_and_applicant_favourites 

def fliter_vacancies_by_similarity(
    vacancies: list, 
    applicant_data: dict, 
    applicant_favourites_vacancies_data: dict, 
    applicant_search_history: dict,
    threshold=0.8
    ) -> list:
    '''
        Фильтрует вакансии, используя косинусное сходство векторов вакансий, полученных из апи, и профиля пользователя с его избранными вакансиями и историей поиска. 
        Возвращает список отсортированных вакансий по убыванию сходства
    '''
    applicant_text_skills = (
        applicant_data['specializations'] + " " + applicant_data['technologies'] + " "
    )
    applicant_text_skills += " ".join(applicant_search_history) # applicant specs, techs and search history
    applicant_text_skills_with_his_search_history = applicant_text_skills.lower()
    print(applicant_text_skills_with_his_search_history)

    vacancies_texts_keywords = []
    for vac in vacancies:
        duties = vac.get('duties') if vac.get('duties') != NOT_FOUND_DUTIES else []
        reqs = vac.get('requirements') if vac.get('requirements') != NOT_FOUND_REQS else []
        keywords = extract_keywords_from_lists(" ".join(duties + reqs))
        vacancies_texts_keywords.append(keywords)

    vectorizer = TfidfVectorizer()

    tfidf_matrix = vectorizer.fit_transform(
        [applicant_text_skills_with_his_search_history] + vacancies_texts_keywords
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
            total_similarity += similarity_with_favourites_ratio * 0.9
        # print(similarities[0][idx], similarity_with_applicant_profile_ratio, total_similarity)
        if total_similarity >= threshold:
            filtered_vacancies.append((vacancy, similarities[0][idx]))
    filtered_vacancies.sort(key=lambda x: x[1], reverse=True)
    return [i[0] for i in filtered_vacancies]


def get_recommended_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))
    all_latest_it_vacancies = store_in_cache_vacancies_gathered_from_api_for_recommendations(user, lifetime=4*3600)
    for vac in all_latest_it_vacancies:
        if vac["duties"] == NOT_FOUND_DUTIES and vac["requirements"] == NOT_FOUND_REQS:
            all_latest_it_vacancies.remove(vac)
    filtered_vacancies = fliter_vacancies_by_similarity(
        all_latest_it_vacancies, 
        applicant_data, 
        applicant_fav_vacancies_data,
        applicant_search_histories
    )
    return filtered_vacancies