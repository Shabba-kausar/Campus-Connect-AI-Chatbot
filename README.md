# College AI Chatbot

An intelligent chatbot system designed to provide information about college-related queries using Django, Natural Language Processing, and OpenAI.

## Features

### 1. Intelligent Response System
- Multi-layered response generation using:
  - Quick reply handlers for common queries
  - Category-based matching
  - Keyword matching
  - Semantic search + vector retrieval (FAISS or local embeddings)
  - OpenAI ChatCompletion for enhanced responses and summarization
  - Fallback responses

### 2. Information Categories
The chatbot provides information about:
- College Facilities
- Course Information
- Class Timetables
- Exam Schedules
- Campus Events
- Student Clubs
- Library Hours
- Admission Process
- Faculty Information
- Contact Information

### 3. Interactive Interface
- Clean and responsive chat interface
- Quick reply buttons for common queries
- Real-time message updates
- User session management
- Message history tracking

### 4. AI Integration
- Integrated with OpenAI for enhanced responses (ChatCompletion + Embeddings)
- Natural Language Processing for query understanding
- Semantic similarity matching
- Context-aware responses

## Technical Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **AI/ML**:
  - OpenAI (ChatCompletion for generation, OpenAI or sentence-transformers for embeddings)
  - scikit-learn for NLP
  - TF-IDF Vectorization
  - Cosine Similarity

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
cd collage-AI-chatbot
```

2. Create and activate a virtual environment:
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

# College AI Chatbot

An intelligent chatbot system designed to provide information about college-related queries using Django and OpenAI.

## Features

1. Intelligent Response System
- Multi-layered response generation using:
  - Quick reply handlers for common queries
  - Category-based matching
  - Keyword matching
  - Semantic search + vector retrieval (FAISS or local embeddings)
  - OpenAI for enhanced responses (LLM generation + embeddings)
  - Fallback responses

2. Information Categories
The chatbot provides information about:
- College Facilities
- Course Information
- Class Timetables
- Exam Schedules
- Campus Events
- Student Clubs
- Library Hours
- Admission Process
- Faculty Information
- Contact Information

3. Interactive Interface
- Clean and responsive chat interface
- Quick reply buttons for common queries
- Real-time message updates
- User session management
- Message history tracking

4. AI Integration
- Integrated with OpenAI for enhanced responses
- Natural Language Processing for query understanding
- Semantic similarity matching
- Context-aware responses

## Technical Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **AI/ML**:
  - OpenAI (LLM generation and embeddings)
  - sentence-transformers for fallback embeddings
  - scikit-learn for NLP
  - TF-IDF Vectorization
  - Cosine Similarity

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
cd collage-AI-chatbot
```

2. Create and activate a virtual environment:
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env` and replace placeholders with your secrets.
- Required:
```
OPENAI_API_KEY=your_openai_api_key_here
```

5. Initialize the database:
```powershell
python manage.py migrate
# optional: python manage.py populate_data
```

6. Run the development server:
```powershell
python manage.py runserver
```

7. Access the chatbot at: `http://localhost:8000`

## Usage

1. **Quick Replies**: Click on the suggested quick reply buttons for common queries
2. **Custom Questions**: Type your questions in natural language
3. **Follow-up Questions**: The chatbot will suggest related topics you can ask about
4. **Detailed Information**: Ask for specific details about any topic

## Project Structure

```
collage-AI-chatbot/
├── bot/                    # Main application directory
│   ├── management/        # Custom management commands
│   ├── migrations/        # Database migrations
│   ├── models.py         # Database models
│   ├── views.py          # View logic and response generation
│   ├── urls.py           # URL routing
│   └── openai_helper.py  # OpenAI integration helper
├── static/                # Static files
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/             # HTML templates
├── manage.py             # Django management script
└── requirements.txt      # Project dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for enhanced response generation
- Django framework
- scikit-learn for NLP capabilities
- Contributors and maintainers