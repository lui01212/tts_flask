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
                # "bccb2e5c-b63c-4f98-a27f-c35638268cfe",
                # "cef09e7e-d376-4db2-ae68-d4786c9694a0",
                # "d687c2aa-09f9-478c-879f-5510015aa89b",
                # "9e2027ea-c223-4baf-b258-567a8ada0a73",
                # "d87df77d-440f-48d5-9174-affca31612fe",
                # "279a5f74-dd12-4609-a9e5-54e8b86329b4",
                # "20bef995-b386-46bf-a88e-a675f3b244d0",
                # "c74434bc-cc36-4ca1-af22-f2f899015443",

                # "c76c6fca-cf7f-46f8-99e9-999530ff174e",
                # "d53e15f8-12b1-4220-ab28-e8295428912e",
                # "a0617033-328e-4f68-96f1-733f27cc8c1e",
                # "91ff63b2-cf8f-433c-b8a1-6127667c074c",
                # "9df70521-f9d8-4110-813d-2ec59819b7d3",
                # "9ffae82b-76cd-421d-8856-2fb39b459596",
                # "7c3eb695-a9a4-413b-ba66-1b55a7cd8ce9"

                # "dbae66a3-aa98-4816-91e9-144bd8ab0755",
                # "d39a7d54-fa1e-4732-91f8-a7cb552fb5b2",
                # "89857644-69f9-4f71-a35c-84cac539fae0",
                # "9ede1965-8a84-4ee9-b989-291d70f5cc49",
                # "0a96cc71-4a31-46fe-baf4-2b1db3351380",
                # "f7e63c72-1ea7-452d-af1d-e27bae1ed8dd",
                # "d0f82b0c-b389-4215-bff0-8327eb2676cf"

                # "d82a3b01-17ab-4b27-8076-a83a17dbbb74",
                # "85ffc8df-6125-4d16-9339-73b70b09f9c5",
                # "0a6de8fa-7b2c-4c48-a359-25d22ca3750b",
                # "937ad2b8-018f-4455-a1ce-2cd5bfc1f119"

                # "d2197384-d71e-47ed-8108-64e82b54ab6c",
                # "20c613d4-40ed-4596-a24c-a5ab0730b519",
                # "954a58de-9a4f-40d3-9d92-59e2dc943260",
                # "6fdd3d72-21d2-4fe4-91e1-1cb4496e994a"

                # "713ae243-9466-4884-ac4c-5324cc37e6c6",
                # "9b0fc0df-5cfb-4ef3-83d6-67e8fc8f6b99",
                # "73aed128-d73a-4439-a4ea-b755da42cf2e",
                # "d783d817-8910-4f64-9871-c1f8071ac990",
                # "ca14ea62-251f-40b1-8457-fc6a6964b6b4",
                # "ab0cca97-f873-4c22-9b71-b1217bef75f4",
                # "b43e8f22-6955-4599-aea9-c209eab9ebaa"

                "d266f870-844c-4404-939f-5b1836861152",
                "cbcd3186-0834-4ad7-8ad1-5fc99060ab57",
                "d3820c3b-51f2-4aa9-9fe6-863ef064e1ab",
                "e1c64a11-49c2-47e9-bd38-9fb24ebc71bb",
                "b8ebd810-36ba-4063-833d-3932ee41abdb"

                # "d19ba343-6437-47fd-9b10-e289d5a6cb7d",
                # "d5104879-84f6-4a14-96f6-42025bbd77f0",
                # "a1728647-bdf0-49d6-a999-f9643d9c4723",
                # "d5c986ca-584f-42b0-a3f4-53df6d2e6df7",

                # "28210745-e873-48f7-840c-3b64365ea722",
                # "9fda5a86-1adb-482f-88ad-19c321c19ecf",
                # "9f8d396f-8139-4ecb-91db-8d3eb11b2ece",
                # "233cbe1f-1624-4631-9ad8-53530d0ee7c2",
                # "d314db04-c60e-41ec-9550-3f176d5e2eb3",
                # "d0b3bf0f-8ea2-4b24-81e2-605bc1a9602b",
                # "a7f56c74-c463-4458-a5c7-22edec394ec6",

                # "9f2a605b-b1e5-4702-92c4-8afa91025a1e",
                # "3995c563-4305-497b-ba8c-ee84342ef4de",
                # "a2756db1-4b53-482f-b6c0-5259ce4e88e7",
                # "e0b98a64-81dd-4165-bcd5-0650bfa0c7a0",
                # "d1963d7a-d16b-4cb8-9911-01c42bc38c84",

                # "9e07a09f-8bc1-4933-95ac-e90ee6a4f4dd",
                # "e53365b6-37bf-4dc1-af81-0267f263d166",
                # "f83f5e22-f34e-4ded-b7dd-a34069d0db14",
                # "d6bb78b0-4a03-4076-b0f5-2e7c8dedac11",
                # "cdd6d5cd-5b44-41a5-ab5b-a9bf4a4b0573",

                # "9f16a682-be49-48c4-8315-c227d133fff2",
                # "54225702-6624-460e-9735-6259275cf18e",
                # "c68a0616-b749-4562-a240-0443f4e2b029",
                # "d52f7d62-823f-431e-8df6-b9ab97094fc1",
                # "a7a04c30-7a92-412a-8669-310cf8777424",
                # "f571e97c-b0be-48a8-9d82-a84f4b127e43"
                ]
    for book in books:
        create_up_chapter_by_book_id(book)

run_all_book()