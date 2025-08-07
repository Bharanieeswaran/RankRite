
# database.py

"""
Database models and utilities for RankRite Resume Ranker
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    resume_analyses = db.relationship('ResumeAnalysis', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.get_full_name(),
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.username}>'

class JobDescription(db.Model):
    """Job description model"""
    __tablename__ = 'job_descriptions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.Text, nullable=True)  # JSON string
    experience_required = db.Column(db.String(50), nullable=True)
    education_required = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    analyses = db.relationship('ResumeAnalysis', backref='job_description', lazy=True)

    def get_skills_list(self):
        """Get skills as list"""
        if self.skills_required:
            try:
                return json.loads(self.skills_required)
            except:
                return []
        return []

    def set_skills_list(self, skills_list):
        """Set skills from list"""
        self.skills_required = json.dumps(skills_list)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'content': self.content,
            'skills_required': self.get_skills_list(),
            'experience_required': self.experience_required,
            'education_required': self.education_required,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<JobDescription {self.title}>'

class Resume(db.Model):
    """Resume model"""
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Extracted information
    skills = db.Column(db.Text, nullable=True)  # JSON string
    experience_years = db.Column(db.Float, nullable=True)
    education = db.Column(db.Text, nullable=True)  # JSON string
    contact_info = db.Column(db.Text, nullable=True)  # JSON string

    # Metadata
    file_size = db.Column(db.Integer, nullable=True)
    file_type = db.Column(db.String(10), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    analyses = db.relationship('ResumeAnalysis', backref='resume', lazy=True)

    def get_skills_list(self):
        """Get skills as list"""
        if self.skills:
            try:
                return json.loads(self.skills)
            except:
                return []
        return []

    def set_skills_list(self, skills_list):
        """Set skills from list"""
        self.skills = json.dumps(skills_list)

    def get_education_list(self):
        """Get education as list"""
        if self.education:
            try:
                return json.loads(self.education)
            except:
                return []
        return []

    def set_education_list(self, education_list):
        """Set education from list"""
        self.education = json.dumps(education_list)

    def get_contact_info(self):
        """Get contact info as dict"""
        if self.contact_info:
            try:
                return json.loads(self.contact_info)
            except:
                return {}
        return {}

    def set_contact_info(self, contact_dict):
        """Set contact info from dict"""
        self.contact_info = json.dumps(contact_dict)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'content_preview': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'skills': self.get_skills_list(),
            'experience_years': self.experience_years,
            'education': self.get_education_list(),
            'contact_info': self.get_contact_info(),
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat()
        }

    def __repr__(self):
        return f'<Resume {self.original_filename}>'

class ResumeAnalysis(db.Model):
    """Resume analysis results"""
    __tablename__ = 'resume_analyses'

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    job_description_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Matching scores
    overall_score = db.Column(db.Float, nullable=False)
    skills_score = db.Column(db.Float, nullable=False)
    experience_score = db.Column(db.Float, nullable=False)
    education_score = db.Column(db.Float, nullable=False)

    # Detailed analysis
    matched_skills = db.Column(db.Text, nullable=True)  # JSON string
    missing_skills = db.Column(db.Text, nullable=True)  # JSON string
    skill_gap_suggestions = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    improvements = db.Column(db.Text, nullable=True)

    # Analysis metadata
    analysis_method = db.Column(db.String(50), default='tfidf', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_matched_skills(self):
        """Get matched skills as list"""
        if self.matched_skills:
            try:
                return json.loads(self.matched_skills)
            except:
                return []
        return []

    def set_matched_skills(self, skills_list):
        """Set matched skills from list"""
        self.matched_skills = json.dumps(skills_list)

    def get_missing_skills(self):
        """Get missing skills as list"""
        if self.missing_skills:
            try:
                return json.loads(self.missing_skills)
            except:
                return []
        return []

    def set_missing_skills(self, skills_list):
        """Set missing skills from list"""
        self.missing_skills = json.dumps(skills_list)

    # IMPORTANT: Add @property decorator here
    @property
    def rank_level(self):
        """Get rank level based on overall score"""
        # Assuming overall_score is a float between 0.0 and 1.0 (e.g., 0.85)
        # If it's already scaled to 0-100, adjust thresholds accordingly.
        # Based on app.py's to_dict() returning score * 100,
        # and ResumeAnalysis() in app.py expecting a score,
        # let's assume overall_score is 0-1 and this method
        # scales it for display.
        if self.overall_score >= 0.90:
            return "Excellent Match"
        elif self.overall_score >= 0.75:
            return "Strong Match"
        elif self.overall_score >= 0.50:
            return "Moderate Match"
        else:
            return "Needs Improvement"

    # IMPORTANT: Add @property decorator here
    @property
    def rank_color(self):
        """Get color class based on rank"""
        if self.overall_score >= 0.90:
            return "success"
        elif self.overall_score >= 0.75:
            return "primary"
        elif self.overall_score >= 0.50:
            return "warning"
        else:
            return "danger"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'job_description_id': self.job_description_id,
            'overall_score': round(self.overall_score * 100, 2), # Scale for display (0-100)
            'skills_score': round(self.skills_score * 100, 2),
            'experience_score': round(self.experience_score * 100, 2),
            'education_score': round(self.education_score * 100, 2),
            'matched_skills': self.get_matched_skills(),
            'missing_skills': self.get_missing_skills(),
            'skill_gap_suggestions': self.skill_gap_suggestions,
            'strengths': self.strengths,
            'improvements': self.improvements,
            'rank_level': self.rank_level,  # Now correctly accessed as a property
            'rank_color': self.rank_color,  # Now correctly accessed as a property
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<ResumeAnalysis {self.id}: {self.overall_score:.2%}>'

def init_db(app):
    """Initialize database"""
    if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
        db.init_app(app)

    with app.app_context():
        # Create tables
        db.create_all()

        # Create default admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@rankrite.com',
                first_name='Admin',
                last_name='User'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user (username: admin, password: admin123)")

def get_user_stats(user_id):
    """Get user statistics"""
    analyses = ResumeAnalysis.query.filter_by(user_id=user_id).all()

    if not analyses:
        return {
            'total_analyses': 0,
            'avg_score': 0,
            'best_score': 0,
            'recent_analyses': 0
        }

    scores = [a.overall_score for a in analyses] # Use the raw score here
    recent_analyses = ResumeAnalysis.query.filter_by(user_id=user_id)\
        .filter(ResumeAnalysis.created_at >= datetime.utcnow().replace(day=1))\
        .count()

    return {
        'total_analyses': len(analyses),
        'avg_score': round(sum(scores) / len(scores) * 100, 1), # Scale for display (0-100)
        'best_score': round(max(scores) * 100, 1), # Scale for display (0-100)
        'recent_analyses': recent_analyses
    }
