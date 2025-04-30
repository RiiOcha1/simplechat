import json
import os
import urllib.request
import urllib.error
import re
import boto3
from botocore.exceptions import ClientError

def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"

#bedrock_client = None
#MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
INFERENCE_URL = "https://21e0-34-16-251-129.ngrok-free.app/generate"

def lambda_handler(event, context):
    try:
 #       global bedrock_client
 #       if bedrock_client is None:
 #           region = extract_region_from_arn(context.invoked_function_arn)
 #           bedrock_client = boto3.client('bedrock-runtime', region_name=region)
 #           print(f"Initialized Bedrock client in region: {region}")

 #       print("Received event:", json.dumps(event))

        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        print("Processing message:", message)
        #print("Using model:", MODEL_ID)

        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPI 用のリクエストペイロード
        request_payload = {
                "prompt": message,
                "max_new_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
        }

        # FastAPI 推論サーバーを呼び出し
        req = urllib.request.Request(
                INFERENCE_URL,
                data=json.dumps(request_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
        )

        try:
            with urllib.request.urlopen(req) as res:
                response_body = res.read()
                response = json.loads(response_body)
                print("FastAPI response:", json.dumps(response, ensure_ascii=False))
        except urllib.error.HTTPError as e:
            print(f"HTTPError: {e.code} - {e.reason}")
            return {
                    "statusCode": e.code,
                    "body": json.dumps({"error": f"HTTPError: {e.code} - {e.reason}"})
            }
        except urllib.error.URLError as e:
            print(f"URLError: {e.reason}")
            return {
                    "statusCode": 500,
                    "body": json.dumps({"error": f"URLError: {e.reason}"})
            }
            
        assistant_response = response.get("generated_text", "No response content")
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": True,
                    "response": assistant_response,
                    "conversationHistory": messages
                })
        }

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
        }
