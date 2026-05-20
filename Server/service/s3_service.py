from __future__ import annotations

import importlib
import os
from typing import Any, Optional

from dotenv import load_dotenv
from botocore.config import Config


load_dotenv()


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint:
        return endpoint
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"http://{endpoint}"


class S3Client:
    """Basic boto3 S3 client initializer.

    Default env keys supported:
      - AWS_S3_ENDPOINT_URL (preferred)
      - MINIO_ENDPOINT (fallback for local MinIO)
      - AWS_ACCESS_KEY_ID (preferred)
      - MINIO_ACCESS_KEY (fallback)
      - AWS_SECRET_ACCESS_KEY (preferred)
      - MINIO_SECRET_KEY (fallback)
      - AWS_DEFAULT_REGION (optional, default: us-east-1)
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
    ) -> None:
        endpoint_url = endpoint_url or os.getenv("AWS_S3_ENDPOINT_URL") or os.getenv("MINIO_ENDPOINT")
        access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ACCESS_KEY")
        secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_SECRET_KEY")
        region_name = region_name or os.getenv("MINIO_REGION", "us-east-1")

        if not endpoint_url or not access_key_id or not secret_access_key:
            raise ValueError("S3 endpoint URL and credentials must be provided")

        self.endpoint_url = _normalize_endpoint(endpoint_url)
        self.region_name = region_name
        boto3 = importlib.import_module("boto3")
        self.client: Any = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
            config=Config(signature_version='s3v4')
        )

    def __getattr__(self, item: str) -> Any:
        return getattr(self.client, item)

