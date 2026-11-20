from types import SimpleNamespace
from collections import Counter
from django.db.models import Count
from home.models import Book, UserPreference


def get_popularity_fallback(num_recommendations=5):
    popular_books = (
        Book.objects.annotate(num_borrows=Count("bookissue"))
        .order_by("-num_borrows")[:num_recommendations]
    )
    return [(book, 0, set(), set()) for book in popular_books]


def build_quiz_tags(user_preference):
    tags = set()
    tags.add(user_preference.pace)
    tags.add(user_preference.reading_focus)
    tags.add(user_preference.ending_preference)
    for genre in user_preference.genres:
        tags.add(genre.lower())
    return tags


def get_adaptive_recommendations(user_preference, borrowed_books, num_recommendations=5):
    """
    borrowed_books: list/queryset of Book objects the user has actually
    borrowed (real BookIssue history). Passed in explicitly so this core
    function is easy to test without touching the database.
    """
    quiz_tags = build_quiz_tags(user_preference)
    borrowed_books = list(borrowed_books)
    warmth = len(borrowed_books)
    borrowed_ids = {b.id for b in borrowed_books}

    behavior_tag_counts = Counter()
    for b in borrowed_books:
        behavior_tag_counts.update(set(b.recommendation_tags))

    # More borrows -> more trust in real behavior, capped at 70% so the
    # quiz never fully disappears.
    w_behavior = min(warmth / 10, 0.7)
    w_quiz = 1 - w_behavior

    scored = []
    for book in Book.objects.exclude(recommendation_tags=[]).exclude(id__in=borrowed_ids):
        book_tags = set(book.recommendation_tags)

        quiz_matched = book_tags & quiz_tags
        quiz_score = len(quiz_matched)

        if warmth > 0:
            behavior_matched = {t for t in book_tags if t in behavior_tag_counts}
            behavior_score = sum(behavior_tag_counts[t] for t in book_tags) / warmth
        else:
            behavior_matched = set()
            behavior_score = 0

        combined = (w_quiz * quiz_score) + (w_behavior * behavior_score)
        if combined > 0:
            scored.append((book, combined, quiz_matched, behavior_matched))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return get_popularity_fallback(num_recommendations), warmth, w_quiz, w_behavior, True

    return scored[:num_recommendations], warmth, w_quiz, w_behavior, False


def explain_adaptive_match(quiz_matched, behavior_matched, warmth, used_fallback):
    if used_fallback:
        return "No close match yet -- showing popular books in the meantime."
    parts = []
    if quiz_matched:
        parts.append(f"quiz preferences ({', '.join(sorted(quiz_matched))})")
    if behavior_matched:
        parts.append(f"your recent borrowing ({', '.join(sorted(behavior_matched))})")
    if not parts:
        return "Matched general reading trends."
    return f"Matches your {' and '.join(parts)}. [warmth={warmth} borrows]"


def run_test(label, pace, reading_focus, ending_preference, genres, borrowed_ids):
    fake_pref = SimpleNamespace(
        pace=pace, reading_focus=reading_focus,
        ending_preference=ending_preference, genres=genres,
    )
    borrowed_books = list(Book.objects.filter(id__in=borrowed_ids))

    results, warmth, w_quiz, w_behavior, used_fallback = get_adaptive_recommendations(
        fake_pref, borrowed_books
    )

    print(f"\n=== {label} ===")
    print(f"Quiz: pace={pace}, focus={reading_focus}, ending={ending_preference}, genres={genres}")
    print(f"Borrowed: {[b.title for b in borrowed_books]}")
    print(f"warmth={warmth}, w_quiz={w_quiz:.2f}, w_behavior={w_behavior:.2f}, fallback={used_fallback}")
    for book, score, quiz_matched, behavior_matched in results:
        print(f"  {book.title}  (score={score:.2f})")
        print(f"    -> {explain_adaptive_match(quiz_matched, behavior_matched, warmth, used_fallback)}")


# --- Test 1: zero borrows -- should exactly match the old cold-start behavior ---
run_test(
    "Cold (0 borrows) -- sanity check vs old function",
    pace="fast", reading_focus="mystery", ending_preference="thought_provoking",
    genres=["Thriller"],
    borrowed_ids=[],
)

# --- Test 2: quiz and behavior AGREE (thriller quiz, thriller borrows) ---
run_test(
    "Reinforcing: Thriller quiz + Thriller borrows",
    pace="fast", reading_focus="mystery", ending_preference="thought_provoking",
    genres=["Thriller"],
    borrowed_ids=[18, 22],  # 2nd Chance, The Woman in the Window
)

# --- Test 3: quiz and behavior CONFLICT, light warmth (2 borrows) ---
run_test(
    "Conflict, light warmth: Thriller quiz but Fantasy borrows (2)",
    pace="fast", reading_focus="mystery", ending_preference="thought_provoking",
    genres=["Thriller"],
    borrowed_ids=[42, 44],  # Fourth Wing, The Cruel Prince
)

# --- Test 4: same conflict, HEAVY warmth (6 borrows) -- should shift much more toward Fantasy ---
run_test(
    "Conflict, heavy warmth: Thriller quiz but Fantasy borrows (6)",
    pace="fast", reading_focus="mystery", ending_preference="thought_provoking",
    genres=["Thriller"],
    borrowed_ids=[42, 43, 44, 45, 46, 47],  # all 6 fantasy books
)