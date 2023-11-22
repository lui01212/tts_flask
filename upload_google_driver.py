import os
import re
import time
import requests
import json

def get_request(url, params=None, jwt=None):
    headers = {}
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print('GET request failed:', e)
        return None

def post_request(url, data=None, json=None):
    headers = {}
    try:
        response = requests.post(url, data=data, json=json, headers=headers)
        response.raise_for_status()
        #print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Failed to get JSON:', e)
    except requests.exceptions.RequestException as e:
        print('POST request failed:', e)
        return None
def put_request(url, data=None, json=None):
    headers = {}
    try:
        response = requests.put(url, data=data, json=json, headers=headers)
        response.raise_for_status()
        print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Failed to get JSON:', e)
    except requests.exceptions.RequestException as e:
        print('PUT request failed:', e)
        return None

def create_folder_id(folder_name):
    access_token = get_request('https://server.audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/drive/v3/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    folder_metadata = {
        'name': f'{folder_name}',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    response = requests.post(endpoint, headers=headers, json=folder_metadata)
    if response.status_code == 200:
        folder_data = response.json()
        folder_id = folder_data['id']
        return folder_id
    else:
        return None

def create_child_folder_id(folder_name, folder_id):
    access_token = get_request('https://server.audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/drive/v3/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    folder_metadata = {
        'name': f'{folder_name}',
        'parents': [f'{folder_id}'],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    response = requests.post(endpoint, headers=headers, json=folder_metadata)
    if response.status_code == 200:
        folder_data = response.json()
        folder_id = folder_data['id']
        return folder_id
    else:
        return None

def create_up_chapter_by_book_id(id):
    folder_id = ""
    text_folder_id = ""
    book = get_request(f'https://server.audiotruyencv.org/api/book/{id}')
    if book is not None:
        if book["Folderid"] is None:
            folder_id = create_folder_id(book["Booknm"])
            if folder_id is not None:
                text_folder_id = create_child_folder_id("text", folder_id)
                if text_folder_id is not None:
                    post_response = put_request('https://server.audiotruyencv.org/api/book/update-folder-id', json={"Id": book["Id"], "Folderid": folder_id, "Textfolderid": text_folder_id, "Audiofolderid": book["AudioFolderId"]})
                    if post_response is None:
                        print("Lỗi khi update Textfolderid lên Book : " + book["Booknm"])
                        return False
                else:
                    print("Lỗi khi tạo Textfolderid của Book : " + book["Booknm"])
                    return False     
            else: 
                print("không tạo được folder_id của Book : " + book["Booknm"])
                return False
        else:
              folder_id = book["Folderid"]
              text_folder_id = book["TextFolderId"]

        if folder_id is not None:
              chapters = get_request(f'https://server.audiotruyencv.org/api/chapter/{book["Id"]}/chapter-not-run')
            
              if chapters is not None:
                  for chapter in chapters:
                      chapter_data = get_request(f'https://server.audiotruyencv.org/api/chapter/{chapter["Id"]}')
                      if chapter_data is not None:
                          if chapter_data["Status"] == '1':
                              continue
                          if chapter_data["Status"] == '3':
                              continue

                          upload_file(chapter_data, text_folder_id)
                        

def replace_source(text):
    return text.replace("truyenfull.vn", "audiotruyencv.org")

def upload_text_on_folder_id(file_name, folder_id, text):
    access_token = get_request('https://server.audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    metadata = {
        'name': f'{file_name}.txt',
        'parents': [f'{folder_id}']
    }

    file_path = './chapter.txt'

    try:
        os.remove(file_path)
    except OSError:
        pass

    with open('chapter.txt', 'w') as f:
        f.write(text)
    files = {
        'data': ('metadata', json.dumps(metadata), 'application/json; charset=UTF-8'),
        'file': open(file_path, "rb")
    }
    response = requests.post(endpoint, headers=headers, files=files)
    if response.status_code == 200:
        uploaded_file_data = response.json()
        file_id = uploaded_file_data['id']
        return file_id
    else:
        return None

def upload_file(chapter, text_folder_id):
    
    try:
        chapter_content = chapter["Content"]
        if chapter_content is not None:

            chapter_content = replace_source(chapter_content)

            status_upload_text_on_folder_id = upload_text_on_folder_id(chapter['Name'] + "-" + chapter["Id"], text_folder_id, chapter_content)
            
            if status_upload_text_on_folder_id is not None:
                #print(status_upload_text_on_folder_id)
                post_response = put_request('https://server.audiotruyencv.org/api/chapter/update-info', json={"Id": chapter["Id"], "Status": "3", "Audiofileid": chapter["AudioFileid"], "Textfileid": status_upload_text_on_folder_id})
                #print(post_response)
                #return False
                if post_response is None:
                    return "lỗi khi cập nhật Textfileid ở Chapter"
                else:
                    print(chapter["Id"] + chapter['Name'] + ": Thành Công")
            else:
                return "lỗi khi tạo  Textfileid"
            return "success"
        else:
            return False
    except Exception as e:
        return str(e)
        
def run_all_book():
    books = [
                # "9df70521-f9d8-4110-813d-2ec59819b7d3"

                # "a8e1bb82-6822-4649-b42f-85e374ea521e"

                "9ffae82b-76cd-421d-8856-2fb39b459596"

                # "7c3eb695-a9a4-413b-ba66-1b55a7cd8ce9",
                # "9fda5a86-1adb-482f-88ad-19c321c19ecf",
                # "74183b16-0426-4c4a-a754-e2758dd201c7"
                ]
    for book in books:
        create_up_chapter_by_book_id(book)

run_all_book()