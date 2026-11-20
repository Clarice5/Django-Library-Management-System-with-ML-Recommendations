from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from datetime import datetime, date
from home.models import Contact, Book, BookIssue, Review,UserPreference
from django.contrib import messages
from collections import Counter
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Avg
from django.contrib.auth.decorators import login_required
from functools import wraps
from requests.exceptions import RequestException
from django.shortcuts import redirect
from .quiz_recommender import get_adaptive_recommendations, explain_adaptive_match
from django.db.models import Count
import requests
import openpyxl
from django.db.models.functions import TruncMonth
from django.db.models import Count
import json



# ============================================================
# HOME
# ============================================================

def index(request):
    if request.user.is_anonymous:
        return redirect("/login")

    if not hasattr(request.user, 'userpreference'):
        return redirect('quiz')

    popular_books = Book.objects.annotate(
        issue_count=Count("bookissue")
    ).order_by("-issue_count")[:6]

    context = {
        'variable': "this is sent",
        'popular_books': popular_books
    }

    return render(request, 'index.html', context)

# ============================================================
# ABOUT
# ============================================================

def about(request):
    return render(request, "about.html")


# ============================================================
# SERVICES
# ============================================================

def services(request):
    return render(request, "services.html")


# ============================================================
# CONTACT
# ============================================================

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        desc = request.POST.get("desc")

        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            desc=desc,
            date=datetime.today()
        )

        contact.save()

        messages.success(request, "Message submitted")

    return render(request, "contact.html")


# ============================================================
# LOGIN
# ============================================================

