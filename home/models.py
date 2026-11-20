from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date

# Create your models here.
class Contact(models.Model):
    name=models.CharField(max_length=122)
    email=models.CharField(max_length=122)
    phone=models.CharField(max_length=12)
    desc=models.TextField()
    date=models.DateField()

    def __str__(self):
        return self.name

class Book(models.Model):
    STATUS_CHOICES=(
        ('available', 'Available'),
        ('issued', 'Issued'),
    )


    
    title=models.CharField(max_length=122)
    author=models.CharField(max_length=122)
    isbn = models.CharField(max_length=13, unique=True)
    category=models.CharField(max_length=122)
    location=models.CharField(max_length=122)
    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default='available')
    cover_url=models.URLField(blank=True, null=True)
    recommendation_tags = models.JSONField(
    default=list,
    blank=True
)
    def __str__(self):
        return f"{self.title} by {self.author}"
    
def default_return_date():
    return date.today() + timedelta(days=14)
class BookIssue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(default=default_return_date)
    returned = models.BooleanField(default=False)
    fine = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.IntegerField()
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class UserPreference(models.Model):

    PACE_CHOICES = [
        ('fast', 'Fast-paced and intense'),
        ('slow', 'Slow-paced and thoughtful'),
        ('emotional', 'Emotional and character-driven'),
        ('analytical', 'Analytical and idea-driven'),
        ('mixed', 'A mix of everything'),
    ]

    FOCUS_CHOICES = [
        ('mystery', 'Mystery and discovering what happened'),
        ('characters', 'Characters and relationships'),
        ('learning', 'Learning something useful'),
        ('exploring', 'Exploring ideas and different worlds'),
        ('suspense', 'Suspense, twists and surprises'),
    ]

    ENDING_CHOICES = [
        ('happy', 'Satisfying / happy'),
        ('sad', 'Sad / emotional'),
        ('thought_provoking', 'Thought-provoking'),
        ('bittersweet', 'Bittersweet'),
        ('any', "I don't really care about the ending"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    pace = models.CharField(
        max_length=50,
        choices=PACE_CHOICES
    )

    reading_focus = models.CharField(
        max_length=50,
        choices=FOCUS_CHOICES
    )

    ending_preference = models.CharField(
        max_length=50,
        choices=ENDING_CHOICES
    )

    genres = models.JSONField(
        default=list,
        blank=True
    )

    selected_books = models.ManyToManyField(
        Book,
        blank=True
    )

    quiz_completed = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user.username}'s preferences"