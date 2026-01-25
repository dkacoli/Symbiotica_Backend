import boto3
import os
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional
import hashlib

class S3StorageService:
    """S3-compatible object storage service"""
    
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET", "symbiotica-datasets")
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY", "minioadmin"),
            region_name=os.getenv("S3_REGION", "us-east-1"),
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure bucket exists, create if not"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
    
    def upload_chunk(
        self,
        file_data: bytes,
        dataset_id: str,
        chunk_number: int,
    ) -> tuple[str, str]:
        """Upload dataset chunk to S3"""
        s3_key = f"datasets/{dataset_id}/chunk_{chunk_number}.bin"
        checksum = hashlib.sha256(file_data).hexdigest()
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
              #  ServerSideEncryption="AES256",
                Metadata={
                    "dataset-id": dataset_id,
                    "chunk-number": str(chunk_number),
                    "sha256": checksum,
                }
            )
            return s3_key, checksum
        except ClientError as e:
            raise Exception(f"Failed to upload chunk: {str(e)}")
    
    def download_file(self, s3_key: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def get_file_metadata(self, s3_key: str) -> dict:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"],
            }
        except ClientError as e:
            raise Exception(f"Failed to get metadata: {str(e)}")