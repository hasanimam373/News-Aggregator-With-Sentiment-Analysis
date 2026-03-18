# 📰 News Aggregator with Sentiment Analysis

A full-stack, cloud-native news aggregation platform that fetches real-time news, performs sentiment analysis, and serves data through a scalable serverless backend using AWS services.

---

## 🚀 Features

- 🔍 Fetch real-time news using external News API  
- 🤖 Perform sentiment analysis (Positive / Negative / Neutral) using Gemini API  
- ⚡ Serverless backend using AWS Lambda  
- 🌐 REST APIs exposed via AWS API Gateway  
- 🗄️ Data storage using AWS DynamoDB  
- 💻 Static frontend served via Nginx on Amazon EC2  
- ☁️ Scalable and production-ready cloud architecture  

---

## 🛠️ Tech Stack

### Backend
- Python (Lambda functions)
- AWS Lambda
- AWS API Gateway

### Frontend
- HTML, CSS, JavaScript
- Nginx (on EC2)

### Cloud & DevOps
- AWS EC2
- AWS DynamoDB
- AWS Lambda
- AWS API Gateway

### APIs
- News Data API
- Gemini API (for sentiment analysis)

---

## 📁 Project Structure


├── Lambda/
│ ├── NewsAggregatorBackend/
│ ├── NewsAggregatorFrontendAPI/
│ └── auth api/
├── Table/
│ ├── users schema
│ ├── articles schema
│ └── comments schema
├── API/
├── index.html
├── login.html
└── README.md


---

## ⚙️ Architecture Overview


Frontend (EC2 + Nginx)
↓
API Gateway
↓
AWS Lambda (Backend)
↓
DynamoDB (Storage)
↓
External APIs (News + Gemini)


---

## 🧑‍💻 Setup & Deployment Guide

### 🔹 1. Clone the Repository

```bash
git clone https://github.com/hasanimam373/News-Aggregator-With-Sentiment-Analysis.git
cd News-Aggregator-With-Sentiment-Analysis
☁️ AWS Setup
🔹 2. Create DynamoDB Tables

Create the following tables:

news-aggregator-users

news-aggregator-articles

news-aggregator-comments

👉 Use schemas provided in the /Table folder

🔹 3. Deploy AWS Lambda Functions

Go to AWS Lambda Console

Create the following functions:

NewsAggregatorBackend

NewsAggregatorFrontendAPI

Auth API

Upload code from respective /Lambda folders

Configure Environment Variables:

DYNAMODB_TABLE_NAME=news-aggregator-articles
USERS_TABLE_NAME=news-aggregator-users
COMMENTS_TABLE_NAME=news-aggregator-comments
GEMINI_API_KEY=your-api-key
NEWS_API_KEY=your-api-key
🔹 4. Setup API Gateway

Go to API Gateway

Create a REST API

Create endpoints such as:

/news

/login

/comments

Integrate each route with corresponding Lambda function

Enable CORS

Deploy the API

🔹 5. Launch EC2 Instance

Launch an EC2 instance (Ubuntu recommended)

Allow inbound rules:

HTTP (80)

SSH (22)

Connect via SSH:

ssh -i your-key.pem ubuntu@your-ec2-public-ip
🔹 6. Install Nginx
sudo apt update
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
🔹 7. Deploy Frontend Files
cd /var/www/html
sudo rm -rf *

Upload files using SCP:

scp -i your-key.pem -r * ubuntu@your-ec2-public-ip:/var/www/html
🔹 8. Configure Frontend API URL

Update your frontend JavaScript:

const API_URL = "https://your-api-id.execute-api.region.amazonaws.com/prod";
🔹 9. Access Application

Open browser:

http://your-ec2-public-ip
🔐 Security Best Practices

Never expose API keys in code

Use environment variables

Consider AWS Secrets Manager for production

Restrict API Gateway access with authentication

📊 Future Improvements

Add JWT Authentication

Deploy frontend using S3 + CloudFront

Add CI/CD pipeline (Jenkins/GitHub Actions)

Improve UI/UX

Add caching (Redis)

🤝 Contributing

Contributions are welcome. Fork the repo and submit a pull request.
