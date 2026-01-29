from ..models import Vacancy
from ..api_utils import get_hh_vacancy_data_from_api

def payment_from_gt_applicant_option(payment: dict):
    '''
        Проверка зп у вакансии: если payment_from != 0, то payment_from должно быть максимум на 20.000 меньше, чем введенный вариант пользователем. 
        Иначе зп должно лежать в диапазоне от введенного пользователем варианта до макс. установленного работадателем
    '''
    if payment['by_agreement']:
        return False
    if payment["payment_to"] == 0:
        return True if payment["payment_from"] >= 100_000 else False
    return True if payment["payment_to"] >= 100_000 else False

def create_more_vacancy_models(user, founded_vacancies_data: dict):
    for fv in founded_vacancies_data:
        fv_info = get_hh_vacancy_data_from_api(external_id=fv.get('external_id'))
        vacancy = Vacancy.objects.create(
            user=user,
            initial_source=fv_info["initial_source"],
            external_id=fv_info["external_id"],
            title=fv_info["title"],
            duties=fv_info["duties"],
            requirements=fv_info["requirements"],
            working_conditions=fv_info["working_conditions"],
            payment_from=fv_info["payment"]["payment_from"],
            payment_to=fv_info["payment"]["payment_to"],
            currency=fv_info["payment"]["currency"],
            experience=fv_info["experience"],
            education=fv_info["education"],
            date_published=fv_info["date_published"],
            valid_until=fv_info["valid_until"],
            original_link=fv_info["original_link"],
        )