from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from apps.accounts.models import EXPERIENCE_CHOICES
from ..helpers import extract_keywords_from_text

MAX_PAYMENT_DIFF = 50_000

def calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(vacancy: dict, fav: dict, similarity_by_keywords: float) -> float:
    '''
        Рассчёт коэффициента совпадения вакансии с избранной, используя доп поля (experience, work_format, payment)
    '''
    # рассчёт коэффициента совпадения форматов работ у вакансии и пользователя
    fav_work_formats = sorted(fav["work_format"])
    vacancy_work_formats = sorted([wf.name for wf in vacancy["work_formats"]])
    work_format_similarity_ratio = 0
    if fav_work_formats == vacancy_work_formats:
        work_format_similarity_ratio = 1 * 0.15
        if len(fav_work_formats) > 1 and len(vacancy_work_formats) > 1:
            work_format_similarity_ratio = 1 * 0.25
    else:
        for i in range(len(vacancy_work_formats)):
            if vacancy_work_formats[i] in fav_work_formats:
                work_format_similarity_ratio = 0.7 * 0.15

    experience_similarity_ratio = 0
    if vacancy["experience_ru"] == fav["experience"]:
        experience_similarity_ratio = 1 * 0.25
    else:
        applicant_profile_experience_index = EXPERIENCE_CHOICES.index((fav["experience_eng"], fav["experience"]))
        vacancy_experience_index = EXPERIENCE_CHOICES.index((vacancy["experience"], vacancy["experience_ru"]))
        if applicant_profile_experience_index > vacancy_experience_index:
            experience_similarity_ratio = 0.85 * 0.25

    # рассчёт совпадения заработной платы у вакансий
    fav_payment_from, fav_payment_to = fav["payment_from"], fav["payment_to"]
    vacancy_payment_from, vacancy_payment_to = vacancy["payment"]["payment_from"], vacancy["payment"]["payment_to"]
    payment_similarity_ratio = 0
    if vacancy["payment"]["by_agreement"] and (fav_payment_to == 0 and fav_payment_from == 0):
        payment_similarity_ratio = 0.75
    if not vacancy["payment"]["by_agreement"]:
        if vacancy_payment_to == 0:
            if fav_payment_to == 0:
                payment_similarity_ratio = 1 if abs(vacancy_payment_from - fav_payment_from) <= MAX_PAYMENT_DIFF else 0
            elif fav_payment_from == 0:
                payment_similarity_ratio = 1 if abs(vacancy_payment_from - fav_payment_to) <= MAX_PAYMENT_DIFF else 0
            else:
                payment_similarity_ratio = 1 if abs(vacancy_payment_from - fav_payment_from) <= MAX_PAYMENT_DIFF else 0
        elif vacancy_payment_from == 0:
            if fav_payment_from == 0:
                payment_similarity_ratio = 1 if abs(vacancy_payment_to - fav_payment_to) <= MAX_PAYMENT_DIFF else 0
            elif fav_payment_to == 0:
                payment_similarity_ratio = 1 if abs(vacancy_payment_to - fav_payment_from) <= MAX_PAYMENT_DIFF else 0
            else:
                payment_similarity_ratio = 1 if abs(vacancy_payment_to - fav_payment_to) <= MAX_PAYMENT_DIFF else 0
        else:
            payment_similarity_ratio = 1 if abs(vacancy_payment_from - fav_payment_from) <= MAX_PAYMENT_DIFF else 0
    payment_similarity_ratio = payment_similarity_ratio * 0.1
    
    total_similarity = similarity_by_keywords * 0.5 + round(work_format_similarity_ratio, 5) + round(experience_similarity_ratio, 5) + round(payment_similarity_ratio, 5)
    return total_similarity

def calculate_total_similarity_between_vacancy_and_applicant_favourites(vacancy: dict, vacancy_text_only_keywords: str, favourites: dict, threshold=0.5):
    '''
        Рассчёт конечного коэффициента совпадения между вакансией и вакансиями, которые пользователь добавил в избранное
    '''
    favourites_texts_keywords = []
    for key, value in favourites.items():
        keywords = extract_keywords_from_text(" ".join(favourites[key].get('vacancy_texts')))
        favourites_texts_keywords.append(keywords)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(
        [vacancy_text_only_keywords] + favourites_texts_keywords
    )
    vac_vector = tfidf_matrix[0]
    favourites_vector = tfidf_matrix[1:]
    similarities = cosine_similarity(vac_vector, favourites_vector)

    if len(favourites.keys()) == 1:
        each_vacancy_similarity_with_fav_ratio = 0.9
    elif 2 <= len(favourites.keys()) <= 3:
        each_vacancy_similarity_with_fav_ratio = 0.35
    elif 3 < len(favourites.keys()) < 6:
        each_vacancy_similarity_with_fav_ratio = 0.1
    else:
        each_vacancy_similarity_with_fav_ratio = 0.03
    total = 0
    for idx, fav_uuid in enumerate(favourites):
        total_similarity = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vacancy,
            fav=favourites.get(fav_uuid),
            similarity_by_keywords=similarities[0][idx],
        ) 
        total += total_similarity * each_vacancy_similarity_with_fav_ratio
    return threshold if total > threshold else total

