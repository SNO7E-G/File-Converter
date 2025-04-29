"""
Storage utility module for handling file storage in different backends.
Supports local filesystem, AWS S3, Google Cloud Storage, and Azure Blob Storage.
"""

import os
import logging
import shutil
import uuid
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage as gcloud_storage
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from io import BytesIO
from werkzeug.utils import secure_filename
from app.config import Config

# Set up logging
logger = logging.getLogger(__name__)

class StorageFactory:
    """Factory for creating storage handlers based on configuration"""
    
    @staticmethod
    def get_storage_handler(storage_type=None):
        """
        Get the appropriate storage handler based on type
        
        Args:
            storage_type: Type of storage ('local', 's3', 'gcs', 'azure')
            
        Returns:
            StorageHandler: Instance of the appropriate storage handler
        """
        if not storage_type:
            storage_type = os.environ.get('STORAGE_TYPE', 'local')
            
        storage_type = storage_type.lower()
        
        if storage_type == 'local':
            return LocalStorageHandler()
        elif storage_type == 's3':
            return S3StorageHandler()
        elif storage_type == 'gcs':
            return GCSStorageHandler()
        elif storage_type == 'azure':
            return AzureStorageHandler()
        else:
            logger.warning(f"Unknown storage type: {storage_type}, falling back to local storage")
            return LocalStorageHandler()

