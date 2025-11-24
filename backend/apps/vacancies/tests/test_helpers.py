from django.test import SimpleTestCase

from ..api_utils.api_hh import get_hh_vacancy_from_cache
from ..api_utils.constants import HH_API_HEADERS
from ..helpers import get_payment_from_hh_vacancy

class VacanciesHelpersTests(SimpleTestCase):
    def setUp(self):
        self.salary_data = get_hh_vacancy_from_cache("128013899", HH_API_HEADERS)["salary"]
    
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
