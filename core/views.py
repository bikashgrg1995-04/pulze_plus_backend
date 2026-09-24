from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return Response(
            {
                "status": "ok",
                "service": "pulze_plus_backend",
                "database": "connected",
            }
        )