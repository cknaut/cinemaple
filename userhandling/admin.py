from django.contrib import admin

from .models import MovieNightEvent, Movie, Profile, PasswordReset

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