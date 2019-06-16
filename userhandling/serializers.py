from .models import MovieNightEvent
from rest_framework import serializers


class MovieNightEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = MovieNightEvent
        fields = (
            'id', 'motto', 'date', "isactive"
        )

