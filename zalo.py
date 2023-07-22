from underthesea import sent_tokenize
from underthesea import text_normalize
import os
import re
import subprocess
import time
import requests
import json

# import required modules
from time import sleep
import random



import nltk
nltk.download('punkt')
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
    return any(char not in (',', '.', ' ') for char in text)


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
    cookie=''
    for p in data:
        session = requests.Session()
        text = quote(str(p))
        response = session.get(source)
        cookie = response.cookies.get_dict()
        # text.encode('utf-8')  # Totally fine.
        payload = "input="+text+"&speaker_id=1&speed=0.9&dict_id=0&quality=1"
        for k,v in cookie.items():
            cookie = k+'='+v

        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=utf-8",
            "origin": "https://zalo.ai",
            "referer": "https://zalo.ai/experiments/text-to-audio-converter",
            "cookie": cookie,
        }

        response = requests.request("POST", url, data=payload.encode(
            'utf-8'), headers=headers)

        print(response.text)
        f.write(response.text+"\n")

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
    command = 'cd '+full+' && rm -rf *'
    os.system(command)
    f = open('list_name.txt', 'w')
    for i in links:
        url = i
        des_fol = str(os.getcwd())+"/tmp_audio/"
        namefile = str(id)+".mp3"
        command = 'ffmpeg  -i '+url+' -ab 128k ' + des_fol + namefile + ' -y'
        id = id + 1
        os.system(command)
        f.write("file '"+full+namefile+"'\n")
    f.close()
    print("done")

def mer_audio(id):
    path_list = str(os.getcwd()) + "/list_name.txt"
    path = str(os.getcwd())+"/final_audio/"
    mp3_path = path + "clip.mp3"
    command = 'ffmpeg -f concat -safe 0 -i ' + \
        path_list + ' -c copy '+mp3_path + ' -y'
    os.system(command)
    mp3_path = mp3_path.replace(os.getcwd(), '.')
    return mp3_path

def change_speed(input_file, output_file, speed):
    # Sử dụng ffmpeg để thay đổi tốc độ âm thanh của file WAV
    cmd = f'ffmpeg -i {input_file} -filter:a "atempo={speed}" -vn {output_file}'
    subprocess.call(cmd, shell=True)


def text_to_speech(text, filename):
    tts = gTTS(text=text, lang='vi')
    tts.save(filename)

def delete_all_file():
    for file_name in os.listdir("./"):
        if file_name.endswith((".wav", ".mp3",".txt")):
            file_path = os.path.join("./", file_name)
            os.remove(file_path)
    for file_name in os.listdir("./tmp_audio"):
      if file_name.endswith((".wav", ".mp3",".txt")):
          file_path = os.path.join("./", file_name)
          os.remove(file_path)
    for file_name in os.listdir("./final_audio"):
      if file_name.endswith((".wav", ".mp3",".txt")):
          file_path = os.path.join("./", file_name)
          os.remove(file_path)


def add_guide(text):
    try:
         # connect to VPN
        os.system("windscribe connect")
        
        path = str(os.getcwd()) + "/tmp_audio"

        if os.path.exists(path) == False:
            os.system("mkdir tmp_audio")

        path = str(os.getcwd()) + "/final_audio"

        if os.path.exists(path) == False:
            os.system("mkdir final_audio")

        lst = data_processor(text)

        zalo_api(sentence)
        links = get_links()
        connect_audio(links)
        path = mer_audio(id)

    except Exception as e:
        # disconnect VPN
        os.system("windscribe disconnect")
        print(e)
        return None
    finally:
        # disconnect VPN
        os.system("windscribe disconnect")

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

def put_request(url, data=None, json=None):
    try:
        response = requests.put(url, data=data, json=json)
        response.raise_for_status()  # Nếu có lỗi, raise exception
        print(response.status_code)
        try:
            return response.json()
        except ValueError as e:
            print('Lấy JSON không thành công:', e)
    except requests.exceptions.RequestException as e:
        print('Yêu cầu PUT không thành công:', e)
        return None

