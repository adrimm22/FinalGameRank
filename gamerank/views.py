from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Comment, CommentVote, Follow, Game, Rating


def home(request):
    games = Game.objects.all().order_by('title')
    return render(request, 'gamerank/home.html', {
        'games': games,
    })


def game_detail(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    comments = Comment.objects.filter(game=game)
    return render(request, 'gamerank/game_detail.html', {
        'game': game,
        'comments': comments,
        'average_rating': game.average_rating(),
        'total_votes': game.total_votes(),
    })


def user_page(request):
    return render(request, 'gamerank/user.html', {})


def rated_games(request):
    return render(request, 'gamerank/rated.html', {})


def followed_games(request):
    return render(request, 'gamerank/followed.html', {})


def settings_page(request):
    return render(request, 'gamerank/settings.html', {})


def vote_comment(request, comment_id):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Unauthorized'}, status=401)

    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get('type') or request.GET.get('type')
    if vote_type not in {'like', 'dislike'}:
        return JsonResponse({'detail': 'Invalid vote type'}, status=400)

    CommentVote.objects.update_or_create(
        user=request.user,
        comment=comment,
        defaults={'type': vote_type},
    )
    return JsonResponse({
        'status': 'ok',
        'likes': comment.num_likes(),
        'dislikes': comment.num_dislikes(),
    })


def vote_comment_htmx(request, comment_id):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    comment = get_object_or_404(Comment, id=comment_id)
    vote_type = request.POST.get('type') or request.GET.get('type')
    if vote_type not in {'like', 'dislike'}:
        return HttpResponse('Invalid vote type', status=400)

    CommentVote.objects.update_or_create(
        user=request.user,
        comment=comment,
        defaults={'type': vote_type},
    )
    html = f'<span data-comment="{comment.id}">Likes: {comment.num_likes()} · Dislikes: {comment.num_dislikes()}</span>'
    return HttpResponse(html)


def game_json(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    data = {
        'game_id': game.game_id,
        'title': game.title,
        'platform': game.platform,
        'genre': game.genre,
        'developer': game.developer,
        'publisher': game.publisher,
        'release_date': game.release_date.isoformat() if game.release_date else None,
        'short_description': game.short_description,
        'thumbnail': game.thumbnail,
        'game_url': game.game_url,
        'profile_url': game.profile_url,
        'average_rating': game.average_rating(),
        'total_votes': game.total_votes(),
    }
    return JsonResponse(data)


def game_detail_htmx(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    comments = Comment.objects.filter(game=game)
    # Minimal: return a small fragment
    return render(request, 'gamerank/game_detail.html', {
        'game': game,
        'comments': comments,
        'average_rating': game.average_rating(),
        'total_votes': game.total_votes(),
    })


def comments_htmx(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    comments = Comment.objects.filter(game=game)
    return render(request, 'gamerank/_comments.html', {
        'game': game,
        'comments': comments,
    })


def post_comment_htmx(request, game_id):
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    game = get_object_or_404(Game, pk=game_id)
    text = (request.POST.get('text') or '').strip()
    if not text:
        return HttpResponse('Text is required', status=400)

    Comment.objects.create(game=game, user=request.user, text=text)
    comments = Comment.objects.filter(game=game)
    return render(request, 'gamerank/_comments.html', {
        'game': game,
        'comments': comments,
    })


def unified_games_api(request):
    games = Game.objects.all().order_by('title')
    data = [
        {
            'game_id': g.game_id,
            'title': g.title,
            'platform': g.platform,
            'genre': g.genre,
            'average_rating': g.average_rating(),
            'total_votes': g.total_votes(),
        }
        for g in games
    ]
    return JsonResponse({'results': data})
