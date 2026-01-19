from django.db.models import Q

from rest_framework import serializers

from .models import Applicant, Technology

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = "__all__"

    def validate(self, attrs):
        tech_name = attrs.get("name")
        if Technology.objects.filter(name__iexact=tech_name, is_approved=True).exists():
            raise serializers.ValidationError('Название инструмента не должно совпадать с названием уже существующего инструмента!!!')


class ApplicantSerializer(serializers.ModelSerializer):
    technologies = serializers.PrimaryKeyRelatedField(queryset=Technology.objects.filter(creator=None, is_approved=True), many=True)
    class Meta:
        model = Applicant
        fields = ['id', 'username', 'first_name', 'email', 'city', 'experience', 'preferred_work_format', 'specializations', 'technologies', 'is_sub', 'linked_telegram']
        read_only_fields = ['id', 'username', 'is_sub', 'linked_telegram']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__( *args, **kwargs)
        if self.user:
            self.fields["technologies"].queryset = Technology.objects.filter(
                Q(is_approved=True) | Q(creator=self.user)
            )