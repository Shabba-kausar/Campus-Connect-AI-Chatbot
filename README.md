# JEC AI Chatbot

An intelligent AI-powered chatbot for Jorhat Engineering College designed to assist students with college-related queries.

## Features

- **Interactive Q&A**: Provides real-time answers to student questions
- **AI-Powered**: Uses Natural Language Processing to understand and respond to queries
- **Topics Covered**:
  - Admission procedures
  - Exam schedules
  - College festivals
  - Clubs and societies
  - Canteen information
  - Hostel details
  - Faculty information
  - Placement details
  - Library resources
  - Campus facilities
- **Personalized Experience**: Remembers users across sessions
- **Beautiful UI**: Modern, responsive interface with animations
- **24/7 Availability**: Always accessible to answer questions

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript, jQuery
- **Backend**: Python, Django
- **AI/NLP**: scikit-learn, TF-IDF, Cosine Similarity
- **Database**: SQLite (default), can be configured for PostgreSQL/MySQL

## Installation Instructions

### Prerequisites

- Python 3.8+ installed
- Git (optional, for cloning)
- pip (Python package manager)

### Step 1:  Download the Repository

```bash
Extract project Zip file
# or download and extract the ZIP file
cd JECAiBot
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Packages

```bash
pip install -r requirements.txt
# If requirements.txt is not available, run:
pip install django scikit-learn numpy
```

### Step 4: Configure Database

The project uses SQLite by default. No additional configuration is needed unless you want to use a different database.

### Step 5: Migrate Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Populate Initial Data

```bash
python manage.py populate_data
```

### Step 7: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 8: Create a Superuser (Optional, for Admin Access)

```bash
python manage.py createsuperuser
# Follow the prompts to create an admin account
```

## Running the Application

```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Usage

1. Open your web browser and navigate to http://127.0.0.1:8000/
2. Click on the chat bubble in the bottom right corner to open the chatbot
3. For first-time users, the chatbot will ask for your name and phone number
4. Type your question in the input field and press Enter or click the send button
5. The AI will process your question and provide a relevant answer

## Accessing the Admin Panel

1. Navigate to http://127.0.0.1:8000/admin/
2. Log in with the superuser credentials you created
3. Here you can manage categories, college data, conversations, and messages

## Customization

### Adding More Questions and Answers

1. Log in to the admin panel
2. Navigate to "College Data"
3. Click "Add College Data"
4. Select a category, add a question, answer, and relevant keywords
5. Save the entry

### Modifying the UI

- CSS styles are located in `static/css/chatbot.css`
- JavaScript functionality is in `static/js/chatbot.js`
- HTML template is in `templates/index.html`

## Deployment

For production deployment:

1. Set `DEBUG = False` in `JECAiBot/settings.py`
2. Configure a production-ready database like PostgreSQL
3. Use a WSGI server like Gunicorn
4. Set up a reverse proxy with Nginx or Apache
5. Configure static file serving through your web server

## License

[Include license information here]

## Contributors

[List contributors here]

## Contact

For any queries, please contact [Your Email Address] 