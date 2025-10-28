from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg


class Game(models.Model):
    game_id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=100)
    platform = models.CharField(max_length=100)
    genre = models.CharField(max_length=100)
    developer = models.CharField(max_length=100, blank=True)
    publisher = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(null=True, blank=True)
    short_description = models.TextField(blank=True)
    thumbnail = models.URLField(blank=True)
    game_url = models.URLField(blank=True)
    profile_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.title}: {self.game_id}"

    def average_rating(self):
        result = self.rating_set.aggregate(average=Avg('vote'))
        return round(result['average'], 2) if result['average'] is not None else None

    def total_votes(self):
        return self.rating_set.count()


class Comment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.game.title}"

    def num_likes(self):
        return self.votes.filter(type='like').count()

    def num_dislikes(self):
        return self.votes.filter(type='dislike').count()


class CommentVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='votes')
    type = models.CharField(max_length=10, choices=[('like', 'Like'), ('dislike', 'Dislike')])

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} - {self.type} on comment {self.comment.id}"


class Rating(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.game.title}: {self.vote}"


class Follow(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f"{self.user.username} follows {self.game.title}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    alias = models.CharField(max_length=100, blank=True)
    font_type = models.CharField(
        max_length=30,
        choices=[
            ('fuente-sans-serif', 'Sans Serif (Rubik)'),
            ('fuente-serif', 'Serif (Roboto Slab)'),
            ('fuente-monospace', 'Monospaced (Fira Code)'),
            ('fuente-decorativa', 'Decorative (Pacifico)'),
        ],
        default='fuente-sans-serif'
    )

    text_size = models.CharField(
        max_length=20,
        choices=[
            ('tamano-small', 'Small'),
            ('tamano-medium', 'Medium'),
            ('tamano-large', 'Large'),
            ('tamano-xl', 'Extra Large'),
        ],
        default='tamano-medium'
    )

    def __str__(self):
        return f"Settings for {self.user.username}"