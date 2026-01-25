from django.core.management import call_command
from django.urls import reverse

from rest_framework.test import APITestCase, override_settings

from config.settings import TELEGRAM_ID_FOR_TESTS
from apps.vacancies.models import WorkFormat
from ..models import Applicant, ApplicantLinkedTelegram, Technology, Specialization

class ApplicantsViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()

    def setUp(self):
        self.username = "user"
        self.email = "a@a.com"
        self.first_name = "user name"
        self.specs = list(Specialization.objects.all().values_list("id", flat=True))
        self.techs = list(Technology.objects.all().values_list("id", flat=True))
        self.password = "user123"

        self.tg = ApplicantLinkedTelegram.objects.create(
            user_id=TELEGRAM_ID_FOR_TESTS,
            chat_id=TELEGRAM_ID_FOR_TESTS,
            is_active=True,
        )
        self.applicant = Applicant.objects.create_user(
            username=self.username,
            first_name=self.first_name,
            email=self.email,
            city="Moscow",
            experience="Year",
            linked_telegram=self.tg,
            password=self.password,
        )
        self.applicant.specializations.add(*[self.specs[0], self.specs[3]])
        self.applicant.technologies.add(*[self.techs[0], self.techs[3], self.techs[7], self.techs[12]])
        self.applicant.preferred_work_format.add(*[WorkFormat.objects.get(name_eng="REMOTE")])

        self.tech = Technology.objects.create(name='Test', creator=self.applicant)

        self.admin_user = Applicant.objects.create_superuser(
            username="SUPERADMIN",
            first_name="superadmin name",
            password="123"
        )
        self.admin_tech = Technology.objects.create(name='ADMIN TEST', creator=self.admin_user)


    def test_all_applicants_info_list_permissions(self):
        '''Проверка permissions для экшена list (login_required + admin) (GET)'''
        url = reverse("api:accounts-list")
        anonymous_response = self.client.get(url)

        # authenticated as admin
        self.client.force_login(self.admin_user)
        admin_user_response = self.client.get(url)
        self.client.logout()

        # authenticated as regular user
        self.client.force_login(self.applicant)
        regular_user_response = self.client.get(url)
        self.client.logout()

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")

        self.assertEqual(admin_user_response.status_code, 200)
        self.assertTrue(str(self.applicant.id) in [i.get("id") for i in admin_user_response.json()])
    
        self.assertEqual(regular_user_response.status_code, 403)
        self.assertEqual(regular_user_response.json()["detail"], "You do not have permission to perform this action.")

    def test_applicant_info_retrieve_permissions(self):
        '''Проверка permissions для запроса к конкретному соискателю по id (login_required + admin) (GET)'''
        applicant = Applicant.objects.all().first()
        url = reverse("api:accounts-detail", args=(applicant.id, ))
        anonymous_response = self.client.get(url)

        # authenticated as admin
        self.client.force_login(self.admin_user)
        admin_user_response = self.client.get(url)
        self.client.logout()

        #authenticated as regular user
        self.client.force_login(self.applicant)
        regular_user_response = self.client.get(url)
        self.client.logout()

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")

        self.assertEqual(admin_user_response.status_code, 200)
        self.assertEqual(str(applicant.id), admin_user_response.json()["id"])
    
        self.assertEqual(regular_user_response.status_code, 403)
        self.assertEqual(regular_user_response.json()["detail"], "You do not have permission to perform this action.")


    def test_applicant_profile_login_required(self):
        '''Проверка: только авторизованный пользователь имеет доступ к странице своего профиля (GET)'''
        url = reverse("api:accounts-me")
        anonymous_response = self.client.get(url)

        self.client.force_login(self.applicant)
        auth_response = self.client.get(url)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(auth_response.status_code, 200)
        self.assertEqual(auth_response.json()["username"], self.applicant.username)

    def test_applicant_profile_for_different_users(self):
        '''Проверка корректного вывода данных в зависимости от пользователя при запросе к странице профиля (GET)'''
        url = reverse("api:accounts-me")
        
        # first applicant
        self.client.force_login(self.applicant)
        first_response = self.client.get(url)
        self.client.logout()

        # second applicant
        self.client.force_login(self.admin_user)
        second_response = self.client.get(url)
        self.client.logout()

        self.assertNotEqual(first_response.json()["id"], second_response.json()["id"])
        self.assertEqual(first_response.json()["username"], self.applicant.username)
        self.assertEqual(second_response.json()["username"], self.admin_user.username)

    def test_partial_editing_applicant_profile(self):
        '''Проверка частичного редактирования профиля пользователя (PATCH)'''
        url = reverse("api:accounts-me")
        new_partial_data = {
            'experience': 'No exp'
        }

        self.client.force_login(self.applicant)
        partial_response = self.client.patch(url, data=new_partial_data)

        self.assertEqual(partial_response.status_code, 200)
        self.assertEqual(Applicant.objects.get(username=self.username).experience, new_partial_data["experience"])
    
    def test_forbid_editing_applicant_profile_with_read_only_fields(self):
        '''Проверка запрета редактирования пользовательского профиля, используя read_only поля (PATCH)'''
        url = reverse("api:accounts-me")
        read_only_data = {
            'username': 'READ ONLY admin username',
            'linked_telegram': 1000000001
        }
        
        self.client.force_login(self.applicant)
        response = self.client.patch(url, data=read_only_data)

        self.assertEqual(response.status_code, 200)
        # Ничего не изменилось, он просто скипает их
        self.assertEqual(response.json()["username"], self.applicant.username)
        self.assertEqual(response.json()["linked_telegram"], str(self.applicant.linked_telegram))

    def test_full_editing_applicant_profile_with_own_tech(self):
        '''Проверка полного редактирования профиля пользователя, при этом в поле технологий добавится собственный вариант (PUT)'''
        url = reverse("api:accounts-me")
        new_tech = Technology.objects.create(name="Ruby", creator=self.applicant)
        new_data = {
            'first_name': 'NEW admin name',
            'city': 'Saint Petersburg',
            'experience': 'No exp',
            'specializations': [self.specs[1], self.specs[2]],
            'technologies': [new_tech.id, self.techs[2], self.techs[4]], # new_tech новая созданная
        }

        self.client.force_login(self.applicant)
        response = self.client.put(url, data=new_data)
        edited_applicant = Applicant.objects.filter(username=self.applicant).first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(edited_applicant.first_name, new_data["first_name"])
        self.assertEqual(edited_applicant.city, new_data["city"])
        self.assertEqual(edited_applicant.experience, new_data["experience"])
        self.assertTrue(str(new_tech.id) in response.json()["technologies"])

    def test_full_editing_applicant_profile_with_other_applicant_unapproved_techs(self):
        '''Проверка ОТМЕНЫ редактирования профиля пользователя, если в поле технологий добавится ЧУЖОЙ вариант (КОТОРЫЙ НЕ ПОДТВЕРЖДЕН МОДЕРАЦИЕЙ) (PATCH)'''
        url = reverse("api:accounts-me")
        new_tech = Technology.objects.create(name="OTHER", creator=self.admin_user) # other user tech UNAPPROVED option
        new_data = {
            'technologies': [new_tech.id, self.techs[2], self.techs[4]],
        }
        self.client.force_login(self.applicant)
        response = self.client.patch(url, data=new_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["technologies"], [f'Invalid pk "{str(new_tech.id)}" - object does not exist.'])

    def test_full_editing_applicant_profile_with_other_applicant_approved_techs(self):
        '''Проверка редактирования профиля пользователя, если в поле технологий добавится ЧУЖОЙ вариант, подтвержденный модерацией (PATCH)'''
        url = reverse("api:accounts-me")
        new_tech = Technology.objects.create(name="OTHER", is_approved=True, creator=self.admin_user) # other user tech APPROVED option
        new_data = {
            'technologies': [new_tech.id, self.techs[2], self.techs[4]],
        }
        self.client.force_login(self.applicant)
        response = self.client.patch(url, data=new_data)

        self.assertEqual(response.status_code, 200)

    def test_adding_technology_to_applicant_login_required(self):
        '''Проверка: только авторизованнный пользователь имеет доступ к созданию собсвтенного варианта технологии (POST)'''
        url = reverse("api:accounts-add_technology")
        data = {
            'name': 'New tech'
        }
        anonymous_response = self.client.post(url, data=data)

        self.client.force_login(self.applicant)
        auth_response = self.client.post(url, data=data)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 201)

    def test_adding_technology_to_applicant_correct_data(self):
        '''Проверка добавления пользовательского варианта (подходящий) технологии в свой профиль (POST)'''
        url = reverse("api:accounts-add_technology")
        data = {
            'name': 'New tech'
        }
        
        self.client.force_login(self.applicant)
        response = self.client.post(url, data=data)
        created_tech = Technology.objects.filter(name=data["name"]).first()

        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(created_tech, None)
        self.assertEqual(created_tech.creator, self.applicant)
        self.assertEqual(self.applicant.technologies.filter(name=data["name"]).exists(), True)

    def test_adding_technology_to_applicant_wrong_data(self):
        '''Проверка отмены добавления пользовательского варианта технологии, не прошедшей валидацию, в свой профиль (POST)'''
        url = reverse("api:accounts-add_technology")
        wrong_data = {
            'name': 'Python' # уже существует
        }

        self.client.force_login(self.applicant)
        response = self.client.post(url, data=wrong_data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Название инструмента не должно совпадать', response.json()["name"][0])
    
    def test_editing_technology_login_required(self):
        '''Проверка: только авторизованный пользователь может редактировать свою технологию (PUT/PATCH)'''
        url = reverse("api:accounts-edit_technology", args=(self.applicant.id, self.tech.id))
        data = {
            'name': 'Edit tech name'
        }
        anonymous_response = self.client.patch(url, data=data)

        self.client.force_login(self.applicant)
        auth_response = self.client.patch(url, data=data)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 200)

    def test_editing_technology_only_owner_access(self):
        '''Проверка: только автор варианта технологии имеет доступ к её редакттированию (PUT/PATCH)'''
        url = reverse("api:accounts-edit_technology", args=(self.applicant.id, self.tech.id))
        data = {
            'name': 'Edit test'
        }
        #other user
        self.client.force_login(self.admin_user)
        regular_response = self.client.patch(url, data=data)
        self.client.logout()

        #owner
        self.client.force_login(self.applicant)
        owner_response = self.client.patch(url, data=data)

        self.assertEqual(regular_response.status_code, 403)
        self.assertIn("Доступ к технологии может получить", regular_response.json()["message"])
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).first().name, data["name"])

    def test_tech_status_changed_after_editing(self):
        '''Проверка статуса is_approved при редактировании варианта технологии (если она до этого была одобрена) (PUT/PATCH)'''
        self.tech.is_approved = True
        self.tech.save()
        url = reverse("api:accounts-edit_technology", args=(self.applicant.id, self.tech.id))
        data = {
            'name': 'Edited name for test'
        }

        self.client.force_login(self.applicant)
        response = self.client.put(url, data=data)

        self.assertEqual(Technology.objects.filter(creator=self.applicant).first().is_approved, False)
    
    def test_delete_technology_login_required(self):
        '''Проверка: только авторизованный пользователь может удалить свой вариант технологии (DELETE)'''
        url = reverse("api:accounts-delete_technology", args=(self.applicant.id, self.tech.id))
        
        anonymous_response = self.client.delete(url)

        self.client.force_login(self.applicant)
        auth_response = self.client.delete(url)

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 204)

    def test_delete_technology_only_owner_access(self):
        '''Проверка: только создатель варианта технологии имеет доступ к её удалению (DELETE)'''
        url = reverse("api:accounts-delete_technology", args=(self.applicant.id, self.tech.id))

        #other user
        self.client.force_login(self.admin_user)
        regular_response = self.client.delete(url)
        self.client.logout()

        #owner 
        self.client.force_login(self.applicant)
        owner_response = self.client.delete(url)

        self.assertEqual(regular_response.status_code, 403)
        self.assertIn("Доступ к технологии может получить", regular_response.json()["message"])
        self.assertEqual(owner_response.status_code, 204)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).first(), None)
    
    def test_forbid_deletion_of_approved_technology(self):
        '''Проверка: нельзя удалить подтверждённый вариант технологии, даже если являешься создаталем этого варианта (DELETE)'''
        self.tech.is_approved = True
        self.tech.save()
        url = reverse("api:accounts-delete_technology", args=(self.applicant.id, self.tech.id))

        self.client.force_login(self.applicant)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Нельзя удалить одобренную', response.json()["message"])

    def test_applicant_created_technologies_list_login_required(self):
        '''Проверка: список созданных пользователем вариантов технологий доступен только авторизованным пользователям (GET)'''
        url = reverse('api:accounts-applicant_created_technologies_list', args=(self.applicant.id, ))
        anonymous_response = self.client.get(url)

        self.client.force_login(self.applicant)
        auth_response = self.client.get(url)
        
        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")
        self.assertEqual(auth_response.status_code, 200)
        self.assertEqual(auth_response.json()[0].get('name'), self.tech.name)

    def test_pending_technologies_list_permissions(self):
        '''Проверка permissions для экшена pending_technologies_list (login_required + admin) (GET)'''
        url = reverse("api:accounts-pending_technologies_list")
        anonymous_response = self.client.get(url)

        # authenticated as regular user
        self.client.force_login(self.applicant)
        regular_user_response = self.client.get(url)
        self.client.logout()

        # authenticated as admin
        self.client.force_login(self.admin_user)
        admin_user_response = self.client.get(url)
        self.client.logout()

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")

        self.assertEqual(regular_user_response.status_code, 403)
        self.assertEqual(regular_user_response.json()["detail"], "You do not have permission to perform this action.")

        self.assertEqual(admin_user_response.status_code, 200)
        self.assertEqual(len(admin_user_response.json()), Technology.objects.filter(is_approved=False).count())
    
    def test_moderate_technology_permissions(self):
        '''Проверка permissions для экшена moderate_technology (login_required + admin) (PATCH/DELETE)'''
        url = reverse('api:accounts-moderate_technology', args=(self.tech.id, ))
        anonymous_response = self.client.patch(url)

        # authenticated as regular user
        self.client.force_login(self.applicant)
        regular_user_response = self.client.patch(url)
        self.client.logout()

        # authenticated as admin
        self.client.force_login(self.admin_user)
        admin_user_response = self.client.patch(url)
        self.client.logout()

        self.assertEqual(anonymous_response.status_code, 403)
        self.assertEqual(anonymous_response.json()["detail"], "Authentication credentials were not provided.")

        self.assertEqual(regular_user_response.status_code, 403)
        self.assertEqual(regular_user_response.json()["detail"], "You do not have permission to perform this action.")

        self.assertEqual(admin_user_response.status_code, 200)
    
    def test_no_access_to_moderate_already_approved_technology(self):
        '''Проверка отмены доступа при попытке модерации уже подтверждённой технологии (PATCH/DELETE)'''
        self.tech.is_approved = True
        self.tech.save()
        url = reverse('api:accounts-moderate_technology', args=(self.tech.id, ))

        self.client.force_login(self.admin_user)
        patch_response = self.client.patch(url)
        delete_response = self.client.delete(url)

        self.assertEqual(patch_response.status_code, 403)
        self.assertIn("Технология уже прошла модерацию", patch_response.json()["message"])
        self.assertEqual(delete_response.status_code, 403)
        self.assertIn("Технология уже прошла модерацию", delete_response.json()["message"])

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory' # Use in-memory broker
    )
    def test_denying_technology_while_moderation(self):
        '''Проверка удаления (отклонения) технологии при модерировании (DELETE)'''
        url = reverse('api:accounts-moderate_technology', args=(self.tech.id, ))

        self.client.force_login(self.admin_user)
        delete_response = self.client.delete(url)

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(Technology.objects.filter(creator=self.applicant).count(), 0)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory' # Use in-memory broker
    )
    def test_approving_technology_while_moderation(self):
        '''Проверка подтверждения технологии при модерировании (PATCH)'''
        url = reverse('api:accounts-moderate_technology', args=(self.tech.id, ))

        self.client.force_login(self.admin_user)
        patch_response = self.client.patch(url)
        
        self.assertEqual(patch_response.status_code, 200)
        self.assertIn("была подтверждена модерацией", patch_response.json()["message"])
        self.assertEqual(Technology.objects.filter(creator=self.applicant).first().is_approved, True)