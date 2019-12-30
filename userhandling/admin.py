from django.contrib import admin
from singlemodeladmin import SingleModelAdmin

from .models import (Location, LocationPermission, Movie, MovieNightEvent,
                     MovienightTopping, PasswordReset, Profile, Topping,
                     UserAttendence, VotePreference, VotingParameters)

# Register your models here.
# admin.site.register(MovieNightEvent)
admin.site.register(Movie)
admin.site.register(Profile)
# admin.site.register(PasswordReset)


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )


@admin.register(MovieNightEvent)
class MovieNightEventAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(VotePreference)
class VotePreferenceAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(Topping)
class TopingAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(MovienightTopping)
class MovienightToppingAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(UserAttendence)
class UserAttendenceAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


@admin.register(LocationPermission)
class LocationPermissionAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'invitation_code',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


admin.site.register(VotingParameters, SingleModelAdmin)
