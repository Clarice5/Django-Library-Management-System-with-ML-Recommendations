from types import SimpleNamespace
from django.db.models import Count
from home.models import Book, UserPreference


def get_popularity_fallback(num_recommendations=5):
    """
    Used when tag-matching finds nothing at all. Falls back to whatever
    books have been borrowed most, using the existing BookIssue history.
    Returns the same (book, score, matched_tags) shape as the main
    function so calling code doesn't need to branch on which path ran --
    score is 0 and matched_tags is empty to signal "this was a fallback,
    not a real match."
    """
    popular_books = (
        Book.objects.annotate(num_borrows=Count("bookissue"))
        .order_by("-num_borrows")[:num_recommendations]
    )
    return [(book, 0, set()) for book in popular_books]


def get_quiz_based_recommendations(user_preference, num_recommendations=5):
    user_tags = set()
    user_tags.add(user_preference.pace)
    user_tags.add(user_preference.reading_focus)
    user_tags.add(user_preference.ending_preference)
    for genre in user_preference.genres:
        user_tags.add(genre.lower())

    scored_books = []
    for book in Book.objects.exclude(recommendation_tags=[]):
        book_tags = set(book.recommendation_tags)
        overlap = len(user_tags & book_tags)
        if overlap > 0:
            scored_books.append((book, overlap, book_tags & user_tags))

    scored_books.sort(key=lambda x: x[1], reverse=True)

    if not scored_books:
        # No tag overlap at all -- fall back to popularity rather than
        # showing the user a blank page.
        return get_popularity_fallback(num_recommendations), user_tags, True

    return scored_books[:num_recommendations], user_tags, False


def explain_quiz_match(matched_tags, total_user_tags, used_fallback):
    if used_fallback:
        return "No close match to your preferences yet -- showing popular books in the meantime."
    matched_sorted = sorted(matched_tags)
    return f"Matched {len(matched_tags)} of {total_user_tags} preferences: {', '.join(matched_sorted)}"


def run_test(label, pace, reading_focus, ending_preference, genres):
    fake_pref = SimpleNamespace(
        pace=pace,
        reading_focus=reading_focus,
        ending_preference=ending_preference,
        genres=genres,
    )
    results, user_tags, used_fallback = get_quiz_based_recommendations(fake_pref)

    print(f"\n=== {label} ===")
    print(f"Quiz answers: pace={pace}, focus={reading_focus}, ending={ending_preference}, genres={genres}")
    print(f"Fallback used: {used_fallback}")
    if not results:
        print("  STILL EMPTY -- even the fallback returned nothing (no books have any borrow history yet).")
    for book, score, matched_tags in results:
        explanation = explain_quiz_match(matched_tags, len(user_tags), used_fallback)
        print(f"  {book.title}  (score={score})")
        print(f"    -> {explanation}")


# --- Real saved user, as before ---
p = UserPreference.objects.last()
real_results, real_tags, real_fallback = get_quiz_based_recommendations(p)
print("=== Real saved UserPreference ===")
print(f"Fallback used: {real_fallback}")
for book, score, matched_tags in real_results:
    print(f"  {book.title}  (score={score})")
    print(f"    -> {explain_quiz_match(matched_tags, len(real_tags), real_fallback)}")

# --- Deliberately try to force a true zero-match case ---
run_test(
    "Forced Empty-Match Edge Case",
    pace="mixed", reading_focus="learning", ending_preference="any",
    genres=[],
)

# --- Another attempt with genuinely nonsense/unmatched values ---
run_test(
    "Nonsense Values (should always hit fallback)",
    pace="zzz_no_such_tag", reading_focus="zzz_no_such_tag",
    ending_preference="zzz_no_such_tag", genres=[],
)