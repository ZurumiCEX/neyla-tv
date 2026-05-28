"""Endpoints admin : gestion des utilisateurs (liste filtrable + rôle)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from .models import User
from .permissions import IsAdminRole
from .serializers import AdminUserSerializer


class AdminUserListView(ListAPIView):
    """Liste paginée des utilisateurs avec recherche (`q`) et filtre rôle."""

    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(username__icontains=q)
        return qs


@api_view(["PATCH"])
@permission_classes([IsAdminRole])
def admin_user_detail(request: Request, pk: int) -> Response:
    user = User.objects.filter(pk=pk).first()
    if user is None:
        return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
    serializer = AdminUserSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    from audit.services import record

    record(request.user, "user.update", target=user, meta=dict(serializer.validated_data))
    return Response(serializer.data)
