# 🛡️ PhishGuard AI – URL Phishing Detection System

🌐 **Live Demo:** [Open PhishGuard AI](https://phishguard-ai-n5ss.onrender.com)

💻 **GitHub Repository:** [View Source Code](https://github.com/Kiruthigakiruthiga18/PhishGuard-AI)

---

## 📌 About the Project

PhishGuard AI is a Machine Learning-based web application designed to identify potentially harmful phishing URLs.

Phishing is an online fraud technique in which attackers create fake websites or links to steal personal information such as passwords, banking details, and other sensitive data.

This application analyzes a given URL and predicts whether it is **Phishing** or **Legitimate** using a trained Machine Learning model.

The main aim of this project is to help users identify suspicious website links before visiting them.

## 🎯 Project Objectives

- Detect suspicious and phishing URLs.
- Extract important features from URLs.
- Classify URLs using Machine Learning.
- Display prediction results with probability.
- Provide a simple and user-friendly web interface.
- Help users become more aware of online phishing threats.

## ⚙️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Backend web framework |
| HTML | Web page structure |
| CSS | Web page design |
| JavaScript | Frontend interaction |
| Scikit-learn | Machine Learning |
| Random Forest | Classification algorithm |
| Pandas | Dataset processing |
| NumPy | Numerical operations |
| Joblib | Model saving and loading |
| SHAP | Model prediction explanations |

## 🧠 How Does It Work?

PhishGuard AI follows these steps:

1. **Enter URL:** The user enters a website URL in the application.
2. **Feature Extraction:** The system extracts 22 URL-based features.
3. **Machine Learning:** The extracted features are passed to the trained Random Forest model.
4. **URL Classification:** The model predicts whether the URL is phishing or legitimate.
5. **Display Result:** The application displays the prediction and phishing probability.

## 🔍 Features Extracted

The system analyzes 22 URL-based features, including:

- URL Length
- Hostname Length
- Path Length
- Query Length
- Number of Dots
- Number of Hyphens
- Number of Special Characters
- Number of Digits and Letters
- HTTPS Availability
- IP Address Usage
- Subdomain Count
- Path Segment Count
- Suspicious Word Count
- URL Shortener Detection
- Punycode Detection
- Port Detection
- URL Entropy

These features help the Machine Learning model identify patterns commonly found in phishing and legitimate URLs.

## 📊 Dataset

This project uses the **PhiUSIIL Phishing URL Dataset** for model development.

The dataset contains phishing and legitimate URL samples.

The dataset is processed before training to prepare the required URL features.

**Note:** The original dataset is not included in this repository.

## 🤖 Machine Learning Model

The project uses the **Random Forest Classifier** to classify URLs.

The model is trained using extracted URL features and evaluated using a separate test dataset.

Model evaluation includes:

- Accuracy
- Precision
- Recall
- F1-Score
- ROC-AUC
- Confusion Matrix

The application also uses probability calibration to improve the reliability of predicted probabilities.

SHAP is used to help explain model predictions.

**Note:** Evaluation results are based on the selected test dataset and do not guarantee the same performance on every real-world URL.

## 🖥️ Application Features

- User-friendly URL input field.
- Phishing or Legitimate prediction.
- Phishing probability display.
- Machine Learning-based URL analysis.
- Simple and interactive web interface.

## 🌐 Live Project Demo

**Live Website:**  
https://phishguard-ai-n5ss.onrender.com

**Deployment Platform:** Render

The application is hosted as a Flask web application.

## 📁 Project Structure

```text
PhishGuard-AI/
│
├── app.py
├── url_features.py
├── train_model.py
├── explain_model.py
├── inspect_dataset.py
├── check_duplicates.py
├── test_root_domains.py
│
├── models/
│   └── phishguard_model_wwwfix.joblib
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── results/
│   └── Model evaluation plots
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 How to Run the Project Locally

### Step 1: Clone the Repository

```bash
git clone https://github.com/Kiruthigakiruthiga18/PhishGuard-AI.git
```

### Step 2: Open the Project Folder

```bash
cd PhishGuard-AI
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### Step 5: Install Required Packages

```bash
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open in Browser

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

Now you can enter a URL and check its prediction.

## ⚠️ Limitations

- The prediction is based on URL features only.
- The system does not fully analyze website content.
- Some legitimate URLs may be incorrectly classified.
- Some phishing URLs may not be detected.
- The prediction is not a guarantee that a website is safe.
- Model performance may vary on URLs that were not represented in the training dataset.

Users should not depend only on this application when deciding whether a website is safe.

## 🔮 Future Enhancements

- Real-time URL checking.
- Website content analysis.
- Domain reputation checking.
- Browser extension integration.
- Mobile application support.
- Improved detection using advanced Machine Learning techniques.

## 👩‍💻 Developed By

**Kiruthiga R**

Master of Computer Applications (MCA)  
Mailam Engineering College

**GitHub:** [Kiruthigakiruthiga18](https://github.com/Kiruthigakiruthiga18)

---

## 📜 Disclaimer

This project is developed for educational and learning purposes. It is intended to help identify potentially suspicious URLs. It should be used as an additional security tool and not as a replacement for professional cybersecurity solutions.
