from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters, authentication, permissions, views, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from projects import serializers
from core.permissions import IsAdminOrReadOnly
from core import models
from core import models_project

from projects.utils import project_prize


class ProjectModelViewSet(viewsets.ModelViewSet):
    """Project Viewset"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.ProjectModelSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "proposed_by")
    queryset = models_project.ProjectModel.objects.all()

    def get_queryset(self):
        """Return list of charities"""
        queryset = self.queryset
        return queryset.order_by('name')

    def perform_create(self, serializer):
        """Start new project"""
        serializer.save(proposed_by=self.request.user)


class TeamRequirementsViews(views.APIView):
    """Team Requirements Views"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.TeamRequirementsModelSerializer

    def get(self, request, pk):
        """Get team requirements for specific project"""
        team_requirements = get_object_or_404(models_project.TeamRequirementsModel, project=pk)
        serializer_context = {"request": request}
        serializer = self.serializer_class(team_requirements, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Create team requirements for specific project"""
        team_requirements = get_object_or_404(models_project.TeamRequirementsModel, project=pk)
        serializer = serializers.TeamRequirementsModelSerializer(team_requirements, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectPhaseViews(views.APIView):
    """View for advancing project"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.ProjectPhaseSerializer

    def get(self, request, pk):
        """Get project phase specific project"""
        project_phase = get_object_or_404(models_project.ProjectModel, id=pk)
        serializer_context = {"request": request}
        serializer = self.serializer_class(project_phase, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Advance project to the next phase"""
        project_phase = get_object_or_404(models_project.ProjectModel, id=pk)
        serializer = serializers.ProjectPhaseSerializer(project_phase, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteProjectView(views.APIView):
    """View for completing project"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM

    def get(self, request, pk):
        return Response({"message": f"Finish the project with id: {pk}"})

    def post(self, request, pk):
        """Finish the project"""
        project = get_object_or_404(models_project.ProjectModel, id=pk)
        project_team = models_project.TeamMembershipModel.objects.filter(project=project)
        project_manager = models.MyProfile.objects.get(owner=project.proposed_by)

        team_members, prize = project_prize(project, project_team)
        try:
            project_manager.my_wallet = project_manager.my_wallet + 540
            project_manager.save()

            for element in project_team:
                member = element.member
                winners = models.MyProfile.objects.filter(owner=member)
                for element in winners:
                    element.my_wallet += prize
                    element.save()

                # project.delete()
            return Response(
                ({"message": f"Project was successfully completed. Each of {team_members} team members "
                             f"received {prize} LeanCoins. Additionally 540 LeanCoins has been transferred "
                             f"to {project_manager} for successful project completion"}))

        except Http404:
            return Response({"error": "We couldn't finish project at this time. Try again later"})


class TeamJoinView(views.APIView):
    """View for joining project team"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.TeamMembershipModelSerializer

    def post(self, request, pk):
        request_user = self.request.user
        project = get_object_or_404(models_project.ProjectModel, id=pk)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(member=request_user, project=project)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamRejectView(views.APIView):
    """View for rejecting team member"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.TeamRejectionSerializer

    def get(self, request, pk, id):
        project = get_object_or_404(models_project.ProjectModel, id=pk)
        team_member = get_object_or_404(models_project.TeamMembershipModel, project=project, member=id)
        serializer_context = {"request": request}
        serializer = self.serializer_class(team_member, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, id):
        project = get_object_or_404(models_project.ProjectModel, id=pk)
        try:
            team_member = get_object_or_404(models_project.TeamMembershipModel, project=project, member=id)
            team_member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TeamMembershipModel.DoesNotExist:
            raise Http404

class ProjectIssueView(views.APIView):
    """Project Issue Viewset"""
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrReadOnly)  ## DEL ADMIN ONLY, CREATE PM
    serializer_class = serializers.IssueModelSerializer

    def get(self, request, pk):
        return Response({"message": f"Report an issue for the project with id: {pk}"})
