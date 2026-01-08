from apps.accounts.models import EXPERIENCE_CHOICES

def calculate_total_similarity_between_appilicant_profile_and_vacancy(applicant_profile: dict, vacancy: dict, tech_similarity: float) -> float:
    '''
        Вычисление конечного коэффициента совпадения вакансий с профилем пользователя, используя доп поля (experience, work_format)
    '''
    applicant_work_formats = sorted(applicant_profile["preferred_work_format"])
    vacancy_work_formats = sorted([wf.name for wf in vacancy["work_formats"]])
    work_format_similarity_ratio = 0
    if applicant_work_formats == vacancy_work_formats:
        work_format_similarity_ratio = 1 * 0.15
        if len(applicant_work_formats) > 1 and len(vacancy_work_formats) > 1:
            work_format_similarity_ratio = 1 * 0.22
    else:
        for i in range(len(vacancy_work_formats)):
            if vacancy_work_formats[i] in applicant_work_formats:
                work_format_similarity_ratio = 0.7 * 0.15

    experience_similarity_ratio = 0
    if vacancy["experience_ru"] == applicant_profile["experience"]:
        experience_similarity_ratio = 1 * 0.15
    else:
        applicant_profile_experience_index = EXPERIENCE_CHOICES.index((applicant_profile["experience_eng"], applicant_profile["experience"]))
        vacancy_experience_index = EXPERIENCE_CHOICES.index((vacancy["experience"], vacancy["experience_ru"]))
        if applicant_profile_experience_index > vacancy_experience_index:
            experience_similarity_ratio = 0.85 * 0.15
    total_similarity = tech_similarity + round(work_format_similarity_ratio, 5) + round(experience_similarity_ratio, 5)
    return total_similarity
