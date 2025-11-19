from datetime import timedelta
from urllib.parse import urlparse

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST
from apps.accounts.models import Applicant
from ..models import SearchHistory, Vacancy, WorkFormat


class VacanciesViewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()
    
    def setUp(self):
        self.applicant_email = 'applicant@example.com'
        self.applicant_password = 'applicant123'

        self.applicant = Applicant.objects.create_user(email=self.applicant_email, password=self.applicant_password)
        self.applicant.save()

        self.other_user_email = 'other@example.com'
        self.other_user_password = 'other123'
        self.other_user = Applicant.objects.create(email=self.other_user_email, password=self.other_user_password)
        self.other_user.save()

        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            external_id=51320730,
            title='Разработчик DWH (Oracle)',
            duties=['Разработка и проектирование архитектуры DWH', 'Оптимизация процессов загрузки и трансформации', 'Участие в задачах анализа систем источников'], 
            requirements=['Опыт в качестве разработчика баз данных от 3 лет', 'Умение читать план и оптимизировать SQL запросы', 'Опыт работы с Oracle Database', 'Знание Python', 'Базовое умение работать с git.'], 
            working_conditions=['Стабильность и гарантии  оформление в соответствии с ТК РФ', 'Полис ДМС через 3 месяца работы в компании', 'Скидки на покупки в сети магазинов «Подружка», скидки у компаний партнеров'],
            payment_from=0, 
            payment_to=0, 
            currency='RUR',
            experience='От 3 лет', 
            date_published=timezone.now() + timedelta(days=-7), 
            valid_until=timezone.now() + timedelta(days=30),
            initial_source='HH', 
        )
        self.vacancy.work_format.add(WorkFormat.objects.get(name='Не имеет значения'))
        self.vacancy.save()

    def test_home_view_anonymous_response(self):
        '''Проверка анонимного GET запроса к начальной странице'''
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(reverse('accounts:login'), response.content.decode('utf-8'))
    
    def test_home_view_authenticated_response(self):
        '''Проверка авторизированного GET запроса к начальной странице'''
        self.client.login(email=self.applicant_email, password=self.applicant_password)
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 302) # redirect to recommendations
        self.assertEqual(response.url, reverse('vacancies:recom_vacancies'))
    
    def test_recommendations_view_is_login_required(self):
        '''Проверка:только авторизованные пользователи могут зайти на страницу рекомендованных вакансий'''
        #anonymous
        response = self.client.get(reverse("vacancies:recom_vacancies"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(email=self.applicant_email, password=self.applicant_password)
        response_authenticated = self.client.get(reverse('vacancies:recom_vacancies'))
        self.assertEqual(response_authenticated.status_code, 200)
    
    def test_search_vacancies_view_is_login_required(self):
        '''Проверка: только авторизованные пользователи могут зайти на страницу поиска'''
        #anonymous
        response = self.client.get(reverse("vacancies:search_vacancies"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(email=self.applicant_email, password=self.applicant_password)
        response_authenticated = self.client.get(reverse('vacancies:search_vacancies'), query_params={'query': 'Python'})
        self.assertEqual(response_authenticated.status_code, 200)
    
    def test_search_vacancies_view_query_param_query(self):
        '''Проверка наличия параметра query в url поиска вакансий'''
        self.client.login(email=self.applicant_email, password=self.applicant_password)

        response_with_query_param = self.client.get(reverse('vacancies:search_vacancies'), query_params={'query': 'Python'})
        self.assertEqual(response_with_query_param.status_code, 200)
        
        other_response = self.client.get(reverse('vacancies:search_vacancies'))
        self.assertEqual(other_response.status_code, 302)
        self.assertEqual(other_response.url, reverse('vacancies:recom_vacancies'))
    
    def test_search_vacancies_view_searchHistory_model_creation(self):
        '''Проверка создания модели SearcHistory в различных ситуациях:
            1. Нашлось N кол-во вакансий и при этом запрос новый - создаётся
            2. Нашлось N кол-во вакансий, но запрос уже до этого где-то использовался - не создаётся
            3. He нашлось вакансий по запросу - не создаётся
        '''
        prev_search_query = SearchHistory.objects.create(user=self.applicant, search_query='DevOps-engineer')
        query_new = 'Python'
        query_not_found = 'BLABLABLA'
        self.client.login(email=self.applicant_email, password=self.applicant_password)

        # old vacancy name/query
        search_response_with_old_query = self.client.get(reverse("vacancies:search_vacancies"), query_params={'query': 'DevOps'})
        self.assertEqual(SearchHistory.objects.all().count(), 1) # 1 -> 1

        # # strange/not found query (0 results)
        search_response_with_new_query = self.client.get(reverse("vacancies:search_vacancies"), query_params={'query': query_not_found})
        self.assertEqual(SearchHistory.objects.all().count(), 1) # 1 -> 1

        # new vacancy name/query
        search_response_with_new_query = self.client.get(reverse("vacancies:search_vacancies"), query_params={'query': query_new})
        self.assertEqual(SearchHistory.objects.all().count(), 2) # 1 -> 2

    def test_favourite_vacancies_view_is_login_required(self):
        '''Проверка: только авторизованные пользователи могут зайти на страницу избранных вакансий'''
        #anonymous
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(email=self.applicant_email, password=self.applicant_password)
        response_authenticated = self.client.get(reverse('vacancies:favourite_vacancies'))
        self.assertEqual(response_authenticated.status_code, 200)
    
    def test_favourite_vacancies_view_access_to_vacancies(self):
        '''Проверка: только пользователь, который добавил вакансию(-ии) в избранное, может их просматривать'''
        #vacancy owner
        vac = Vacancy.objects.all().first()
        self.client.login(email=self.applicant_email, password=self.applicant_password)
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertIn(vac.title, response.content.decode('utf-8'))

        self.client.logout()

        #other user
        self.client.login(email=self.other_user_email, password=self.other_user_password)
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertNotIn(vac.title, response.content.decode('utf-8'))