def loginUser(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("/")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(request, "login.html")

    return render(request, "login.html")


# ============================================================
# LOGOUT
# ============================================================

def logoutUser(request):

    logout(request)

    return redirect("/login")


# ============================================================
# BOOK LIST
# ============================================================

def book_list(request):

    query = request.GET.get("q")
    status = request.GET.get("status")

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

    # Calculate average rating for every book
    books = books.annotate(
        average_rating=Avg("reviews__rating")
    )

    return render(
        request,
        "books.html",
        {
            "books": books
        }
    )


# ============================================================
# ISSUE BOOK
# ============================================================

def issue_book(request, book_id):

    if request.method == "POST":

        book = get_object_or_404(
            Book,
            id=book_id
        )

        # Check if user already has this book
        if BookIssue.objects.filter(
            user=request.user,
            book=book,
            returned=False
        ).exists():

            messages.warning(
                request,
                "You already issued this book."
            )

        else:

            # Maximum 3 active books per user
            issued_count = BookIssue.objects.filter(
                user=request.user,
                returned=False
            ).count()

            if issued_count >= 3:

                messages.error(
                    request,
                    "You have reached your issue limit."
                )

            else:

                BookIssue.objects.create(
                    user=request.user,
                    book=book
                )

                book.status = "issued"
                book.save()

                messages.success(
                    request,
                    "Book issued successfully!"
                )

        return redirect("/books")

    return redirect("/books")


# ============================================================
# RETURN BOOK
# ============================================================

def return_book(request, book_id):

    if request.method == "POST":

        book = get_object_or_404(
            Book,
            id=book_id
        )

        issue = BookIssue.objects.filter(
            user=request.user,
            book=book,
            returned=False
        ).first()

        if issue:

            today = date.today()

            # Calculate overdue fine
            if today > issue.return_date:

                overdue_days = (
                    today - issue.return_date
                ).days

                issue.fine = overdue_days * 10

            else:

                issue.fine = 0

            issue.returned = True
            issue.save()

            book.status = "available"
            book.save()

            messages.success(
                request,
                f"Book returned successfully! Fine: ₹{issue.fine}"
            )

        else:

            messages.warning(
                request,
                "You haven't issued this book."
            )

        return redirect("/books")

    return redirect("/books")


# ============================================================
# ADMIN ACCESS CONTROL
# ============================================================

def admin_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # User is not logged in
        if not request.user.is_authenticated:

            return redirect("/login")

        # User is logged in but not staff/admin
        if not request.user.is_staff:

            messages.error(
                request,
                "You don't have permission to access this page."
            )

            return redirect("books_list")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# ADD BOOK
# ============================================================

# ============================================================
# ADD BOOK
# ============================================================

@admin_required
def add_book(request):

    # --------------------------------------------------------
    # SAVE BOOK
    # --------------------------------------------------------

    if request.method == "POST":

        title = request.POST.get("title")
        author = request.POST.get("author")
        isbn = request.POST.get("isbn")
        cover_url = request.POST.get("cover_url", "")
        category = request.POST.get("category")
        location = request.POST.get("location")

        # Check duplicate ISBN
        book_exists = Book.objects.filter(
            isbn=isbn
        ).exists()

        if book_exists:

            messages.error(
                request,
                "Book already exists!"
            )

        else:

            Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                category=category,
                location=location,
                cover_url=cover_url
            )

            messages.success(
                request,
                "Book added successfully!"
            )

        return redirect("books_list")

    # --------------------------------------------------------
    # ISBN LOOKUP
    # --------------------------------------------------------

    context = {}

    isbn = request.GET.get("isbn")

    if isbn:

        # Remove spaces and hyphens from ISBN
        isbn = isbn.replace("-", "").replace(" ", "")

        url = "https://openlibrary.org/search.json"

        params = {
            "isbn": isbn,
            "limit": 1
        }

        print("Calling Open Library Search API...")
        print("ISBN:", isbn)

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers={
                    "User-Agent": "SFIT-Library-Management-System/1.0"
                }
            )

            print("STATUS:", response.status_code)
            print("URL:", response.url)
            print("RESPONSE:", response.text[:500])
            print("Response received")

        except RequestException as e:

            print("REQUEST ERROR:", e)

            messages.error(
                request,
                "Unable to fetch book details right now. Please try again."
            )

            return render(
                request,
                "add_book.html",
                context
            )

        # ----------------------------------------------------
        # SUCCESSFUL API RESPONSE
        # ----------------------------------------------------

        if response.status_code == 200:

            data = response.json()

            docs = data.get(
                "docs",
                []
            )

            print("BOOKS FOUND:", len(docs))

            if docs:

                book = docs[0]

                # ------------------------------------------------
                # TITLE
                # ------------------------------------------------

                title = book.get(
                    "title",
                    "Unknown"
                )

                # ------------------------------------------------
                # AUTHOR
                # ------------------------------------------------

                authors = book.get(
                    "author_name",
                    []
                )

                author = (
                    authors[0]
                    if authors
                    else "Unknown"
                )

                # ------------------------------------------------
                # PUBLISHER
                # ------------------------------------------------

                publishers = book.get(
                    "publisher",
                    []
                )

                publisher = (
                    publishers[0]
                    if publishers
                    else "Unknown"
                )

                # ------------------------------------------------
                # PUBLICATION DATE
                # ------------------------------------------------

                publish_year = book.get(
                    "first_publish_year",
                    "Unknown"
                )

                # ------------------------------------------------
                # COVER
                # ------------------------------------------------

                cover_id = book.get(
                    "cover_i"
                )

                if cover_id:

                    cover_url = (
                        f"https://covers.openlibrary.org/b/id/"
                        f"{cover_id}-M.jpg"
                    )

                else:

                    cover_url = ""

                # ------------------------------------------------
                # SEND DATA TO TEMPLATE
                # ------------------------------------------------

                context = {

                    "title": title,

                    "author": author,

                    "publisher": publisher,

                    "publish_date": publish_year,

                    "isbn": isbn,

                    "cover_url": cover_url
                }

                print("BOOK DATA:", context)

            else:

                messages.error(
                    request,
                    "Book not found for this ISBN."
                )

        else:

            print(
                "Open Library returned:",
                response.status_code
            )

            messages.error(
                request,
                "Unable to fetch book details right now."
            )

    # --------------------------------------------------------
    # DISPLAY ADD BOOK PAGE
    # --------------------------------------------------------

    return render(
        request,
        "add_book.html",
        context
    )
# ============================================================
# UPLOAD BOOKS FROM EXCEL
# ============================================================

@admin_required
def upload_books(request):

    if request.method == "POST":

        imported_count = 0
        duplicate_count = 0

        excel_file = request.FILES.get(
            "books"
        )

        workbook = openpyxl.load_workbook(
            excel_file
        )

        sheet = workbook.active

        for row in sheet.iter_rows(
            min_row=2,
            values_only=True
        ):

            book_exists = Book.objects.filter(
                isbn=row[2]
            ).exists()

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
            f"Imported {imported_count} books. "
            f"Skipped {duplicate_count} duplicate books."
        )

    return render(
        request,
        "upload_books.html"
    )


