from django.utils import timezone
import pytz
from rest_framework import serializers

from .models import LocationPermission, MovieNightEvent, UserAttendence
from .utils import badgify


def strfdelta(tdelta, fmt):
    days = {"days": abs(tdelta.days)}
    days["hours"], rem = divmod(tdelta.seconds, 3600)
    days["minutes"], days["seconds"] = divmod(rem, 60)
    return fmt.format(**days)


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

    # We locally disable the no-self-use pylint errors which are thrown
    # due to the specific ways the Serializers are defined.
    def get_rawdate(self, movienight):  # pylint: disable=no-self-use
        return movienight.date

    def get_reg_users(self, movienight):  # pylint: disable=no-self-use
        return movienight.get_num_registered()

    def get_movies(self, movienight):  # pylint: disable=no-self-use
        return ', '.join([str(movie.title)
                          for movie in movienight.MovieList.all()])

    def get_status(self, movienight):  # pylint: disable=no-self-use
        return movienight.get_status()

    def get_vote_enabled(self, movienight):  # pylint: disable=no-self-use
        return movienight.voting_enabled()

    def get_winning_movie(self, movienight):  # pylint: disable=no-self-use
        winning_movie, _, _ = movienight.get_winning_movie()
        if winning_movie is None:
            return '-No votes yet-'
        return '{} ({})'.format(winning_movie.title, winning_movie.year)

    def get_date_delta(self, movienight):  # pylint: disable=no-self-use
        date = movienight.date
        now = timezone.now()
        timedelta = date - now
        timedelta_secs = int(timedelta.total_seconds())

        # localize to boston TZ
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz)

        if timedelta_secs > 0:
            return date_boston_time.strftime(fmt) + " (" + \
                strfdelta(timedelta, "In {days}d, {hours}hrs, \
                {minutes}min") + ")"

        timedelta = now - date
        return date_boston_time.strftime(fmt) + " (" + \
            strfdelta(timedelta, "{days}d, {hours}hrs, \
            {minutes}min ago") + ")"

    class Meta:
        model = MovieNightEvent
        fields = (
            'id',
            'motto',
            'date',
            'movies',
            'isdraft',
            'movies',
            'date_delta',
            'vote_enabled',
            'status',
            'reg_users',
            'winning_movie',
            'rawdate'
        )


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    join_date = serializers.SerializerMethodField()
    is_invitor = serializers.SerializerMethodField()
    invitation_key = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()

    def get_firstlastname(self, profile):  # pylint: disable=no-self-use
        return profile.user.first_name + " " + profile.user.last_name

    def get_invitation_key(self, profile):  # pylint: disable=no-self-use
        return profile.invitation_key

    def get_is_invitor(self, profile):  # pylint: disable=no-self-use
        return profile.is_invitor

    def get_join_date(self, profile):  # pylint: disable=no-self-use
        return profile.user.date_joined

    class Meta:
        model = UserAttendence
        fields = (
            'id',
            'firstlastname',
            'is_invitor',
            'invitation_key',
            'join_date'
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

    def get_has_access(
        self, locationpermission
    ):  # pylint: disable=no-self-use
        return locationpermission.revoked_access is False

    def get_location(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.location.name

    def get_username(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.username

    def get_firstlastname(
        self, locationpermission
    ):  # pylint: disable=no-self-use
        return locationpermission.user.first_name + " " \
            + locationpermission.user.last_name

    def get_role(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.get_role_display()

    def get_invitation_key(
        self, locationpermission
    ):  # pylint: disable=no-self-use
        return locationpermission.get_invite_code()

    def get_join_date(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.date_joined

    def get_user_id(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.id

    class Meta:
        model = LocationPermission
        fields = (
            'id',
            'location',
            'username',
            'firstlastname',
            'role',
            'invitation_key',
            'join_date',
            'user_id',
            'has_access'
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

    def get_revoke_access_hash(
        self, locationpermission
    ):  # pylint: disable=no-self-use

        if locationpermission.can_invite():
            return "<button type='button' class='btn btn-secondary btn-sm' \
                data-toggle='modal' data-target='#no_change_modal'>\
                N/A</button>"
        if locationpermission.revoked_access:
            return "<a class='btn btn-success btn-sm' \
                href='/toggle_access_invite/" + \
                locationpermission.rev_access_hash + \
                "' role='button'>Grant Access</a>"
        return "<a class='btn btn-danger btn-sm' \
            href='/toggle_access_invite/" + \
            locationpermission.rev_access_hash + \
            "' role='button'>Revoke Access</a>"

    def get_has_access(
        self, locationpermission
    ):  # pylint: disable=no-self-use
        return locationpermission.revoked_access is False

    def get_location(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.location.name

    def get_username(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.username

    def get_firstlastname(
        self, locationpermission
    ):  # pylint: disable=no-self-use
        return locationpermission.user.first_name + " " \
            + locationpermission.user.last_name

    def get_role(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.get_role_display()

    def get_join_date(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.date_joined

    def get_user_id(self, locationpermission):  # pylint: disable=no-self-use
        return locationpermission.user.id

    class Meta:
        model = LocationPermission
        fields = (
            'revoke_access_hash',
            'id',
            'location',
            'username',
            'firstlastname',
            'role',
            'join_date',
            'user_id',
            'has_access'
        )


class UserAttendenceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.SerializerMethodField()
    toppings = serializers.SerializerMethodField()
    reg_date = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()

    def get_firstlastname(self, userattendence):  # pylint: disable=no-self-use
        return userattendence.user.first_name + " " \
            + userattendence.user.last_name

    def get_reg_date(self, userattendence):  # pylint: disable=no-self-use
        date = userattendence.registered_at
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz).strftime(fmt)
        return date_boston_time

    def get_user(self, userattendence):  # pylint: disable=no-self-use
        return userattendence.user.username

    def get_toppings(self, userattendence):  # pylint: disable=no-self-use
        return ' '.join([badgify(o.topping.topping, 'primary')
                         for o in userattendence.get_toppings()])

    class Meta:
        model = UserAttendence
        fields = (
            'id',
            'user',
            'toppings',
            'reg_date',
            'registration_complete',
            'movienight',
            'firstlastname'
        )
