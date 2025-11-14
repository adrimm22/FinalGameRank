import os
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
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


@login_required
def settings_page(request):
    """
    Allows the user to change their alias, font type and text size.
    """
    config, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        alias = request.POST.get("alias", "").strip()
        font_type = request.POST.get("font_type", "")
        text_size = request.POST.get("text_size", "")

        config.alias = alias
        config.font_type = font_type
        config.text_size = text_size
        config.save()

        messages.success(request, "Your settings have been updated successfully.")
        return redirect("settings_page")

    return render(request, "gamerank/settings.html")


@login_required
def vote_comment(request, comment_id):
    """
    Allows a user to like or dislike a comment.
    Updates the vote if there was a previous one.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get("vote_type")

    if vote_type in ['like', 'dislike']:
        CommentVote.objects.update_or_create(
            user=request.user,
            comment=comment,
            defaults={'type': vote_type}
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_GET
def game_json(request, game_id):
    """
    Returns the data of a game in JSON format, including number of comments.
    """
    game = get_object_or_404(Game, game_id=game_id)
    comments_count = Comment.objects.filter(game=game).count()
    average_rating = game.average_rating()

    data = {
        "game_id": game.game_id,
        "title": game.title,
        "genre": game.genre,
        "platform": game.platform,
        "developer": game.developer,
        "publisher": game.publisher,
        "release_date": game.release_date.strftime('%Y-%m-%d') if game.release_date else None,
        "short_description": game.short_description,
        "game_url": game.game_url,
        "thumbnail": game.thumbnail,
        "average_rating": round(average_rating, 2) if average_rating is not None else None,
        "comments_count": comments_count
    }

    return JsonResponse(data)


@login_required
def game_detail_htmx(request, game_id):
    """
    Main page with HTMX. Loads dynamic sections (comments + form).
    """
    game = get_object_or_404(Game, game_id=game_id)
    followed = game.follow_set.filter(user=request.user).exists()
    user_rating = Rating.objects.filter(game=game, user=request.user).first()

    # Load comments for the game with like/dislike counters already calculated
    comments = comments_with_votes(game)

    return render(request, "gamerank/game_detail_htmx.html", {
        "game": game,
        "followed": followed,
        "user_rating": user_rating,
        "rating_range": range(1, 6),
        "comments": comments,
    })


@require_GET
@login_required
def comments_htmx(request, game_id):
    """
    Returns only the comments of the game in HTML for HTMX.
    """
    game = get_object_or_404(Game, game_id=game_id)
    comments = comments_with_votes(game)
    return render(request, "gamerank/includes/comments_htmx.html", {
        "comments": comments
    })


@require_POST
@login_required
def post_comment_htmx(request, game_id):
    """
    Publishes a new comment and returns the updated HTML list.
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

    comments = comments_with_votes(game)
    return render(request, "gamerank/includes/comments_htmx.html", {
        "comments": comments,
        "game": game
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
