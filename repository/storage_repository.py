import os
import tempfile
from google.cloud import storage
from werkzeug.datastructures import FileStorage
from io import BytesIO


class StorageRepository:
    def __init__(self, storage_client: storage.Client, review_bucket: str, production_bucket: str):
        self.review_bucket = review_bucket
        self.production_bucket = production_bucket
        self.storage_client = storage_client

    def _get_next_version(self, blob_prefix: str) -> int:
        """
        Get the next available version number for a given blob prefix.

        Args:
            blob_prefix: The prefix to check versions for (e.g. 'artist/album/title/')

        Returns:
            int: The next available version number
        """
        bucket = self.storage_client.bucket(self.review_bucket)
        blobs = bucket.list_blobs(prefix=blob_prefix)
        versions = set()

        for blob in blobs:
            try:
                version = int(blob.name.split("/")[-2])
                versions.add(version)
            except (ValueError, IndexError):
                continue

        if not versions:
            return 1
        return max(versions) + 1

    def _get_blob_path(self, artist: str, album: str, title: str, filename: str) -> str:
        """
        Generate a versioned blob path following the structure: artist/album/title/version/filename

        Args:
            artist: Artist name
            album: Album name
            title: Song title
            filename: Name of the file to store

        Returns:
            str: The complete blob path
        """
        artist = artist.strip()
        album = album.strip()
        title = title.strip()

        base_path = f"{artist}/{album}/{title}"
        version = self._get_next_version(base_path)

        return f"{base_path}/{version}/{filename}"

    def upload_file(
        self, file: FileStorage, artist: str, album: str, title: str
    ) -> str:
        """
        Uploads a file to Google Cloud Storage bucket using the versioned path structure.

        Args:
            file: The file to upload
            artist: Artist name
            album: Album name
            title: Song title

        Returns:
            str: The public URL of the uploaded file
        """
        destination_blob_name = self._get_blob_path(artist, album, title, file.filename)
        bucket = self.storage_client.bucket(self.review_bucket)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file, content_type=file.content_type)
        return f"gs://{self.review_bucket}/{destination_blob_name}"

    def upload_file_object(
        self,
        file_object: BytesIO,
        artist: str,
        album: str,
        title: str,
        filename: str,
        content_type: str,
    ) -> str:
        """
        Uploads a file-like object to Google Cloud Storage bucket using the versioned path structure.

        Args:
            file_object: The file-like object to upload
            artist: Artist name
            album: Album name
            title: Song title
            filename: Name of the file to store
            content_type: The content type of the file

        Returns:
            str: The public URL of the uploaded file
        """
        destination_blob_name = self._get_blob_path(artist, album, title, filename)
        bucket = self.storage_client.bucket(self.review_bucket)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_file(file_object, content_type=content_type)
        return f"gs://{self.review_bucket}/{destination_blob_name}"

    def delete_file(self, blob_name: str) -> None:
        """
        Deletes a file from Google Cloud Storage bucket.

        Args:
            blob_name: The name of the blob to delete
        """
        bucket = self.storage_client.bucket(self.review_bucket)
        blob = bucket.blob(blob_name)
        blob.delete()

    def get_file_url(self, blob_name: str) -> str:
        """
        Gets the public URL for a file in Google Cloud Storage.

        Args:
            blob_name: The name of the blob

        Returns:
            str: The public URL of the file
        """
        return f"gs://{self.review_bucket}/{blob_name}"

    def download_file(self, gcs_url: str) -> str:
        """
        Downloads a file from Google Cloud Storage to a temporary location.

        Args:
            gcs_url: The GCS URL of the file (gs://bucket-name/path/to/file)

        Returns:
            str: The path to the downloaded file
        """
        if not gcs_url.startswith("gs://"):
            return gcs_url

        path = gcs_url.replace(f"gs://{self.review_bucket}/", "")
        bucket = self.storage_client.bucket(self.review_bucket)
        blob = bucket.blob(path)

        temp_dir = tempfile.gettempdir()
        local_path = os.path.join(temp_dir, os.path.basename(path))

        blob.download_to_filename(local_path)
        return local_path

    def move_approved_transcription(
        self, artist: str, album: str, title: str, version: int
    ) -> dict:
        """
        Moves approved transcription files from review bucket to final storage bucket.

        Args:
            artist: Artist name
            album: Album name
            title: Song title
            version: Version number to move

        Returns:
            dict: Dictionary with new URLs for the moved files
        """
        source_prefix = f"{artist}/{album}/{title}/{version}/"
        source_bucket = self.storage_client.bucket(self.review_bucket)
        target_bucket = self.storage_client.bucket(self.production_bucket)

        moved_files = {}
        blobs = list(source_bucket.list_blobs(prefix=source_prefix))

        if not blobs:
            raise FileNotFoundError(
                f"No files found in review bucket at {source_prefix}"
            )

        for source_blob in blobs:
            # Keep the same path structure in the production bucket
            file_name = source_blob.name

            # Copy to production bucket
            target_blob = target_bucket.blob(file_name)
            token = source_bucket.copy_blob(source_blob, target_bucket, file_name)

            # Delete from review bucket
            source_blob.delete()

            # Store the new URL
            moved_files[os.path.basename(file_name)] = (
                f"gs://{self.production_bucket}/{file_name}"
            )

        return moved_files
