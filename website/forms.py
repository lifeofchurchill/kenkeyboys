from django import forms

from club.models import Player, TrialRequest


class TrialRequestForm(forms.ModelForm):
    """The trial request form on the Join page, built from the TrialRequest model."""

    # A trap for spam bots. Real visitors never see this box (CSS hides it),
    # but bots fill in every box they find. If it comes back filled in, the view
    # quietly throws the submission away
    website = forms.CharField(required=False)

    class Meta:
        model = TrialRequest
        # Only what the applicant may fill in. "status" is left out on purpose:
        # that is the captain's decision, never the visitor's
        fields = ["gamertag", "email", "position", "platform", "message"]
        # The wording shown above each box
        labels = {
            "gamertag": "Gamertag / PSN ID",
            "email": "Email (only used to reply about your trial)",
            "position": "Best position",
            "platform": "Platform",
            "message": "Anything else? (optional)",
        }
        widgets = {
            # autocomplete="email" lets phones fill in the address with one tap
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            # A taller box for the message
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The model allows a blank email (for old requests), but every new
        # applicant must give one, or the captain has no way to reply
        self.fields["email"].required = True

    def clean_gamertag(self):
        """Extra checks on the gamertag. Django runs any method named clean_<field> automatically."""
        # strip() removes spaces typed by accident before or after the name
        gamertag = self.cleaned_data["gamertag"].strip()

        # Someone already in the squad has no need for a trial
        if Player.objects.filter(gamertag__iexact=gamertag, is_active=True).exists():
            raise forms.ValidationError("That gamertag is already in the squad.")

        # One waiting request per player is enough
        if TrialRequest.objects.filter(gamertag__iexact=gamertag, status=TrialRequest.Status.NEW).exists():
            raise forms.ValidationError("A request for this gamertag is already waiting for the captain.")

        # Whatever is returned here is what gets saved
        return gamertag

    def clean_email(self):
        """Tidy the email: no stray spaces, all lower case, so it's stored one consistent way."""
        return self.cleaned_data["email"].strip().lower()