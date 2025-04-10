# AFFAIR - Dating Website

AFFAIR is a modern dating platform designed to help users find meaningful connections. This application provides a seamless experience for users to create profiles, browse potential matches, engage in real-time conversations, and build relationships.

## Features

- **User Authentication**: Secure signup and login functionality.
- **Profile Management**: Create and customize your profile with personal details, photos, and interests.
- **Matching System**: Discover potential matches and express interest through likes.
- **Real-time Chat**: Communicate with matches through a real-time messaging system.
- **Match Management**: View and manage your matches easily.

## Tech Stack

- **Backend**: Django (Python web framework)
- **Frontend**: HTML, CSS, JavaScript, TailwindCSS
- **Real-time Communication**: Django Channels (WebSockets)
- **Database**: SQLite (development), PostgreSQL (recommended for production)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/affair-dating-website.git
   cd affair-dating-website
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # For Windows
   venv\Scripts\activate
   # For macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser for admin access:
   ```
   python manage.py createsuperuser
   ```

6. Add initial interest categories (optional):
   ```
   python add_interests.py
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Visit `http://127.0.0.1:8000` in your browser to access the application.

## Project Structure

- **app/**: Main application directory with models, views, and templates
- **dating_site/**: Project settings and configuration
- **templates/**: HTML templates
- **static/**: Static files (CSS, JavaScript, images)
- **media/**: User-uploaded files (profile pictures, etc.)

## Deployment

For production deployment, consider the following steps:

1. Set `DEBUG = False` in settings.py
2. Configure a production database (PostgreSQL recommended)
3. Set up static file serving (e.g., AWS S3, DigitalOcean Spaces)
4. Use a production-ready web server (Gunicorn, uWSGI)
5. Set up HTTPS with a valid SSL certificate
6. Configure environment variables for sensitive settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 