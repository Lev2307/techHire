from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Applicant, Specialization, Technology
from ..api_utils.api_hh import get_hh_vacancy_data_from_api, get_hh_vacancy_from_cache, get_vacancies_from_headhunter_source
from ..api_utils.constants import HH_API_HEADERS
from ..models import Vacancy, WorkFormat, SearchHistory
from ..helpers import (
    get_payment_from_hh_vacancy, 
    extract_keywords_from_text,
    get_payment_from_hh_vacancy,
    convert_vacancy_payment_to_ru_currency,
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies, 
    prepare_vacancy_for_telegram_message
)

class VacanciesHelpersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()

    def setUp(self):
        self.salary_data = get_hh_vacancy_from_cache("128013899", HH_API_HEADERS)["salary"]
        self.username = 'Admin'
        self.password = '123'
        self.specs_list = list(Specialization.objects.all().values_list("id", flat=True))
        self.techs_list = list(Technology.objects.all().values_list("id", flat=True))
        self.applicant = Applicant.objects.create_user(
            username=self.username,
            password=self.password,
            city='Moscow',
            experience='No exp',
        )
        self.applicant.specializations.add(*[self.specs_list[3], self.specs_list[5], self.specs_list[0]])
        self.applicant.technologies.add(*[self.techs_list[0], self.techs_list[2], self.techs_list[4], self.techs_list[6], self.techs_list[32]])
        self.applicant.preferred_work_format.add(*[WorkFormat.objects.get(name_eng="ON_SITE")])

        self.search_h1 = SearchHistory.objects.create(user=self.applicant, search_query='Python')
        self.search_h2 = SearchHistory.objects.create(user=self.applicant, search_query='Rust')

        self.vacancy_gath_from_api = get_vacancies_from_headhunter_source(query='Flutter Backend', applicant_city_ru_format='Москва', salary_from=0, pages_count=1, are_for_recommendations=False)[1]
        self.vacancy_info = get_hh_vacancy_data_from_api(self.vacancy_gath_from_api.get("external_id"))

        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            initial_source=self.vacancy_info["initial_source"],
            external_id=self.vacancy_info["external_id"],
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
    
    def test_get_payment_from_hh_vacancy(self):
        '''Проверка корректного формата данных о зп вакансии из api HH'''

        # payment exists in vacancy
        payment_from, payment_to = get_payment_from_hh_vacancy(self.salary_data)
        self.assertEqual(payment_from, self.salary_data["from"])
        self.assertEqual(payment_to, self.salary_data["to"])

        # payment is None in vacancy
        payment_from_none, payment_to_none = get_payment_from_hh_vacancy(None)
        self.assertEqual(payment_from_none, 0)
        self.assertEqual(payment_to_none, 0)

        # payment_from/payment_to are None
        payment_from_is_none = {'from': None, 'to': 100_000}
        payment_to_is_none = {'from': 200_000, 'to': None}

        payment_from, payment_to = get_payment_from_hh_vacancy(payment_from_is_none)
        self.assertEqual(payment_from, 0)
        self.assertEqual(payment_to, payment_from_is_none["to"])

        payment_from, payment_to = get_payment_from_hh_vacancy(payment_to_is_none)
        self.assertEqual(payment_from, payment_to_is_none["from"])
        self.assertEqual(payment_to, 0)

    def test_extract_keywords_from_text(self):
        '''Проверка извлечения ключевых навыков/специальностей из текста'''
        text1 = 'Текст состоящий из слов Gemini, Rust, C++. Также в нём присутствует Python и React'
        text2 = 'Второй текст в нём всего два кийворда Docker и Linux, CI/CD'

        keywords1 = extract_keywords_from_text(text1)
        keywords2 = extract_keywords_from_text(text2)

        self.assertEqual(sorted(keywords1.split()), 'c++ gemini python react rust'.split())
        self.assertEqual(sorted(keywords2.split()), 'ci/cd docker linux'.split())

    def test_getting_from_hh_vacancy(self):
        '''Проверка вывода информации о зарплате из HH вакансии'''
        #1
        salary_data1 = None
        payment1 = get_payment_from_hh_vacancy(salary_data1)
        #2 
        salary_data2 = {
            "from": None,
            "to": 1_000_000,
        }
        payment2 = get_payment_from_hh_vacancy(salary_data2)
        #3 
        salary_data3 = {
            "from": 1_000_000,
            "to": None
        }
        payment3 = get_payment_from_hh_vacancy(salary_data3)

        self.assertEqual(payment1, [0, 0])
        self.assertEqual(payment2, [0, 1_000_000])
        self.assertEqual(payment3, [1_000_000, 0])
    
    def test_converting_payment_data_to_rub(self):
        '''Проверка перевода валют с иностранной на рубли (1000USD -> 80_000RUB)'''
        #1
        curr1, pf1, pt1 = 'RUB', 100_000, 350_000
        payment1 = convert_vacancy_payment_to_ru_currency(curr1, pf1, pt1)

        #2
        curr2, pf2, pt2 = 'USD', 1_000, 2_500
        payment2 = convert_vacancy_payment_to_ru_currency(curr2, pf2, pt2)

        self.assertEqual(payment1, [pf1, pt1])
        self.assertNotEqual(payment2, [pf2, pt2])

    def test_getting_applicant_criterias_for_filtering_vacancies(self):
        '''Проверка получения пользовательских критерий (инструменты/специализации, город, опыт работы) для рекомендаций в определённом формате'''
        specs = list(Specialization.objects.all().values_list("name", flat=True))
        techs = list(Technology.objects.all().values_list("name", flat=True))
        applicant_data = get_applicant_criterias_for_filtering_vacancies(self.applicant)
        self.assertEqual(applicant_data['city'], 'Москва')
        self.assertEqual(applicant_data['experience'], 'Нет опыта')
        self.assertEqual(applicant_data['specializations'], " ".join([specs[0], specs[3], specs[5]]))
        self.assertEqual(applicant_data['technologies'], " ".join([techs[0], techs[2], techs[4], techs[6], techs[32]]))

    def test_getting_applicant_search_history_info_for_filtering_vacancies(self):
        '''Проверка получения информации пользователя о его истории поиска'''
        all_searchH = SearchHistory.objects.filter(user=self.applicant)
        data = get_applicant_search_history_info_for_filtering_vacancies(all_searchH)
        self.assertEqual(data, ['Python', 'Rust'])

    def test_getting_applicant_favourite_vacancies_info_for_filtering_vacancies(self):
        '''Проверка получения информации об избранных вакансиях пользователя в определённом формате'''
        q = Vacancy.objects.filter(user=self.applicant)
        data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(q)

        self.assertTrue(data.get(self.vacancy.id))
        self.assertEqual(data[self.vacancy.id]["title"], self.vacancy.title)
        self.assertEqual(data[self.vacancy.id]["payment_from"], self.vacancy.payment_from)
        self.assertEqual(data[self.vacancy.id]["payment_to"], self.vacancy.payment_to)
        self.assertEqual(data[self.vacancy.id]["experience"], 'От 3 до 6 лет')

    def test_prepare_vacancy_for_telegram_message(self):
        '''Проверка корректного вывода текста для определённой вакансии'''
        vac = self.vacancy_gath_from_api
        vac["work_formats"] = [wf.name for wf in vac["work_formats"]]
        result_text = prepare_vacancy_for_telegram_message(vac)
        print(result_text)
