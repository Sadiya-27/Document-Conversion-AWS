# Document Conversion AWS

A serverless document conversion system that converts Office files into PDF using **AWS Lambda (Docker Image + Python + LibreOffice)** with a multi-step processing pipeline and status polling.

---

## 🚀 Features

* Convert documents to PDF (DOCX, XLSX, PPTX)
* AWS Lambda using **Docker container image**
* Python-based conversion logic
* **Multi-Lambda architecture**
* Amazon S3 for storage
* **Status polling (`check-status`) API**
* Lightweight frontend for file upload

---

## 🧠 Architecture

<img width="1536" height="1024" alt="ChatGPT Image May 7, 2026, 05_19_04 PM" src="https://github.com/user-attachments/assets/3fa68d82-94e0-4af7-ad72-5bcb381bae5c" />


```text id="b9h4l2"
User uploads file
        ↓
Frontend (HTML/JS)
        ↓
API → input Lambda
        ↓
File stored in S3 (/input)
        ↓
Conversion Lambda (Docker + Python + LibreOffice)
        ↓
PDF stored in S3 (/output)
        ↓
Frontend polls → check-status API
        ↓
Returns PDF URL
```

---

## ⚙️ Lambda Functions

### 1. input Lambda

* Receives file upload request
* Uploads file to S3 `/input` bucket
* Triggers conversion process

---

### 2. Conversion Lambda (Docker Image)

* Built using Docker with LibreOffice installed
* Runs Python code to:

  * Download file from S3
  * Convert to PDF
  * Upload result to `/output`

---

### 3. check-status API

* Used by frontend
* Checks if converted PDF exists
* Returns:

  * `processing` OR
  * `completed + pdf_url`

---

## 🛠️ Tech Stack

* **Python (Lambda functions)**
* **AWS Lambda (Container + Standard)**
* **Docker + LibreOffice**
* **Amazon S3**
* **HTML / JavaScript (Frontend)**

---

## 📁 Project Structure

```bash id="5m4wxy"
Document-Conversion-AWS/
│
├── lambda/
│   ├── input/              # Upload handler Lambda
│   ├── convert/            # Conversion logic (Python)
│   └── check-status/       # Status API
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── Dockerfile              # LibreOffice container image
├── requirements.txt
└── README.md
```

---

## 🔄 Workflow

### Step 1: Upload

User uploads file → handled by **input Lambda**

### Step 2: Store

File saved in:

```id="jhm6g8"
/input/
```

### Step 3: Convert

Conversion Lambda:

* Runs LibreOffice
* Converts file → PDF

### Step 4: Save Output

```id="zj7p2d"
/output/
```

### Step 5: Poll Status

Frontend calls:

```id="a7p0sl"
check-status
```

---

## 📡 check-status Response

### Processing

```json id="c0mw6u"
{
  "status": "processing"
}
```

### Completed

```json id="y4r2vt"
{
  "status": "completed",
  "pdf_url": "https://your-bucket.s3.amazonaws.com/output/file.pdf"
}
```

---

## 🐳 Docker Setup

```bash id="u0v0j1"
docker build -t libreoffice-lambda .
```

Push to AWS ECR and use in Lambda.

---

## ☁️ AWS Configuration

### S3 Structure

```id="o41g5v"
/input
/output
```

---

### Lambda Settings

* Memory: 3008 MB recommended
* Timeout: 45–60 seconds
* Env variable:

```id="k2u2yt"
HOME=/tmp
```

---

## ▶️ Run Frontend

```bash id="2pq7bd"
frontend/index.html
```

---

## ⚠️ Common Issues

### 403 Forbidden (S3)

* Bucket permissions not public
* Missing IAM roles
* Expired presigned URL

---

### Conversion Errors

* Increase memory
* Increase timeout
* Unsupported file format

---

## 🔮 Future Improvements

* Drag & drop UI
* Upload progress bar
* Multi-file conversion
* Authentication system
* Queue (SQS) for scalability

---

## 👩‍💻 Author

Sadiya Fatima Khwaja

* GitHub: https://github.com/Sadiya-27
* LinkedIn: https://www.linkedin.com/in/sadiya-khwaja

---

## 📜 License

MIT License
