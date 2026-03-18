import boto3
import os
import json
from datetime import datetime
from uuid import uuid4
import requests
import time
from boto3.dynamodb.conditions import Attr

# Configuration
dynamodb = boto3.resource('dynamodb')
articles_table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_NAME"))
users_table = dynamodb.Table(os.environ.get("USERS_TABLE_NAME"))
comments_table = dynamodb.Table(os.environ.get("COMMENTS_TABLE_NAME"))

# Helper Functions
def get_sentiment(text):
    if not text: return 'neutral'
    text_lower = text.lower()
    if 'good' in text_lower or 'great' in text_lower: return 'positive'
    elif 'bad' in text_lower or 'terrible' in text_lower: return 'negative'
    return 'neutral'

def fetch_articles_from_api():
    try:
        NEWS_API_URL = os.environ.get("NEWS_API_URL")
        NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
        response = requests.get(f"{NEWS_API_URL}?apikey={NEWS_API_KEY}&language=en&country=in", timeout=10)
        data = response.json()
        return [{
            "title": art.get("title") or "No Title",
            "url": art.get("link") or "No URL",
            "summary": art.get("description") or "No Summary",
            "source": art.get("source_id") or "Unknown",
            "category": art.get("category", ["Uncategorized"])[0] if isinstance(art.get("category"), list) else art.get("category", "Uncategorized"),
            "image": art.get("image_url") or "",
            "sentiment": "neutral",
            "likes": [],
            "dislikes": []
        } for art in data.get("results", [])]
    except: return []

def save_articles():
    articles = fetch_articles_from_api()
    saved_count = 0
    for article in articles:
        try:
            existing = articles_table.get_item(Key={'url': article['url']})
            if 'Item' not in existing:
                article['sentiment'] = get_sentiment(article['summary'])
                article['id'] = str(uuid4())
                article['timestamp'] = datetime.now().isoformat()
                articles_table.put_item(Item=article)
                saved_count += 1
        except: continue
    return {"message": f"Saved {saved_count} new articles"}

def get_paginated_articles(limit=500):
    print("🔄 get_paginated_articles function called")
    response = articles_table.scan(Limit=limit)
    items = response.get("Items", [])
    for item in items:
        item['likes'] = item.get('likes', [])
        item['dislikes'] = item.get('dislikes', [])
        item['likeCount'] = len(item['likes'])
        item['dislikeCount'] = len(item['dislikes'])
    print(f"📄 Returning {len(items)} articles from get_paginated_articles")
    return items

# User Management
def register_user(event):
    try:
        body = json.loads(event.get("body", "{}"))
        email, password, name = body.get("email"), body.get("password"), body.get("name")
        if not all([email, password, name]): return {"error": "Missing fields"}
        if 'Item' in users_table.get_item(Key={'email': email}): return {"error": "User exists"}
        users_table.put_item(Item={'email': email, 'password': password, 'name': name, 'createdAt': datetime.now().isoformat()})
        return {"message": "User registered"}
    except Exception as e: return {"error": str(e)}

def login_user(event):
    try:
        body = json.loads(event.get("body", "{}"))
        email, password = body.get("email"), body.get("password")
        if not all([email, password]): return {"error": "Missing fields"}
        user = users_table.get_item(Key={'email': email}).get('Item')
        if not user or user['password'] != password: return {"error": "Invalid credentials"}
        return {"message": "Login successful", "user": {"email": user['email'], "name": user['name']}}
    except Exception as e: return {"error": str(e)}

