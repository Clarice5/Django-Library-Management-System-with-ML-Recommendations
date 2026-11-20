# Django Library Management System with ML-Based Book Recommendations

A Django-based Library Management System integrated with a personalized book recommendation system. The application helps users discover books based on their reading preferences and borrowing activity.

## Features

### Library Management
- User authentication and login
- Browse and search the book catalogue
- View book details and cover images
- Issue and return books
- Track due dates and overdue fines
- Personal borrowing history
- Admin book management
- Bulk book upload
- Book reviews and ratings

### Machine Learning-Based Recommendations
- Reading preference quiz for new users
- Personalized recommendations based on quiz responses
- Adaptive recommendations using borrowing history
- Book metadata and recommendation tags
- Popularity-based fallback when personalized matches are unavailable
- Recommendation explanations showing matched preferences and borrowing interests

## Technology Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript, Bootstrap (if used in the templates)
- **Database:** SQLite
- **Recommendation System:** Python-based recommendation logic, content/tag matching and adaptive scoring

## Project Structure

```text
Hello/
├── Hello/                 # Django project configuration
├── home/                  # Main Django application
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── recommender.py
│   └── quiz_recommender.py
├── templates/             # HTML templates
├── static/                # Static assets
├── manage.py
├── requirements.txt
└── README.md
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/Clarice5/Django-Library-Management-System-with-ML-Recommendations.git
cd Django-Library-Management-System-with-ML-Recommendations
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply database migrations:

```bash
python manage.py migrate
```

5. Start the development server:

```bash
python manage.py runserver
```

6. Open `http://127.0.0.1:8000/` in your browser.

## Recommendation System Overview

The recommendation system uses a reading preference quiz to understand a user's interests. As users borrow books, their interaction history can also contribute to recommendations.

The system combines preference-based matching and borrowing behaviour, and uses a popularity-based fallback when suitable personalized matches are unavailable.

## Future Improvements

- Expand recommendation experiments and evaluation
- Improve recommendation personalization as more interaction data becomes available
- Explore additional recommendation algorithms
- Enhance explainability and recommendation quality

## Author

**Clarice Lopes**

GitHub: https://github.com/Clarice5

## Screenshots


### Reading Preference Quiz
![Preference Quiz](C:\Users\Rasika\django\Hello\Hello\ss\q1.png)
![Preference Quiz](C:\Users\Rasika\django\Hello\Hello\ss\q2.png)
![Preference Quiz](C:\Users\Rasika\django\Hello\Hello\ss\q3.png)


### Personalized Recommendations
![Recommendations](C:\Users\Rasika\django\Hello\Hello\ss\admin.png)
![Recommendations](Hello/ss/admin1.png)
![Recommendations](C:\Users\Rasika\django\Hello\Hello\ss\admin2.png)