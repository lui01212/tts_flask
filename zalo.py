from flask import Flask, request
from flask import send_file
from underthesea import sent_tokenize
from underthesea import text_normalize
import os
import re
import subprocess
import time
import requests
import json
from urllib.parse import quote
# import required modules
from time import sleep
import random

import nltk
nltk.download('punkt')

app = Flask(__name__)

app.config['idserver'] = ''
app.config['jwt'] = ''
app.config['refreshToken'] = ''

#-----------------------------------------

def split_text(payload):
    text = []
    MAX_LENGTH = 200

    payload = text_normalize(payload)

    if len(payload) <= MAX_LENGTH:
        return [payload]

    sentences = nltk.sent_tokenize(payload)
    sub_para = sentences[0]

    for sen in sentences[1:]:
        if len(sub_para) > 499:
            splits = sub_para.split(",")

            for split in splits:
                text.append(split)

            sub_para = sen
        elif len(sub_para) + len(sen) + 1 <= MAX_LENGTH:
            sub_para += " " + sen
        else:
            text.append(sub_para)
            sub_para = sen

    text.append(sub_para)

    return text

def contains_valid_characters(text):
    return any(char not in (',', '.', ' ', '!') for char in text)

def filter_elements_with_valid_characters(input_list):
    return [item for item in input_list if contains_valid_characters(item.strip())]

def progress_data(data):
    MAX_LENGTH = 499
    sentences = []
    current_sentence = data[0]

    for word in data[1:]:
        if len(current_sentence) + len(word) <= MAX_LENGTH:
            current_sentence += word
        else:
            sentences.append(current_sentence)
            current_sentence = word

    sentences.append(current_sentence)
    return sentences

def remove_meaningless_characters(text):
    meaningless_chars = ['-', '_', '(', ')', '[', ']', '{', '}', '<', '>', '*', '/', '\\',
                         '|', '@', '#', '$', '%', '^', '&', '=', '+', '~', '`', '"', "'", '\n', '\r', '\t']

    for char in meaningless_chars:
        text = text.replace(char, '')

    return text

def data_processor(text):
    lst = split_text(text)
    lst = list(map(remove_meaningless_characters, lst))
    lst = filter_elements_with_valid_characters(lst)
    sentence = progress_data(lst)

    return sentence

#-----------------------------------------------------------------------------------------

def zalo_api(data):
    # get proxies
    source = "https://zalo.ai/"
    url = "https://zalo.ai/api/demo/v1/tts/synthesize"

    f = open("output.txt", "w")
    cookie = ''
    for p in data:
        session = requests.Session()
        text = quote(str(p))
        response = session.get(source)
        cookie = response.cookies.get_dict()
        payload = "input=" + text + "&speaker_id=1&speed=0.9&dict_id=0&quality=1"
        for k, v in cookie.items():
            cookie = k + '=' + v

        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "origin": "https://zalo.ai",
            "referer": "https://zalo.ai/experiments/text-to-audio-converter",
            "cookie": cookie,
        }

        response = requests.request("POST", url, data=payload.encode(
            'utf-8'), headers=headers)

        print(response.text)
        f.write(response.text + "\n")

    f.close()


def get_links():
    out = open('output.txt', 'r').read()
    links = re.findall(
        r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}.m3u8)', out)
    return links

def connect_audio(links):
    id = 1
    path = str(os.getcwd())
    full = path + '/tmp_audio/'
    command = 'cd ' + full + ' && rm -rf *'
    os.system(command)
    f = open('list_name.txt', 'w')
    for i in links:
        url = i
        des_fol = str(os.getcwd()) + "/tmp_audio/"
        namefile = str(id) + ".mp3"
        command = 'ffmpeg  -i ' + url + ' -ab 64k ' + des_fol + namefile + ' -y'
        id = id + 1
        os.system(command)
        f.write("file '" + full + namefile + "'\n")
    f.close()
    print("done")

def mer_audio(id):
    path_list = str(os.getcwd()) + "/list_name.txt"
    path = str(os.getcwd()) + "/final_audio/"
    mp3_path = path + "clip.mp3"
    command = 'ffmpeg -f concat -safe 0 -i ' + \
        path_list + ' -c copy '+mp3_path + ' -y'
    os.system(command)
    mp3_path = mp3_path.replace(os.getcwd(), '.')
    return mp3_path

def delete_all_file():
    for file_name in os.listdir("./"):
        if file_name.endswith((".wav", ".mp3", ".txt")):
            file_path = os.path.join("./", file_name)
            os.remove(file_path)
    for file_name in os.listdir("./tmp_audio"):
        if file_name.endswith((".wav", ".mp3", ".txt")):
            file_path = os.path.join("./tmp_audio/", file_name)
            os.remove(file_path)
    for file_name in os.listdir("./final_audio"):
        if file_name.endswith((".wav", ".mp3", ".txt")):
            file_path = os.path.join("./final_audio/", file_name)
            os.remove(file_path)


def add_guide(text):
    try:
        os.system("windscribe connect")
        time.sleep(20)
        path = str(os.getcwd()) + "/tmp_audio/"
        if os.path.exists(path) == False:
            os.system("mkdir tmp_audio")

        path = str(os.getcwd()) + "/final_audio/"
        if os.path.exists(path) == False:
            os.system("mkdir final_audio")

        lst = data_processor(text)
        zalo_api(lst)
        links = get_links()
        connect_audio(links)
        path = mer_audio(id)
    except Exception as e:
        return str(e)
    finally:
        os.system("windscribe disconnect")

    return "success"

def get_request(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print('GET request failed:', e)
        return None

def post_request(url, data=None, json=None):
    try:
        response = requests.post(url, data=data, json=json)
        response.raise_for_status()
        print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Failed to get JSON:', e)
    except requests.exceptions.RequestException as e:
        print('POST request failed:', e)
        return None

def put_request(url, data=None, json=None):
    try:
        response = requests.put(url, data=data, json=json)
        response.raise_for_status()
        print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Failed to get JSON:', e)
    except requests.exceptions.RequestException as e:
        print('PUT request failed:', e)
        return None

def create_child_folder_id(folder_name, folder_id):
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["token"]
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

def create_folder_id(folder_name):
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["token"]
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

def upload_audio_on_folder_id(file_name, folder_id):
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    metadata = {
        'name': f'{file_name}.mp3',
        'parents': [f'{folder_id}']
    }
    file_path = "./final_audio/clip.mp3"
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

def upload_text_on_folder_id(file_name, folder_id, text):
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    metadata = {
        'name': f'{file_name}.txt',
        'parents': [f'{folder_id}']
    }
    with open('chapter.txt', 'w') as f:
        f.write(text)
    file_path = './chapter.txt'
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

def get_all_folder():
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/drive/v3/files'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
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
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["Token"]
    endpoint = 'https://www.googleapis.com/drive/v3/files'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': f"'{folder_id}' in parents",
        'fields': 'files(id, name)'
    }
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

def create_file_audio(chapter, audio_folder_id, text_folder_id):
    print("start chapter")
    try:
        chapter_content = chapter["Content"]
        if chapter_content is not None:
            status_add_guide = add_guide(chapter["Content"])
            if status_add_guide == "success":
                status_upload_audio_on_folder_id = upload_audio_on_folder_id(chapter["Id"], audio_folder_id)
                status_upload_text_on_folder_id = upload_text_on_folder_id(chapter["Id"], text_folder_id, chapter["Content"])
            else:
                return status_add_guide
            if status_upload_audio_on_folder_id is not None and status_upload_text_on_folder_id is not None:
                post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"Id": chapter["Id"], "Status": "1", "Audiofileid": status_upload_audio_on_folder_id, "Textfileid": status_upload_text_on_folder_id})
                print("end chapter")
                if post_response is None:
                    return "lỗi khi cập nhật Audiofileid và Textfileid ở Chapter"
            else:
                return "lỗi khi tạo Audiofileid và Textfileid"
            return "success"
        else:
            post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"Id": chapter["Id"], "Status": "2"})
            return "lỗi lấy nội dung chương None"
    except Exception as e:
        post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"Id": chapter["Id"], "Status": "2"})
        return str(e)


def create_audio_all_chapter_by_book_id(id):
    folder_id = ""
    audio_folder_id = ""
    text_folder_id = ""
    book = get_request(f'https://audiotruyencv.org/api/book/{id}')
    if book is not None:
        
        if book["Folderid"] is None:
            folder_id = create_folder_id(book["Id"])
            if folder_id is not None:
                audio_folder_id = create_child_folder_id("audio", folder_id)
                text_folder_id = create_child_folder_id("text", folder_id)
                if audio_folder_id is not None and text_folder_id is not None:
                    post_response = put_request('https://audiotruyencv.org/api/book/update-folder-id', json={"Id": book["Id"], "Folderid": folder_id, "Textfolderid": text_folder_id, "Audiofolderid": audio_folder_id})
                    if post_response is None:
                        log_server("Lỗi khi update Textfolderid và Audiofolderid lên Book", "error")
                        return False
                else:
                    log_server("Lỗi khi tạo Textfolderid và Audiofolderid", "error")
                    return False     
            else: 
                log_server("không tạo được folder_id", "error")
                return False
        else:
            folder_id = book["Folderid"]
            audio_folder_id = book["AudioFolderId"]
            text_folder_id = book["TextFolderId"]
            
        if folder_id is not None:
            chapters = get_request(f'https://audiotruyencv.org/api/book/{book["Id"]}/chapter-not-run')
           
            if chapters is not None:
                
                for chapter in chapters:
                    server = get_request(f'https://audiotruyencv.org/api/server/{app.config["idserver"]}')
                    if server is None:
                        return False    
                    elif server["Status"] == "stop":
                        log_server("Đã đóng server theo yêu cầu")
                        return False
                    elif server["Status"] == "error":  
                        log_server("Server đang ở trạng thái error. Xin hãy kiểm tra hoặc chuyển sang start trước khi chạy")
                        return False 
                    
                    chapter_data = get_request(f'https://audiotruyencv.org/api/chapter/{chapter["Id"]}')
                    if chapter_data is not None:
                        if chapter_data["Status"] == '1':
                            continue
                        statusx = create_file_audio(chapter_data, audio_folder_id, text_folder_id)
                        if statusx != "success":
                            log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - Lỗi khi tạo file audio-" + statusx, "error", book["Id"], chapter_data["Id"])
                            return False
                        else:
                            log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - Tạo file audio thành công", None, book["Id"], chapter_data["Id"])
                    else:
                        log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - không tìm thấy chapter", "error", book["Id"], chapter_data["Id"])
            else:
                log_server("Không tìm thấy chapters chưa tạo audio", "error")
        else: 
            log_server("Không tìm thấy folder_id", "error")

        log_server(book["Booknm"] + "-" + "- Tạo all audio thành công", "stop")

    else:
        log_server(f'không tìm thấy bookId-{id}', "error")
    


def create_audio_chapter(bookid, chapterid):
    folder_id = ""
    audio_folder_id = ""
    text_folder_id = ""
    book = get_request(f'https://audiotruyencv.org/api/book/{bookid}')
    if book is not None:
        
        if book["Folderid"] is None:
            folder_id = create_folder_id(book["Id"])
            if folder_id is not None:
                audio_folder_id = create_child_folder_id("audio", folder_id)
                text_folder_id = create_child_folder_id("text", folder_id)
                if audio_folder_id is not None and text_folder_id is not None:
                    post_response = put_request('https://audiotruyencv.org/api/book/update-folder-id', json={"Id": book["Id"], "Folderid": folder_id, "Textfolderid": text_folder_id, "Audiofolderid": audio_folder_id})
                    if post_response is None:
                        log_server("Lỗi khi update Textfolderid và Audiofolderid lên Book", "error")
                        return False
                else:
                    log_server("Lỗi khi tạo Textfolderid và Audiofolderid", "error")
                    return False     
            else: 
                log_server("không tạo được folder_id", "error")
                return False
        else:
            folder_id = book["Folderid"]
            audio_folder_id = book["AudioFolderId"]
            text_folder_id = book["TextFolderId"]
            
        if folder_id is not None:
            server = get_request(f'https://audiotruyencv.org/api/server/{app.config["idserver"]}')
            if server is None:
                return False    
            elif server["Status"] == "stop":
                log_server("Đã đóng server theo yêu cầu")
                return False  
            elif server["Status"] == "error":  
                log_server("Server đang ở trạng thái error. Xin hãy kiểm tra hoặc chuyển sang start trước khi chạy")
                return False   
            
            chapter_data = get_request(f'https://audiotruyencv.org/api/chapter/{chapterid}')
            if chapter_data is not None:
                if chapter_data["Status"] == '1':
                    log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - chương đã được tạo audio trước" + statusx, "error", book["Id"], chapter_data["Id"])
                    return False
                statusx = create_file_audio(chapter_data, audio_folder_id, text_folder_id)
                if statusx != "success":
                    log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - Lỗi khi tạo file audio-" + statusx, "error", book["Id"], chapter_data["Id"])
                else:
                    log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - Tạo file audio thành công ", "stop")
            else:
                log_server(book["Booknm"] + "-" + chapter_data["Name"] + " - không tìm thấy chapter", "error", book["Id"], chapter_data["Id"])
        else: 
            log_server("Không tìm thấy folder_id", "error")
    else:
        log_server(f'không tìm thấy bookId-{bookid}', "error")



def log_server(Log, Status=None, Bookid=None, Chapterid=None):
    server = get_request(f'https://audiotruyencv.org/api/server/{app.config["idserver"]}')
    if Bookid is not None:
        server["Bookid"] = Bookid
    if Chapterid is not None:
        server["Chapterid"] = Chapterid
    if Status is not None:
        server["Status"] = Status
    server["Log"] = Log
    put_response = put_request(f'https://audiotruyencv.org/api/server/{server["Id"]}', json=server)
    if put_response is None:
        return False
    return True


@app.route('/create_audio_all_chapter_by_book_id', methods=["GET"])
def create_audio_all_chapter_by_book_id():

    AUTHORIZATION_HEADER = 'Authorization'

    try:
        id = request.args.get('id')
        app.config['idserver'] = request.args.get('idserver')

        if request.headers.get(AUTHORIZATION_HEADER):
            app.config['jwt'] = request.headers.get(AUTHORIZATION_HEADER)

        if 'refreshToken' in request.cookies:
            app.config['refreshToken'] = request.cookies.get('refreshToken')

        #if id is not None and app.config['idserver'] is not None:
        #    create_audio_all_chapter_by_book_id(id)
    except Exception as e:
        print("a" + str(e))

    return "đã hoàn thành tất cả các chapter của book"

@app.route('/create_audio_chapter', methods=["GET"])
def create_audio_chapter():
    AUTHORIZATION_HEADER = 'Authorization'
    try:
        bookid = request.args.get('bookid')
        chapterid = request.args.get('chapterid')
        app.config['idserver'] = request.args.get('idserver')
        if request.headers.get(AUTHORIZATION_HEADER):
            app.config['jwt'] = request.headers.get(AUTHORIZATION_HEADER)

        if 'refreshToken' in request.cookies:
            app.config['refreshToken'] = request.cookies.get('refreshToken')
        print(app.config['jwt'])
        print(app.config['refreshToken'])
        #if bookid is not None and chapterid is not None and app.config['idserver'] is not None:
        #    create_audio_chapter(bookid, chapterid)
    except Exception as e:
        print("a" + str(e))

    return "đã hoàn thành tất cả các chapter của book"

@app.route('/')
def hello_world():
    return 'hello_world!'
