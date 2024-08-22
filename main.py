from collections import deque
from datetime import datetime
from functools import wraps
import os
import http.client
import json
from flask import Flask, request, jsonify, render_template, g
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ollama
from flask_cors import CORS
from flask import redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import uuid
from dotenv import load_dotenv
from models import db, UserLogin, ActiveQueue
import pytz
import threading


# Load environment variables from cred.env file
load_dotenv('cred.env')

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
CORS(app)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Load sensitive information from environment variables
SERPER_API_KEY = os.getenv('SERPER_API_KEY', 'a39926ec01e9bbc12beeab8cfbc4927dc856a03e')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:instruct')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_text(text):
    lines = text.splitlines()
    cleaned_lines = [line for line in lines if line.strip() and not line.startswith('%')]
    return '\n'.join(cleaned_lines)

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        text = str(e)
    return text

def extract_text_from_image(image_file):
    text = ""
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        text = str(e)
    return text

def extract_text(file_path):
    if file_path.lower().endswith('.pdf'):
        with open(file_path, 'rb') as f:
            return extract_text_from_pdf(f)
    elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        return extract_text_from_image(file_path)
    return "Unsupported file format."

def serper_search(query):
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def ollama_analyze(prompt):
    try:
        # Ensure that the prompt includes the latest data and is formatted correctly
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception as e:
        return {"error": str(e)}



def fetch_example_resumes(job_title):
    try:
        query = f"expert {job_title} resume examples global"
        search_results = serper_search(query)
        if 'error' in search_results:
            return {"error": search_results['error']}
        
        examples = search_results.get('organic', [])
        return [result.get('snippet', '') for result in examples[:5]]  
    except Exception as e:
        return {"error": str(e)}

def generate_embeddings(texts):
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(texts)
    return embeddings, vectorizer

def get_potential_companies(job_title, location="India"):
    try:
        query = f"top companies hiring {job_title} in {location}"
        search_results = serper_search(query)
        if 'error' in search_results:
            return {"error": search_results['error']}
        
        companies = search_results.get('organic', [])
        return [result.get('title', '').split('-')[0].strip() for result in companies[:10]]
    except Exception as e:
        return {"error": str(e)}

# Initialize the queue
app.app_context().push()
g.queue = deque()
g.queue_lock = threading.Lock()

# Configure OAuth
oauth = OAuth(app)

# Register Google OAuth
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
    redirect_url='http://biai.techtantra.tech/auth'
)

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login')
def login():
    google_client = oauth.create_client('google')
    nonce = str(uuid.uuid4())
    session['nonce'] = nonce
    redirect_uri = url_for('auth', _external=True)
    return google_client.authorize_redirect(redirect_uri, nonce=nonce)

# Authentication route
@app.route('/auth')
def auth():
    try:
        google_client = oauth.create_client('google')
        token = google_client.authorize_access_token()
        nonce = session.pop('nonce', None)
        user_info = google_client.parse_id_token(token, nonce=nonce)

        # Save user info in session
        session['user'] = {
            'id': user_info['sub'],
            'name': user_info['name'],
            'email': user_info['email'],
            'picture': user_info['picture'],
        }
        local_tz = pytz.timezone('Asia/Kolkata')  # Replace with your server's time zone
        local_time = datetime.now(local_tz)
        # Log the user's login in the database
        existing_user = UserLogin.query.filter_by(email=user_info['email']).first()
        if existing_user:
            existing_user.login_time = local_time
        else:
            new_user = UserLogin(
                email=user_info['email'],
                name=user_info['name'],
                login_time=datetime.utcnow()
            )
            db.session.add(new_user)
        
        db.session.commit()
        return redirect('/')
    except Exception as e:
        app.logger.error(f'Exception on /auth [GET]: {e}')
        return jsonify({'error': str(e)}), 500


# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    return f"Hello, {user['name']}!"

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/')
def home():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/analyze_resume', methods=['POST'])
@login_required
def analyze_resume():
    user_email = session['user']['email']

    def process_request():
        user = UserLogin.query.filter_by(email=user_email).first()

        # Check if the user has performed 2 analyses in the current month
        current_month = datetime.now().month
        if user.last_resume_analysis and user.last_resume_analysis.month == current_month:
            if user.resume_analysis_count >= 2:
                return jsonify({'error': 'You have reached the limit of 2 resume analyses for this month.'})

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            resume_text = clean_text(extract_text(file_path))
            job_title = request.form.get('job_title')

            if not resume_text:
                return jsonify({'error': 'Failed to extract text from resume'})

            # Fetch job market data for India and globally
            india_job_market_data = serper_search(f"{job_title} job requirements India")
            global_job_market_data = serper_search(f"{job_title} job requirements global")

            if 'error' in india_job_market_data or 'error' in global_job_market_data:
                return jsonify({'error': 'Failed to fetch job market data'})

            india_organic_results = india_job_market_data.get('organic', [])
            global_organic_results = global_job_market_data.get('organic', [])

            india_job_requirements = "\n".join([result.get('snippet', '') for result in india_organic_results[:3]])
            global_job_requirements = "\n".join([result.get('snippet', '') for result in global_organic_results[:3]])

            example_resumes = fetch_example_resumes(job_title)

            if 'error' in example_resumes:
                return jsonify({'error': example_resumes['error']})

            documents = [resume_text, india_job_requirements, global_job_requirements] + example_resumes
            embeddings, vectorizer = generate_embeddings(documents)

            resume_embedding = embeddings[0]
            india_market_embedding = embeddings[1]
            global_market_embedding = embeddings[2]
            example_embeddings = embeddings[3:]

            india_market_similarity = cosine_similarity(resume_embedding, india_market_embedding)[0][0]
            global_market_similarity = cosine_similarity(resume_embedding, global_market_embedding)[0][0]
            example_similarity = cosine_similarity(resume_embedding, example_embeddings).mean()

            potential_companies_india = get_potential_companies(job_title, "India")
            potential_companies_global = get_potential_companies(job_title, "global")

            analysis_prompt = f"""
            Analyze the following resume for a {job_title} position, considering both Indian and global job markets:

            Resume:
            {resume_text}

            Indian job market requirements:
            {india_job_requirements}

            Global job market requirements:
            {global_job_requirements}

            Example resumes:
            {''.join([resume for resume in example_resumes])}

            Resume Similarity to Indian Job Market Requirements: {india_market_similarity:.2f}
            Resume Similarity to Global Job Market Requirements: {global_market_similarity:.2f}
            Resume Similarity to Example Resumes: {example_similarity:.2f}

            Please provide a detailed analysis of the resume based on these similarities and suggest improvements. 
            Consider both Indian and global job markets, with a primary focus on India. 
            Provide a score out of 100, list strengths and areas for improvement, and suggest keywords to include.
            Also, provide a tailored summary and full analysis.
            """

            ai_analysis = ollama_analyze(analysis_prompt)

            if 'error' in ai_analysis:
                return jsonify({'error': ai_analysis['error']})

            # Update user analysis count and last analysis time
            user.resume_analysis_count += 1
            user.last_resume_analysis = datetime.now()
            db.session.commit()



            return jsonify({
                'india_job_market_similarity': india_market_similarity,
                'global_job_market_similarity': global_market_similarity,
                'example_similarity': example_similarity,
                'full_analysis': ai_analysis,
                'potential_companies_india': potential_companies_india,
                'potential_companies_global': potential_companies_global
            })

        else:
            return jsonify({'error': 'Unsupported file type'})

    # Process the request
    response = process_request()

    return response



if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Create the database tables within the application context
    with app.app_context():
        db.create_all()
    
    # For production, use Gunicorn or another WSGI server
    app.run(debug=False, port=5124)