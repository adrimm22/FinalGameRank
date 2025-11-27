from .models import Game, Comment, Rating, UserSettings

def user_alias(request):
    """
    Returns the authenticated user's alias, or 'Anonymous' if not logged in.
    """
    if request.user.is_authenticated:
        try:
            # Access the OneToOne relationship.
            # Since the model is UserSettings, the default reverse name is 'usersettings'.
            return {'user_alias': request.user.usersettings.alias or request.user.username}
        except UserSettings.DoesNotExist:
            return {'user_alias': request.user.username}
    return {'user_alias': "Anonymous"}


def footer_metrics(request):
    """
    Returns total Games/Comments + User's votes/comments.
    Renamed from 'metricas_footer'.
    """
    context = {
        'total_games': Game.objects.count(),
        'total_comments': Comment.objects.count(),
    }

    if request.user.is_authenticated:
        context.update({
            'user_votes': Rating.objects.filter(user=request.user).count(),
            'user_comments': Comment.objects.filter(user=request.user).count(),
        })
    else:
        # Avoid errors if we try to print these variables for anonymous users
        context.update({
            'user_votes': 0,
            'user_comments': 0,
        })

    return context


def user_settings(request):
    """
    Loads the user's custom visual style for all templates.
    Renamed from 'configuracion_usuario'.
    """
    if request.user.is_authenticated:
        try:
            config = UserSettings.objects.get(user=request.user)
        except UserSettings.DoesNotExist:
            config = None
        return {'user_config': config}
    return {'user_config': None}