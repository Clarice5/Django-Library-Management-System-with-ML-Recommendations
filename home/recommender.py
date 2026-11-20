from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Book
def get_recommendations(book_id, num_recommendations=5):

    books = list(Book.objects.all())

    if len(books) <= 1:
        return []

    # Create text representation for each book
    book_text = []

    for book in books:
        text = f"{book.title} {book.author} {book.category}"
        book_text.append(text)

    # Convert book information into TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(book_text)

    # Calculate similarity between books
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Find the position of the selected book
    book_index = next(
        (i for i, book in enumerate(books) if book.id == book_id),
        None
    )

    if book_index is None:
        return []

    # Get similarity scores for the selected book
    similarity_scores = list(enumerate(similarity_matrix[book_index]))

    # Sort from most similar to least similar
    similarity_scores = sorted(
        similarity_scores,
        key=lambda x: x[1],
        reverse=True
    )

    # Remove the selected book itself
    similarity_scores = [
        item for item in similarity_scores
        if item[0] != book_index
    ]

    # Get the recommended books
    recommended_books = [
        books[index]
        for index, score in similarity_scores[:num_recommendations]
    ]

    return recommended_books