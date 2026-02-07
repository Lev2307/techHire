from rest_framework import serializers

from ..models import Vacancy, WorkFormat

class VacancySerializer(serializers.ModelSerializer):
    def get_experience_ru(self, obj):
        return obj.get_experience_display()
    
    experience_ru = serializers.SerializerMethodField(source='get_experience_ru')
    class Meta:
        model = Vacancy
        fields = "__all__"
        read_only_fields = ['initial_source', "user"]
    
class WorkFormatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFormat
        fields = "__all__"