from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class ObtainAuthToken(APIView):
    """Return a DRF token for valid username/password credentials."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', ObtainAuthToken.as_view(), name='api-token-auth'),
    path('', include('trials.urls', namespace='trials')),
]
