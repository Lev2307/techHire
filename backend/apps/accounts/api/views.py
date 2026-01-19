from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .serializers import ApplicantSerializer, TechnologySerializer
from ..models import Applicant, Technology

class ApplicantsViewSet(viewsets.ModelViewSet):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer

    def get_permissions(self):
        # list, retrieve, pending_technologies, moderate_technology доступны только админам
        if self.action in ['list', 'retrieve', 'pending_technologies_list', 'moderate_technology']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        applicant = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(applicant)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'patch', 'put'], url_path='me', url_name='me')
    def me(self, request):
        applicant = get_object_or_404(Applicant, user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(applicant) 
            return Response(serializer.data)
        
        serializer = self.get_serializer(applicant, data=request.data, partial=True, user=request.user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
        
    @action(methods=['post'], url_path='add-technology', url_name='add_technology', detail=False)
    def add_own_technology(self, request, *args, **kwargs):
        applicant = request.user
        serializer = TechnologySerializer(request.data)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save(creator=applicant)
            applicant.technologies.add(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["put", "patch"], url_path='edit-technology', url_name='edit_technology', detail=True)
    def edit_own_technology(self, request, pk=None):
        technology = get_object_or_404(Technology, pk=pk)
        applicant = request.user
        if technology.creator != applicant:
            return Response({"message": "Доступ к технологии может получить только её владелец."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TechnologySerializer(technology, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["delete"], url_path='delete-technology', url_name='delete_technology', detail=True)
    def delete_own_technology(self, request, pk=None):
        tech = get_object_or_404(Technology, pk=pk)
        applicant = request.user
        if tech.creator != applicant:
            return Response({"message": "Доступ к технологии может получить только её владелец."}, status=status.HTTP_403_FORBIDDEN)

        if tech.is_approved:
            return Response({"message": "Нельзя удалить одобренную технологию из общей базы"}, status=status.HTTP_400_BAD_REQUEST)
        
        tech.delete()
        return Response({"message": "Technology was deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=["get"], url_path="applicant-technologies", url_name="applicant_created_technologies_list", detail=False)
    def applicant_created_technologies_list(self, request, *args, **kwargs):
        applicant_created_techs_list = Technology.objects.filter(creator=request.user).order_by("-created_at")
        serializer = TechnologySerializer(applicant_created_techs_list, many=True)
        return Response(serializer.data)
    
    @action(methods=["get"], url_path="pending-technologies", url_name="pending_technologies_list", detail=False)
    def pending_technologies_list(self, request, *args, **kwargs):
        techs_list_non_approved = Technology.objects.filter(is_approved=False)
        serializer = TechnologySerializer(techs_list_non_approved)
        return Response(serializer.data)
    
    @action(methods=["post", "delete"], url_path="moderate-technology", url_name="moderate_technology", detail=True)
    def moderate_technology(self, request, pk=None):
        tech = get_object_or_404(Technology, pk=pk)
        creator = tech.creator
        if request.method == "DELETE":
            name = tech.name
            tech.delete()
            return Response({"message": f"Технология {name} была отклонена модерацией"}, status=status.HTTP_204_NO_CONTENT)
        tech.is_approved = True
        tech.save()
        if creator and not creator.technologies.filter(name=tech.name).exists(): # автоматически присваивается к пользователю после модерации
            creator.technologies.add(tech)

        return Response({"message": f"Технология {tech.name} была подтвержедна модерацией"}, status=status.HTTP_200_OK)