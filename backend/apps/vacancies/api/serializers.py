from rest_framework import serializers

from ..models import Vacancy, WorkFormat

class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = "__all__"
        read_only_fields = ['initial_source', "user"]

class WorkFormatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFormat
        fields = "__all__"