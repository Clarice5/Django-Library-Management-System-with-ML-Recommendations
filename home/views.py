from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from datetime import datetime
from home.models import Contact,Book,BookIssue
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
import requests

# Create your views here.
def index(request):
    if request.user.is_anonymous:
        return redirect("/login")
    context={
        'variable': "this is sent"
    }
   
    #return HttpResponse("this is home page")
    return render(request,'index.html',context)

def about(request):
    #return HttpResponse("this is about page")
    return render(request,'about.html')

def services(request):
    #return HttpResponse("this is services page")
    return render(request,'services.html')

def contact(request):
    #return HttpResponse("this is contact page")
    if request.method == "POST":
        name=request.POST.get('name')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        desc=request.POST.get('desc')
        contact=Contact(name=name,email=email,phone=phone,desc=desc,date=datetime.today())
        contact.save()
        messages.success(request, "message submitted")
    return render(request,'contact.html')

def loginUser(request):
    if request.method=="POST":
        username=request.POST.get('username')
        password=request.POST.get('password')
        print(username,password)
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request,user)
            return redirect("/")
    # A backend authenticated the credentials
    
        else:
            return render(request,'login.html')

    return render(request,'login.html')
    # No backend authenticated the credentials
    #return HttpResponse("this is about page")
    

def logoutUser(request):
    logout(request)
    #return HttpResponse("this is services page")
    return redirect("/login")



def book_list(request):
    query = request.GET.get('q')
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(category__icontains=query)
        )
    else:
        books = Book.objects.all()
    return render(request, 'books.html', {'books': books})


def issue_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)

        if BookIssue.objects.filter(user=request.user, book=book, returned=False).exists():
            messages.warning(request, "You already issued this book.")
        else:
            issued_count = BookIssue.objects.filter(user=request.user, returned=False).count()
            if issued_count >= 3:
                messages.error(request, "You have reached your issue limit.")
            else:
                BookIssue.objects.create(user=request.user, book=book)
                book.status = 'issued'
                book.save()
                messages.success(request, "Book issued successfully!")
        return redirect('/books')
    return redirect('/books')

def return_book(request,book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        issue = BookIssue.objects.filter(user=request.user, book=book, returned=False).first()

        if issue:
            issue.returned = True
            issue.save()
            book.status = 'available'
            book.save()
            messages.success(request, "Book returned successfully!")
        else:
            messages.warning(request, "You haven't issued this book.")
        
        return redirect('/books')

    return redirect('/books')

def add_book(request):
    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        isbn = request.POST.get("isbn")
        category = request.POST.get("category")
        location = request.POST.get("location")

        Book.objects.create(
        title=title,
        author=author,
        isbn=isbn,
        category=category,
        location=location
)
        messages.success(request, "Book added successfully!")
        return redirect("books_list")
    context = {}

    isbn = request.GET.get("isbn")

    if isbn:

        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"

        #response = requests.get(url)
        print("Calling Open Library...")
        response = requests.get(url, timeout=5)
        print("Response received")
        if response.status_code == 200:

            data = response.json()

            book = data.get(f"ISBN:{isbn}")

            if book:

                title = book.get("title")
                print(title)

                authors = book.get("authors", [])
                author = authors[0]["name"] if authors else "Unknown"

                publishers = book.get("publishers", [])
                publisher = publishers[0]["name"] if publishers else "Unknown"
                print(author)
                print(publisher)
                publish_date = book.get("publish_date", "Unknown")
                print(publish_date)
                context = {
                "title": title,
                "author": author,
                "publisher": publisher,
                "publish_date": publish_date,
                "isbn":isbn
                    }
            else:
                print("Book not found.")

        else:
            print("Error:", response.status_code)
            print(response.text)

    return render(request, "add_book.html", context)