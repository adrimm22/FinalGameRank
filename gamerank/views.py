import os
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.models import User
from .utils import process_following, get_followed_games_ids, comments_with_votes
from finalgamerank import settings
from .models import Game, Comment, Rating, Follow, UserSettings, CommentVote

import requests


def home(request):
    """
    Main page that shows games ordered by average rating (descending).
    If there is a POST from follow/unfollow buttons, it is processed and redirected.
    If the user is authenticated, it marks which games are currently followed.
    """
    games = list(Game.objects.all())
    games.sort(key=lambda g: g.average_rating() or 0, reverse=True)

    followed_ids = set()

    if request.user.is_authenticated:
        # Process follow/unfollow action if there is POST
        response = process_following(request, games, "home")
        if response:
            return response

        # Retrieve followed games to mark active buttons
        followed_ids = get_followed_games_ids(request.user)

        for game in games:
            game.followed = game.game_id in followed_ids

    return render(request, 'gamerank/home.html', {
        'games': games,
        'followed_ids': followed_ids,
    })


@login_required()
def game_detail(request, game_id):
    """
    Shows the detail page for a game with its detailed information, comments and form
    to rate, comment and follow/unfollow. Only available for authenticated users.
    """
    # Find the game by its ID or raise 404 if it does not exist
    game = get_object_or_404(Game, game_id=game_id)

    # Load comments for the game with like/dislike counters already calculated
    comments = comments_with_votes(game)

    # Initialize variables in case the user is not authenticated
    user_rating = None
    user_follow = None

    if request.user.is_authenticated:
        # Check if the user has already rated this game
        user_rating = Rating.objects.filter(game=game, user=request.user).first()

        # Check if the user is following this game
        user_follow = Follow.objects.filter(game=game, user=request.user).first()

        if request.method == "POST":
            # 1. Add a comment
            text = request.POST.get("comment_text", "").strip()
            if text:
                Comment.objects.create(
                    game=game,
                    user=request.user,
                    text=text,
                    date=timezone.now()
                )
                return redirect("game_detail", game_id=game_id)

            # 2. Rate (only if the user has not rated before)
            vote = request.POST.get("vote")
            if vote and not user_rating:
                try:
                    value = int(vote)
                    if 0 <= value <= 5:
                        Rating.objects.create(game=game, user=request.user, vote=value)
                        return redirect("game_detail", game_id=game_id)
                except ValueError:
                    pass  # Ignore invalid votes

            # 3. Follow the game
            if "follow" in request.POST and not user_follow:
                Follow.objects.create(game=game, user=request.user)
                return redirect("game_detail", game_id=game_id)

            # 4. Unfollow the game
            if "unfollow" in request.POST and user_follow:
                user_follow.delete()
                return redirect("game_detail", game_id=game_id)

    # Render the template with all the required data
    return render(request, "gamerank/game_detail.html", {
        "game": game,
        "comments": comments,
        "user_rating": user_rating,
        "user_follow": user_follow,
        "rating_range": range(1, 6),
    })

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

