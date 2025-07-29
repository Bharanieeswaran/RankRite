"""
Resume processing and ranking utilities for RankRite
"""
import os
import re
import fitz  # PyMuPDF
import docx2txt
from docx import Document
import spacy
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Main class for processing and ranking resumes"""
    
    def __init__(self):
        """Initialize the processor"""
        self.nlp = None
        self.skills_database = self._load_skills_database()
        self.education_keywords = self._load_education_keywords()
        self._load_spacy_model()
    
    def _load_spacy_model(self):
        """Load spaCy model with fallback"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Using basic processing.")
            self.nlp = None
    
    def _load_skills_database(self):
        """Load comprehensive skills database"""
        return {
            'programming': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin',
                'swift', 'typescript', 'scala', 'r', 'matlab', 'sql', 'nosql', 'html', 'css'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'nodejs',
                'express', 'bootstrap', 'tailwind', 'jquery', 'redux', 'vuex', 'nextjs', 'nuxtjs'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle',
                'cassandra', 'dynamodb', 'firebase', 'mariadb', 'couchdb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
                'terraform', 'ansible', 'vagrant', 'heroku', 'digitalocean', 'cloudflare'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'data analysis', 'pandas', 'numpy', 'scikit-learn',
                'tensorflow', 'pytorch', 'keras', 'matplotlib', 'seaborn', 'plotly', 'tableau',
                'power bi', 'jupyter', 'apache spark', 'hadoop'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'slack', 'trello', 'asana', 'figma', 'adobe xd',
                'photoshop', 'illustrator', 'sketch', 'invision', 'zeplin', 'postman'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
                'time management', 'project management', 'agile', 'scrum', 'kanban', 'analytical',
                'creative', 'adaptable', 'collaborative', 'detail oriented'
            ],
            'business': [
                'project management', 'business analysis', 'requirements gathering', 'stakeholder management',
                'process improvement', 'strategic planning', 'budget management', 'risk management',
                'quality assurance', 'customer service', 'sales', 'marketing', 'seo', 'sem'
            ]
        }
    
    def _load_education_keywords(self):
        """Load education-related keywords"""
        return {
            'degrees': [
                'bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma', 'certificate',
                'bs', 'ba', 'ms', 'ma', 'mba', 'btech', 'mtech', 'bsc', 'msc'
            ],
            'fields': [
                'computer science', 'software engineering', 'information technology', 'data science',
                'artificial intelligence', 'machine learning', 'cybersecurity', 'business administration',
                'marketing', 'finance', 'accounting', 'engineering', 'mathematics', 'statistics',
                'physics', 'chemistry', 'biology', 'psychology', 'economics'
            ],
            'institutions': [
                'university', 'college', 'institute', 'school', 'academy', 'mit', 'stanford',
                'harvard', 'berkeley', 'carnegie mellon', 'georgia tech', 'caltech'
            ]
        }
    
    def extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX file"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            # Try with python-docx first for better formatting
            try:
                doc = Document(file_path)
                text = []
                for paragraph in doc.paragraphs:
                    text.append(paragraph.text)
                return '\n'.join(text).strip()
            except:
                # Fallback to docx2txt
                return docx2txt.process(file_path).strip()
                
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise
    
    def extract_contact_info(self, text):
        """Extract contact information from resume text"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone number extraction
        phone_patterns = [
            r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(\+\d{1,3}[-.\s]?)?\d{10}',
            r'(\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info['phone'] = phones[0] if isinstance(phones[0], str) else ''.join(phones[0])
                break
        
        # LinkedIn profile
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin:
            contact_info['linkedin'] = f"https://{linkedin[0]}"
        
        # GitHub profile
        github_pattern = r'github\.com/[\w-]+'
        github = re.findall(github_pattern, text, re.IGNORECASE)
        if github:
            contact_info['github'] = f"https://{github[0]}"
        
        return contact_info
    
    def extract_skills(self, text):
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        # Search for skills in each category
        for category, skills in self.skills_database.items():
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.append({
                        'skill': skill,
                        'category': category,
                        'confidence': 1.0
                    })
        
        # Use spaCy for additional skill extraction if available
        if self.nlp:
            found_skills.extend(self._extract_skills_with_spacy(text))
        
        # Remove duplicates and sort by confidence
        unique_skills = {}
        for skill_info in found_skills:
            skill_name = skill_info['skill'].lower()
            if skill_name not in unique_skills or skill_info['confidence'] > unique_skills[skill_name]['confidence']:
                unique_skills[skill_name] = skill_info
        
        return list(unique_skills.values())
    
    def _extract_skills_with_spacy(self, text):
        """Extract additional skills using spaCy NER"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        skills = []
        
        # Extract entities that might be skills
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG'] and len(ent.text) > 2:
                # Check if it's a potential technical skill
                if any(keyword in ent.text.lower() for keyword in ['tech', 'soft', 'program', 'develop']):
                    skills.append({
                        'skill': ent.text,
                        'category': 'technical',
                        'confidence': 0.7
                    })
        
        return skills
    
    def extract_experience(self, text):
        """Extract years of experience from resume text"""
        experience_patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'(\d+)\+?\s*years?\s+in',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+(?:working|professional)',
        ]
        
        years = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(match) for match in matches])
        
        # Also look for date ranges
        date_patterns = [
            r'(\d{4})\s*[-–]\s*(\d{4})',
            r'(\d{4})\s*[-–]\s*present',
            r'(\d{4})\s*[-–]\s*current'
        ]
        
        current_year = datetime.now().year
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                start_year = int(match[0])
                end_year = current_year if match[1].lower() in ['present', 'current'] else int(match[1])
                years.append(max(0, end_year - start_year))
        
        return max(years) if years else 0
    
    def extract_education(self, text):
        """Extract education information from resume text"""
        education_info = []
        text_lower = text.lower()
        
        # Look for degree patterns
        degree_patterns = [
            r'(bachelor|master|phd|doctorate|associate|diploma|certificate|bs|ba|ms|ma|mba|btech|mtech|bsc|msc)\s+(?:of\s+|in\s+)?([a-z\s]+)',
            r'(bachelor|master|phd|doctorate|associate|diploma|certificate|bs|ba|ms|ma|mba|btech|mtech|bsc|msc)(?:\s+degree)?(?:\s+in\s+([a-z\s]+))?',
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                degree = match[0].strip()
                field = match[1].strip() if len(match) > 1 and match[1] else 'Unknown'
                
                education_info.append({
                    'degree': degree.title(),
                    'field': field.title(),
                    'confidence': 0.9
                })
        
        # Look for specific fields mentioned
        for field in self.education_keywords['fields']:
            if field in text_lower:
                education_info.append({
                    'degree': 'Unknown',
                    'field': field.title(),
                    'confidence': 0.7
                })
        
        # Remove duplicates
        unique_education = []
        seen = set()
        for edu in education_info:
            key = (edu['degree'], edu['field'])
            if key not in seen:
                seen.add(key)
                unique_education.append(edu)
        
        return unique_education
    
    def calculate_similarity_scores(self, resume_text, job_description, resume_skills=None, resume_experience=0, resume_education=None):
        """Calculate comprehensive similarity scores between resume and job description"""
        
        if resume_skills is None:
            resume_skills = self.extract_skills(resume_text)
        if resume_education is None:
            resume_education = self.extract_education(resume_text)
        
        # Extract job requirements
        job_skills = self.extract_skills(job_description)
        job_experience = self.extract_experience(job_description)
        job_education = self.extract_education(job_description)
        
        # Calculate individual scores
        skills_score = self._calculate_skills_score(resume_skills, job_skills)
        experience_score = self._calculate_experience_score(resume_experience, job_experience)
        education_score = self._calculate_education_score(resume_education, job_education)
        
        # Calculate text similarity using TF-IDF
        text_similarity = self._calculate_text_similarity(resume_text, job_description)
        
        # Weighted overall score
        weights = {
            'skills': 0.4,
            'experience': 0.25,
            'education': 0.15,
            'text_similarity': 0.2
        }
        
        overall_score = (
            skills_score * weights['skills'] +
            experience_score * weights['experience'] +
            education_score * weights['education'] +
            text_similarity * weights['text_similarity']
        )
        
        # Generate analysis details
        matched_skills, missing_skills = self._analyze_skill_match(resume_skills, job_skills)
        
        return {
            'overall_score': min(overall_score, 1.0),
            'skills_score': skills_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'text_similarity': text_similarity,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'job_skills': [skill['skill'] for skill in job_skills],
            'resume_skills': [skill['skill'] for skill in resume_skills]
        }
    
    def _calculate_skills_score(self, resume_skills, job_skills):
        """Calculate skills matching score"""
        if not job_skills:
            return 0.8  # If no specific skills required, give benefit of doubt
        
        resume_skill_names = set(skill['skill'].lower() for skill in resume_skills)
        job_skill_names = set(skill['skill'].lower() for skill in job_skills)
        
        if not resume_skill_names:
            return 0.0
        
        # Calculate intersection
        matched_skills = resume_skill_names.intersection(job_skill_names)
        
        # Base score from direct matches
        direct_match_score = len(matched_skills) / len(job_skill_names) if job_skill_names else 0
        
        # Bonus for having more skills than required
        skill_abundance_bonus = min(0.2, (len(resume_skill_names) - len(job_skill_names)) * 0.02) if len(resume_skill_names) > len(job_skill_names) else 0
        
        # Category-based matching (similar skills in same category)
        category_match_score = self._calculate_category_match_score(resume_skills, job_skills)
        
        total_score = direct_match_score + skill_abundance_bonus + (category_match_score * 0.3)
        return min(total_score, 1.0)
    
    def _calculate_category_match_score(self, resume_skills, job_skills):
        """Calculate score based on skill category overlap"""
        resume_categories = Counter(skill['category'] for skill in resume_skills)
        job_categories = Counter(skill['category'] for skill in job_skills)
        
        if not job_categories:
            return 0
        
        category_overlap = 0
        for category, job_count in job_categories.items():
            resume_count = resume_categories.get(category, 0)
            category_overlap += min(resume_count / job_count, 1.0) if job_count > 0 else 0
        
        return category_overlap / len(job_categories)
    
    def _calculate_experience_score(self, resume_experience, job_experience):
        """Calculate experience matching score"""
        if job_experience == 0:
            return 0.8  # If no specific experience required
        
        if resume_experience == 0:
            return 0.1  # Some credit for fresh graduates
        
        # Perfect match or more experience
        if resume_experience >= job_experience:
            return 1.0
        
        # Partial credit for less experience
        return max(0.2, resume_experience / job_experience)
    
    def _calculate_education_score(self, resume_education, job_education):
        """Calculate education matching score"""
        if not job_education:
            return 0.8  # If no specific education required
        
        if not resume_education:
            return 0.3  # Some base score
        
        # Extract degree levels for comparison
        resume_levels = set()
        job_levels = set()
        
        degree_hierarchy = {
            'associate': 1, 'diploma': 1, 'certificate': 1,
            'bachelor': 2, 'bs': 2, 'ba': 2, 'btech': 2, 'bsc': 2,
            'master': 3, 'ms': 3, 'ma': 3, 'mba': 3, 'mtech': 3, 'msc': 3,
            'phd': 4, 'doctorate': 4
        }
        
        for edu in resume_education:
            level = degree_hierarchy.get(edu['degree'].lower(), 1)
            resume_levels.add(level)
        
        for edu in job_education:
            level = degree_hierarchy.get(edu['degree'].lower(), 1)
            job_levels.add(level)
        
        if not job_levels:
            return 0.8
        
        # Check if resume meets minimum education requirement
        max_resume_level = max(resume_levels) if resume_levels else 0
        min_job_level = min(job_levels)
        
        if max_resume_level >= min_job_level:
            return 1.0
        
        # Partial credit based on level difference
        return max(0.3, max_resume_level / min_job_level) if min_job_level > 0 else 0.3
    
    def _calculate_text_similarity(self, resume_text, job_description):
        """Calculate text similarity using TF-IDF and cosine similarity"""
        try:
            # Preprocess texts
            texts = [self._preprocess_text(resume_text), self._preprocess_text(job_description)]
            
            # Calculate TF-IDF vectors
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return max(0, similarity)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.3  # Default similarity score
    
    def _preprocess_text(self, text):
        """Preprocess text for similarity calculation"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()
    
    def _analyze_skill_match(self, resume_skills, job_skills):
        """Analyze which skills match and which are missing"""
        resume_skill_names = set(skill['skill'].lower() for skill in resume_skills)
        job_skill_names = set(skill['skill'].lower() for skill in job_skills)
        
        # Find matched skills
        matched = list(resume_skill_names.intersection(job_skill_names))
        
        # Find missing skills
        missing = list(job_skill_names - resume_skill_names)
        
        return matched, missing
    
    def generate_skill_gap_suggestions(self, missing_skills, matched_skills):
        """Generate suggestions to fill skill gaps"""
        suggestions = []
        
        if not missing_skills:
            suggestions.append("Great! You have all the required skills for this position.")
            return suggestions
        
        # Prioritize missing skills by category
        critical_skills = []
        nice_to_have = []
        
        for skill in missing_skills:
            skill_lower = skill.lower()
            # Categorize as critical or nice-to-have based on common patterns
            if any(keyword in skill_lower for keyword in ['python', 'java', 'sql', 'project management', 'leadership']):
                critical_skills.append(skill)
            else:
                nice_to_have.append(skill)
        
        if critical_skills:
            suggestions.append(f"Focus on learning these critical skills: {', '.join(critical_skills[:3])}")
        
        if nice_to_have:
            suggestions.append(f"Consider adding these skills to strengthen your profile: {', '.join(nice_to_have[:3])}")
        
        # Learning resource suggestions
        suggestions.append("Consider online courses, certifications, or hands-on projects to develop these skills.")
        
        return suggestions
    
    def generate_improvement_suggestions(self, analysis_result):
        """Generate overall improvement suggestions"""
        suggestions = []
        scores = analysis_result
        
        # Skills suggestions
        if scores['skills_score'] < 0.6:
            suggestions.append("Skills Match: Consider highlighting more relevant technical skills and tools mentioned in the job description.")
        
        # Experience suggestions
        if scores['experience_score'] < 0.6:
            suggestions.append("Experience: Emphasize relevant work experience and quantify your achievements with specific metrics.")
        
        # Education suggestions
        if scores['education_score'] < 0.6:
            suggestions.append("Education: Highlight relevant educational background, certifications, or ongoing learning initiatives.")
        
        # Overall text match
        if scores['text_similarity'] < 0.4:
            suggestions.append("Content: Use more keywords from the job description and tailor your resume content to better match the role.")
        
        # General suggestions
        suggestions.extend([
            "Use action verbs and quantify your accomplishments with specific numbers and results.",
            "Customize your resume for each application to better match the specific requirements.",
            "Consider adding a skills section that prominently features the most relevant technical skills."
        ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def rank_multiple_resumes(self, resume_data_list, job_description):
        """Rank multiple resumes against a job description"""
        rankings = []
        
        for i, resume_data in enumerate(resume_data_list):
            try:
                # Calculate scores for each resume
                analysis = self.calculate_similarity_scores(
                    resume_data['text'],
                    job_description,
                    resume_data.get('skills'),
                    resume_data.get('experience', 0),
                    resume_data.get('education')
                )
                
                rankings.append({
                    'resume_id': resume_data.get('id', i),
                    'filename': resume_data.get('filename', f'Resume_{i+1}'),
                    'analysis': analysis,
                    'rank_position': 0  # Will be set after sorting
                })
                
            except Exception as e:
                logger.error(f"Error ranking resume {i}: {str(e)}")
                # Add with low score if processing fails
                rankings.append({
                    'resume_id': resume_data.get('id', i),
                    'filename': resume_data.get('filename', f'Resume_{i+1}'),
                    'analysis': {
                        'overall_score': 0.1,
                        'skills_score': 0.1,
                        'experience_score': 0.1,
                        'education_score': 0.1,
                        'text_similarity': 0.1,
                        'matched_skills': [],
                        'missing_skills': [],
                        'job_skills': [],
                        'resume_skills': []
                    },
                    'rank_position': 0
                })
        
        # Sort by overall score (descending)
        rankings.sort(key=lambda x: x['analysis']['overall_score'], reverse=True)
        
        # Assign rank positions
        for i, ranking in enumerate(rankings):
            ranking['rank_position'] = i + 1
        
        return rankings
    
    def export_analysis_to_dict(self, analysis_result, resume_filename, job_title="Job Position"):
        """Export analysis result to dictionary for reports"""
        return {
            'resume_filename': resume_filename,
            'job_title': job_title,
            'analysis_date': datetime.now().isoformat(),
            'scores': {
                'overall': round(analysis_result['overall_score'] * 100, 2),
                'skills': round(analysis_result['skills_score'] * 100, 2),
                'experience': round(analysis_result['experience_score'] * 100, 2),
                'education': round(analysis_result['education_score'] * 100, 2),
                'text_similarity': round(analysis_result['text_similarity'] * 100, 2)
            },
            'skills_analysis': {
                'matched_skills': analysis_result['matched_skills'],
                'missing_skills': analysis_result['missing_skills'],
                'total_resume_skills': len(analysis_result['resume_skills']),
                'total_job_skills': len(analysis_result['job_skills'])
            },
            'recommendations': self.generate_improvement_suggestions(analysis_result),
            'skill_gap_suggestions': self.generate_skill_gap_suggestions(
                analysis_result['missing_skills'],
                analysis_result['matched_skills']
            )
        }

# Utility functions for trend analysis and statistics
def analyze_skill_trends(analyses_data):
    """Analyze trending skills from multiple analyses"""
    skill_frequency = Counter()
    
    for analysis in analyses_data:
        if 'job_skills' in analysis:
            skill_frequency.update(analysis['job_skills'])
    
    # Get top trending skills
    trending_skills = skill_frequency.most_common(20)
    
    return {
        'trending_skills': trending_skills,
        'total_analyses': len(analyses_data),
        'unique_skills': len(skill_frequency)
    }

def get_industry_insights():
    """Get predefined industry insights and tips"""
    return {
        'high_demand_skills': [
            'Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker',
            'Kubernetes', 'Machine Learning', 'Data Analysis', 'SQL'
        ],
        'emerging_technologies': [
            'Artificial Intelligence', 'Blockchain', 'IoT', 'Edge Computing',
            'Quantum Computing', 'AR/VR', 'DevOps', 'Microservices'
        ],
        'soft_skills_importance': [
            'Communication', 'Leadership', 'Problem Solving', 'Adaptability',
            'Teamwork', 'Critical Thinking', 'Time Management', 'Creativity'
        ],
        'resume_tips': [
            "Use action verbs to start bullet points (e.g., 'Developed', 'Implemented', 'Led')",
            "Quantify achievements with specific numbers and percentages",
            "Tailor your resume for each job application",
            "Include relevant keywords from the job description",
            "Keep your resume concise (1-2 pages maximum)",
            "Use a clean, professional format",
            "Include a skills section with technical competencies",
            "Highlight recent and relevant experience first",
            "Proofread carefully for grammar and spelling errors",
            "Update your resume regularly with new achievements"
        ]
    }