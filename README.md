# Django Blog Application

A feature-rich blog application built with Django that supports multiple authors, blog posts, and comments.

## Features

- Blog post listing with pagination
- Author profiles and posts
- Comment system for authenticated users
- Django admin integration
- User authentication

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the blog.
Visit http://127.0.0.1:8000/admin/ to access the admin interface. 