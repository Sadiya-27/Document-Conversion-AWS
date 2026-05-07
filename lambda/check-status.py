import boto3
import json
import os

s3 = boto3.client("s3")
BUCKET_NAME = "document-converter-bucket-v1"

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }

    params = event.get("queryStringParameters") or {}
    input_key = params.get("key")

    if not input_key:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Missing key"})
        }

    basename = os.path.splitext(os.path.basename(input_key))[0]
    output_key = f"output/{basename}.pdf"

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=output_key)

        # ✅ Direct public URL
        pdf_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{output_key}"

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "status": "ready",
                "pdfUrl": pdf_url
            })
        }

    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"status": "processing"})
            }
        else:
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({"error": str(e)})
            }