class BaseStorageHandler:
    """Base class for all storage handlers"""
    
    def save_file(self, file_obj, filename=None, directory=None):
        """
        Save a file to storage
        
        Args:
            file_obj: File-like object or path to file
            filename: Name to save the file as (optional)
            directory: Directory path within the storage (optional)
            
        Returns:
            str: URL or path to the stored file
        """
        raise NotImplementedError("Subclasses must implement save_file method")
    
    def get_file(self, file_path):
        """
        Get a file from storage
        
        Args:
            file_path: Path or URL to the file
            
        Returns:
            BytesIO: File-like object containing the file data
        """
        raise NotImplementedError("Subclasses must implement get_file method")
    
    def delete_file(self, file_path):
        """
        Delete a file from storage
        
        Args:
            file_path: Path or URL to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement delete_file method")
    
    def get_file_url(self, file_path, expiry=None):
        """
        Get a URL for accessing the file
        
        Args:
            file_path: Path to the file
            expiry: Expiration time in seconds (optional)
            
        Returns:
            str: URL to access the file
        """
        raise NotImplementedError("Subclasses must implement get_file_url method")

class LocalStorageHandler(BaseStorageHandler):
    """Handler for local filesystem storage"""
    
    def __init__(self):
        """Initialize the local storage handler"""
        self.base_dir = os.environ.get('UPLOAD_DIR', Config.UPLOAD_DIR)
        self.base_url = os.environ.get('UPLOAD_URL', '/uploads')
        
        # Ensure the directory exists
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save_file(self, file_obj, filename=None, directory=None):
        """Save a file to the local filesystem"""
        if not filename:
            if hasattr(file_obj, 'filename'):
                filename = secure_filename(file_obj.filename)
            else:
                filename = f"{uuid.uuid4()}"
        
        # Create subdirectory based on date
        if not directory:
            today = datetime.now().strftime('%Y-%m-%d')
            directory = os.path.join(self.base_dir, today)
        else:
            directory = os.path.join(self.base_dir, directory)
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Full path to save file
        file_path = os.path.join(directory, filename)
        
        # Save the file
        if hasattr(file_obj, 'save'):
            # If it's a werkzeug file object
            file_obj.save(file_path)
        elif hasattr(file_obj, 'read'):
            # If it's a file-like object
            with open(file_path, 'wb') as f:
                f.write(file_obj.read())
        elif isinstance(file_obj, str) and os.path.exists(file_obj):
            # If it's a path to a file
            shutil.copy(file_obj, file_path)
        else:
            raise ValueError("Invalid file object provided")
        
        # Return relative path from base_dir
        return os.path.relpath(file_path, self.base_dir)
    
    def get_file(self, file_path):
        """Get a file from the local filesystem"""
        full_path = os.path.join(self.base_dir, file_path)
        
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return None
        
        file_data = BytesIO()
        with open(full_path, 'rb') as f:
            file_data.write(f.read())
        
        file_data.seek(0)
        return file_data
    
    def delete_file(self, file_path):
        """Delete a file from the local filesystem"""
        full_path = os.path.join(self.base_dir, file_path)
        
        if not os.path.exists(full_path):
            logger.warning(f"File not found for deletion: {full_path}")
            return False
        
        try:
            os.remove(full_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting file {full_path}: {str(e)}")
            return False
    
    def get_file_url(self, file_path, expiry=None):
        """Get URL for a file in the local filesystem"""
        # For local storage, we just return a relative URL
        return f"{self.base_url}/{file_path}"

class S3StorageHandler(BaseStorageHandler):
    """Handler for AWS S3 storage"""
    
    def __init__(self):
        """Initialize the S3 storage handler"""
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', 'file-converter')
        self.region = os.environ.get('S3_REGION', 'us-east-1')
        self.base_prefix = os.environ.get('S3_PREFIX', '')
        
        # Create S3 client
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
    
    def save_file(self, file_obj, filename=None, directory=None):
        """Save a file to S3"""
        if not filename:
            if hasattr(file_obj, 'filename'):
                filename = secure_filename(file_obj.filename)
            else:
                filename = f"{uuid.uuid4()}"
        
        # Create key based on directory and date
        if not directory:
            today = datetime.now().strftime('%Y-%m-%d')
            key = f"{self.base_prefix}/{today}/{filename}"
        else:
            key = f"{self.base_prefix}/{directory}/{filename}"
        
        # Remove leading slash if present
        key = key.lstrip('/')
        
        # Upload file
        try:
            if hasattr(file_obj, 'read'):
                # If it's a file-like object
                self.s3.upload_fileobj(file_obj, self.bucket_name, key)
            elif isinstance(file_obj, str) and os.path.exists(file_obj):
                # If it's a path to a file
                self.s3.upload_file(file_obj, self.bucket_name, key)
            else:
                raise ValueError("Invalid file object provided")
            
            return key
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise
    
    def get_file(self, file_path):
        """Get a file from S3"""
        file_data = BytesIO()
        try:
            self.s3.download_fileobj(self.bucket_name, file_path, file_data)
            file_data.seek(0)
            return file_data
        except ClientError as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Delete a file from S3"""
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            logger.error(f"Error deleting from S3: {str(e)}")
            return False
    
    def get_file_url(self, file_path, expiry=None):
        """Get a presigned URL for a file in S3"""
        if not expiry:
            expiry = 3600  # Default to 1 hour
        
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expiry
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating S3 URL: {str(e)}")
            return None

