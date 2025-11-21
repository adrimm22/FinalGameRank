from django.contrib.auth.models import User
from .models import UserSettings, Game, Rating, Comment, Follow


def user_alias(request):
    """
    Adds user alias to context if user is authenticated.
    """
    context = {}
    if request.user.is_authenticated:
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            context['user_alias'] = user_settings.alias if user_settings.alias else request.user.username
        except UserSettings.DoesNotExist:
            context['user_alias'] = request.user.username
    else:
        context['user_alias'] = None
    return context


def metricas_footer(request):
    """
    Adds site metrics to context for footer display.
    """
    total_games = Game.objects.count()
    total_users = User.objects.count()
    total_ratings = Rating.objects.count()
    total_comments = Comment.objects.count()
    
    return {
        'total_games': total_games,
        'total_users': total_users,
        'total_ratings': total_ratings,
        'total_comments': total_comments,
    }


def configuracion_usuario(request):
    """
    Adds user configuration (font, text size) to context.
    """
    context = {}
    if request.user.is_authenticated:
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            context['user_font_type'] = user_settings.font_type
            context['user_text_size'] = user_settings.text_size
        except UserSettings.DoesNotExist:
            context['user_font_type'] = 'fuente-sans-serif'
            context['user_text_size'] = 'tamano-medium'
    else:
        context['user_font_type'] = 'fuente-sans-serif'
        context['user_text_size'] = 'tamano-medium'
    return context

