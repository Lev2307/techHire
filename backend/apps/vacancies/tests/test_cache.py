from django.test import TestCase
from django.core.cache import cache
from django.core.management import call_command

from apps.accounts.models import Applicant, CITY_CHOICES
from ..cache import (
    get_user_city_info_from_cache_superjob, 
    get_user_city_info_from_cache_hh,
    get_superjob_vacancy_from_cache,
    get_hh_vacancy_from_cache
)
from ..api_utils.constants import SUPERJOB_API_HEADERS, HH_API_HEADERS

class VacanciesCacheTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("create_init_models_data")
        super().setUpTestData()

    def setUp(self):
        self.moscow = CITY_CHOICES[0][1]
        self.spb = CITY_CHOICES[1][1]

        self.applicant = Applicant.objects.create(email='a@a.com', password='123')
        self.applicant.save()

        cache.clear()

    def test_get_user_city_info_from_cache_superjob_hit(self):
        '''Проверка на корректность кэширования города соискателя для api Superjobа'''
        # Moscow not in cache for Superjob api source
        self.assertEqual(cache.get(f"SUPERJOB_CITY_INFO_{self.moscow}"), None)

        # Moscow in cache for Superjob api source
        city = get_user_city_info_from_cache_superjob(self.moscow, SUPERJOB_API_HEADERS)
        self.assertEqual(cache.get(f"SUPERJOB_CITY_INFO_{self.moscow}")["id"], city)
        
        # check if spb not in cache for Superjob api source
        self.assertEqual(cache.get(f"SUPERJOB_CITY_INFO_{self.spb}"), None)

    def test_get_user_city_info_from_cache_hh_hit(self):
        '''Проверка на корректность кэширования города соискателя для api HH'''
        # Moscow not in cache for HH api source
        self.assertEqual(cache.get(f"HH_CITY_INFO_{self.moscow}"), None)

        # Moscow in cache for HH api source
        city = get_user_city_info_from_cache_hh(self.moscow, HH_API_HEADERS)
        self.assertEqual(cache.get(f"HH_CITY_INFO_{self.moscow}")["id"], city)
        
        # check if spb not in cache for HH api source
        self.assertEqual(cache.get(f"HH_CITY_INFO_{self.spb}"), None)

    def test_get_superjob_vacancy_from_cache_hit(self):
        '''Проверка на корректность кэширования вакансии (24 часа) из api Superjob'''
        superjob_latest_vac_id = "51320730"
        # vacancy not stored in cache
        self.assertEqual(cache.get(f"SUPERJOB_VACANCY_ID_{superjob_latest_vac_id}"), None)

        # vacancy stored in cache
        vac_stored = get_superjob_vacancy_from_cache(superjob_latest_vac_id, SUPERJOB_API_HEADERS)
        self.assertEqual(cache.get(f"SUPERJOB_VACANCY_ID_{superjob_latest_vac_id}"), vac_stored) # external ids equals

    def test_get_hh_vacancy_from_cache(self):
        '''Проверка на корректность кэширования вакансии (24 часа) из api HH'''
        hh_latest_vac_id = "128013899"
        # vacancy not stored in cache
        self.assertEqual(cache.get(f"HH_VACANCY_ID_{hh_latest_vac_id}"), None)

        # vacancy stored in cache
        vac_stored = get_hh_vacancy_from_cache(hh_latest_vac_id, HH_API_HEADERS)
        self.assertEqual(cache.get(f"HH_VACANCY_ID_{hh_latest_vac_id}"), vac_stored) # external ids equals