# ============================================================
# EDIT BOOK
# ============================================================

@admin_required
def edit_book(request, book_id):

    book = get_object_or_404(
        Book,
        id=book_id
    )

    if request.method == "POST":

        book.title = request.POST.get(
            "title"
        )

        book.author = request.POST.get(
            "author"
        )

        book.category = request.POST.get(
            "category"
        )

        book.location = request.POST.get(
            "location"
        )

        book.save()

        messages.success(
            request,
            "Book updated successfully!"
        )

        return redirect(
            "books_list"
        )

    return render(
        request,
        "edit_book.html",
        {
            "book": book
        }
    )


# ============================================================
# DELETE BOOK
# ============================================================

@admin_required
def delete_book(request, book_id):

    book = get_object_or_404(
        Book,
        id=book_id
    )

    if request.method == "POST":

        book.delete()

        messages.success(
            request,
            "Book deleted successfully!"
        )

        return redirect(
            "books_list"
        )

    return render(
        request,
        "delete_book.html",
        {
            "book": book
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

from collections import Counter
import json

def dashboard(request):
    total_books = Book.objects.count()
    issued_books = Book.objects.filter(status="issued").count()
    available_books = total_books - issued_books

    all_dates = list(BookIssue.objects.values_list("issue_date", flat=True))

    day_counts = Counter(all_dates)
    sorted_dates = sorted(day_counts.keys())

    borrow_labels = [d.strftime("%d %b") for d in sorted_dates]
    borrow_data = [day_counts[d] for d in sorted_dates]

    context = {
        "total_books": total_books,
        "issued_books": issued_books,
        "available_books": available_books,
        "borrow_labels": json.dumps(borrow_labels),
        "borrow_data": json.dumps(borrow_data),
    }
    return render(request, "dashboard.html", context)
# ============================================================
# MY BOOKS
# ============================================================

def my_books(request):

    issues = BookIssue.objects.filter(
        user=request.user
    )

    return render(
        request,
        "my_books.html",
        {
            "issues": issues
        }
    )


# ============================================================
# ADD REVIEW
# ============================================================

def add_review(request, book_id):

    book = get_object_or_404(
        Book,
        id=book_id
    )

    # Check whether user has borrowed this book
    has_borrowed = BookIssue.objects.filter(
        user=request.user,
        book=book
    ).exists()

    if not has_borrowed:

        messages.warning(
            request,
            "You can only review books you have borrowed."
        )

        return redirect(
            "books_list"
        )

    if request.method == "POST":

        rating = request.POST.get(
            "rating"
        )

        comment = request.POST.get(
            "comment"
        )

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

        return redirect(
            "books_list"
        )

    return render(
        request,
        "review.html",
        {
            "book": book
        }
    )


# ============================================================
# VIEW BOOK REVIEWS
# ============================================================

def book_reviews(request, book_id):

    book = get_object_or_404(
        Book,
        id=book_id
    )

    reviews = book.reviews.all().order_by(
        "-created_at"
    )

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

@login_required
def quiz(request):

    if request.method == "POST":

        pace = request.POST.get("pace")
        reading_focus = request.POST.get("reading_focus")
        ending_preference = request.POST.get("ending_preference")
        genres = request.POST.getlist("genres")

        UserPreference.objects.update_or_create(
            user=request.user,
            defaults={
                "pace": pace,
                "reading_focus": reading_focus,
                "ending_preference": ending_preference,
                "genres": genres,
                "quiz_completed": True,
            }
        )

        return redirect("books_list")

    return render(request, "quiz.html")



@login_required
def recommendations(request):
    try:
        user_preference = request.user.userpreference
    except UserPreference.DoesNotExist:
        return redirect('quiz')

    borrowed_books = Book.objects.filter(bookissue__user=request.user).distinct()

    results, warmth, w_quiz, w_behavior, used_fallback = get_adaptive_recommendations(
        user_preference, borrowed_books
    )

    recommendations_list = [
        {
            "book": book,
            "score": score,
            "matched_tags": sorted(quiz_matched | behavior_matched),
            "explanation": explain_adaptive_match(quiz_matched, behavior_matched, warmth, used_fallback),
        }
        for book, score, quiz_matched, behavior_matched in results
    ]

    context = {
        "recommendations": recommendations_list,
        "used_fallback": used_fallback,
        "warmth": warmth,
    }
    return render(request, "recommendations.html", context)