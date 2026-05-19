# ==============================================================================
# S3 File Storage Service
# ==============================================================================
#
# Handles uploading and deleting files in the configured S3 bucket.
# Files are stored with UUID-based names to avoid collisions while preserving
# the original extension for content-type inference.

import uuid
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import settings


def get_s3_client():
    """Create and return a boto3 S3 client using app settings."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


def upload_file_to_s3(file: UploadFile, folder: str = "products") -> str:
    """Upload a file to S3 and return the public object URL.

    Generates a unique filename to avoid collisions while preserving the
    original file extension for content-type inference.
    """
    s3_client = get_s3_client()

    # Preserve original extension, generate unique name to avoid collisions.
    extension = PurePosixPath(file.filename).suffix if file.filename else ""
    unique_filename = f"{folder}/{uuid.uuid4()}{extension}"

    try:
        s3_client.upload_fileobj(
            file.file,
            settings.s3_bucket_name,
            unique_filename,
            ExtraArgs={
                "ContentType": file.content_type or "application/octet-stream"
            },
        )
    except ClientError as e:
        raise RuntimeError("upload file to S3") from e

    url = (
        f"https://{settings.s3_bucket_name}"
        f".s3.{settings.aws_region}.amazonaws.com/{unique_filename}"
    )
    return url


def delete_file_from_s3(file_url: str) -> None:
    """Delete a file from S3 given its full URL.

    Extracts the object key from the URL and issues a delete request.
    """
    s3_client = get_s3_client()

    # URL format: https://<bucket>.s3.<region>.amazonaws.com/<key>
    key = file_url.split(".amazonaws.com/", 1)[-1]

    try:
        s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
        )
    except ClientError as e:
        raise RuntimeError("delete file from S3") from e
