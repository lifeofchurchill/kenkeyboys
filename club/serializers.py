from rest_framework import serializers

from .models import Player


class PlayerSerializer(serializers.ModelSerializer):
    """Turns a Player into JSON for the website and app."""

    # The model stores "ST"; this adds the readable label "Striker" alongside it
    position_label = serializers.CharField(source="get_position_display", read_only=True)

    class Meta:
        model = Player
        # Only these fields are exposed. is_active and user stay private
        fields = [
            "id",
            "display_name",
            "gamertag",
            "position",
            "position_label",
            "shirt_number",
            "platform",
            "joined_on",
            "Photo"
        ]