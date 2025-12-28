from datetime import timedelta
from urllib.parse import urlparse

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from apps.accounts.models import Applicant
from ..api_utils.api_hh import get_vacancies_from_headhunter_source
from ..models import SearchHistory, Vacancy, Firm, WorkFormat

class VacanciesViewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()
    
    def setUp(self):
        self.applicant_username = 'applicant'
        self.applicant_password = 'applicant123'

        self.applicant = Applicant.objects.create_user(username=self.applicant_username, password=self.applicant_password)
        self.applicant.save()

        self.other_user_username = 'other'
        self.other_user_password = 'other123'
        self.other_user = Applicant.objects.create(username=self.other_user_username, password=self.other_user_password)
        self.other_user.save()

        self.query_for_latest_hh_request, self.payment_from_for_latest_hh_request = 'backend Python', 0
        self.latest_vacancies_from_hh_source = get_vacancies_from_headhunter_source(self.query_for_latest_hh_request, self.applicant, self.payment_from_for_latest_hh_request, 2, are_for_recommendations=False)
        self.latest_vac_first = self.latest_vacancies_from_hh_source[0]
        self.latest_vac_second = self.latest_vacancies_from_hh_source[1]


        self.firm = Firm.objects.create(
            name=self.latest_vac_first["employer"]["name"],
            address=self.latest_vac_first["employer"]["address"],
            link=self.latest_vac_first["employer"]["alternate_url"],
        )
        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            external_id=51320730,
            title='Разработчик DWH (Oracle)',
            duties='Разработка и проектирование архитектуры DWH;Оптимизация процессов загрузки и трансформации;Участие в задачах анализа систем источников', 
            requirements='Опыт в качестве разработчика баз данных от 3 лет;Умение читать план и оптимизировать SQL запросы;Опыт работы с Oracle Database;Знание Python;Базовое умение работать с git.', 
            working_conditions='Стабильность и гарантии  оформление в соответствии с ТК РФ;Полис ДМС через 3 месяца работы в компании;Скидки на покупки в сети магазинов «Подружка», скидки у компаний партнеров',
            payment_from=0, 
            payment_to=0, 
            currency='RUR',
            experience='От 3 лет', 
            date_published=timezone.now() + timedelta(days=-7), 
            valid_until=timezone.now() + timedelta(days=30),
            initial_source='HH', 
            firm=self.firm
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
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 302) # redirect to recommendations
        self.assertEqual(response.url, reverse('vacancies:recom_vacancies'))
    
    
    def test_search_vacancies_view_is_login_required(self):
        '''Проверка: только авторизованные пользователи могут зайти на страницу поиска'''
        #anonymous
        response = self.client.get(reverse("vacancies:search_vacancies"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_authenticated = self.client.get(reverse('vacancies:search_vacancies'), query_params={'query': 'Python'})
        self.assertEqual(response_authenticated.status_code, 200)
    
    def test_search_vacancies_view_query_param_query(self):
        '''Проверка наличия параметра query в url поиска вакансий'''
        self.client.login(username=self.applicant_username, password=self.applicant_password)

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
        self.client.login(username=self.applicant_username, password=self.applicant_password)

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
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_authenticated = self.client.get(reverse('vacancies:favourite_vacancies'))
        self.assertEqual(response_authenticated.status_code, 200)
    
    def test_favourite_vacancies_view_access_to_vacancies(self):
        '''Проверка: только пользователь, который добавил вакансию(-ии) в избранное, может их просматривать'''
        vac = Vacancy.objects.all().first()

        #vacancy owner
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertIn(vac.title, response.content.decode('utf-8'))

        self.client.logout()

        #other user
        self.client.login(username=self.other_user_username, password=self.other_user_password)
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertNotIn(vac.title, response.content.decode('utf-8'))
    
    def test_favourite_vacancies_view_only_not_archived_vacancies(self):
        '''Проверка: в избранных вакансиях отображаются только вакансии с флагом is_archived=False (т.е не заархивированы/имеют актуальность)'''
        vac = Vacancy.objects.all().first()

        # vacancy is not archived
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertEqual(list(response.context["favourites"]), [vac])

        # make vacancy archived
        vac.is_archived = True
        vac.save()

        response_with_archived_vac = self.client.get(reverse("vacancies:favourite_vacancies"))
        self.assertEqual(list(response_with_archived_vac.context["favourites"]), [])

    def test_add_vacancy_to_favourites_view_is_login_required(self):
        '''Проверка: только авторизованные пользователи могут добавить вакансию в избранное'''
        #anonymous
        response_anon = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_first['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_first['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_first["payment"]["payment_from"]
            }
        )
        self.assertEqual(response_anon.status_code, 302)
        self.assertEqual(urlparse(response_anon.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_auth = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_first['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_first['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_first["payment"]["payment_from"]
            }
        )
        self.assertEqual(response_auth.status_code, 302)
        self.assertEqual(urlparse(response_auth.url).path, reverse("vacancies:search_vacancies"))
    
    def test_add_vacancy_to_favourites_redirects_correctly_to_search_page(self):
        '''Проверка: POST запрос добавления вакансии в избранное корректно редиректит на страницу поиска'''
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_first['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_first['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_first["payment"]["payment_from"]
            }
        )
        self.assertEqual(response.url, reverse("vacancies:search_vacancies", query={'query': self.query_for_latest_hh_request, 'payment_from': self.latest_vac_first["payment"]["payment_from"]}))

    def test_add_vacancy_to_favorites_parse_mode_non_existed(self):
        '''Проверка: невозможность добавления вакансии в избранное из несуществующего ресурса'''
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_first['external_id'], )), 
            query_params={
                'parse_from': 'BLABLABLABLA',
                'q': 'anything', 
                'pf': self.latest_vac_first["payment"]["payment_from"]
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), 'Wrong parse_from query param')

    def test_adding_already_added_to_favourites_vacancy(self):
        '''Проверка: невозможность добавления в избранное уже добавленной вакансии'''
        vac = Vacancy.objects.all().first()
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(vac.external_id, )), 
            query_params={
                'parse_from': vac.initial_source,
                'q': 'anything', 
                'pf': vac.payment_from
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), 'Was already added to favorites!')

    def test_add_vacancy_to_favourites_creating_firm(self):
        '''Проверка: создание фирмы (или просто получение её инфы, если уже существует фирма) при добавлении вакансии в избранное'''
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        # old firm
        response_with_old_firm = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_first['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_first['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_first["payment"]["payment_from"]
            }
        )
        self.assertEqual(Firm.objects.all().count(), 1)

        # new firm
        response = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_second['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_second['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_second["payment"]["payment_from"]
            }
        )
        self.assertEqual(Firm.objects.all().count(), 2) # 1 -> 2
    
    def test_add_vacancy_to_favourites_view_was_vacancy_added_correctly(self):
        '''Проверка корректного добавления вакансии в избранное'''
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response = self.client.post(
            reverse("vacancies:add_vacancy_to_favourites", args=(self.latest_vac_second['external_id'], )), 
            query_params={
                'parse_from': self.latest_vac_second['initial_source'],
                'q': self.query_for_latest_hh_request, 
                'pf': self.latest_vac_second["payment"]["payment_from"]
            }
        )
        created_vacancy = Vacancy.objects.get(title=self.latest_vac_second["title"])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse("vacancies:search_vacancies"))
        self.assertEqual(Vacancy.objects.filter(title=self.latest_vac_second["title"]).exists(), True)
        # check some fields to store correctly
        self.assertEqual(created_vacancy.external_id, int(self.latest_vac_second["external_id"]))
        self.assertEqual(created_vacancy.title, self.latest_vac_second["title"])
        self.assertEqual(created_vacancy.payment_from, self.latest_vac_second["payment"]["payment_from"])
        self.assertEqual(created_vacancy.payment_to, self.latest_vac_second["payment"]["payment_to"])
        self.assertEqual(created_vacancy.currency, self.latest_vac_second["payment"]["currency"])

    def test_remove_vacancy_from_favourites_view_is_login_required(self):
        '''Проверка: только авторизованные пользователи могут удалить вакансию из избранного'''
        #anonymous
        response_anon = self.client.post(
            reverse("vacancies:remove_vacancy_from_favourites", args=(self.vacancy.external_id, )), 
            query_params={
                'pf': self.vacancy.payment_from
            }
        )
        self.assertEqual(response_anon.status_code, 302)
        self.assertEqual(urlparse(response_anon.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_auth = self.client.post(
            reverse("vacancies:remove_vacancy_from_favourites", args=(self.vacancy.external_id, )), 
            query_params={
                'pf': self.vacancy.payment_from
            }
        )
        self.assertEqual(response_auth.status_code, 302)
        self.assertEqual(urlparse(response_auth.url).path, reverse("vacancies:favourite_vacancies"))
        
    def test_remove_vacancy_from_favourites_view_access_to_remove_vacancy(self):
        '''Проверка: только пользователь, который добавил вакансию в избранное, может удалить её из избранного'''
        # other
        self.client.force_login(self.other_user)
        response_other = self.client.post(
            reverse("vacancies:remove_vacancy_from_favourites", args=(self.vacancy.external_id, )), 
            query_params={
                'pf': self.vacancy.payment_from
            }
        )
        self.assertEqual(Vacancy.objects.all().count(), 1) # 1 -> 1
        self.assertEqual(urlparse(response_other.url).path, reverse("vacancies:recom_vacancies"))

        self.client.logout()

        # owner
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_owner = self.client.post(
            reverse("vacancies:remove_vacancy_from_favourites", args=(self.vacancy.external_id, )), 
            query_params={
                'pf': self.vacancy.payment_from
            }
        )
        self.assertEqual(Vacancy.objects.all().count(), 0) # 1 -> 0
        self.assertEqual(urlparse(response_owner.url).path, reverse("vacancies:favourite_vacancies"))

    def test_recommended_vacancies_are_login_required(self):
        '''Проверка: только авторизованный пользователь может попасть на страницу c рекомендованными вакансиями'''
        #anonymous
        response_anon = self.client.get(reverse('vacancies:recom_vacancies'))
        self.assertEqual(response_anon.status_code, 302)
        self.assertEqual(urlparse(response_anon.url).path, reverse('accounts:login'))

        #authenticated
        self.client.login(username=self.applicant_username, password=self.applicant_password)
        response_auth = self.client.get(reverse('vacancies:recom_vacancies'))
        self.assertEqual(response_auth.status_code, 200)
    