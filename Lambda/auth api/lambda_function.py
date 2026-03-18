import boto3
import os
import json
import hashlib

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])

def lambda_handler(event, context):
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    print(f"Path: {path}, Method: {method}")

    # Handle OPTIONS requests for CORS preflight
    if method == 'OPTIONS':
        return cors_response(200, {})

    if path == '/register' and method == 'POST':
        return register_user(event)
    elif path == '/login' and method == 'POST':
        return login_user(event)
    else:
        return cors_response(404, {"error": "Invalid path or method"})


def register_user(event):
    try:
        body = json.loads(event['body'])
        name = body.get('name')
        email = body.get('email')
        password = body.get('password')

        if not all([name, email, password]):
            return cors_response(400, {"error": "All fields are required"})

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        existing = users_table.get_item(Key={'email': email})
        if 'Item' in existing:
            return cors_response(400, {"error": "User already exists"})

        users_table.put_item(Item={
            'email': email,
            'name': name,
            'password': hashed_pw
        })

        return cors_response(200, {"message": "User registered successfully"})

    except Exception as e:
        print("Error:", e)
        return cors_response(500, {"error": str(e)})


def login_user(event):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')

        if not all([email, password]):
            return cors_response(400, {"error": "Email and password required"})

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        user = users_table.get_item(Key={'email': email})

        if 'Item' not in user or user['Item']['password'] != hashed_pw:
            return cors_response(401, {"error": "Invalid credentials"})

        return cors_response(200, {
            "message": "Login successful", 
            "name": user['Item']['name'],
            "email": user['Item']['email']
        })

    except Exception as e:
        print("Error:", e)
        return cors_response(500, {"error": str(e)})


def cors_response(status_code, body):
    """Helper function to return response with CORS headers"""
    response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
    print("Lambda response:", response)
    return response