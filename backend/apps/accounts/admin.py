from django.contrib import admin
from .models import Applicant, Specializations, Technologies

admin.site.register(Applicant)
admin.site.register(Specializations)
admin.site.register(Technologies)