def create_child_folder_id(folder_name, folder_id):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
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
        'parents': [f'{folder_id}'],  # Replace with the desired parent folder ID
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

def create_folder_id(folder_name):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
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

def upload_audio_on_folder_id(file_name ,folder_id):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
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
    file_path = "./final_audio/clip.mp3"

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

def upload_text_on_folder_id(file_name ,folder_id, text):
    # Replace 'YOUR_ACCESS_TOKEN' with the actual access token.
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
    access_token = access_token["token"]
    # Define the API endpoint for file uploads.
    endpoint = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'

    # Define the headers for the API request.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

        # Define the metadata of the file to be uploaded.
    metadata = {
        'name': f'{file_name}.txt',
        'parents': [f'{folder_id}']  # Replace with the desired parent folder ID
    }

    with open('chapter.txt', 'w') as f:
        f.write(text)

    # Define the path to the file on your local machine.
    file_path = './chapter.txt'

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
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
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
    access_token = get_request('https://audiotruyencv.org/api/ggdrive/get-access-token')
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

def create_file_audio(chapter, audio_folder_id, text_folder_id):
    print("start chapter")
    try:
        chapter_content = chapter["content"]
        if chapter_content is not None:
            status_add_guide = add_guide(chapter["content"])
            if status_add_guide is not None :
                status_upload_audio_on_folder_id = upload_audio_on_folder_id(chapter["id"], audio_folder_id)
                status_upload_text_on_folder_id = upload_text_on_folder_id(chapter["id"], text_folder_id, chapter["content"])
            if status_upload_audio_on_folder_id is not None and status_upload_text_on_folder_id is not None:
                post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"id" : chapter["id"], "status" : "1", "audiofileid": status_upload_audio_on_folder_id, "textfileid": status_upload_text_on_folder_id})
                print("end chapter")
                if post_response is None :
                    return False
            return True
        else:
            post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"id" : chapter["id"], "status" : "2"})
            return None
    except Exception as e:
            #print(e)
            post_response = put_request('https://audiotruyencv.org/api/chapter/update-info', json={"id" : chapter["id"], "status" : "2"})
            return None

def create_audio_all_chapter_by_book_id(id):
    # lấy sách
    folder_id = ""
    audio_folder_id = ""
    text_folder_id = ""
    book = get_request(f'https://audiotruyencv.org/api/book/{id}')
    if book is not None:
        if book["folderid"] is None :
            folder_id = create_folder_id(book["id"])
            print(folder_id)
            if folder_id is not None:
                audio_folder_id = create_child_folder_id("audio", folder_id)
                text_folder_id = create_child_folder_id("text", folder_id)
                if audio_folder_id is not None and text_folder_id is not None:
                  post_response = put_request('https://audiotruyencv.org/api/book/update-folder-id', json={"id" : book["id"], "folderid" : folder_id, "textfolderid" : text_folder_id, "audiofolderid" : audio_folder_id})
                  if post_response is None :
                      return False
        else :
            folder_id = book["folderid"]
            audio_folder_id = book["audioFolderId"]
            text_folder_id = book["textFolderId"]
        if folder_id is not None :
            # lấy tất cả sách
            chapters = get_request(f'https://audiotruyencv.org/api/chapter/all/{book["id"]}')
            if chapters is not None:
                for x in chapters:
                    if x["status"] == '1':
                        continue
                    statusx = create_file_audio(x, audio_folder_id, text_folder_id)
                    delete_all_file()
                    #time.sleep(10)  # Tạm dừng chương trình trong 30 giây.
                    break

def create_audio_all_book():
    # lấy tất cả sách
    books = get_request('https://audiotruyencv.org/api/book')
    if books is not None:
        for x in books:
            create_audio_all_chapter_by_book_id(x["id"])
