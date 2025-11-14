from django.contrib import admin

from .models import Vacancy, Firm, SearchHistory, WorkFormat

admin.site.register(Vacancy)
admin.site.register(Firm)
admin.site.register(SearchHistory)
admin.site.register(WorkFormat)
