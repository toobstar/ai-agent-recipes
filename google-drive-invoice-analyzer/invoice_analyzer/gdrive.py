# gdrive.py
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveClient:
    """Client for interacting with Google Drive API."""
    
    def __init__(self, token_path: str = 'token.json', credentials_path: str = 'credentials.json'):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.service = self._authenticate()
        self.watched_folders = {}
        self.last_check_time = {}
        
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_info(
                eval(open(self.token_path, 'r').read()), SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(str(creds.to_json()))
                
        return build('drive', 'v3', credentials=creds)
    
    def get_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get contents of a folder by ID."""
        results = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)',
                pageToken=page_token
            ).execute()
            
            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
                
        return results
    
    def check_for_new_files(self, folder_id: str) -> List[Dict[str, Any]]:
        """Check for new files in a folder since last check."""
        if folder_id not in self.last_check_time:
            self.last_check_time[folder_id] = datetime.now().isoformat()
            return self.get_folder_contents(folder_id)
        
        last_check = self.last_check_time[folder_id]
        files = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed = false and modifiedTime > '{last_check}'",
            spaces='drive',
            fields='files(id, name, mimeType, createdTime, modifiedTime)'
        ).execute().get('files', [])
        
        self.last_check_time[folder_id] = datetime.now().isoformat()
        return files
    
    def download_file(self, file_id: str) -> bytes:
        """Download a file by ID."""
        request = self.service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        return file_content.getvalue()
    
    def is_pdf(self, file_info: Dict[str, Any]) -> bool:
        """Check if a file is a PDF."""
        return file_info.get('mimeType') == 'application/pdf'
    
    def start_watching_folder(self, folder_id: str, callback, interval: int = 60):
        """Start watching a folder for changes."""
        self.watched_folders[folder_id] = {
            'callback': callback,
            'interval': interval
        }
        
    def stop_watching_folder(self, folder_id: str):
        """Stop watching a folder."""
        if folder_id in self.watched_folders:
            del self.watched_folders[folder_id]
            
    def poll_watched_folders(self):
        """Poll all watched folders for changes."""
        for folder_id, config in self.watched_folders.items():
            new_files = self.check_for_new_files(folder_id)
            if new_files:
                config['callback'](new_files)
