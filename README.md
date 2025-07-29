# 💼 RankRite – AI Resume Ranker

RankRite is a smart, elegant, and production-ready **AI Resume Ranker Web App** that helps recruiters and job seekers evaluate and rank resumes based on job descriptions using advanced Natural Language Processing (NLP) techniques.

---

## 🔍 Features

- 🧠 **Semantic Resume Ranking** using TF-IDF + NLP
- 📂 **Multi-Resume Upload** with comparison support
- 📋 **Job Description Analyzer** for relevance scoring
- 📊 **PDF/CSV Report Export** for ranked results
- 🕵️ **History Tracking** (Resume checks and comparisons)
- 🔐 **User Authentication** (Register, Login, Forgot Password)
- 💡 **Resume Tips & Market Trends**
- 🌗 **Light/Dark Mode Toggle**
- 🧪 Built with Flask, Scikit-learn, Pandas, HTML, CSS, JS

---

## 🖥️ Screenshots

> Add screenshots in `static/assets/` and reference them here

```
![Home Page](static/assets/home.png)
![Compare Page](static/assets/compare.png)
![History Page](static/assets/history.png)
```

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Bharanieeswaran/RankRite.git
cd RankRite
```

### 2. Create & Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # For Mac/Linux
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 🧾 Folder Structure

```
RankRite/
│
├── app.py
├── resume_utils.py
├── database.py
├── config.py
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── compare.html
│   └── ...
│
├── static/
│   ├── css/style.css
│   ├── js/
│   │   ├── mode-toggle.js
│   │   ├── spinner.js
│   │   └── ...
│   └── assets/
│       └── logo.png
│
├── uploads/
├── reports/
└── instance/
    └── resume_ranker.db
```

---

## 🧠 Technologies Used

- **Python**, **Flask**, **Scikit-learn**, **Pandas**, **NumPy**
- **HTML5**, **CSS3**, **JavaScript**
- **SQLite**, **Jinja2**, **Matplotlib**
- **PDF/CSV Generation**

---

## 📦 Upcoming Features

- ✅ ChatGPT-powered Resume Improvement Suggestions
- ✅ Integrated Resume Template Generator
- ✅ Recruiter Dashboard with Filters & Analytics

---

## 🙋‍♂️ About Me

**Bharanieeswaran R**  
Aspiring AI Developer | Computer Science Engineering Student  
🔗 [LinkedIn](https://www.linkedin.com/in/bharanieeswaran-r-08a736310/)  
🔗 [GitHub](https://github.com/Bharanieeswaran)

---

## ⭐ Contributing

Contributions are welcome! Feel free to fork the repo and open a pull request.

---

## 📜 License

---

> Made with ❤️ by Bharanieeswaran
