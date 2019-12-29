import pytz
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import LocationPermission, Movie, MovieNightEvent, UserAttendence
from .utils import badgify


def strfdelta(tdelta, fmt):
    d = {"days": abs(tdelta.days)}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


class MovieNightEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(format="%B %d, %Y, %I:%M %p")
    date_delta = serializers.SerializerMethodField()
    movies = serializers.SerializerMethodField()
    vote_enabled = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reg_users = serializers.SerializerMethodField()
    winning_movie = serializers.SerializerMethodField()
    rawdate = serializers.SerializerMethodField()

    def get_rawdate(self, MovieNight):
        return MovieNight.date

    def get_reg_users(self, MovieNight):
        return MovieNight.get_num_registered()

    def get_movies(self, MovieNight):
        return ', '.join([str(movie.title) for movie in MovieNight.MovieList.all()])

    def get_status(self, MovieNight):
        return MovieNight.get_status()

    def get_vote_enabled(self, MovieNight):
        return MovieNight.voting_enabled()

    def get_winning_movie(self, MovieNight):
        try:
            winning_movie, _, _ = MovieNight.get_winning_movie()
            return '{} ({})'.format(winning_movie.title, winning_movie.year)
        except:
            return "?"

    def get_date_delta(self, MovieNight):
        date = MovieNight.date
        now = timezone.now()
        timedelta = date - now
        timedelta_secs = int(timedelta.total_seconds())

        # localize to boston TZ
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz)

        if timedelta_secs > 0:
            return date_boston_time.strftime(fmt) + " (" + strfdelta(timedelta, "In {days}d, {hours}hrs, {minutes}min") + ")"
        else:
            timedelta = now - date
            return date_boston_time.strftime(fmt) + " (" + strfdelta(timedelta, "{days}d, {hours}hrs, {minutes}min ago") + ")"

    class Meta:
        model = MovieNightEvent
        fields = (
            'id', 'motto', 'date', "movies", "isdraft", "movies", "date_delta", "vote_enabled", "status", "reg_users", 'winning_movie', "rawdate"
        )



class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    join_date = serializers.SerializerMethodField()
    is_invitor = serializers.SerializerMethodField()
    invitation_key = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()

    def get_firstlastname(self, Profile):
        return Profile.user.first_name + " " + Profile.user.last_name

    def get_invitation_key(self, Profile):
        return Profile.invitation_key

    def get_is_invitor(self, Profile):
        return Profile.is_invitor 

    def get_join_date(self, Profile):
        return Profile.user.date_joined 

    class Meta:
        model = UserAttendence
        fields = (
            'id', 'firstlastname', 'is_invitor', "invitation_key", 'join_date'
        )


class LocationPermissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    location = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    invitation_key = serializers.SerializerMethodField()
    join_date = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    has_access = serializers.SerializerMethodField()


    def get_has_access(self, LocationPermission):
        return (LocationPermission.revoked_access == False)

    def get_location(self, LocationPermission):
        return LocationPermission.location.name

    def get_username(self, LocationPermission):
        return LocationPermission.user.username

    def get_firstlastname(self, LocationPermission):
        return LocationPermission.user.first_name + " " + LocationPermission.user.last_name

    def get_role(self, LocationPermission):
        return LocationPermission.get_role_display() 

    def get_invitation_key(self, LocationPermission):
        return LocationPermission.get_invite_code() 

    def get_join_date(self, LocationPermission):
        return LocationPermission.user.date_joined 

    def get_user_id(self, LocationPermission):
        return LocationPermission.user.id 

    class Meta:
        model = LocationPermission
        fields = (
            'id', 'location', 'username', "firstlastname", 'role', 'invitation_key', 'join_date', 'user_id', 'has_access'
        )



class RestrictedLocationPermissionSerializer(serializers.ModelSerializer):
    # This is called by Ambassadors and does not return invitation keys
    id = serializers.IntegerField(read_only=True)
    location = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    join_date = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    has_access = serializers.SerializerMethodField()
    revoke_access_hash = serializers.SerializerMethodField()


    def get_revoke_access_hash(self, LocationPermission):

        if LocationPermission.can_invite():
            return "<button type='button' class='btn btn-secondary btn-sm' data-toggle='modal' data-target='#no_change_modal'>N/A</button>"
        elif not LocationPermission.revoked_access:
            return "<a class='btn btn-danger btn-sm' href='/toggle_access_invite/" + LocationPermission.rev_access_hash + "' role='button'>Revoke Access</a>"
        else:
            return "<a class='btn btn-success btn-sm' href='/toggle_access_invite/" + LocationPermission.rev_access_hash + "' role='button'>Grant Access</a>"

    def get_has_access(self, LocationPermission):
        return (LocationPermission.revoked_access == False)

    def get_location(self, LocationPermission):
        return LocationPermission.location.name

    def get_username(self, LocationPermission):
        return LocationPermission.user.username

    def get_firstlastname(self, LocationPermission):
        return LocationPermission.user.first_name + " " + LocationPermission.user.last_name

    def get_role(self, LocationPermission):
        return LocationPermission.get_role_display() 

    def get_join_date(self, LocationPermission):
        return LocationPermission.user.date_joined 

    def get_user_id(self, LocationPermission):
        return LocationPermission.user.id 

    class Meta:
        model = LocationPermission
        fields = (
            'revoke_access_hash', 'id', 'location', 'username', "firstlastname", 'role', 'join_date', 'user_id', 'has_access'
        )

class UserAttendenceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.SerializerMethodField()
    toppings = serializers.SerializerMethodField()
    reg_date = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()

    def get_firstlastname(self, UserAttendence):
        return UserAttendence.user.first_name + " " + UserAttendence.user.last_name

    def get_reg_date(self, UserAttendence):
        date = UserAttendence.registered_at
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz).strftime(fmt)
        return date_boston_time

    def get_user(self, UserAttendence):
        return UserAttendence.user.username

    def get_toppings(self, UserAttendence):
        return ' '.join([badgify(o.topping.topping, 'primary') for o in UserAttendence.get_toppings()])

    class Meta:
        model = UserAttendence
        fields = (
            'id', 'user', 'toppings', 'reg_date', "registration_complete", "movienight", 'firstlastname'
        )
