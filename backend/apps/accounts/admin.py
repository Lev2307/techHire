from django.contrib import admin
from .models import Applicant, Specialization, Technology

admin.site.register(Applicant)
admin.site.register(Specialization)
admin.site.register(Technology)

