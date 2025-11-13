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