from django.contrib import admin
from .models import Applicant, ApplicantLinkedTelegram, Specialization, Technology

admin.site.register(Applicant)
admin.site.register(ApplicantLinkedTelegram)
admin.site.register(Specialization)
admin.site.register(Technology)

