from django.db.models import Q

from rest_framework import serializers

from ..models import Applicant, Technology

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
    class Meta:
        model = Applicant
        fields = ['id', 'username', 'first_name', 'email', 'city', 'experience', 'preferred_work_format', 'specializations', 'technologies', 'is_sub', 'linked_telegram']
        read_only_fields = ['id', 'username', 'is_sub', 'linked_telegram']

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