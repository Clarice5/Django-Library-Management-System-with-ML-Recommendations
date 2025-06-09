from django.contrib import admin
from home.models import Contact,Book,BookIssue

# Register your models here.
admin.site.register(Contact)

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'category', 'location')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('status', 'category')

admin.site.register(Book, BookAdmin)

class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'issue_date', 'return_date', 'returned')
    list_filter = ('returned', 'issue_date')
    search_fields = ('user__username', 'book__title')

admin.site.register(BookIssue, BookIssueAdmin)

