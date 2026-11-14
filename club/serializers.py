from rest_framework import serializers

from .models import NewsPost, Player, Trophy


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
            "Photo",
        ]

class TrophySerializer(serializers.ModelSerializer):
    # Show the winner's name for individual awards; null for team trophies
    player_name = serializers.CharField(source="player.display_name", read_only=True, default=None)

    class Meta:
        model = Trophy
        fields = ["id", "name", "kind", "season", "player", "player_name", "image"]


class NewsPostSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = NewsPost
        fields = ["id", "title", "category", "category_label", "summary", "body", "image", "published_at"]