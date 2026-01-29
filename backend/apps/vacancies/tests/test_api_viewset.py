from django.core.management import call_command
from django.urls import reverse

from rest_framework.test import APITestCase

from apps.accounts.models import Applicant, Specialization, Technology
from ..api_utils.api_hh import (
    get_vacancies_from_headhunter_source,
    get_hh_vacancy_data_from_api
)
from ..models import Vacancy, WorkFormat, SearchHistory
from .factories import payment_from_gt_applicant_option, create_more_vacancy_models

class VacanciesViewsSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()

    def setUp(self):
        self.username = 'applicant'
        self.password = '123'
        self.first_name = "applicant name"
        self.specs = list(Specialization.objects.all().values_list("id", flat=True))
        self.techs = list(Technology.objects.all().values_list("id", flat=True))

        self.applicant = Applicant.objects.create_superuser(
            username=self.username,
            first_name=self.first_name,
            password=self.password,
            city='Moscow',
            experience='Year'
        )
        self.applicant.specializations.add(*[self.specs[0], self.specs[2]])
        self.applicant.technologies.add(*[self.techs[0], self.techs[2], self.techs[4]])
        self.applicant.preferred_work_formats.add(*[WorkFormat.objects.get(name_eng="ON_SITE")])

        self.regular_user = Applicant.objects.create_user(
            username='regular',
            password='123reg'
        )

        self.latest_python_vacancies = get_vacancies_from_headhunter_source(
            query='Python', 
            applicant_city_ru_format='Москва', 
            salary_from=0, 
            pages_count=1, 
            are_for_recommendations=False
        )
        self.first_vacancy_info = get_hh_vacancy_data_from_api(external_id=self.latest_python_vacancies[0].get('external_id'))
        self.vacancy = Vacancy.objects.create(
            user=self.applicant,
            initial_source=self.first_vacancy_info["initial_source"],
            external_id=self.first_vacancy_info["external_id"],
            title=self.first_vacancy_info["title"],
            duties=self.first_vacancy_info["duties"],
            requirements=self.first_vacancy_info["requirements"],
            working_conditions=self.first_vacancy_info["working_conditions"],
            payment_from=self.first_vacancy_info["payment"]["payment_from"],
            payment_to=self.first_vacancy_info["payment"]["payment_to"],
            currency=self.first_vacancy_info["payment"]["currency"],
            experience=self.first_vacancy_info["experience"],
            education=self.first_vacancy_info["education"],
            date_published=self.first_vacancy_info["date_published"],
            valid_until=self.first_vacancy_info["valid_until"],
            original_link=self.first_vacancy_info["original_link"],
        )
        self.vacancy.work_formats.set([WorkFormat.objects.get(name=wf) for wf in self.first_vacancy_info["work_formats"]])

    def test_favourite_vacancies_access(self):
        '''Проверка: только авторизованный пользователь имеет доступ к избранным вакансиям (GET)'''
        url = reverse('api:vacancies-favourites')
        anonymous_response = self.client.get(url)

        self.client.force_login(self.applicant)
        auth_response = self.client.get(url)

        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 200)
        self.assertEqual(auth_response.json()[0]["id"], str(self.vacancy.id))

    def test_retrieve_favourite_vacancy_access(self):
        '''Проверка: только авторизованный пользователь, который добавлял вакансию в избранное, имеет к ней доступ (GET)'''
        url = reverse('api:vacancies-detail', args=(self.vacancy.id, ))
        anonymous_response = self.client.get(url)

        self.client.force_login(self.regular_user) # other user
        reg_response = self.client.get(url)
        self.client.logout()

        self.client.force_login(self.applicant)
        owner_response = self.client.get(url)

        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(reg_response.status_code, 403)
        self.assertIn('имеет к ней доступ', reg_response.json()["detail"])
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(owner_response.json()["id"], str(self.vacancy.id))

    def test_applicant_recommendations_access(self):
        '''Проверка: только авторизованный пользователь имеет доступ к своим рекомендованным вакансиям (GET)'''
        url = reverse('api:vacancies-recommendations')
        anonymous_response = self.client.get(url)

        self.client.force_login(self.applicant)
        auth_response = self.client.get(url)

        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 200)
        self.assertTrue(len(auth_response.json()) > 0)

    def test_search_vacancies_auth_access(self):
        '''Проверка: только авторизованный пользователь имеет доступ к поиску вакансий (POST)'''
        data = {
            'query': 'Flutter'
        }
        url = reverse('api:vacancies-search')
        anonymous_response = self.client.post(url, data=data)

        self.client.force_login(self.applicant)
        auth_response = self.client.post(url, data=data)
        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 200)
        self.assertTrue(auth_response.json()["results_amount"] > 20)

    def test_search_vacancies_with_no_query_param(self):
        '''Проверка вывода ошибки при попытке поиска без query (POST)'''
        url = reverse('api:vacancies-search')
        self.client.force_login(self.applicant)
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], 'Неправильный запрос.')

    def test_search_vacancies_search_history_instance_creation(self):
        '''Проверка создания модели SearchHistory при различных условиях (POST)'''
        data1 = {'query': 'Flutter'}
        data2_weird = {'query': 'выалоруцыклпорммивыалорпимлвроаы'}
        url = reverse('api:vacancies-search')

        self.client.force_login(self.applicant)
        correct_response = self.client.post(url, data=data1)
        weird_response = self.client.post(url, data=data2_weird) 
        
        self.assertNotEqual(SearchHistory.objects.filter(search_query=data1['query'].lower()).first(), None)
        self.assertEqual(SearchHistory.objects.filter(search_query=data2_weird['query'].lower()).first(), None)


    def test_search_vacancies_with_salary_from_param(self):
        '''Проверка корректного списка найденных вакансий с учётом минимальной зп. Корректный - каждая вакансия имеет зп от выбранной границы пользователем (POST)'''
        data = {
            'query': '1С',
            'payment_from': 120_000
        }
        url = reverse('api:vacancies-search')

        self.client.force_login(self.applicant)
        response = self.client.post(url, data=data)
        check_payment = list(map(payment_from_gt_applicant_option, [vac["payment"] for vac in response.json()["vacancies"]]))
        self.assertEqual(all(el == True for el in check_payment), True)

    def test_add_vacancy_to_favourites_access(self):
        '''Проверка: только авторизованный пользователь может добавить вакансию в избранное (POST)'''
        vac = self.latest_python_vacancies[2]
        data = {
            'external_id': vac.get('external_id'),
            'source': 'HH'
        }
        url = reverse('api:vacancies-add_to_favourites')
        anonymous_response = self.client.post(url, data=data)

        self.client.force_login(self.applicant)
        auth_response = self.client.post(url, data=data)

        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 201)
        self.assertIn("Вы успешно добавили вакансию в избранное", auth_response.json()["message"])
        self.assertEqual(auth_response.json()["data"]["id"], str(Vacancy.objects.get(external_id=vac["external_id"]).id))

    def test_add_vacancy_invalid_source_param(self):
        '''Проверка вывода ошибки при неправильном параметре source (POST)'''
        vac = self.latest_python_vacancies[2]
        data = {
            'external_id': vac.get('external_id'),
            'source': 'Sobaka.ru'
        }
        url = reverse('api:vacancies-add_to_favourites')

        self.client.force_login(self.applicant)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Неправильный параметр - source.")

    def test_add_vacancy_invalid_source_param(self):
        '''Проверка вывода ошибки при неправильном параметре external_id (POST)'''
        data = {
            'external_id': '11111111111111',
            'source': 'HH'
        }
        url = reverse('api:vacancies-add_to_favourites')

        self.client.force_login(self.applicant)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Неправильный параметр - external_id.")

    def test_add_vacancy_to_favourites_already_added_vac(self):
        '''Проверка вывода ошибки при попытке добавления в избранное уже добавленной туда вакансии (POST)'''
        data = {
            'external_id': str(self.vacancy.external_id),
            'source': 'HH'
        }
        url = reverse('api:vacancies-add_to_favourites')

        self.client.force_login(self.applicant)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 400)
    #     self.assertEqual(response.json()["detail"], "Эта вакансия уже добавлена в избранное.")
    
    def test_try_to_add_mt_5_vacancies_without_being_sub(self):
        '''Проверка вывода ошибки при попытке добавления вакансии соискателем(НЕ саб) при достижении лимита добавленных в избранное (POST)'''
        # создаю ещё 4 вакансии череп
        create_more_vacancy_models(self.applicant, self.latest_python_vacancies[1:5])
        vac = self.latest_python_vacancies[10]
        data = {
            'external_id': vac.get("external_id"),
            'source': 'HH'
        }
        url = reverse('api:vacancies-add_to_favourites')

        self.client.force_login(self.applicant)
        not_sub_response = self.client.post(url, data=data)
        self.client.logout()

        self.applicant.is_sub = True
        self.applicant.save()
        self.client.force_login(self.applicant)
        sub_response = self.client.post(url, data=data)

        self.assertEqual(not_sub_response.status_code, 403)
        self.assertIn("Ограничение на добавление вакансий в избранное", not_sub_response.json()["detail"])
        self.assertEqual(sub_response.status_code, 201)
        self.assertEqual(sub_response.json()['message'], 'Вы успешно добавили вакансию в избранное.')

    def test_remove_vacancy_from_favourites_access(self):
        '''Проверка: только авторизированный пользователь, который добавил её в избранное, имеет доступ к удалению вакансии из избранного'''
        url = reverse('api:vacancies-remove_from_favourites', args=(self.vacancy.id, ))
        anonymous_response = self.client.delete(url)

        self.client.force_login(self.regular_user) # other user
        reg_response = self.client.delete(url)
        self.client.logout()

        self.client.force_login(self.applicant)
        owner_response = self.client.delete(url)

        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(reg_response.status_code, 404)
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(owner_response.json()["message"], "Успешное удаление вакансии из избранного.")