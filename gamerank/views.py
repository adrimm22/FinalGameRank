from django.shortcuts import render

# Create your views here.
@login_required
def user_page(request):
    """
    View for the authenticated user page.
    Shows:
      - Number of ratings and comments by the user.
      - User's average rating.
      - Rated games with their scores.
      - Followed games.
      - Comments made by the user.
    """
    user = request.user

    # User ratings
    user_ratings = Rating.objects.filter(user=user)
    num_ratings = user_ratings.count()
    user_average = user_ratings.aggregate(average=Avg('vote'))['average']
    user_average = round(user_average, 2) if user_average is not None else None

    # User comments
    user_comments = Comment.objects.filter(user=user).select_related('game')
    num_user_comments = user_comments.count()

    # Rated games with score
    rated_games = [(r.game, r.vote) for r in user_ratings.select_related('game')]

    # Games followed by the user
    followed_games = Game.objects.filter(follow__user=user).distinct()

    return render(request, 'gamerank/user_page.html', {
        'user': user,
        'num_ratings': num_ratings,
        'user_average': user_average,
        'num_user_comments': num_user_comments,
        'rated_games': rated_games,
        'followed_games': followed_games,
        'user_comments': user_comments,
    })


@login_required
def rated_games(request):
    """
    Shows the games rated by the user, ordered by the rating.
    Allows follow/unfollow directly from this view.
    """
    ratings = Rating.objects.filter(user=request.user).select_related('game')
    games = []

    for r in ratings:
        game = r.game
        game.my_vote = r.vote
        game.score = game.average_rating()
        game.total_votes = game.total_votes()
        games.append(game)

    games.sort(key=lambda g: g.my_vote, reverse=True)

    # Process follow/unfollow action if there is POST
    response = process_following(request, games, "home")
    if response:
        return response

    # Retrieve followed games to mark active buttons
    followed_ids = get_followed_games_ids(request.user)

    return render(request, 'gamerank/rated_games.html', {
        'games': games,
        'followed_ids': followed_ids,
    })


@login_required
def followed_games(request):
    """
    Shows the games that the user follows, ordered by average rating.
    Allows unfollow directly from this view.
    """
    follows = Follow.objects.filter(user=request.user).select_related('game')
    games = [f.game for f in follows]
    games.sort(key=lambda g: g.average_rating() or 0, reverse=True)

    # Process follow/unfollow action if there is POST
    response = process_following(request, games, "followed_games")
    if response:
        return response  # Nothing else should go here

    # Retrieve followed games to mark active buttons
    followed_ids = get_followed_games_ids(request.user)

    return render(request, 'gamerank/followed_games.html', {
        'games': games,
        'followed_ids': followed_ids,
    })
