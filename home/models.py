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

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

