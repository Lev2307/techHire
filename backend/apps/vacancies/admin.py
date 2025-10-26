from django.contrib import admin

from .models import Vacancy, Firm, SearchHistory

admin.site.register(Vacancy)
admin.site.register(Firm)
admin.site.register(SearchHistory)
