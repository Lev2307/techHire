import time

from django.db.models import Q

from rest_framework import serializers

from apps.vacancies.api.serializers import WorkFormatsSerializer
from ..models import Applicant, ApplicantLinkedTelegram, Technology, Specialization, CITY_CHOICES, EXPERIENCE_CHOICES

class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ["name"]

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = "__all__"

    def validate(self, attrs):
        tech_name = attrs.get("name")
        if Technology.objects.filter(name__iexact=tech_name, is_approved=True).exists():
            raise serializers.ValidationError({'name': 'Название инструмента не должно совпадать с названием уже существующего инструмента!!!'})
        return attrs

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.is_approved = False
        instance.save()
        return instance

class ApplicantSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    class Meta:
        model = Applicant
        fields = ['id', 'username', 'first_name', 'email', 'city', 'experience', 'preferred_work_formats', 'specializations', 'technologies', 'is_sub', 'notifications_enabled', 'linked_telegram']
        read_only_fields = ['username', 'linked_telegram']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__( *args, **kwargs)
        if user:
            qs = Technology.objects.filter(Q(is_approved=True) | Q(creator=user))
        else:
            qs = Technology.objects.filter(is_approved=True, creator=None)
            
        self.fields['technologies'] = serializers.PrimaryKeyRelatedField(
            queryset=qs, 
            many=True
        )

    def create(self, validated_data):
        specializations = validated_data.pop('specializations', [])
        technologies = validated_data.pop('technologies', [])
        preferred_work_formats = validated_data.pop('preferred_work_formats', [])
        
        tg_user_data = self.context['tg_user_data']
        username = tg_user_data.get('username')
        first_name = tg_user_data.get('first_name')
        telega_id = tg_user_data.get('id')

        linked_telega = ApplicantLinkedTelegram.objects.create(user_id=telega_id)
        obj = Applicant.objects.create(
            username=username,
            first_name=first_name,
            linked_telegram=linked_telega,
            **validated_data
        )
        if specializations:
            obj.specializations.set(specializations)
        if technologies:
            obj.technologies.set(technologies)
        if preferred_work_formats:
            obj.preferred_work_formats.set(preferred_work_formats)

        return obj

class ApplicantFullSerializer(serializers.ModelSerializer):
    city = serializers.ChoiceField(
        source='get_city_display',
        choices=CITY_CHOICES
    )
    experience = serializers.ChoiceField(
        source='get_experience_display',
        choices=EXPERIENCE_CHOICES
    )
    preferred_work_formats = WorkFormatsSerializer(many=True, read_only=True)
    specializations = SpecializationSerializer(many=True, read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = Applicant
        fields = ('id', 'first_name', 'email', 'city', 'experience', 'preferred_work_formats', 'specializations', 'technologies', 'is_sub', 'notifications_enabled')

class ApplicantLinkedTelegramSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicantLinkedTelegram
        fields = ["auth_token"]