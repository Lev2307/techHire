from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from django.core.cache import cache

from apps.accounts.models import Applicant
from ..api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from ..models import Vacancy, SearchHistory
from ..helpers import (
    extract_keywords_from_text,
    get_applicant_criterias_for_filtering_vacancies, 
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies
)
from .applicant_profile import calculate_total_similarity_between_appilicant_profile_and_vacancy
from .favourites import calculate_total_similarity_between_vacancy_and_applicant_favourites 

def filter_vacancies_by_similarity(
    vacancies: list, 
    applicant_data: dict, 
    applicant_favourites_vacancies_data: dict, 
    applicant_search_history: dict,
    threshold=0.6
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

    vacancies_texts_keywords = []
    for vac in vacancies:
        title = vac.get("title").split()
        duties = vac.get('duties') if vac.get('duties') != NOT_FOUND_DUTIES else []
        reqs = vac.get('requirements') if vac.get('requirements') != NOT_FOUND_REQS else []
        keywords = extract_keywords_from_text(" ".join(title*2 + duties + reqs))
        vacancies_texts_keywords.append(keywords)

    vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w[\w\+#]*\b')

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
        # print(total_similarity, vacancy["title"], similarities[0][idx])
        if len(applicant_favourites_vacancies_data.keys()) > 0:
            similarity_with_favourites_ratio = calculate_total_similarity_between_vacancy_and_applicant_favourites(
                vacancy=vacancy,
                vacancy_text_only_keywords=vacancies_texts_keywords[idx], 
                favourites=applicant_favourites_vacancies_data
            )
            total_similarity += similarity_with_favourites_ratio
            if total_similarity >= threshold:
                filtered_vacancies.append((vacancy, similarities[0][idx], total_similarity))
        else:
            if total_similarity >= threshold-0.2:
                filtered_vacancies.append((vacancy, similarities[0][idx], total_similarity))
    filtered_vacancies.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return [i[0] for i in filtered_vacancies][:12] # get top 12 recommended


def get_recommended_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))
    all_latest_it_vacancies = [] if not cache.get(f"STORED_VACANCIES_FOR_RECOMMENDATIONS_CITY_{user.get_city_display()}") else cache.get(f"STORED_VACANCIES_FOR_RECOMMENDATIONS_CITY_{user.get_city_display()}") # get vacancies for user city from cache
    all_latest_it_vacancies = [d for d in all_latest_it_vacancies if d]
    for vac in all_latest_it_vacancies:

        if vac["duties"] == NOT_FOUND_DUTIES and vac["requirements"] == NOT_FOUND_REQS:
            all_latest_it_vacancies.remove(vac)
        if vac["is_added_to_favorites"] == True:
            all_latest_it_vacancies.remove(vac)
    if all_latest_it_vacancies:
        filtered_vacancies = filter_vacancies_by_similarity(
            all_latest_it_vacancies, 
            applicant_data, 
            applicant_fav_vacancies_data,
            applicant_search_histories
        )
        return filtered_vacancies
    return []