import io
import os.path

from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_service():
    creds = None
    if os.path.exists("token.json"):
      creds = Credentials.from_authorized_user_file("token.json", SCOPES)
      
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
        
      with open("token.json", "w") as token:
        token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)



def upload_file(file_path, file_name):
    
    print("woeifjoewijfoiwejgoiwerjoiwejgoiwerjgoiewjgoiewjgoiwerjgoiwejgoiewjgoiewjoiewgjoiewgj")
    
    service = get_service()
    
    file_metadata = {'name': file_name}
    
    media = MediaFileUpload(file_path, mimetype='video/mp4')
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return uploaded_file.get('id')
  
  
def get_most_recent_video_id():
    service = get_service()
    
    # Search for the 1 most recently created mp4 file
    results = service.files().list(
        q="mimeType='video/mp4'",      # Only look for videos
        orderBy="createdTime desc",    # Sort by newest first
        pageSize=1,                    # We only need the top 1 result
        fields="files(id, name)"       # Only return the ID and Name
    ).execute()
    
    items = results.get('files', [])
    
    if not items:
        print("No videos found in your Drive!")
        return None, None
        
    recent_file = items[0]
    print(f"Found most recent video: {recent_file['name']}")
    
    return recent_file['id'], recent_file['name']


def download_recent_file():
    service = get_service()
    
    # 1. Get the ID of the newest video
    file_id, file_name = get_most_recent_video_id()
    
    if not file_id:
        return "Download failed: No file found."

    # 2. Request the download using that ID
    request = service.files().get_media(fileId=file_id)

    # 3. Save it to your computer
    print(f"Downloading {file_name}...")
    with open(file_name, "wb") as local_file:
        downloader = MediaIoBaseDownload(local_file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
            
    print("Download complete!")
    return file_name
            
            
if __name__ == "__main__":
    print("Attempting to log in to Google Drive...")
    # Calling this function will trigger the browser popup!
    get_service() 
    print("Success! token.json has been generated.")