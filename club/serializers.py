from rest_framework import serializers

from .models import NewsPost, Player, Trophy, TrialRequest


class PlayerSerializer(serializers.ModelSerializer):
    """Turns a Player into JSON for the website and app, with EA's totals."""

    position_label = serializers.CharField(source="get_position_display", read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "display_name",
            "gamertag",
            "position",
            "position_label",
            "shirt_number",
            "platform",
            "photo",
            "joined_on",
            "season_games",
            "season_goals",
            "season_assists",
            "season_rating",
            "season_motm",
            "career_games",
            "career_goals",
            "career_assists",
            "career_rating",
            "career_motm",
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


class TrialRequestSerializer(serializers.ModelSerializer):
    """Accepts a trial request from the website form."""

    class Meta:
        model = TrialRequest
        # Only these four can be sent. "status" is left out on purpose,
        # so nobody can submit a request already marked "accepted"
        fields = ["gamertag", "position", "platform", "message"]