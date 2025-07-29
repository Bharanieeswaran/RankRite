from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory, jsonify, session, Response
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from datetime import datetime, timedelta
import os
import secrets
import json
import logging
import re
from sqlalchemy.orm import joinedload # NEW: For eager loading in history route

# Import your configuration and database modules
from config import config
from database import db, User, Resume, JobDescription, ResumeAnalysis, init_db, get_user_stats
from resume_utils import ResumeProcessor, analyze_skill_trends, get_industry_insights

# Import for PDF/CSV generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import io

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on environment (defaulting to development)
app_config = config[os.environ.get('FLASK_ENV', 'default')]
app.config.from_object(app_config)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database
init_db(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Route for login page
login_manager.login_message_category = 'info' # Bootstrap class for flash messages

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database for Flask-Login."""
    return User.query.get(int(user_id))

# Create upload folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    """Checks if a file's extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize ResumeProcessor (can be done once globally or per request if stateful)
resume_processor = ResumeProcessor()

# --- Routes ---

@app.route('/')
@app.route('/index')
def index():
    """Renders the homepage."""
    return render_template('index.html', title='Welcome to RankRite')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        if not (username and email and password and confirm_password):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')

        new_user = User(username=username, email=email, first_name=first_name, last_name=last_name)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot_password')
def forgot_password():
    """Renders the forgot password page."""
    # This route would typically handle email-based password reset
    flash('Password reset functionality is not yet implemented. Please contact support.', 'warning')
    return render_template('forgot_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Renders the user dashboard."""
    user_stats = get_user_stats(current_user.id)
    return render_template('dashboard.html', title='Dashboard', user_stats=user_stats)


@app.route('/check', methods=['GET', 'POST'])
def check_resume():
    """
    Handles single resume analysis against a job description.
    Allows both authenticated and unauthenticated users.
    """
    analysis_results = None
    show_results = False

    if request.method == 'POST':
        jd_title = request.form.get('jd_title')
        job_description_content = request.form.get('job_description')

        if not job_description_content:
            flash('Job Description is required.', 'danger')
            return render_template('check.html', show_results=False)

        # Handle resume file upload
        if 'resume_file' not in request.files:
            flash('No resume file part', 'danger')
            return render_template('check.html', show_results=False)

        resume_file = request.files['resume_file']
        if resume_file.filename == '':
            flash('No selected resume file', 'danger')
            return render_template('check.html', show_results=False)

        if resume_file and allowed_file(resume_file.filename):
            original_filename = secure_filename(resume_file.filename)
            # Generate a unique filename to prevent overwrites
            unique_filename = f"{secrets.token_hex(8)}_{original_filename}"
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            try:
                resume_file.save(resume_path)
                logger.info(f"Resume saved to: {resume_path}")

                # Extract text from resume
                resume_text = resume_processor.extract_text_from_file(resume_path)
                if not resume_text:
                    flash('Could not extract text from the resume file. Please ensure it is a readable PDF or DOCX.', 'danger')
                    return render_template('check.html', show_results=False)

                # Extract features from resume
                resume_skills = resume_processor.extract_skills(resume_text)
                resume_experience_years = resume_processor.extract_experience(resume_text)
                resume_education = resume_processor.extract_education(resume_text)
                resume_contact_info = resume_processor.extract_contact_info(resume_text)

                # Calculate similarity scores and other analysis
                analysis_results = resume_processor.calculate_similarity_scores(
                    resume_text,
                    job_description_content,
                    resume_skills,
                    resume_experience_years,
                    resume_education
                )

                # Generate suggestions
                improvement_suggestions = resume_processor.generate_improvement_suggestions(analysis_results)
                skill_gap_suggestions = resume_processor.generate_skill_gap_suggestions(
                    analysis_results['missing_skills'], analysis_results['matched_skills']
                )

                # Store data in database if user is authenticated
                resume_db_obj = None
                job_desc_db_obj = None
                analysis_db_obj = None

                try:
                    # Save Job Description
                    # Check if a JD with the same content (and title if provided) already exists for this user
                    existing_jd = JobDescription.query.filter(
                        JobDescription.content == job_description_content,
                        JobDescription.created_by == (current_user.id if current_user.is_authenticated else None)
                    ).first()

                    if existing_jd:
                        job_desc_db_obj = existing_jd
                    else:
                        job_desc_db_obj = JobDescription(
                            title=jd_title if jd_title else "Unnamed Job Description",
                            content=job_description_content,
                            created_by=current_user.id if current_user.is_authenticated else None
                        )
                        job_desc_db_obj.set_skills_list(resume_processor.extract_skills(job_description_content))
                        db.session.add(job_desc_db_obj)
                        db.session.flush() # Assigns ID without committing yet

                    # Save Resume
                    resume_db_obj = Resume(
                        filename=unique_filename,
                        original_filename=original_filename,
                        file_path=resume_path, # Path to the permanently stored file
                        content=resume_text,
                        file_size=resume_file.content_length,
                        file_type=original_filename.rsplit('.', 1)[1].upper(),
                        experience_years=resume_experience_years
                    )
                    # Corrected: Assign user_id as an attribute after object creation
                    resume_db_obj.uploaded_by = current_user.id if current_user.is_authenticated else None # Use uploaded_by from Resume model
                    resume_db_obj.set_skills_list(resume_skills)
                    resume_db_obj.set_education_list(resume_education)
                    resume_db_obj.set_contact_info(resume_contact_info)
                    db.session.add(resume_db_obj)
                    db.session.flush() # Assigns ID without committing yet

                    # Save Analysis
                    analysis_db_obj = ResumeAnalysis(
                        resume_id=resume_db_obj.id,
                        job_description_id=job_desc_db_obj.id,
                        user_id=current_user.id if current_user.is_authenticated else None,
                        overall_score=analysis_results['overall_score'],
                        skills_score=analysis_results['skills_score'],
                        experience_score=analysis_results['experience_score'],
                        education_score=analysis_results['education_score'],
                        improvements="\n".join(improvement_suggestions),
                        skill_gap_suggestions="\n".join(skill_gap_suggestions)
                    )
                    analysis_db_obj.set_matched_skills(analysis_results['matched_skills'])
                    analysis_db_obj.set_missing_skills(analysis_results['missing_skills'])
                    db.session.add(analysis_db_obj)
                    db.session.commit()
                    flash('Resume analyzed and saved to history!', 'success')

                    # Pass all data to template for display
                    show_results = True
                    return render_template(
                        'check.html',
                        show_results=show_results,
                        resume_filename=original_filename,
                        job_description_content=job_description_content,
                        analysis=analysis_db_obj.to_dict(), # Use to_dict for easy template access
                        resume_details={
                            'skills': resume_skills,
                            'experience_years': resume_experience_years,
                            'education': resume_education,
                            'contact_info': resume_contact_info,
                            'content': resume_text # Full content for detailed view
                        },
                        job_skills=analysis_results['job_skills'],
                        jd_title=job_desc_db_obj.title,
                        analysis_id=analysis_db_obj.id
                    )

                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Database error during resume analysis storage: {e}")
                    flash(f'An error occurred while saving analysis: {e}', 'danger')
                    # Still show results if analysis was successful but saving failed
                    show_results = True
                    return render_template(
                        'check.html',
                        show_results=show_results,
                        resume_filename=original_filename,
                        job_description_content=job_description_content,
                        analysis={
                            'overall_score': analysis_results['overall_score'],
                            'skills_score': analysis_results['skills_score'],
                            'experience_score': analysis_results['experience_score'],
                            'education_score': analysis_results['education_score'],
                            'matched_skills': analysis_results['matched_skills'],
                            'missing_skills': analysis_results['missing_skills'],
                            'improvements': "\n".join(improvement_suggestions),
                            'skill_gap_suggestions': "\n".join(skill_gap_suggestions),
                            'rank_level': ResumeAnalysis(overall_score=analysis_results['overall_score']).rank_level,
                            'rank_color': ResumeAnalysis(overall_score=analysis_results['overall_score']).rank_color
                        },
                        resume_details={
                            'skills': resume_skills,
                            'experience_years': resume_experience_years,
                            'education': resume_education,
                            'contact_info': resume_contact_info,
                            'content': resume_text
                        },
                        job_skills=analysis_results['job_skills'],
                        jd_title=jd_title if jd_title else "Unnamed Job Description"
                    )
                finally:
                    # Removed os.remove(resume_path) here as per Scenario 1: Keep the file
                    logger.info(f"Resume file retained at: {resume_path}")

            except (RuntimeError, NotImplementedError, ValueError) as e:
                flash(f"File processing error: {e}", 'danger')
                return render_template('check.html', show_results=False)
            except Exception as e:
                flash(f"An unexpected error occurred during processing: {e}", 'danger')
                logger.error(f"Unexpected error in check_resume: {e}")
                return render_template('check.html', show_results=False)
        else:
            flash('Invalid resume file type. Allowed types are: PDF, DOCX, DOC.', 'danger')
            return render_template('check.html', show_results=False)

    return render_template('check.html', show_results=show_results)


@app.route('/compare', methods=['GET', 'POST'])
@login_required
def compare_resumes():
    """Handles comparison of two resumes against a single job description."""
    comparison_results = []
    show_results = False

    if request.method == 'POST':
        jd_title = request.form.get('jd_title', 'Unnamed Job Description')
        job_description_content = request.form.get('job_description')

        if not job_description_content:
            flash('Job Description is required for comparison.', 'danger')
            return render_template('compare.html', show_results=False)

        resume_files = []
        if 'resumeA' in request.files:
            resume_files.append(request.files['resumeA'])
        if 'resumeB' in request.files:
            resume_files.append(request.files['resumeB'])

        candidateA_name = request.form.get('candidateA', 'Resume A')
        candidateB_name = request.form.get('candidateB', 'Resume B')
        candidate_names = [candidateA_name, candidateB_name]


        if len(resume_files) < 2:
            flash('Please upload at least two resumes for comparison.', 'danger')
            return render_template('compare.html', show_results=False)

        processed_resumes_data = []
        uploaded_paths = [] # To keep track of files to delete

        for i, resume_file in enumerate(resume_files):
            if resume_file and allowed_file(resume_file.filename):
                original_filename = secure_filename(resume_file.filename)
                unique_filename = f"{secrets.token_hex(8)}_{original_filename}"
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                try:
                    resume_file.save(resume_path)
                    uploaded_paths.append(resume_path) # Keep track for potential deletion if not permanent

                    resume_text = resume_processor.extract_text_from_file(resume_path)
                    if not resume_text:
                        flash(f'Could not extract text from {original_filename}. Skipping.', 'warning')
                        continue # Skip this file and proceed with others

                    resume_skills = resume_processor.extract_skills(resume_text)
                    resume_experience_years = resume_processor.extract_experience(resume_text)
                    resume_education = resume_processor.extract_education(resume_text)
                    resume_contact_info = resume_processor.extract_contact_info(resume_text) # Extract contact info for Resume DB object

                    processed_resumes_data.append({
                        'id': i, # Temporary ID for sorting within this request
                        'filename': original_filename,
                        'unique_filename': unique_filename, # Pass unique filename
                        'file_path': resume_path, # Pass the path
                        'content': resume_text, # Pass full content
                        'file_size': resume_file.content_length,
                        'file_type': original_filename.rsplit('.', 1)[1].upper(),
                        'skills': resume_skills,
                        'experience': resume_experience_years,
                        'education': resume_education,
                        'contact_info': resume_contact_info,
                        'candidate_name': candidate_names[i] if i < len(candidate_names) else f"Candidate {i+1}"
                    })
                except (RuntimeError, NotImplementedError, ValueError) as e:
                    flash(f"Error processing {original_filename}: {e}. Skipping.", 'danger')
                except Exception as e:
                    flash(f"An unexpected error occurred with {original_filename}: {e}. Skipping.", 'danger')
            else:
                flash(f"Invalid file type for {resume_file.filename}. Allowed types are: PDF, DOCX, DOC. Skipping.", 'danger')

        if not processed_resumes_data:
            flash('No valid resumes were processed for comparison. Please check file types.', 'danger')
            return render_template('compare.html', show_results=False)

        # Perform ranking
        ranked_resumes = resume_processor.rank_multiple_resumes(processed_resumes_data, job_description_content)

        # Store Job Description (if not already existing)
        job_desc_db_obj = JobDescription.query.filter(
            JobDescription.content == job_description_content,
            JobDescription.created_by == current_user.id
        ).first()

        if not job_desc_db_obj:
            job_desc_db_obj = JobDescription(
                title=jd_title,
                content=job_description_content,
                created_by=current_user.id
            )
            job_desc_db_obj.set_skills_list(resume_processor.extract_skills(job_description_content))
            db.session.add(job_desc_db_obj)
            db.session.flush() # Get ID before commit

        # Prepare results for display and save each analysis
        candidate_A_analysis = None
        candidate_B_analysis = None

        for i, ranked_resume in enumerate(ranked_resumes):
            original_data = next(item for item in processed_resumes_data if item['id'] == ranked_resume['resume_id'])

            # Save Resume to DB
            existing_resume = Resume.query.filter(
                Resume.filename == original_data['unique_filename'], # Check by unique filename
                Resume.uploaded_by == current_user.id
            ).first()

            if existing_resume:
                resume_db_obj = existing_resume
            else:
                resume_db_obj = Resume(
                    filename=original_data['unique_filename'],
                    original_filename=original_data['filename'],
                    file_path=original_data['file_path'],
                    content=original_data['content'],
                    file_size=original_data['file_size'],
                    file_type=original_data['file_type'],
                    experience_years=original_data['experience']
                )
                resume_db_obj.uploaded_by = current_user.id if current_user.is_authenticated else None
                resume_db_obj.set_skills_list(original_data['skills'])
                resume_db_obj.set_education_list(original_data['education'])
                resume_db_obj.set_contact_info(original_data['contact_info'])
                db.session.add(resume_db_obj)
                db.session.flush()

            analysis_db_obj = ResumeAnalysis(
                resume_id=resume_db_obj.id,
                job_description_id=job_desc_db_obj.id,
                user_id=current_user.id,
                overall_score=ranked_resume['analysis']['overall_score'],
                skills_score=ranked_resume['analysis']['skills_score'],
                experience_score=ranked_resume['analysis']['experience_score'],
                education_score=ranked_resume['analysis']['education_score'],
                improvements="\n".join(resume_processor.generate_improvement_suggestions(ranked_resume['analysis'])),
                skill_gap_suggestions="\n".join(resume_processor.generate_skill_gap_suggestions(ranked_resume['analysis']['missing_skills'], ranked_resume['analysis']['matched_skills']))
            )
            analysis_db_obj.set_matched_skills(ranked_resume['analysis']['matched_skills'])
            analysis_db_obj.set_missing_skills(ranked_resume['analysis']['missing_skills'])
            db.session.add(analysis_db_obj)

            # Assign to candidate A or B for display
            display_data = {
                'name': original_data['candidate_name'],
                'overall_score': round(ranked_resume['analysis']['overall_score'] * 100, 1), # Scale to 0-100
                'breakdown': {
                    'skills': round(ranked_resume['analysis']['skills_score'] * 100, 1),
                    'experience': round(ranked_resume['analysis']['experience_score'] * 100, 1),
                    'education': round(ranked_resume['analysis']['education_score'] * 100, 1)
                },
                'strengths': resume_processor.generate_improvement_suggestions(ranked_resume['analysis']), # Re-use for strengths
                'weaknesses': resume_processor.generate_skill_gap_suggestions(ranked_resume['analysis']['missing_skills'], ranked_resume['analysis']['matched_skills'])
            }

            if i == 0: # Assuming first file is Resume A
                candidate_A_analysis = display_data
            elif i == 1: # Assuming second file is Resume B
                candidate_B_analysis = display_data

        try:
            db.session.commit()
            flash('Resumes compared and analysis saved to history!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during comparison analysis storage: {e}")
            flash(f'An error occurred while saving comparison analysis: {e}', 'danger')

        logger.info(f"Comparison resume files retained.")

        # Return JSON response for frontend to update dynamically
        return jsonify({
            'success': True,
            'results': {
                'candidateA': candidate_A_analysis,
                'candidateB': candidate_B_analysis,
                'job_description_content': job_description_content,
                'jd_title': jd_title
            }
        })

    return render_template('compare.html', show_results=show_results)


@app.route('/multiple', methods=['GET', 'POST'])
@login_required
def multiple_resumes():
    """Handles analysis and ranking of multiple resumes."""
    ranked_results = []
    show_results = False

    if request.method == 'POST':
        jd_title = request.form.get('job_title', 'Unnamed Job Description')
        job_description_content = request.form.get('job_description')

        if not job_description_content:
            flash('Job Description is required.', 'danger')
            return render_template('multiple_resume.html', show_results=False)

        resume_files = request.files.getlist('resume_files[]')
        if not resume_files or resume_files[0].filename == '':
            flash('No resumes selected for upload.', 'danger')
            return render_template('multiple_resume.html', show_results=False)

        processed_resumes_data = []
        uploaded_paths = []

        for i, resume_file in enumerate(resume_files):
            if resume_file and allowed_file(resume_file.filename):
                original_filename = secure_filename(resume_file.filename)
                unique_filename = f"{secrets.token_hex(8)}_{original_filename}"
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                try:
                    resume_file.save(resume_path)
                    uploaded_paths.append(resume_path)

                    resume_text = resume_processor.extract_text_from_file(resume_path)
                    if not resume_text:
                        flash(f'Could not extract text from {original_filename}. Skipping.', 'warning')
                        continue

                    resume_skills = resume_processor.extract_skills(resume_text)
                    resume_experience_years = resume_processor.extract_experience(resume_text)
                    resume_education = resume_processor.extract_education(resume_text)
                    resume_contact_info = resume_processor.extract_contact_info(resume_text)

                    processed_resumes_data.append({
                        'id': i,
                        'filename': original_filename,
                        'unique_filename': unique_filename,
                        'file_path': resume_path,
                        'content': resume_text,
                        'file_size': resume_file.content_length,
                        'file_type': original_filename.rsplit('.', 1)[1].upper(),
                        'skills': resume_skills,
                        'experience': resume_experience_years,
                        'education': resume_education,
                        'contact_info': resume_contact_info
                    })
                except (RuntimeError, NotImplementedError, ValueError) as e:
                    flash(f"Error processing {original_filename}: {e}. Skipping.", 'danger')
                except Exception as e:
                    flash(f"An unexpected error occurred with {original_filename}: {e}. Skipping.", 'danger')
            else:
                flash(f"Invalid file type for {resume_file.filename}. Allowed types are: PDF, DOCX, DOC. Skipping.", 'danger')

        if not processed_resumes_data:
            flash('No valid resumes were processed. Please check file types.', 'danger')
            return render_template('multiple_resume.html', show_results=False)

        # Perform ranking
        ranked_resumes_analysis = resume_processor.rank_multiple_resumes(processed_resumes_data, job_description_content)

        # Store Job Description (if not already existing)
        job_desc_db_obj = JobDescription.query.filter(
            JobDescription.content == job_description_content,
            JobDescription.created_by == current_user.id
        ).first()

        if not job_desc_db_obj:
            job_desc_db_obj = JobDescription(
                title=jd_title,
                content=job_description_content,
                created_by=current_user.id
            )
            job_desc_db_obj.set_skills_list(resume_processor.extract_skills(job_description_content))
            db.session.add(job_desc_db_obj)
            db.session.flush()

        # Save each resume and its analysis to the database
        for ranked_resume in ranked_resumes_analysis:
            original_data = next(item for item in processed_resumes_data if item['id'] == ranked_resume['resume_id'])

            # Save Resume to DB
            existing_resume = Resume.query.filter(
                Resume.filename == original_data['unique_filename'],
                Resume.uploaded_by == current_user.id
            ).first()

            if existing_resume:
                resume_db_obj = existing_resume
            else:
                resume_db_obj = Resume(
                    filename=original_data['unique_filename'],
                    original_filename=original_data['filename'],
                    file_path=original_data['file_path'],
                    content=original_data['content'],
                    file_size=original_data['file_size'],
                    file_type=original_data['file_type'],
                    experience_years=original_data['experience']
                )
                resume_db_obj.uploaded_by = current_user.id
                resume_db_obj.set_skills_list(original_data['skills'])
                resume_db_obj.set_education_list(original_data['education'])
                resume_db_obj.set_contact_info(original_data['contact_info'])
                db.session.add(resume_db_obj)
                db.session.flush()

            analysis_db_obj = ResumeAnalysis(
                resume_id=resume_db_obj.id,
                job_description_id=job_desc_db_obj.id,
                user_id=current_user.id,
                overall_score=ranked_resume['analysis']['overall_score'],
                skills_score=ranked_resume['analysis']['skills_score'],
                experience_score=ranked_resume['analysis']['experience_score'],
                education_score=ranked_resume['analysis']['education_score'],
                improvements="\n".join(resume_processor.generate_improvement_suggestions(ranked_resume['analysis'])),
                skill_gap_suggestions="\n".join(resume_processor.generate_skill_gap_suggestions(ranked_resume['analysis']['missing_skills'], ranked_resume['analysis']['matched_skills']))
            )
            analysis_db_obj.set_matched_skills(ranked_resume['analysis']['matched_skills'])
            analysis_db_obj.set_missing_skills(ranked_resume['analysis']['missing_skills'])
            db.session.add(analysis_db_obj)

            ranked_results.append({
                'filename': original_data['filename'],
                'overall_score': round(ranked_resume['analysis']['overall_score'] * 100, 1),
                'rank_level': ResumeAnalysis(overall_score=ranked_resume['analysis']['overall_score']).rank_level,
                'rank_color': ResumeAnalysis(overall_score=ranked_resume['analysis']['overall_score']).rank_color,
                'skills_score': round(ranked_resume['analysis']['skills_score'] * 100, 1),
                'experience_score': round(ranked_resume['analysis']['experience_score'] * 100, 1),
                'education_score': round(ranked_resume['analysis']['education_score'] * 100, 1),
                'matched_skills': ranked_resume['analysis']['matched_skills'],
                'missing_skills': ranked_resume['analysis']['missing_skills'],
                'improvements': resume_processor.generate_improvement_suggestions(ranked_resume['analysis']),
                'skill_gap_suggestions': resume_processor.generate_skill_gap_suggestions(ranked_resume['analysis']['missing_skills'], ranked_resume['analysis']['matched_skills'])
            })

        try:
            db.session.commit()
            flash('Multiple resumes analyzed and ranked successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during multiple resume analysis storage: {e}")
            flash(f'An error occurred while saving analysis: {e}', 'danger')

        logger.info(f"Multiple resume files retained.")
        show_results = True
        return render_template(
            'multiple_resume.html',
            show_results=show_results,
            job_description_content=job_description_content,
            jd_title=job_desc_db_obj.title,
            ranked_results=ranked_results
        )

    return render_template('multiple_resume.html', show_results=show_results)

@app.route('/history')
@login_required
def history():
    """Renders the user's analysis history."""
    # Eager load Resume and JobDescription to avoid N+1 queries
    analyses = ResumeAnalysis.query.options(
        joinedload(ResumeAnalysis.resume),
        joinedload(ResumeAnalysis.job_description)
    ).filter_by(user_id=current_user.id).order_by(ResumeAnalysis.timestamp.desc()).all()

    return render_template('history.html', title='Analysis History', analyses=analyses)

@app.route('/analysis/<int:analysis_id>')
@login_required
def view_analysis(analysis_id):
    """Displays a detailed view of a specific analysis."""
    analysis = ResumeAnalysis.query.options(
        joinedload(ResumeAnalysis.resume),
        joinedload(ResumeAnalysis.job_description)
    ).get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        flash('You do not have permission to view this analysis.', 'danger')
        return redirect(url_for('history'))

    # Re-process text content if needed, or rely on stored parsed data
    # For simplicity, we'll use the data stored in the database objects
    resume_details = {
        'filename': analysis.resume.original_filename,
        'content': analysis.resume.content,
        'skills': analysis.resume.get_skills_list(),
        'experience_years': analysis.resume.experience_years,
        'education': analysis.resume.get_education_list(),
        'contact_info': analysis.resume.get_contact_info()
    }
    job_details = {
        'title': analysis.job_description.title,
        'content': analysis.job_description.content,
        'skills': analysis.job_description.get_skills_list()
    }

    return render_template(
        'check.html', # Re-use check.html for detailed single analysis view
        show_results=True,
        analysis=analysis.to_dict(),
        resume_details=resume_details,
        job_description_content=job_details['content'],
        jd_title=job_details['title'],
        job_skills=job_details['skills'],
        analysis_id=analysis.id,
        from_history=True # To differentiate template behavior if needed
    )

@app.route('/delete_analysis/<int:analysis_id>', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """Deletes a specific analysis from history."""
    analysis = ResumeAnalysis.query.get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        flash('You do not have permission to delete this analysis.', 'danger')
        return redirect(url_for('history'))

    try:
        # Note: We are not deleting the associated resume or job description files/entries
        # unless they are no longer linked to any other analyses or users.
        # For this setup, we're only deleting the analysis record itself.
        db.session.delete(analysis)
        db.session.commit()
        flash('Analysis deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        flash('An error occurred while deleting the analysis.', 'danger')

    return redirect(url_for('history'))

@app.route('/tips')
def tips():
    """Renders the tips page."""
    return render_template('tips.html', title='Resume Tips')

@app.route('/trends')
def trends():
    """Renders the trends page with skill and industry insights."""
    try:
        all_job_descriptions = [jd.content for jd in JobDescription.query.all()]
        skill_trends = analyze_skill_trends(all_job_descriptions)
        industry_insights = get_industry_insights(all_job_descriptions)
    except Exception as e:
        logger.error(f"Error generating trends: {e}")
        skill_trends = {}
        industry_insights = {}
        flash('Could not load trends data at this time.', 'warning')

    return render_template('trends.html', title='Trends & Insights', skill_trends=skill_trends, industry_insights=industry_insights)

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template('about.html', title='About RankRite')

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serves uploaded resume files (for authenticated users only)."""
    # This checks if the user is logged in, but not if they are the original uploader.
    # For production, you might want to add a check that the filename is associated
    # with an analysis record belonging to the current_user to prevent access to
    # other users' uploaded files.
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        flash('File not found.', 'danger')
        return redirect(url_for('history')) # Or a 404 page

@app.route('/download_report/<int:analysis_id>/<report_type>')
@login_required
def download_report(analysis_id, report_type):
    """Generates and downloads a PDF or CSV report for a given analysis."""
    analysis = ResumeAnalysis.query.options(
        joinedload(ResumeAnalysis.resume),
        joinedload(ResumeAnalysis.job_description)
    ).get_or_404(analysis_id)

    if analysis.user_id != current_user.id:
        flash('You do not have permission to generate a report for this analysis.', 'danger')
        return redirect(url_for('history'))

    # Helper function to format content for reports
    def format_list_for_report(data_list):
        if isinstance(data_list, str):
            try:
                # Attempt to load as JSON list
                parsed_list = json.loads(data_list)
                if isinstance(parsed_list, list):
                    return ', '.join(parsed_list)
                else:
                    return data_list # Not a list in JSON, return as is
            except json.JSONDecodeError:
                return data_list # Not JSON, return as is
        elif isinstance(data_list, list):
            return ', '.join(data_list)
        return str(data_list)

    if report_type == 'pdf':
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, height - 50, f"Resume Analysis Report for {analysis.resume.original_filename}")

        p.setFont("Helvetica", 10)
        y_position = height - 80

        def draw_text(text, x, y, font_size=10, bold=False):
            p.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
            p.drawString(x, y, text)
            return y - font_size - 5 # Return next y position

        y_position = draw_text("Analysis Details:", 50, y_position, 12, True)
        y_position = draw_text(f"Overall Score: {analysis.overall_score:.2f} (Rank: {analysis.rank_level})", 60, y_position)
        y_position = draw_text(f"Skills Score: {analysis.skills_score:.2f}", 60, y_position)
        y_position = draw_text(f"Experience Score: {analysis.experience_score:.2f}", 60, y_position)
        y_position = draw_text(f"Education Score: {analysis.education_score:.2f}", 60, y_position)
        y_position -= 10

        y_position = draw_text("Job Description:", 50, y_position, 12, True)
        y_position = draw_text(f"Title: {analysis.job_description.title}", 60, y_position)
        y_position = draw_text(f"Content: {analysis.job_description.content[:200]}...", 60, y_position) # Truncate for report
        y_position = draw_text(f"Required Skills: {format_list_for_report(analysis.job_description.get_skills_list())}", 60, y_position)
        y_position -= 10

        y_position = draw_text("Resume Details:", 50, y_position, 12, True)
        y_position = draw_text(f"Filename: {analysis.resume.original_filename}", 60, y_position)
        y_position = draw_text(f"Uploaded On: {analysis.resume.uploaded_on.strftime('%Y-%m-%d %H:%M')}", 60, y_position)
        y_position = draw_text(f"Experience: {analysis.resume.experience_years} years", 60, y_position)
        y_position = draw_text(f"Skills: {format_list_for_report(analysis.resume.get_skills_list())}", 60, y_position)
        y_position = draw_text(f"Education: {format_list_for_report(analysis.resume.get_education_list())}", 60, y_position)
        y_position -= 10

        y_position = draw_text("Matched Skills:", 50, y_position, 12, True)
        y_position = draw_text(format_list_for_report(analysis.get_matched_skills()), 60, y_position)
        y_position -= 10

        y_position = draw_text("Missing Skills:", 50, y_position, 12, True)
        y_position = draw_text(format_list_for_report(analysis.get_missing_skills()), 60, y_position)
        y_position -= 10

        y_position = draw_text("Improvement Suggestions:", 50, y_position, 12, True)
        for line in analysis.improvements.split('\n'):
            if y_position < 50: # Check for page overflow
                p.showPage()
                y_position = height - 50
                p.setFont("Helvetica", 10)
            y_position = draw_text(line, 60, y_position)
        y_position -= 10

        y_position = draw_text("Skill Gap Suggestions:", 50, y_position, 12, True)
        for line in analysis.skill_gap_suggestions.split('\n'):
            if y_position < 50: # Check for page overflow
                p.showPage()
                y_position = height - 50
                p.setFont("Helvetica", 10)
            y_position = draw_text(line, 60, y_position)
        y_position -= 10

        p.showPage()
        p.save()

        buffer.seek(0)
        filename = f"analysis_report_{analysis_id}.pdf"
        return Response(buffer.getvalue(),
                        mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment;filename={filename}'})

    elif report_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['Report Type', 'Resume Filename', 'Job Title', 'Overall Score',
                         'Skills Score', 'Experience Score', 'Education Score',
                         'Matched Skills', 'Missing Skills', 'Improvement Suggestions',
                         'Skill Gap Suggestions', 'Uploaded On'])

        writer.writerow([
            'Single Analysis',
            analysis.resume.original_filename,
            analysis.job_description.title,
            f"{analysis.overall_score:.2f}",
            f"{analysis.skills_score:.2f}",
            f"{analysis.experience_score:.2f}",
            f"{analysis.education_score:.2f}",
            format_list_for_report(analysis.get_matched_skills()),
            format_list_for_report(analysis.get_missing_skills()),
            analysis.improvements.replace('\n', ' | '), # Flatten for CSV
            analysis.skill_gap_suggestions.replace('\n', ' | '), # Flatten for CSV
            analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])

        output.seek(0)
        filename = f"analysis_report_{analysis_id}.csv"
        return Response(output.getvalue(),
                        mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment;filename={filename}'})

    else:
        flash('Invalid report type.', 'danger')
        return redirect(url_for('view_analysis', analysis_id=analysis_id))

@app.errorhandler(401)
def unauthorized(error):
    flash('Please log in to access this page.', 'info')
    return redirect(url_for('login', next=request.path))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    # When running locally, set FLASK_ENV to 'development'
    # This will load DevelopmentConfig from config.py
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug=True)