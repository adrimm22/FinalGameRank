from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [

    # MAIN PAGE AND GAME
    path('', views.home, name='home'),
    path('game/<str:game_id>/', views.game_detail, name='game_detail'),

    # USER
    path('user/', views.user_page, name='user_page'),
    path('rated/', views.rated_games, name='rated_games'),
    path('followed/', views.followed_games, name='followed_games'),
    path('settings/', views.settings_page, name='settings_page'),
    path('help/', TemplateView.as_view(template_name='gamerank/help.html'), name='help'),

    # COMMENTS
    path("comment/<int:comment_id>/vote/", views.vote_comment, name="vote_comment"),
    path("comment/<int:comment_id>/vote_htmx/", views.vote_comment_htmx, name="vote_comment_htmx"),

    # JSON
    path("game/<str:game_id>.json", views.game_json, name="game_json"),

    # HTMX
    path("game/<str:game_id>/htmx/", views.game_detail_htmx, name="game_detail_htmx"),
    path("game/<str:game_id>/htmx/comments/", views.comments_htmx, name="comments_htmx"),
    path("game/<str:game_id>/htmx/comment/", views.post_comment_htmx, name="post_comment_htmx"),
    path("game/<str:game_id>/htmx/follow/", views.follow_game_htmx, name="follow_game_htmx"),

    # EXTRAS
    path("games/api/", views.unified_games_api, name="games_api"),
]