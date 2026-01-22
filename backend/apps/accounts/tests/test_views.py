from urllib.parse import urlparse

from bs4 import BeautifulSoup

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.vacancies.models import WorkFormat
from ..models import Applicant, Specialization, Technology

class TestAccounts(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()
    
    def setUp(self):
        self.username = 'admin'
        self.first_name = 'Вася'
        self.email = 'a@b.com'
        self.specs = list(Specialization.objects.all().values_list("id", flat=True))
        self.techs = list(Technology.objects.all().values_list("id", flat=True))
        self.password = '123'
        self.applicant = Applicant.objects.create_user(username=self.username, password=self.password)
        self.applicant.specializations.add(*[self.specs[0], self.specs[1]])
        self.applicant.techs.add(*[self.techs[0], self.techs[1]])
        self.applicant.preferred_work_format.add(*[WorkFormat.objects.get(name_eng="ON_SITE")])

        self.own_tech = Technology.objects.create(
            name='admin tech',
            creator=self.applicant
        )

        self.other_username = "other"
        self.other_us_password = "123"
        self.other_us = Applicant.objects.create_user(username=self.other_username, password=self.other_us_password)


    def test_login_page_access(self):
        '''Проверка доступа к странице логина'''
        response = self.client.get(reverse("accounts:login"))
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(soup.find('a', id="login-button"))

    # регистрацию + сам логин я протестить не смогу, поскольку нужно использовать виджет телеграма для входа в аккаунт по номеру телефона (но теперь оно супер безопасно ;>, фэйк запрос сделать не получится ;>)

    def test_profile_page_is_login_required(self):
        '''Проверка: только авторизованный пользователь может попасть на страницу своего профиля'''
        anon_response = self.client.get(reverse("accounts:profile"))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_edit_profile_page_is_login_required(self): # user has only access to his profile, cause no using pk or smth in url
        '''Проверка: только авторизованный пользователь может попасть на страницу редактирования своего профиля'''
        anon_response = self.client.get(reverse("accounts:edit-profile"))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:edit-profile"))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_edit_profile(self): # неправильные данные могут быть только со стороны запроса, поскольку каждое заполняемое поле - select ;>
        '''Проверка реадктирования профиля пользователя'''
        old_exp = Applicant.objects.all().first().experience
        new_data = {
            'city': 'Moscow',
            'experience': 'Three years',
            'preferred_work_format': '2',
            'specializations': [Specialization.objects.get(name="DevOps").id],
            'technologies': [Technology.objects.get(name="Java").id],
        }
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse("accounts:edit-profile"), data=new_data)
        print(Applicant.objects.all().first().experience)
        overrided_applicant_exp = Applicant.objects.all().first().experience
        self.assertEqual(response.status_code, 302)
        self.assertEqual(overrided_applicant_exp, new_data["experience"])
        self.assertNotEqual(old_exp, overrided_applicant_exp)

    def test_adding_own_technology_option_is_login_required(self):
        '''Проверка: только авторизованный пользователь может добавить собсвтенный вариант технологии к себе'''
        anon_response = self.client.get(reverse("accounts:add-own-technology"))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:add-own-technology"))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_adding_own_technology_option_correct_data(self):
        '''Проверка добавления нового варианта технологии с правильными ввёденными данными'''
        old_techs = Technology.objects.all().count()
        self.client.login(username=self.username, password=self.password)
        correct_data = {
            'name': 'New'
        }
        corr_response = self.client.post(reverse("accounts:add-own-technology"), data=correct_data)
        self.assertEqual(corr_response.status_code, 302)
        self.assertEqual(Technology.objects.filter(name=correct_data["name"]).exists(), True)
        self.assertEqual(Technology.objects.all().count() - old_techs, 1)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).count(), 2)

    def test_adding_own_technology_option_wrong_data(self):
        '''Проверка добавления нового варианта технологии, но введенные данные - неправильные (такой ПОДТВЕРЖДЁННЫЙ вариант уже существует)'''
        self.client.login(username=self.username, password=self.password)
        wrong_data = {
            'name': 'Python' # уже есть питон
        }
        wrong_response = self.client.post(reverse("accounts:add-own-technology"), data=wrong_data)
        soup = BeautifulSoup(wrong_response.content.decode('utf-8'), 'html.parser')
        self.assertEqual(wrong_response.status_code, 200)
        self.assertNotEqual(soup.find('ul', {'class': 'errorlist nonfield'}), None)

    def editing_own_technology_option_is_login_required(self):
        '''Проверка: редактирование собственного варианта технологии доступно только авторизованному пользователю'''
        anon_response = self.client.get(reverse("accounts:edit-own-technology", args=(self.own_tech.id, )))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:edit-own-technology", args=(self.own_tech.id, )))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_editing_own_technology_option_only_creator_access(self):
        '''Проверка: только создатель нового варианта технологии может его редачить'''
        self.client.login(username=self.other_username, password=self.other_us_password)
        other_response = self.client.get(reverse("accounts:edit-own-technology", args=(self.own_tech.id, )))

        self.client.logout()

        self.client.login(username=self.username, password=self.password)
        creator_response = self.client.get(reverse("accounts:edit-own-technology", args=(self.own_tech.id, )))

        self.assertEqual(other_response.status_code, 302)
        self.assertEqual(urlparse(other_response.url).path, reverse('accounts:profile'))
        self.assertEqual(creator_response.status_code, 200)

    def test_editing_own_technology_option(self):
        '''Проверка редактирования собственного варианта технологии'''
        self.client.login(username=self.username, password=self.password)
        correct_data = {
            'name': 'New admin tech' # уже есть питон
        }
        correct_response = self.client.post(reverse("accounts:edit-own-technology", args=(self.own_tech.id, )), data=correct_data)
        self.assertEqual(correct_response.status_code, 302)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).first().name, correct_data["name"])

    def deleting_own_technology_option_is_login_required(self):
        '''Проверка: удаление собственного варианта технологии доступно только авторизованному пользователю'''
        anon_response = self.client.get(reverse("accounts:delete-own-technology", args=(self.own_tech.id, )))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:delete-own-technology", args=(self.own_tech.id, )))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 202)

    def test_deleting_own_technology_option_only_creator_access(self):
        '''Проверка: только создатель нового варианта технологии может его удалить'''
        self.client.login(username=self.other_username, password=self.other_us_password)
        other_response = self.client.post(reverse("accounts:delete-own-technology", args=(self.own_tech.id, )))

        self.client.logout()

        self.client.login(username=self.username, password=self.password)
        creator_response = self.client.post(reverse("accounts:delete-own-technology", args=(self.own_tech.id, )))

        self.assertEqual(other_response.status_code, 302)
        self.assertEqual(urlparse(other_response.url).path, reverse('accounts:profile'))
        self.assertEqual(creator_response.status_code, 302)

    def test_deleting_own_technology_option(self):
        '''Проверка удаления собственного варианта технологии'''
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(reverse("accounts:delete-own-technology", args=(self.own_tech.id, )))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).count(), 0)

    def test_pending_technologies_list_is_login_required(self):
        '''Проверка: странциа модерации вариантов технологий только для авторизованных пользователей'''
        anon_response = self.client.get(reverse("accounts:pending_technologies"))

        self.client.login(username=self.username, password=self.password)
        auth_response = self.client.get(reverse("accounts:pending_technologies"))

        self.assertEqual(anon_response.status_code, 302)
        self.assertEqual(urlparse(anon_response.url).path, reverse('accounts:login'))
        self.assertEqual(auth_response.status_code, 200)

    def test_pending_technologies_list_is_login_required(self):
        '''Проверка: странциа модерации вариантов технологий только для пользователей с админскими правами'''
        self.client.login(username=self.username, password=self.password)
        non_admin_response = self.client.get(reverse("accounts:pending_technologies"))

        self.client.logout()
        self.applicant.is_superuser = True
        self.applicant.save()
        self.client.login(username=self.username, password=self.password)
        admin_response = self.client.get(reverse("accounts:pending_technologies"))
        self.assertEqual(non_admin_response.status_code, 403)
        self.assertEqual(admin_response.status_code, 200)

    def test_pending_technologies_list_approving_technology_variant(self):
        '''Проверка подтверждения варианта технологии, которую создал другой пользователь'''
        self.applicant.is_superuser = True
        self.applicant.save()
        self.client.force_login(user=self.applicant)
        data = {
            'tech_id': self.own_tech.id,
            'action': 'approve'
        }
        admin_response = self.client.post(reverse("accounts:pending_technologies"), data=data)
        self.assertEqual(admin_response.status_code, 302)
        self.assertEqual(Technology.objects.filter(name=self.own_tech.name).first().is_approved, True)

    def test_pending_technologies_list_denying_technology_variant(self):
        '''Проверка удаления варианта технологии, которую создал другой пользователь'''
        self.applicant.is_superuser = True
        self.applicant.save()
        self.client.force_login(user=self.applicant)
        data = {
            'tech_id': self.own_tech.id,
            'action': 'delete'
        }
        admin_response = self.client.post(reverse("accounts:pending_technologies"), data=data)
        self.assertEqual(admin_response.status_code, 302)
        self.assertEqual(Technology.objects.filter(name=self.own_tech.name).first(), None)