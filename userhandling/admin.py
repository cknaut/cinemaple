from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from django.contrib.auth.models import User


from .models import MovieNightEvent, Movie, Profile, PasswordReset, VotePreference, \
     VotingParameters, Topping, MovienightTopping

# Register your models here.
#admin.site.register(MovieNightEvent)
admin.site.register(Movie)
admin.site.register(Profile)
#admin.site.register(PasswordReset)



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

admin.site.register(VotingParameters, SingleModelAdmin)