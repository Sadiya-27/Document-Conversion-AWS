import boto3
import json
import time
import urllib.parse

s3 = boto3.client("s3")

BUCKET_NAME = "document-converter-bucket-v1"

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method")

        if method == "OPTIONS":
            return response(200, {"message": "CORS OK"})

        params = event.get("queryStringParameters") or {}

        file_name = params.get("fileName", f"upload-{int(time.time())}")
        content_type = params.get("contentType", "application/octet-stream")

        safe_file_name = urllib.parse.unquote(file_name).replace("/", "-").replace("\\", "-")
        key = f"input/{int(time.time())}-{safe_file_name}"

        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": key,
                "ContentType": content_type
            },
            ExpiresIn=300
        )

        return response(200, {
            "url": upload_url,
            "bucket": BUCKET_NAME,
            "key": key
        })

    except Exception as e:
        return response(500, {
            "error": str(e)
        })
