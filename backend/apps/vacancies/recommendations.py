from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.accounts.models import Applicant, EXPERIENCE_CHOICES
from config.settings import SPECIALIZATIONS_LIST
from .api_utils.api_base import get_vacancies_from_combined_api_sources_with_requirements_or_duties_fullfilled_both
from .api_utils.constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS
from .helpers import (
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies
)
from .models import WorkFormat

ALL_TECHNOLOGIES_FOR_RECOMMENDATIONS = [
    'Python', 'TypeScript', 'Javascript', 'Rust', 'C#', 'C++', 'Swift', 'Kotlin', 'Flutter', 'Java', 'Go', 'Ruby',
    'PHP', 'HTML', 'XML', 'CSS', 'SASS', 'Tailwind', 'Bootstrap' 'React', 'Vue', 'Angular', 'Git', 'Gitlab', 'Docker', 'Kubernetes', 
    'MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis', 'Elasticsearch', 'ClearML', 'MLFlow', 'NLTK', 'TensorFlow', 'Scikit-learn', 
    'NLP', 'CV', 'LLM', '1С', 'GraphQL', 'REST', 'RabbitMQ', 'Kafka', 'Apache', 'Linux', 'Excel',
    'ML', 'AI', 'ChatGPT', 'Grok', 'Gemini',
    'Django', 'Spark', 'Flask', 'FastApi', 'NestJS', 'Express', 'Laravel', 'Spring', 'Figma', 'AdobeXd'
]
ALL_KEYWORDS_LIST = SPECIALIZATIONS_LIST + ALL_TECHNOLOGIES_FOR_RECOMMENDATIONS

def extract_keywords_from_lists(text: str) -> str:
    text_lower = text.lower()
    keywords = [i.lower() for i in ALL_KEYWORDS_LIST]
    founed_keywords = set()
    for keyword in keywords:
        if keyword in text_lower:
            founed_keywords.add(keyword)

    return " ".join(list(founed_keywords))

def calculate_total_similarity(applicant_profile: dict, vacancy: dict, tech_similarity: float) -> float:
    '''
        Подсчёт дополнительных критериев из вакансии и вычисление конечного коэффициента совпадения вакансий с профилем пользователя
    '''
    applicant_work_formats = sorted(applicant_profile["preferred_work_format"])
    vacancy_work_formats = sorted([wf.name for wf in vacancy["work_formats"]])
    all_work_formats = WorkFormat.objects.all().count()
    work_format_similarity_ratio = 0
    for i in range(len(vacancy_work_formats)):
        if vacancy_work_formats[i] in applicant_work_formats:
            work_format_similarity_ratio += 1 / all_work_formats

    experience_similarity_ratio = 0

    if vacancy["experience_ru"] == applicant_profile["experience"]:
        experience_similarity_ratio = 1
    else:
        vacancy_experience_index_count_till = EXPERIENCE_CHOICES.index((vacancy["experience"], vacancy["experience_ru"]))
        for idx in range(len(EXPERIENCE_CHOICES)):
            if idx < vacancy_experience_index_count_till:
                experience_similarity_ratio += 0.25
            
    total_similarity = tech_similarity * 1.2 + work_format_similarity_ratio * 0.3 + experience_similarity_ratio * 0.3
    return total_similarity

def filter_vacancies_by_similarity(vacancies: list, applicant_data: dict, threshold=0.45) -> list:
    '''Фильтрует вакансии, используя косинусное сходство векторов вакансий (строк). Возвращает список отсортированных вакансий по убыванию сходства'''
    applicant_text_techs = (
        applicant_data['specializations'] + " " + applicant_data['technologies'] + " "
    )
    applicant_text_techs = applicant_text_techs.lower()

    vacancies_texts = []
    for vac in vacancies:
        duties = vac.get('duties') if vac.get('duties') != NOT_FOUND_DUTIES else []
        reqs = vac.get('requirements') if vac.get('requirements') != NOT_FOUND_REQS else []
        keywords = extract_keywords_from_lists(" ".join(duties + reqs))
        vacancies_texts.append(keywords)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(
        [applicant_text_techs] + vacancies_texts
    )

    applicant_vector = tfidf_matrix[0]
    vacancies_vector = tfidf_matrix[1:]
    similarities = cosine_similarity(applicant_vector, vacancies_vector)

    filtered_vacancies = []
    mx = 0
    for idx, vacancy in enumerate(vacancies):
        mx = max(mx, similarities[0][idx])
        total_similarity = calculate_total_similarity(applicant_data, vacancy, similarities[0][idx])
        print(similarities[0][idx], total_similarity)
        if total_similarity >= threshold:
            filtered_vacancies.append((vacancy, similarities[0][idx]))
    filtered_vacancies.sort(key=lambda x: x[1], reverse=True)
    return [i[0] for i in filtered_vacancies]


def get_recommended_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    # applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    # applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))
    all_latest_it_vacancies = get_vacancies_from_combined_api_sources_with_requirements_or_duties_fullfilled_both(user, 100)
    filtered_vacancies = filter_vacancies_by_similarity(all_latest_it_vacancies, applicant_data)
    return filtered_vacancies


