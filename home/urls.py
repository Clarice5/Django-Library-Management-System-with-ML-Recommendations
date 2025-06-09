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
     path('return-book/<int:book_id>/', views.return_book, name='return-book')


    
]
