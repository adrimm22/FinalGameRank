from django.shortcuts import redirect
from .models import Follow, Comment

def process_following(request, games, redirect_to):
    """
    Processes the actions of following or unfollowing games for a user.
    Returns a redirect if any button was clicked, or None if nothing was done.
    """
    if request.method == 'POST':
        for game in games:
            if f"Follow_{game.game_id}" in request.POST:
                Follow.objects.get_or_create(user=request.user, game=game)
                return redirect(redirect_to)
            elif f"Unfollow_{game.game_id}" in request.POST:
                Follow.objects.filter(user=request.user, game=game).delete()
                return redirect(redirect_to)
    return None


def get_followed_games_ids(user):
    """
    Returns a set of game IDs that the user is currently following.
    """
    return set(
        Follow.objects.filter(user=user).values_list('game_id', flat=True)
    )


def comments_with_votes(game):
    """
    Returns a list of comments for the game with num_likes and num_dislikes preprocessed.
    """
    comments = Comment.objects.filter(game=game)
    for c in comments:
        c.num_likes = c.num_likes()
        c.num_dislikes = c.num_dislikes()
    return comments
