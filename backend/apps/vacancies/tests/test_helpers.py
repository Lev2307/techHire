from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST
from apps.accounts.models import Applicant
from apps.accounts.tests.factories import generate_techs, generate_specs
from ..api_utils.api_hh import get_hh_vacancy_from_cache
from ..api_utils.constants import HH_API_HEADERS, NOT_FOUND_WORK_COND
from ..models import Vacancy, WorkFormat, SearchHistory
from ..helpers import (
    get_payment_from_hh_vacancy, 
    extract_keywords_from_text,
    get_payment_from_hh_vacancy,
    convert_vacancy_payment_to_ru_currency,
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies
)

class VacanciesHelpersTests(TestCase):
    def setUp(self):
        self.salary_data = get_hh_vacancy_from_cache("128013899", HH_API_HEADERS)["salary"]
        self.username = 'Admin'
        self.password = '123'
        self.specs_list = [SPECIALIZATIONS_LIST[3], SPECIALIZATIONS_LIST[5], SPECIALIZATIONS_LIST[0]]
        self.techs_list = [TECHNOLOGIES_LIST[0], TECHNOLOGIES_LIST[2], TECHNOLOGIES_LIST[7], TECHNOLOGIES_LIST[11]]
        self.specializations = generate_specs(self.specs_list)
        self.technologies = generate_techs(self.techs_list)
        self.wf = WorkFormat.objects.create(name='Очная', name_eng='ON_SITE')
        self.applicant = Applicant.objects.create_user(
            username=self.username,
            password=self.password,
            city='Moscow',
            experience='No exp',
        )
        self.applicant.specializations.add(*self.specializations)
        self.applicant.technologies.add(*self.technologies)
        self.applicant.preferred_work_format.add(*[self.wf])

        self.search_h1 = SearchHistory.objects.create(user=self.applicant, search_query='Python')
        self.search_h2 = SearchHistory.objects.create(user=self.applicant, search_query='Rust')

        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            external_id=51320730,
            title='Разработчик DWH (Oracle)',
            duties='Разработка и проектирование архитектуры DWH;Оптимизация процессов загрузки и трансформации;Участие в задачах анализа систем источников', 
            requirements='Опыт в качестве разработчика баз данных от 3 лет;Умение читать план и оптимизировать SQL запросы;Опыт работы с Oracle Database;Знание Python;Базовое умение работать с git.', 
            working_conditions=NOT_FOUND_WORK_COND,
            payment_from=10_000, 
            payment_to=100_000, 
            currency='RUR',
            experience='От 3 лет', 
            date_published=timezone.now() + timedelta(days=-7), 
            valid_until=timezone.now() + timedelta(days=30),
            initial_source='HH', 
        )
        self.vacancy.work_format.add(*[self.wf])

    
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
        text2 = 'Второй текст в нём всего два кийворда Docker и Linux'

        keywords1 = extract_keywords_from_text(text1)
        keywords2 = extract_keywords_from_text(text2)

        self.assertEqual(sorted(keywords1.split()), 'c++ gemini python react rust'.split())
        self.assertEqual(sorted(keywords2.split()), 'docker linux'.split())

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
        applicant_data = get_applicant_criterias_for_filtering_vacancies(self.applicant)

        self.assertEqual(applicant_data['city'], 'Москва')
        self.assertEqual(applicant_data['experience'], 'Нет опыта')
        self.assertEqual(applicant_data['specializations'], " ".join(self.specs_list))
        self.assertEqual(applicant_data['technologies'], " ".join(self.techs_list))

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
        self.assertEqual(data[self.vacancy.id]["experience"], 'От 3 лет')
        self.assertEqual(data[self.vacancy.id]["work_format"], ['Очная'])


