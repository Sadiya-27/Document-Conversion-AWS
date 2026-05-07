import boto3
import subprocess
import os
import json
import shutil
import logging
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

BUCKET_NAME = "document-converter-bucket-v1"
SOFFICE = shutil.which("soffice") or "/usr/bin/soffice"

def prepare_fontconfig():
    font_cache = "/tmp/fontconfig-cache"
    fonts_conf = "/tmp/fonts.conf"

    os.makedirs(font_cache, exist_ok=True)

    with open(fonts_conf, "w") as f:
        f.write("""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/opt/libreoffice7.6/share/fonts</div>
  <dir>/opt/libreoffice7.6/share/fonts/truetype</dir>
  <dir>/opt/libreoffice7.6/share/fonts/opentype</dir>
  <cachedir>/tmp/fontconfig-cache</cachedir>
</fontconfig>
""")

    return fonts_conf

def convert_to_pdf(bucket, key):
    logger.info(f"Starting conversion: s3://{bucket}/{key}")
    logger.info(f"Using soffice at: {SOFFICE}")

    fonts_conf = prepare_fontconfig()

    input_path = f"/tmp/{os.path.basename(key)}"
    output_dir = "/tmp"

    # Download from S3
    logger.info(f"Downloading from S3...")
    s3.download_file(bucket, key, input_path)
    logger.info(f"Downloaded to {input_path}, size: {os.path.getsize(input_path)} bytes")

    profile_dir = "/tmp/lo-profile"
    os.makedirs(profile_dir, exist_ok=True)

    env = os.environ.copy()
    env["HOME"] = "/tmp"
    env["TMPDIR"] = "/tmp"
    env["FONTCONFIG_FILE"] = fonts_conf
    env["FONTCONFIG_PATH"] = "/tmp"
    env["LD_LIBRARY_PATH"] = "/opt/libreoffice7.6/program"
    env["LANG"] = "C"
    env["LC_ALL"] = "C"

    command = [
        SOFFICE,
        "--headless",
        "--nologo",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--norestore",
        "--invisible",
        "--nocrashreport",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", output_dir,
        input_path
    ]

    logger.info(f"Running command: {' '.join(command)}")

    result = subprocess.run(
        command,
        env=env,
        capture_output=True,
        text=True,
        timeout=120  # increased from 60
    )

    logger.info(f"soffice returncode: {result.returncode}")
    logger.info(f"soffice stdout: {result.stdout}")
    logger.info(f"soffice stderr: {result.stderr}")

    if result.returncode != 0:
        raise Exception(f"LibreOffice failed (code {result.returncode}): {result.stderr}")

    output_file = os.path.splitext(os.path.basename(key))[0] + ".pdf"
    output_path = f"/tmp/{output_file}"
    output_key = f"output/{output_file}"

    logger.info(f"Checking for output at: {output_path}")

    if not os.path.exists(output_path):
        files_in_tmp = os.listdir("/tmp")
        logger.error(f"PDF not found. Files in /tmp: {files_in_tmp}")
        raise Exception(f"PDF not created. Files in /tmp: {files_in_tmp}")

    logger.info(f"PDF created, size: {os.path.getsize(output_path)} bytes")

    # Upload PDF to S3
    s3.upload_file(
        output_path,
        bucket,
        output_key,
        ExtraArgs={"ContentType": "application/pdf"}
    )

    logger.info(f"Uploaded PDF to s3://{bucket}/{output_key}")

    # Cleanup
    os.remove(input_path)
    os.remove(output_path)

    return output_key

def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        # ── S3 trigger event ──────────────────────────────────────────
        if "Records" in event and event["Records"][0].get("eventSource") == "aws:s3":
            record = event["Records"][0]["s3"]
            bucket = record["bucket"]["name"]
            key = urllib.parse.unquote_plus(record["object"]["key"])

            logger.info(f"S3 trigger: bucket={bucket}, key={key}")

            # Skip if not in input/ folder (safety guard)
            if not key.startswith("input/"):
                logger.info(f"Skipping key not in input/: {key}")
                return {"statusCode": 200, "body": "Skipped"}

            output_key = convert_to_pdf(bucket, key)
            logger.info(f"S3 trigger conversion complete: {output_key}")
            return {"statusCode": 200, "body": json.dumps({"outputKey": output_key})}

        # ── API Gateway event (fallback / testing) ────────────────────
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        if method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": json.dumps({"message": "CORS OK"})
            }

        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        elif body is None:
            body = event

        bucket = body.get("bucket", BUCKET_NAME)
        key = body["key"]

        output_key = convert_to_pdf(bucket, key)

        pdf_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": output_key},
            ExpiresIn=3600
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"message": "Success", "pdfUrl": pdf_url})
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }