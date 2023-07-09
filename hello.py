from flask import Flask, request
from flask import send_file
from underthesea import sent_tokenize
from underthesea import text_normalize
from pydub import AudioSegment
from vietnam_number import n2w
from pyvi import ViTokenizer
import requests
import json
import re

import subprocess
app = Flask(__name__)


def process_text(text):
    # Phân tách văn bản thành danh sách các từ
    tokens = text.split()

    # Xử lý các từ chứa "z", "j", "w" và "F" dựa trên ngữ cảnh
    processed_tokens = []
    for token in tokens:
        if any(char in token for char in ['z', 'j', 'w', 'f', 'Z', 'J', 'W', 'F']):
            # Có ít nhất một chữ cái cần xử lý trong từ
            # Tiến hành xử lý từ
            token = token.replace('z', 'd').replace('j', 'gi').replace('w', 'qu').replace('f', 'ph').replace('Z', 'd').replace('J', 'gi').replace('W', 'qu').replace('F', 'ph')
        processed_tokens.append(token)

    # Gộp các từ đã xử lý thành văn bản mới
    processed_text = ' '.join(processed_tokens)

    return processed_text


def replace_numbers_with_letters(text):
    
    def replace(match):
        number = match.group(0)
        return n2w(number)
    
    return re.sub(r'\d+', replace, text)


def remove_meaningless_characters(text):
    meaningless_chars = ['-', '_', '(', ')', '[', ']', '{', '}', '<', '>', '*', '/', '\\', '|', '@', '#', '$', '%', '^', '&', '=', '+', '~', '`', '"', "'", '\n', '\r', '\t']
    
    for char in meaningless_chars:
        text = text.replace(char, '')
    
    return text

def add_guide(text):
    command_tts = ""
    step = ""
    text_cut = ""
    try:
        text_cut_nomal = sent_tokenize(text)
        text_cut_nomal = list(map(remove_meaningless_characters, text_cut_nomal))
        text_cut_nomal = list(map(replace_numbers_with_letters, text_cut_nomal))
        text_cut_nomal = list(map(process_text, text_cut_nomal))
        text_cut = list(map(text_normalize, text_cut_nomal))

        for i in range(len(text_cut)):
            command_tts = f'python3 -m vietTTS.synthesizer --lexicon-file assets/infore/lexicon.txt --text="{text_cut[i]}" --output=clip{i}.wav --silence-duration 0.2'
            result_tts = subprocess.check_output(
                        [command_tts], shell=True)

        combined_sounds = AudioSegment.from_wav(f'clip0.wav')

        for i in range(len(text_cut)):
            if i > 0 :
                sound = AudioSegment.from_wav(f'clip{i}.wav')
                combined_sounds += sound

        combined_sounds.export("clip.wav", format="wav")
        AudioSegment.from_wav("clip.wav").export("clip.mp3", format="mp3")

    except subprocess.CalledProcessError as e:
        print(e)
        return None

    return True


def get_request(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Nếu có lỗi, raise exception
        return response.json()
    except requests.exceptions.RequestException as e:
        print('Yêu cầu GET không thành công:', e)
        return None

def post_request(url, data=None, json=None):
    try:
        response = requests.post(url, data=data, json=json)
        response.raise_for_status()  # Nếu có lỗi, raise exception
        print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Lấy JSON không thành công:', e)
    except requests.exceptions.RequestException as e:
        print('Yêu cầu POST không thành công:', e)
        return None

def create_folder_id(folder_name):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/GetAccessToken')
    access_token = access_token["token"]
    # Define the API endpoint for creating a folder.
    endpoint = 'https://www.googleapis.com/drive/v3/files'

    # Define the headers for the API request.
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Define the metadata for the folder.
    folder_metadata = {
        'name': f'{folder_name}',
        'mimeType': 'application/vnd.google-apps.folder'
    }

    # Send the POST request to create the folder.
    response = requests.post(endpoint, headers=headers, json=folder_metadata)

    if response.status_code == 200:
        folder_data = response.json()
        folder_id = folder_data['id']
        return folder_id
    else:
        return None

def upload_file_on_folder_id(file_name ,folder_id):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/GetAccessToken')
    access_token = access_token["token"]
    # Define the API endpoint for file uploads.
    endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'

    # Define the headers for the API request.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

        # Define the metadata of the file to be uploaded.
    metadata = {
        'name': f'{file_name}.mp3',
        'parents': [f'{folder_id}']  # Replace with the desired parent folder ID
    }

    # Define the path to the file on your local machine.
    file_path = './clip.mp3'

    files = {
        'data': ('metadata', json.dumps(metadata), 'application/json; charset=UTF-8'),
        'file': open(file_path, "rb")
    }

    # Send the POST request to upload the file.
    response = requests.post(endpoint, headers=headers, files=files)

    if response.status_code == 200:
        uploaded_file_data = response.json()
        file_id = uploaded_file_data['id']
        return file_id
    else:
        return None

def get_all_folder():
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/GetAccessToken')
    access_token = access_token["token"]
    # Define the API endpoint.
    endpoint = 'https://www.googleapis.com/drive/v3/files'

    # Define the headers for the API requests.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Send a GET request to list files in Drive.
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        files_data = response.json()
        files = files_data.get('files', [])
        if files:
            print('Files in Drive:')
            for file in files:
                print(file['name'])
        else:
            print('No files found in Drive.')
    else:
        print('Failed to list files.')

def get_all_file_folder_id(folder_id):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/GetAccessToken')
    access_token = access_token["token"]

    # Define the API endpoint for retrieving files.
    endpoint = 'https://www.googleapis.com/drive/v3/files'

    # Define the headers for the API request.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Define the query parameters to search for files within the specified folder.
    params = {
        'q': f"'{folder_id}' in parents",
        'fields': 'files(id, name)'
    }

    # Send the GET request to retrieve the files.
    response = requests.get(endpoint, headers=headers, params=params)

    if response.status_code == 200:
        files_data = response.json()
        files = files_data.get('files', [])
        if files:
            print('Files in the folder:')
            for file in files:
                print(f"File ID: {file['id']}, File Name: {file['name']}")
        else:
            print('No files found in the folder.')
    else:
        print('Failed to retrieve files.')

def create_file_audio(chapter, folder_id):
    try:
        chapter_content = get_request(f'https://audiotruyencv.org/api/leech/GetChapterContent?Id={chapter["id"]}')
        if chapter_content is not None:
            status_add_guide = add_guide(chapter_content["content"])
            if status_add_guide is not None :
                status_upload_file_on_folder_id = upload_file_on_folder_id(chapter["id"], folder_id)
            if status_upload_file_on_folder_id is not None :
                post_response = post_request('https://audiotruyencv.org/api/chapter/UpdateInfo', json={"id" : chapter["id"], "status" : "1", "fileid": status_upload_file_on_folder_id})
                if post_response is None :
                    return False
            return True
        else:
            post_response = post_request('https://audiotruyencv.org/api/chapter/UpdateInfo', json={"id" : chapter["id"], "status" : "2"})
            return None
    except Exception as e:
            #print(e)
            post_response = post_request('https://audiotruyencv.org/api/chapter/UpdateInfo', json={"id" : chapter["id"], "status" : "2"})
            return None

def create_audio_all_chapter_by_book_id(id):
    # lấy sách
    folder_id = ""
    book = get_request(f'https://audiotruyencv.org/api/book/GetBook?Id={id}')
    if book is not None:
        if book["folderid"] is None :
            folder_id = create_folder_id(book["id"])
            if folder_id is not None:
                post_response = post_request('https://audiotruyencv.org/api/book/UpdateInfo', json={"id" : book["id"], "folderid" : folder_id})
            if post_response is None :
                return False
        else :
            folder_id = book["folderid"]
        if folder_id is not None :
            # lấy tất cả sách
            chapters = get_request(f'https://audiotruyencv.org/api/chapter/GetAllChapter?Id={book["id"]}')
            if chapters is not None:
                for x in chapters:
                    if x["status"] == '1':
                        continue
                    statusx = create_file_audio(x, folder_id)
                    break

def create_audio_all_book():
    # lấy tất cả sách
    books = get_request('https://audiotruyencv.org/api/book/GetAllBook')
    if books is not None:
        for x in books:
            create_audio_all_chapter_by_book_id(x["id"])

# Endpoint to create mp3 from text
@app.route('/create_audio_all_book', methods=["GET"])
def get_data():
    try:
        # Lấy giá trị của tham số id từ query string
        id = request.args.get('id')

        if id is not None:
            create_audio_all_chapter_by_book_id(id)
    except Exception as e:
            print("a" + e)
    # Trả về kết quả dưới dạng JSON
    return "đã hoàn thành"


@app.route('/')
def hello_world():
    return 'hello_world!'


@app.route('/download')
def downloadFile ():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "./clip.mp3"
    return send_file(path, as_attachment=True)