class GCSStorageHandler(BaseStorageHandler):
    """Handler for Google Cloud Storage"""
    
    def __init__(self):
        """Initialize the GCS storage handler"""
        self.bucket_name = os.environ.get('GCS_BUCKET_NAME', 'file-converter')
        self.base_prefix = os.environ.get('GCS_PREFIX', '')
        
        # Create GCS client (uses application default credentials)
        self.client = gcloud_storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
    
    def save_file(self, file_obj, filename=None, directory=None):
        """Save a file to GCS"""
        if not filename:
            if hasattr(file_obj, 'filename'):
                filename = secure_filename(file_obj.filename)
            else:
                filename = f"{uuid.uuid4()}"
        
        # Create blob name based on directory and date
        if not directory:
            today = datetime.now().strftime('%Y-%m-%d')
            blob_name = f"{self.base_prefix}/{today}/{filename}"
        else:
            blob_name = f"{self.base_prefix}/{directory}/{filename}"
        
        # Remove leading slash if present
        blob_name = blob_name.lstrip('/')
        
        # Upload file
        blob = self.bucket.blob(blob_name)
        
        try:
            if hasattr(file_obj, 'read'):
                # If it's a file-like object
                content = file_obj.read()
                blob.upload_from_string(content)
            elif isinstance(file_obj, str) and os.path.exists(file_obj):
                # If it's a path to a file
                blob.upload_from_filename(file_obj)
            else:
                raise ValueError("Invalid file object provided")
            
            return blob_name
        except Exception as e:
            logger.error(f"Error uploading to GCS: {str(e)}")
            raise
    
    def get_file(self, file_path):
        """Get a file from GCS"""
        blob = self.bucket.blob(file_path)
        file_data = BytesIO()
        
        try:
            blob.download_to_file(file_data)
            file_data.seek(0)
            return file_data
        except Exception as e:
            logger.error(f"Error downloading from GCS: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Delete a file from GCS"""
        blob = self.bucket.blob(file_path)
        
        try:
            blob.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting from GCS: {str(e)}")
            return False
    
    def get_file_url(self, file_path, expiry=None):
        """Get a signed URL for a file in GCS"""
        blob = self.bucket.blob(file_path)
        
        if not expiry:
            expiry = 3600  # Default to 1 hour
        
        try:
            url = blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(seconds=expiry),
                method='GET'
            )
            return url
        except Exception as e:
            logger.error(f"Error generating GCS URL: {str(e)}")
            return None

class AzureStorageHandler(BaseStorageHandler):
    """Handler for Azure Blob Storage"""
    
    def __init__(self):
        """Initialize the Azure storage handler"""
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.environ.get('AZURE_CONTAINER_NAME', 'file-converter')
        self.base_prefix = os.environ.get('AZURE_PREFIX', '')
        self.account_name = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
        self.account_key = os.environ.get('AZURE_STORAGE_ACCOUNT_KEY')
        
        # Create Azure client
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
        # Create container if it doesn't exist
        try:
            self.container_client.get_container_properties()
        except Exception:
            self.container_client.create_container()
    
    def save_file(self, file_obj, filename=None, directory=None):
        """Save a file to Azure Blob Storage"""
        if not filename:
            if hasattr(file_obj, 'filename'):
                filename = secure_filename(file_obj.filename)
            else:
                filename = f"{uuid.uuid4()}"
        
        # Create blob name based on directory and date
        if not directory:
            today = datetime.now().strftime('%Y-%m-%d')
            blob_name = f"{self.base_prefix}/{today}/{filename}"
        else:
            blob_name = f"{self.base_prefix}/{directory}/{filename}"
        
        # Remove leading slash if present
        blob_name = blob_name.lstrip('/')
        
        # Get blob client
        blob_client = self.container_client.get_blob_client(blob_name)
        
        try:
            if hasattr(file_obj, 'read'):
                # If it's a file-like object
                content = file_obj.read()
                blob_client.upload_blob(content, overwrite=True)
            elif isinstance(file_obj, str) and os.path.exists(file_obj):
                # If it's a path to a file
                with open(file_obj, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
            else:
                raise ValueError("Invalid file object provided")
            
            return blob_name
        except Exception as e:
            logger.error(f"Error uploading to Azure: {str(e)}")
            raise
    
    def get_file(self, file_path):
        """Get a file from Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(file_path)
        file_data = BytesIO()
        
        try:
            download_stream = blob_client.download_blob()
            file_data.write(download_stream.readall())
            file_data.seek(0)
            return file_data
        except Exception as e:
            logger.error(f"Error downloading from Azure: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Delete a file from Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(file_path)
        
        try:
            blob_client.delete_blob()
            return True
        except Exception as e:
            logger.error(f"Error deleting from Azure: {str(e)}")
            return False
    
    def get_file_url(self, file_path, expiry=None):
        """Get a SAS URL for a file in Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(file_path)
        
        if not expiry:
            expiry = 3600  # Default to 1 hour
        
        try:
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                account_key=self.account_key,
                container_name=self.container_name,
                blob_name=file_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiry)
            )
            
            # Build the URL
            url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{file_path}?{sas_token}"
            return url
        except Exception as e:
            logger.error(f"Error generating Azure URL: {str(e)}")
            return None 