@login_required
def vote_comment_htmx(request, comment_id):
    """
    Allows voting a comment dynamically with HTMX.
    Registers 'like' or 'dislike' from the current user, updates counters
    and returns the updated HTML of the comment to replace it on the page.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get("vote_type")

    if vote_type in ['like', 'dislike']:
        CommentVote.objects.update_or_create(
            user=request.user,
            comment=comment,
            defaults={'type': vote_type}
        )

    # Manual calculation of counters
    comment.num_likes = comment.num_likes()
    comment.num_dislikes = comment.num_dislikes()

    # Detect the current user's vote
    comment.user_vote = CommentVote.objects.filter(user=request.user, comment=comment).first()

    html = render_to_string(
        "gamerank/includes/comment_item.html",
        {"comment": comment, "user": request.user}
    )
    return HttpResponse(html)


def unified_games_api(request):
    platform_filter = request.GET.get("platform", "").lower().strip()
    final_games = []

    if platform_filter:
        games_dict = {}

        def get_games(api_url, backup_filename):
            if settings.DEBUG:
                try:
                    response = requests.get(api_url, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    print(f"❌ Error connecting to {api_url}:", e)
                    return []
            else:
                try:
                    path = os.path.join(settings.BASE_DIR, "data", backup_filename)
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"❌ Error reading {backup_filename}:", e)
                    return []

        games_freetogame = get_games("https://www.freetogame.com/api/games", "games_freetogame_backup.json")
        games_mmobomb = get_games("https://www.mmobomb.com/api1/games", "games_mmobomb_backup.json")

        for game in games_freetogame + games_mmobomb:
            title = game.get("title", "").strip().lower()
            if title and title not in games_dict:
                games_dict[title] = game

        final_games = list(games_dict.values())
        final_games = [
            g for g in final_games
            if platform_filter in g.get("platform", "").lower()
        ]

    return render(request, "gamerank/games_api.html", {
        "games": final_games,
        "selected_platform": platform_filter
    })


def statistics(request):
    """
    Shows site-wide statistics including:
    - Total games, users, ratings, comments
    - Average rating across all games
    - Most active users
    - Top rated games
    - Games by platform and genre
    """
    total_games = Game.objects.count()
    total_users = User.objects.count()
    total_ratings = Rating.objects.count()
    total_comments = Comment.objects.count()
    total_follows = Follow.objects.count()
    
    all_ratings = Rating.objects.all()
    overall_average = all_ratings.aggregate(average=Avg('vote'))['average']
    overall_average = round(overall_average, 2) if overall_average is not None else None
    
    most_active_users = User.objects.annotate(
        rating_count=Count('rating'),
        comment_count=Count('comment')
    ).annotate(
        total_activity=Count('rating') + Count('comment')
    ).order_by('-total_activity')[:10]
    
    top_rated_games = Game.objects.annotate(
        avg_rating=Avg('rating__vote'),
        rating_count=Count('rating')
    ).filter(
        rating_count__gte=1
    ).order_by('-avg_rating', '-rating_count')[:10]
    
    most_followed_games = Game.objects.annotate(
        follow_count=Count('follow')
    ).filter(follow_count__gt=0).order_by('-follow_count')[:10]
    
    games_by_platform = Game.objects.values('platform').annotate(
        count=Count('game_id')
    ).order_by('-count')[:10]
    
    games_by_genre = Game.objects.values('genre').annotate(
        count=Count('game_id')
    ).order_by('-count')[:10]
    
    return render(request, 'gamerank/statistics.html', {
        'total_games': total_games,
        'total_users': total_users,
        'total_ratings': total_ratings,
        'total_comments': total_comments,
        'total_follows': total_follows,
        'overall_average': overall_average,
        'most_active_users': most_active_users,
        'top_rated_games': top_rated_games,
        'most_followed_games': most_followed_games,
        'games_by_platform': games_by_platform,
        'games_by_genre': games_by_genre,
    })


def activity(request):
    """
    Shows recent activity feed including:
    - Recent comments
    - Recent follows
    - Filter by user/game
    """
    user_filter = request.GET.get('user', '').strip()
    game_filter = request.GET.get('game', '').strip()
    
    recent_comments = Comment.objects.select_related('user', 'game').order_by('-date')[:50]
    recent_follows = Follow.objects.select_related('user', 'game').order_by('-date')[:50]
    
    if user_filter:
        recent_comments = recent_comments.filter(user__username__icontains=user_filter)
        recent_follows = recent_follows.filter(user__username__icontains=user_filter)
    
    if game_filter:
        recent_comments = recent_comments.filter(game__title__icontains=game_filter)
        recent_follows = recent_follows.filter(game__title__icontains=game_filter)
    
    activities = []
    
    for comment in recent_comments[:30]:
        activities.append({
            'type': 'comment',
            'user': comment.user,
            'game': comment.game,
            'text': comment.text[:100],
            'timestamp': comment.date
        })
    
    for follow in recent_follows[:30]:
        activities.append({
            'type': 'follow',
            'user': follow.user,
            'game': follow.game,
            'timestamp': follow.date
        })
    
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    activities = activities[:30]
    
    return render(request, 'gamerank/activity.html', {
        'activities': activities,
        'user_filter': user_filter,
        'game_filter': game_filter,
    })


@login_required
def settings_page(request):
    """
    User settings page for managing preferences.
    """
    from .models import UserSettings
    
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        alias = request.POST.get('alias', '').strip()
        font_type = request.POST.get('font_type', user_settings.font_type)
        text_size = request.POST.get('text_size', user_settings.text_size)
        
        user_settings.alias = alias
        user_settings.font_type = font_type
        user_settings.text_size = text_size
        user_settings.save()
        
        messages.success(request, 'Settings saved successfully!')
        return redirect('settings_page')
    
    return render(request, 'gamerank/settings.html', {
        'user_settings': user_settings,
    })


def vote_comment(request, comment_id):
    """
    Legacy view for voting comments (redirects to HTMX version).
    """
    return redirect('vote_comment_htmx', comment_id=comment_id)


def game_json(request, game_id):
    """
    Returns game data as JSON.
    """
    game = get_object_or_404(Game, game_id=game_id)
    
    data = {
        'game_id': game.game_id,
        'title': game.title,
        'platform': game.platform,
        'genre': game.genre,
        'developer': game.developer,
        'publisher': game.publisher,
        'release_date': str(game.release_date) if game.release_date else None,
        'short_description': game.short_description,
        'thumbnail': game.thumbnail,
        'game_url': game.game_url,
        'average_rating': game.average_rating(),
        'total_votes': game.total_votes(),
    }
    
    return JsonResponse(data)


@login_required
def game_detail_htmx(request, game_id):
    """
    HTMX partial for game detail section.
    """
    game = get_object_or_404(Game, game_id=game_id)
    user_rating = Rating.objects.filter(game=game, user=request.user).first()
    user_follow = Follow.objects.filter(game=game, user=request.user).first()
    
    html = render_to_string(
        "gamerank/includes/game_detail_partial.html",
        {
            "game": game,
            "user_rating": user_rating,
            "user_follow": user_follow,
            "rating_range": range(1, 6),
        }
    )
    return HttpResponse(html)


@login_required
def comments_htmx(request, game_id):
    """
    HTMX partial for comments list.
    """
    game = get_object_or_404(Game, game_id=game_id)
    comments = comments_with_votes(game)
    
    html = render_to_string(
        "gamerank/includes/comments_list.html",
        {"comments": comments, "game": game, "user": request.user}
    )
    return HttpResponse(html)


@login_required
def post_comment_htmx(request, game_id):
    """
    HTMX endpoint for posting comments.
    """
    game = get_object_or_404(Game, game_id=game_id)
    text = request.POST.get("comment_text", "").strip()
    
    if text:
        Comment.objects.create(
            game=game,
            user=request.user,
            text=text,
            date=timezone.now()
        )
    
    return comments_htmx(request, game_id)
