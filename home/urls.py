from django.contrib import admin
from django.urls import path,include
from home import views

urlpatterns = [
     path("",views.index,name='home'),
     path("about",views.about,name='about'),
     path("services",views.services,name='services'),
     path("contact",views.contact,name='contact'),
     path("login",views.loginUser,name='login'),
     path("logout",views.logoutUser,name='logout'),
     path("books",views.book_list,name='books_list'),
     path('issue-book/<int:book_id>/', views.issue_book, name='issue-book'),
     path('return-book/<int:book_id>/', views.return_book, name='return-book'),
     path("add-book",views.add_book,name='add_book'),
     path("upload-books", views.upload_books, name="upload_books"),
     path("edit-book/<int:book_id>/", views.edit_book, name="edit_book"),
     path("delete-book/<int:book_id>",views.delete_book,name="delete_book"), #how django will know which book to delete
     path("dashboard", views.dashboard, name="dashboard"),
     path("my-books/", views.my_books, name="my_books"),
     path("add-review/<int:book_id>/", views.add_review, name="add_review"),
     path("book-reviews/<int:book_id>/",views.book_reviews,name="book_reviews")
]