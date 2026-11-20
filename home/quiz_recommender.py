from collections import Counter

from django.db.models import Count

from .models import Book


def get_popularity_fallback(num_recommendations=5):
    popular_books = (
        Book.objects
        .annotate(num_borrows=Count("bookissue"))
        .order_by("-num_borrows")[:num_recommendations]
    )

    return [
        (book, 0, set(), set())
        for book in popular_books
    ]


def build_quiz_tags(user_preference):
    tags = set()

    if user_preference.pace:
        tags.add(user_preference.pace.lower())

    if user_preference.reading_focus:
        tags.add(user_preference.reading_focus.lower())

    if user_preference.ending_preference:
        tags.add(user_preference.ending_preference.lower())

    for genre in user_preference.genres:
        tags.add(genre.lower())

    return tags


def get_adaptive_recommendations(
    user_preference,
    borrowed_books,
    num_recommendations=5
):

    # ----------------------------------------
    # 1. Get quiz preferences
    # ----------------------------------------

    quiz_tags = build_quiz_tags(user_preference)

    borrowed_books = list(borrowed_books)

    warmth = len(borrowed_books)

    borrowed_ids = {
        book.id
        for book in borrowed_books
    }

    # ----------------------------------------
    # 2. Analyze borrowing behavior
    # ----------------------------------------

    behavior_tag_counts = Counter()

    for book in borrowed_books:

        book_tags = {
            tag.lower()
            for tag in book.recommendation_tags
        }

        behavior_tag_counts.update(book_tags)

    # ----------------------------------------
    # 3. Weight quiz and behavior
    # ----------------------------------------
    #
    # Quiz remains the stronger signal.
    # 0 borrowed books:  Quiz = 100%, Behavior = 0%
# 7+ borrowed books: Quiz = 30%,  Behavior = 70%
    w_behavior = min(warmth / 10, 0.7)

    w_quiz = 1 - w_behavior

    # ----------------------------------------
    # 4. Score candidate books
    # ----------------------------------------

    scored = []

    books = (
        Book.objects
        .exclude(recommendation_tags=[])
        .exclude(id__in=borrowed_ids)
    )

    for book in books:

        # Normalize book tags to lowercase
        book_tags = {
            tag.lower()
            for tag in book.recommendation_tags
        }

        # ----------------------------------------
        # QUIZ SCORE
        # ----------------------------------------

        quiz_matched = book_tags & quiz_tags

        quiz_score = (
            len(quiz_matched)
            / max(len(quiz_tags), 1)
        )

        # ----------------------------------------
        # BEHAVIOR SCORE
        # ----------------------------------------

        if warmth > 0 and book_tags:

            behavior_matched = {
                tag
                for tag in book_tags
                if tag in behavior_tag_counts
            }

            if behavior_matched:

                # Average frequency of the matched
                # tags in the user's borrowing history.
                behavior_score = (
                    sum(
                        behavior_tag_counts[tag]
                        for tag in behavior_matched
                    )
                    /
                    (
                        warmth
                        * len(behavior_matched)
                    )
                )

            else:

                behavior_score = 0

        else:

            behavior_matched = set()
            behavior_score = 0

        # ----------------------------------------
        # COMBINED SCORE
        # ----------------------------------------

        combined_score = (
            (w_quiz * quiz_score)
            +
            (w_behavior * behavior_score)
        )

        # ----------------------------------------
        # Keep relevant books
        # ----------------------------------------

        if combined_score > 0:

            scored.append(
                (
                    book,
                    combined_score,
                    quiz_matched,
                    behavior_matched
                )
            )

    # ----------------------------------------
    # 5. Sort by recommendation score
    # ----------------------------------------

    scored.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # ----------------------------------------
    # 6. Popularity fallback
    # ----------------------------------------

    if not scored:

        return (
            get_popularity_fallback(
                num_recommendations
            ),
            warmth,
            w_quiz,
            w_behavior,
            True
        )

    # ----------------------------------------
    # 7. Return recommendations
    # ----------------------------------------

    return (
        scored[:num_recommendations],
        warmth,
        w_quiz,
        w_behavior,
        False
    )


def explain_adaptive_match(
    quiz_matched,
    behavior_matched,
    warmth,
    used_fallback
):

    if used_fallback:

        return (
            "No close match yet — "
            "showing popular books in the meantime."
        )

    parts = []

    if quiz_matched:

        parts.append(
            "quiz preferences "
            f"({', '.join(sorted(quiz_matched))})"
        )

    if behavior_matched:

        parts.append(
            "your recent borrowing "
            f"({', '.join(sorted(behavior_matched))})"
        )

    if not parts:

        return "Matched general reading trends."

    return (
        "Matches your "
        + " and ".join(parts)
        + "."
    )