# FIXED LIKE FUNCTION - Returns proper object
def like_article(event):
    try:
        print("🎯 LIKE_ARTICLE FUNCTION CALLED")
        body = json.loads(event.get("body", "{}"))
        url, user_email = body.get("url"), body.get("email")
        if not all([url, user_email]): 
            return {"error": "Missing URL or email"}
        
        print(f"🔵 LIKE request - URL: {url}, User: {user_email}")
        
        # Get article
        article_response = articles_table.get_item(Key={'url': url})
        if 'Item' not in article_response:
            return {"error": "Article not found"}
        
        article = article_response['Item']
        likes = article.get('likes', [])
        dislikes = article.get('dislikes', [])
        
        print(f"🔵 Current - Likes: {len(likes)}, Dislikes: {len(dislikes)}")
        
        # Toggle like
        if user_email in likes:
            # User is unliking
            likes.remove(user_email)
            action = "unliked"
            print(f"🔵 User unliked")
        else:
            # User is liking
            likes.append(user_email)
            if user_email in dislikes:
                dislikes.remove(user_email)
            action = "liked"
            print(f"🔵 User liked")
        
        # Update in DynamoDB
        articles_table.update_item(
            Key={'url': url},
            UpdateExpression='SET likes = :likes, dislikes = :dislikes',
            ExpressionAttributeValues={
                ':likes': likes,
                ':dislikes': dislikes
            }
        )
        
        print(f"🔵 Updated - Likes: {len(likes)}, Dislikes: {len(dislikes)}")
        
        # Return PROPER OBJECT that frontend expects
        result = {
            "message": action,
            "likeCount": len(likes),
            "dislikeCount": len(dislikes),
            "userLiked": user_email in likes,
            "userDisliked": user_email in dislikes
        }
        print(f"✅ LIKE returning: {result}")
        return result
        
    except Exception as e: 
        print(f"🔵 Error in like_article: {str(e)}")
        return {"error": str(e)}

# FIXED DISLIKE FUNCTION - Returns proper object
def dislike_article(event):
    try:
        print("🎯 DISLIKE_ARTICLE FUNCTION CALLED")
        body = json.loads(event.get("body", "{}"))
        url, user_email = body.get("url"), body.get("email")
        if not all([url, user_email]): 
            return {"error": "Missing URL or email"}
        
        print(f"🔴 DISLIKE request - URL: {url}, User: {user_email}")
        
        # Get article
        article_response = articles_table.get_item(Key={'url': url})
        if 'Item' not in article_response:
            return {"error": "Article not found"}
        
        article = article_response['Item']
        likes = article.get('likes', [])
        dislikes = article.get('dislikes', [])
        
        print(f"🔴 Current - Likes: {len(likes)}, Dislikes: {len(dislikes)}")
        
        # Toggle dislike
        if user_email in dislikes:
            # User is undisliking
            dislikes.remove(user_email)
            action = "undisliked"
            print(f"🔴 User undisliked")
        else:
            # User is disliking
            dislikes.append(user_email)
            if user_email in likes:
                likes.remove(user_email)
            action = "disliked"
            print(f"🔴 User disliked")
        
        # Update in DynamoDB
        articles_table.update_item(
            Key={'url': url},
            UpdateExpression='SET likes = :likes, dislikes = :dislikes',
            ExpressionAttributeValues={
                ':likes': likes,
                ':dislikes': dislikes
            }
        )
        
        print(f"🔴 Updated - Likes: {len(likes)}, Dislikes: {len(dislikes)}")
        
        # Return PROPER OBJECT that frontend expects
        result = {
            "message": action,
            "likeCount": len(likes),
            "dislikeCount": len(dislikes),
            "userLiked": user_email in likes,
            "userDisliked": user_email in dislikes
        }
        print(f"✅ DISLIKE returning: {result}")
        return result
        
    except Exception as e: 
        print(f"🔴 Error in dislike_article: {str(e)}")
        return {"error": str(e)}

