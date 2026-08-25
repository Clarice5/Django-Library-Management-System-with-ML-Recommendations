from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from datetime import datetime,date
from home.models import Contact,Book,BookIssue,Review
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
import requests
import openpyxl
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Avg

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
    status = request.GET.get('status')

    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(category__icontains=query)
        )
    else:
        books = Book.objects.all()

    if status:
        books = books.filter(status=status)

    books = books.annotate(
        average_rating=Avg("reviews__rating")
    )

    return render(
        request,
        'books.html',
        {'books': books}
    )


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
            today = date.today()

            if today > issue.return_date:
                overdue_days = (today - issue.return_date).days
                issue.fine = overdue_days * 10
            else:
                issue.fine = 0

            issue.returned = True
            issue.save()

            book.status = 'available'
            book.save()

            messages.success(request, f"Book returned successfully! Fine: ₹{issue.fine}")
        else:
            messages.warning(request, "You haven't issued this book.")
        
        return redirect('/books')

    return redirect('/books')
def admin_required(view_func):
    return user_passes_test(lambda user: user.is_staff)(view_func)

@admin_required
def add_book(request):
    
    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        isbn = request.POST.get("isbn")
        cover_url = request.POST.get("cover_url", "")
        print("POST COVER URL:", cover_url)
        category = request.POST.get("category")
        location = request.POST.get("location")

        book_exists = Book.objects.filter(isbn=isbn).exists()

        if book_exists:
            messages.error(request, "Book already exists!")
        else:
            Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            location=location,
            cover_url=cover_url
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
            print(book)
            if book:
                cover = book.get("cover", {})
                cover_url = cover.get("medium", "")
            
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
                "isbn":isbn,
                "cover_url": cover_url
                    }
            else:
                print("Book not found.")

        else:
            print("Error:", response.status_code)
            print(response.text)

    return render(request, "add_book.html", context)
@admin_required
def upload_books(request):

    if request.method == "POST":

        imported_count = 0
        duplicate_count = 0

        excel_file = request.FILES.get("books")

        workbook = openpyxl.load_workbook(excel_file)

        sheet = workbook.active

        for row in sheet.iter_rows(min_row=2, values_only=True):

            book_exists = Book.objects.filter(isbn=row[2]).exists()

            if not book_exists:
                Book.objects.create(
                    title=row[0],
                    author=row[1],
                    isbn=row[2],
                    category=row[3],
                    location=row[4]
                )
                imported_count += 1

            else:
                duplicate_count += 1

        messages.success(
            request,
            f"Imported {imported_count} books. Skipped {duplicate_count} duplicate books."
        )

    return render(request, "upload_books.html")
@admin_required
def edit_book(request, book_id):

    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":

        book.title = request.POST.get("title")
        book.author = request.POST.get("author")
        book.category = request.POST.get("category")
        book.location = request.POST.get("location")

        book.save()

        messages.success(request, "Book updated successfully!")

        return redirect("books_list")

    return render(request, "edit_book.html", {"book": book})
@admin_required
def delete_book(request, book_id):

    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        book.delete()
        messages.success(request, "Book deleted successfully!")
        return redirect("books_list")

    return render(request, "delete_book.html", {"book": book})
def dashboard(request):

    total_books = Book.objects.count()
    issued_books = Book.objects.filter(status="issued").count()
    available_books = Book.objects.filter(status="available").count()

    context = {
        "total_books": total_books,
        "issued_books": issued_books,
        "available_books": available_books,
    }

    return render(request, "dashboard.html", context)

def my_books(request):
    issues = BookIssue.objects.filter(user=request.user)
    return render(request, "my_books.html", {"issues": issues})

def add_review(request, book_id):

    book = get_object_or_404(Book, id=book_id)

    has_borrowed = BookIssue.objects.filter(
        user=request.user,
        book=book
    ).exists()

    if not has_borrowed:
        messages.warning(
            request,
            "You can only review books you have borrowed."
        )
        return redirect("books_list")

    if request.method == "POST":

        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        Review.objects.create(
            user=request.user,
            book=book,
            rating=rating,
            comment=comment
        )

        messages.success(
            request,
            "Review added successfully!"
        )

        return redirect("books_list")

    return render(
        request,
        "review.html",
        {"book": book}
    )
def book_reviews(request, book_id):

    book = get_object_or_404(Book, id=book_id)

    reviews = book.reviews.all().order_by("-created_at")

    average_rating = reviews.aggregate(
        Avg("rating")
    )["rating__avg"]

    review_count = reviews.count()

    return render(
        request,
        "book_reviews.html",
        {
            "book": book,
            "reviews": reviews,
            "average_rating": average_rating,
            "review_count": review_count
        }
    )