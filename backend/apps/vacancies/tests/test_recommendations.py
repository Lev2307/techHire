from django.core.management import call_command
from django.test import TestCase

from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST
from apps.accounts.models import Applicant
from apps.accounts.tests.factories import generate_specs, generate_techs
from ..api_utils.api_hh import get_vacancies_from_headhunter_source, get_hh_vacancy_data_from_api
from ..helpers import (
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies
)
from ..models import Vacancy, WorkFormat
from ..recommendations.applicant_profile import calculate_total_similarity_between_appilicant_profile_and_vacancy
from ..recommendations.favourites import calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy

class RecomendationsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()

    def setUp(self):
        self.applicant_us = 'admin'
        self.applicant_password = '123'
        self.applicant_city, self.applicant_city_ru = 'Moscow', 'Москва'
        self.specs_list = generate_specs([SPECIALIZATIONS_LIST[0], SPECIALIZATIONS_LIST[3]])
        self.techs_list = generate_techs([TECHNOLOGIES_LIST[3], TECHNOLOGIES_LIST[7], TECHNOLOGIES_LIST[14], TECHNOLOGIES_LIST[15]])
        
        self.applicant = Applicant.objects.create_user(
            username=self.applicant_us,
            password=self.applicant_password,
            city=self.applicant_city,
            experience='No exp'
        )
        self.applicant.specializations.add(*self.specs_list)
        self.applicant.technologies.add(*self.techs_list)
        self.applicant.preferred_work_format.add(*[WorkFormat.objects.get(name_eng="REMOTE")])

        self.vacancies_gathered_from_api = get_vacancies_from_headhunter_source(query='Flutter Backend', applicant_city_ru_format=self.applicant_city_ru, salary_from=0, pages_count=1, are_for_recommendations=False)
        self.vacancy_gathered_from_api_1 = self.vacancies_gathered_from_api[0]

        # favourite vacancy
        self.vacancy_gathered_from_api_for_favs = self.vacancies_gathered_from_api[3]
        self.vacancy_info = get_hh_vacancy_data_from_api(self.vacancy_gathered_from_api_for_favs["external_id"])
        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            initial_source=self.vacancy_info["initial_source"],
            external_id=self.vacancy_gathered_from_api_for_favs["external_id"],
            title=self.vacancy_info["title"],
            duties=self.vacancy_info["duties"],
            requirements=self.vacancy_info["requirements"],
            working_conditions=self.vacancy_info["working_conditions"],
            payment_from=self.vacancy_info["payment"]["payment_from"],
            payment_to=self.vacancy_info["payment"]["payment_to"],
            currency=self.vacancy_info["payment"]["currency"],
            experience=self.vacancy_info["experience"],
            education=self.vacancy_info["education"],
            date_published=self.vacancy_info["date_published"],
            valid_until=self.vacancy_info["valid_until"],
            original_link=self.vacancy_info["original_link"],
        )
        self.vacancy.work_format.add(*self.vacancy_info["work_formats"])


    def test_calculate_similarity_between_applicant_profile_and_vacancy_by_work_format(self):
        '''Проверка корректного рассчёта коэффициента сходства профиля пользователя и вакансии, полученной из api, по их формату работы'''
        applicant_data = get_applicant_criterias_for_filtering_vacancies(self.applicant)
        vac = self.vacancy_gathered_from_api_1
        # совпадение 1 формата работы
        vac["work_formats"] = [WorkFormat.objects.get(name_eng="REMOTE")]                          
        coefficient_with_workformat_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(0.15 == coefficient_with_workformat_match)

        # частичное совпадение формата работы
        vac["work_formats"] = [WorkFormat.objects.get(name_eng="REMOTE"), WorkFormat.objects.get(name_eng="HYBRID")]
        coefficient_with_workformat_partial_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(0.105 == coefficient_with_workformat_partial_match)

        # совпадение нескольких форматов
        self.applicant.preferred_work_format.add(*[WorkFormat.objects.get(name_eng="HYBRID")]) # добавляем ещё 1 формат работы
        applicant_data_new = get_applicant_criterias_for_filtering_vacancies(self.applicant)
        coefficient_with_workformat_whole_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data_new,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(coefficient_with_workformat_whole_match == 0.25)

        # несовпадение
        vac["work_formats"] = [WorkFormat.objects.get(name_eng="Not specified")]
        coefficient_with_workformat_no_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(coefficient_with_workformat_no_match == 0.0)

        self.applicant.preferred_work_format.remove(*[WorkFormat.objects.get(name_eng="HYBRID")])


    def test_calculate_similarity_between_applicant_profile_and_vacancy_by_experience(self):
        '''Проверка корректного рассчёта коэффициента сходства профиля пользователя и вакансии, полученной из api, по их опыту работы'''
        applicant_data = get_applicant_criterias_for_filtering_vacancies(self.applicant)
        vac = self.vacancy_gathered_from_api_1
        vac["work_formats"] = [WorkFormat.objects.get(name_eng="Not specified")]

        # 1 НЕсовпадение опыта работы
        coefficient_with_experience_NO_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(coefficient_with_experience_NO_match == 0.0)

        # 2 полное совпадение опыта работы
        self.applicant.experience = 'Three years'
        self.applicant.save()
        applicant_data_with_three_years_exp = get_applicant_criterias_for_filtering_vacancies(self.applicant)

        coefficient_with_experience_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data_with_three_years_exp,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(coefficient_with_experience_match == 0.25)

        # 3 частичное совпадение опыта работы (Пользовательский опыт работы оказался больше чем у вакансии)
        vac["experience"] = 'Year'
        vac["experience_ru"] = 'От 1 года до 3 лет'

        coefficient_with_experience_partial_match = calculate_total_similarity_between_appilicant_profile_and_vacancy(
            applicant_profile=applicant_data_with_three_years_exp,
            vacancy=vac,
            tech_similarity=0
        )
        self.assertTrue(coefficient_with_experience_partial_match == 0.2125)

    def test_calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy_by_work_format(self):
        '''Проверка корректного рассчёта коэффициента сходства избранной вакансии и обычной вакансии, полученной из апи, по их формату работы'''
        fav_vacancy = self.vacancy # Очная
        vac_from_api = self.vacancy_gathered_from_api_1
        
        fav_vacancy.experience = 'No exp'
        fav_vacancy.payment_from = 500_000
        fav_vacancy.payment_to= 700_000
        fav_vacancy.save()
        
        # совпадение 1 формата работы                          
        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=self.applicant))
        vac_from_api["work_formats"] = [WorkFormat.objects.get(name_eng="ON_SITE")]
        coefficient_with_workformat_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vacancy.id),
            similarity_by_keywords=0
        )
        self.assertTrue(0.15 == coefficient_with_workformat_match)

        # частичное совпадение формата работы
        vac_from_api["work_formats"] = [WorkFormat.objects.get(name_eng="ON_SITE"), WorkFormat.objects.get(name_eng="HYBRID")]
        coefficient_with_workformat_partial_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vacancy.id),
            similarity_by_keywords=0
        )
        self.assertTrue(0.105 == coefficient_with_workformat_partial_match)

        # совпадение нескольких форматов
        fav_vacancy.work_format.add(*[WorkFormat.objects.get(name_eng="HYBRID")]) # добавляем ещё 1 формат работы 
        all_favourites_new = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=self.applicant))
        coefficient_with_workformat_whole_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites_new.get(fav_vacancy.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_workformat_whole_match == 0.25)

        # # несовпадение
        vac_from_api["work_formats"] = [WorkFormat.objects.get(name_eng="Not specified")]
        coefficient_with_workformat_no_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites_new.get(fav_vacancy.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_workformat_no_match == 0.0)

        fav_vacancy.work_format.remove(*[WorkFormat.objects.get(name_eng="HYBRID")])

    def test_calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy_by_experience(self):
        '''Проверка корректного рассчёта коэффициента сходства избранной вакансии и обычной вакансии, полученной из апи, по их опыту работы'''
        fav_vac = self.vacancy
        vac_from_api = self.vacancy_gathered_from_api_1

        fav_vac.payment_from = 500_000
        fav_vac.payment_to= 700_000
        fav_vac.save()

        # 1 ПОЛНОЕ совпадение опыта работы
        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_experience_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_experience_match == 0.25)

        # 2 НЕсовпадение опыта работы
        fav_vac.experience = 'No exp'
        fav_vac.save()

        all_favourites_new_no_match_exp = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_experience_no_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites_new_no_match_exp.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_experience_no_match == 0.0)

        # 3 частичное совпадение опыта работы (Пользовательский опыт работы оказался больше чем у вакансии)
        fav_vac.experience = 'Six years'
        fav_vac.save()

        all_favourites_new_partial_exp = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_experience_partial_match = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites_new_partial_exp.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_experience_partial_match == 0.2125)

    def test_calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy_by_payment(self):
        fav_vac = self.vacancy
        vac_from_api = self.vacancy_gathered_from_api_1
        
        fav_vac.experience = 'No exp'
        fav_vac.save()

        # 1 обе вакансии не имеют оплаты (имеется ввиду по договорённости)
        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_payment_equal_by_agreement = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_payment_equal_by_agreement == 0.075)

        # 2 вакансия избранная имеет какую-то инфу о зп, а найденная из api нет (т.е by_agreement)
        fav_vac.payment_from = 500_000
        fav_vac.save()

        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_payment_none_info_for_api_vacancy = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_payment_none_info_for_api_vacancy == 0.0)

        # 3 избранная вакансия и найденная имеют какую-то инфу о зп ( рассмотрю несколько случаев )
        # 3.1 у api вакансии и избранной payment_to=0, но payment_from имеет какие-то значения
        vac_from_api["payment"]["by_agreement"] = False
        vac_from_api["payment"]["payment_from"] = 530_000
        
        coefficient_with_payment_to_0 = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_payment_to_0 == 0.1)

        # 3.2 у api вакансии payment_to=0, а у избранной payment_from = 0
        fav_vac.payment_from = 0
        fav_vac.payment_to = 530_000
        fav_vac.save()
        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_api_vac_payment_to_0 = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_api_vac_payment_to_0 == 0.1)

        # 3.3 у api вакансии payment_to=0, а у избранной всё есть
        fav_vac.payment_from = 550_000
        fav_vac.payment_to = 750_000
        fav_vac.save()

        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_api_vac_payment_to_0 = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_api_vac_payment_to_0 == 0.1)

        # 3.4, 3.5, 3.6 аналогичные, только payment_from у api вакансии = 0, вместо payment_to

        # 3.7 и там и там есть инфа о зп
        vac_from_api["payment"]["payment_from"] = 530_000
        vac_from_api["payment"]["payment_to"] = 800_000

        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_api_all_info = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_api_all_info == 0.1)

        # 4 избранная вакансия не имеет инфы о зп, а найденная имеет
        fav_vac.payment_from = 0
        fav_vac.payment_to = 0
        fav_vac.save()

        all_favourites = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.all())
        coefficient_with_api_no_info_fav = calculate_similarity_by_other_fields_between_vacancy_and_favourite_vacancy(
            vacancy=vac_from_api,
            fav=all_favourites.get(fav_vac.id),
            similarity_by_keywords=0
        )
        self.assertTrue(coefficient_with_api_no_info_fav == 0.0)