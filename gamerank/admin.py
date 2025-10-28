from django.contrib import admin

from gamerank.models import Game, Comment, Rating, Follow, UserSettings, CommentVote

# Register your models here.

admin.site.register(Game)
admin.site.register(Comment)
admin.site.register(Rating)
admin.site.register(Follow)
admin.site.register(UserSettings)
admin.site.register(CommentVote)
