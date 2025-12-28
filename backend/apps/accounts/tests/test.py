from bs4 import BeautifulSoup

from django.test import TestCase
from django.urls import reverse

from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST
from ..models import Applicant, Specialization, Technology
from .factories import generate_specs, generate_techs, generate_applicant_data



class TestAccounts(TestCase):
    def setUp(self):
        self.username = 'admin'
        self.first_name = 'Вася'
        self.email = 'a@b.com'
        self.city = 'Moscow'
        self.exp = 'No exp'
        self.specs = generate_specs([SPECIALIZATIONS_LIST[0], SPECIALIZATIONS_LIST[1]])
        self.techs = generate_techs([TECHNOLOGIES_LIST[0], TECHNOLOGIES_LIST[1]])
        self.password1 = 'pogchamp123'
        self.password2 = 'pogchamp123'
        self.data = generate_applicant_data(self.username, self.first_name, self.email, self.city, self.exp, self.specs, self.techs, self.password1, self.password2)

        self.email_for_login, self.password_for_login = 'a@a.com', 'testpass123'
        self.applicant_for_login = Applicant.objects.create_user(email=self.email_for_login, password=self.password_for_login)
        self.applicant_for_login.save()

    def test_applicant_creation_with_correct_data(self):
        '''Проверка создания учётной записи соискателя с корректными данными'''
        old_applicants = Applicant.objects.all().count()
        response = self.client.post(reverse('accounts:sign-up'), data=self.data)
        
        new_applicants = Applicant.objects.all().count()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(old_applicants+1, new_applicants) # from 0 to 1

    def test_applicant_creation_with_no_fn(self):
        '''Проверка создания учётной записи соискателя без имени'''
        self.data['first_name'] = ''
        response_no_fn = self.client.post(reverse('accounts:sign-up'), data=self.data)
        soup = BeautifulSoup(response_no_fn.content.decode('utf-8'), 'html.parser')
        self.assertEqual(response_no_fn.status_code, 200)
        self.assertNotEqual(soup.find('ul', id='id_first_name_error'), None)

    def test_applicant_creation_with_no_ln(self):
        '''Проверка создания учётной записи соискателя без фамилии'''
        self.data['last_name'] = ''
        response_no_ln = self.client.post(reverse('accounts:sign-up'), data=self.data)
        soup = BeautifulSoup(response_no_ln.content.decode('utf-8'), 'html.parser')
        self.assertEqual(response_no_ln.status_code, 200)
        self.assertNotEqual(soup.find('ul', id='id_last_name_error'), None)

    def test_applicant_creation_with_incorrect_age(self):
        '''Проверка создания учётной записи соискателя c неправильным значением возраста'''
        # age lt 16
        self.data['age'] = 4
        response_lt_16  = self.client.post(reverse('accounts:sign-up'), data=self.data)
        
        # age gt 16
        self.data['age'] = 66
        response_gt_65 = self.client.post(reverse('accounts:sign-up'), data=self.data)

        soup_lt_16 = BeautifulSoup(response_lt_16.content.decode('utf-8'), 'html.parser')
        soup_gt_65 = BeautifulSoup(response_gt_65.content.decode('utf-8'), 'html.parser')

        self.assertEqual(response_lt_16.status_code, 200)
        self.assertNotEqual(soup_lt_16.find('ul', id='id_age_error'), None)

        self.assertEqual(response_gt_65.status_code, 200)
        self.assertNotEqual(soup_gt_65.find('ul', id='id_age_error'), None)

    def test_login_correct_data(self):
        '''Проверка входа в аккаунт c правильными данными'''
        data = {
            'username': self.email_for_login,
            'password': self.password_for_login
        }
        response = self.client.post(reverse('accounts:login'), data=data)
        
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)

    def test_login_incorrect_data(self):
        '''Проверка входа в аккаунт c НЕправильными данными'''
        data = {
            'username': self.email, # other email
            'password': self.password_for_login
        }
        response = self.client.post(reverse('accounts:login'), data=data)
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotEqual(soup.find('ul', class_='errorlist'), None)

    def test_logout(self):
        '''Проверка выхода из системы'''
        self.client.force_login(self.applicant_for_login)

        response = self.client.post(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(response, reverse("homepage"))