# FIXED COMMENT FUNCTION - Returns proper object
def add_comment(event):
    try:
        print("🎯 ADD_COMMENT FUNCTION CALLED")
        body = json.loads(event.get("body", "{}"))
        url, comment_text, user_email, user_name = body.get("url"), body.get("comment"), body.get("email"), body.get("name")
        if not all([url, comment_text, user_email]): 
            return {"error": "Missing fields"}
        
        print(f"💬 COMMENT request - URL: {url}, User: {user_email}")
        
        # Verify article exists
        article_response = articles_table.get_item(Key={'url': url})
        if 'Item' not in article_response:
            return {"error": "Article not found"}
        
        # Add comment
        comment_item = {
            'id': str(uuid4()),
            'articleUrl': url,
            'userEmail': user_email,
            'userName': user_name or 'Anonymous',
            'comment': comment_text,
            'timestamp': datetime.now().isoformat()
        }
        
        comments_table.put_item(Item=comment_item)
        print(f"💬 Comment saved: {comment_item['id']}")

        # Return updated comments
        response = comments_table.scan(FilterExpression=Attr('articleUrl').eq(url))
        comments = sorted(response.get("Items", []), key=lambda x: x.get("timestamp", ""), reverse=True)
        
        print(f"💬 Returning {len(comments)} comments")
        
        # Return PROPER OBJECT that frontend expects
        result = {
            "message": "Comment added successfully", 
            "comments": comments,
            "count": len(comments)
        }
        print(f"✅ COMMENT returning: {result}")
        return result
        
    except Exception as e: 
        print(f"💬 Error in add_comment: {str(e)}")
        return {"error": f"Failed to add comment: {str(e)}"}

def get_comments(event):
    try:
        url = (event.get("queryStringParameters") or {}).get("url")
        if not url: return {"error": "Missing URL"}
        
        response = comments_table.scan(FilterExpression=Attr('articleUrl').eq(url))
        comments = sorted(response.get("Items", []), key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"comments": comments, "count": len(comments)}
    except Exception as e: return {"error": str(e)}

# 🚨 ULTIMATE FIX: COMPLETELY ISOLATED HANDLER
def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Content-Type': 'application/json'
    }
    
    print("🚀 LAMBDA HANDLER STARTED")
    print(f"📨 Event: {json.dumps(event)}")
    
    # CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        print("🔄 CORS Preflight request")
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'CORS'})}
    
    try:
        params = event.get("queryStringParameters") or {}
        action = params.get("action", "fetch")
        
        print(f"🎯 ACTION DETECTED: {action}")
        print(f"🔍 Params: {params}")
        print(f"📝 HTTP Method: {event.get('httpMethod')}")
        
        # 🚨 ULTIMATE FIX: COMPLETELY SEPARATE HANDLERS
        if action == "pagination":
            print("🔄 Handling PAGINATION (returns array)")
            items = get_paginated_articles()
            response = {
                'statusCode': 200, 
                'headers': headers, 
                'body': json.dumps(items, default=str)
            }
            print(f"📄 PAGINATION Response: {len(items)} items")
            return response
            
        elif action == "like":
            print("🔄 Handling LIKE (returns object)")
            result = like_article(event)
            response = {
                'statusCode': 200, 
                'headers': headers, 
                'body': json.dumps(result, default=str)
            }
            print(f"👍 LIKE Response: {result}")
            return response
            
        elif action == "dislike":
            print("🔄 Handling DISLIKE (returns object)")
            result = dislike_article(event)
            response = {
                'statusCode': 200, 
                'headers': headers, 
                'body': json.dumps(result, default=str)
            }
            print(f"👎 DISLIKE Response: {result}")
            return response
            
        elif action == "comment":
            print("🔄 Handling COMMENT (returns object)")
            result = add_comment(event)
            response = {
                'statusCode': 200, 
                'headers': headers, 
                'body': json.dumps(result, default=str)
            }
            print(f"💬 COMMENT Response: {result}")
            return response
            
        elif action == "fetch":
            print("🔄 Handling FETCH")
            result = save_articles()
        elif action == "register":
            print("🔄 Handling REGISTER")
            result = register_user(event)
        elif action == "login":
            print("🔄 Handling LOGIN")
            result = login_user(event)
        elif action == "getComments":
            print("🔄 Handling GET_COMMENTS")
            result = get_comments(event)
        else:
            result = {"error": f"Invalid action: {action}"}
        
        print(f"✅ Action {action} completed. Result: {result}")
        
        # For other actions
        response = {
            'statusCode': 200, 
            'headers': headers, 
            'body': json.dumps(result, default=str)
        }
        print(f"📤 Final Response: {response}")
        return response
        
    except Exception as e:
        print(f"❌ Error in lambda_handler: {str(e)}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return {
            'statusCode': 500, 
            'headers': headers, 
            'body': json.dumps({"error": str(e)})
        }