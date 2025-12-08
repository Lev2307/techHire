from apps.accounts.models import EXPERIENCE_CHOICES
from ..models import WorkFormat

def calculate_total_similarity_between_appilicant_profile_and_vacancy(applicant_profile: dict, vacancy: dict, tech_similarity: float) -> float:
    '''
        Вычисление конечного коэффициента совпадения вакансий с профилем пользователя, используя доп поля (experience, work_format)
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

    total_similarity = tech_similarity * 0.8 + work_format_similarity_ratio * 0.15 + experience_similarity_ratio * 0.3
    return total_similarity



