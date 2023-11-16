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
                # '00a7b9b4-629b-4926-b69f-b988f55dead7',
                # '01216a29-f6b1-4d3f-8e7f-7146d4f2fdce',
                # '0229e7f0-4041-43e9-b15a-d0ebf09b95df',
                # '0346d874-3852-40b8-952b-3de3274fac51',
                # '0352de1c-1e10-45c4-92da-5468423d73e5',
                # '03b3261a-3c5d-4bbf-b92c-5904e462394b',
                # '042d7081-2770-4765-b4df-f5bd67cc77de',
                # '04650a19-bb19-4215-a9e7-86cb748b76ff',
                # '047077bc-1ba0-4322-b89f-2717b611d0d1',
                # '04a33561-2f98-4744-a347-7803fbf54e9c',
                # '04acf86c-5b69-4e5d-8e80-6171caeb8311',
                # '04b97664-c9de-4762-b34e-8828a5067c74',
                # '05181d12-94ba-4b1d-843b-048156b6856a'

                # '055d30ef-dda0-49e2-9db1-da94c782e831',
                # '05900850-ad75-4e62-82ae-d3797f5b748a',
                # '05a482ab-e5a9-43cc-aadd-6a9c205fcb18',
                # '05b4ea7d-9d4e-4e0f-8eb1-93f3fb40902e',
                # '05dcd583-86c7-4964-8e31-c29da35d65e2',
                # '06ef5d51-e33f-45b1-857b-4a6d8c531226',
                # '073c05a2-b70e-4643-ad39-6c06ed6e14f9',
                # '074b7c65-cda8-4138-b6a0-e48017b27934',
                # '07bc32e7-8ca7-436d-8b7f-86ed31b25ee2',
                # '08207150-3e1b-44c5-af30-9d5d5f51cd7c',
                # '09378453-0066-4fa0-956e-1934f8c224c8',
                # '098e6844-1877-4213-b552-f556ba79cc35',
                # '0a6de8fa-7b2c-4c48-a359-25d22ca3750b',
                # '0a96cc71-4a31-46fe-baf4-2b1db3351380'

                # '0ad21971-2e0b-4259-9573-8455859b006b',
                # '0b7685e6-19d1-4d46-a369-05584944f005',
                # '0d404876-55e6-4d2d-8c37-cf993ad6bc88',
                # '0d6a279c-3241-4d7d-bc78-10f7e295de96',
                # '0d909466-2f3c-4802-a629-852195875c45',
                # '0ef3f28d-1da8-4525-92a2-b585b9f50854',
                # '0f2ac64d-d194-4fa1-a959-24ef639de8df',
                # '0f431e0a-cc08-41d4-9ee5-a1186e8002c0',
                # '10eda6ca-4b0d-4f8a-a5f3-11ec68ecde26',
                # '111500d6-cfda-4095-b993-7edb00228763',
                # '111ba15b-1fe1-46c9-84cb-b7c6da0dae67',
                # '115aa5d6-87a8-413c-9c7e-90fd8a783fa7',
                # '1197f90c-2c21-472b-a958-a1795b1e2240',
                # '11aa2198-9489-4f00-b65d-d389b7223ccb',
                # '11d8b3a5-7d89-4b4d-8a04-bc71a9804488'

                # '11f6e2f1-a84e-49f2-8a35-8e68d75135ef',
                # '13709e4a-34de-4aa1-9c53-01603f49657e',
                # '13dd7e89-88e6-4c47-9c9b-283c7216f7f0',
                # '140dffd5-b26d-4995-b383-db9f4a2bebad',
                # '141528b4-f2ea-4587-937c-035a50a220ef',
                # '141bb690-1b94-4990-9a98-b4a4a417a26a',
                # '14256b66-1371-48f7-b431-4ae339ba651f',
                # '14a55e8a-728d-4c04-8888-f22d41838ef8',
                # '150a0a6d-339e-4516-8d65-125edb6d0337',
                # '157754f9-030b-4d8c-bbf2-9d38de0963da',
                # '15cdad98-f1cb-4f92-b750-e02dc5ee088c',
                # '15f8f62b-0fa2-47c8-8473-ae797f261ba7',
                # '1862c44f-2df4-47d2-8c22-0dd0737d4a01',
                # '187524f3-1d92-429a-b07e-3a4f7d925d6b',
                # '194118c9-bf73-4463-a7c5-b990dfaf632e',
                # '19edc187-a116-46d7-a265-0d9e11509646',
                # '19eeb8de-48fe-4db8-93b0-c4eadf8bfc62'

                # '19f1838d-003a-4283-bf96-aa788d2a51f8',
                # '1a43d9a0-6921-4c64-9698-5a6088ddeef4',
                # '1b0757bc-39e9-4224-9315-cf6c63fd2529',
                # '1b9f6ed3-a50b-417c-8591-60cafc4da45f',
                # '1ba10a7c-b60b-4291-9d38-652cdfa3b949',
                # '1c1b35d6-69f4-44be-b9ee-69b3a5bf7576',
                # '1cc27150-f21c-464f-a667-0776778e0af2',
                # '1cee013b-3e49-4dba-a040-3e881f0b7a8f',
                # '1cfa5723-6f95-471f-b3ac-f271db1c1932',
                # '1d97c6bf-a904-40f1-a68b-32116a8931bc',
                # '1f087575-7cc4-49b6-b591-0caa0fc6a350',
                # '1f4b7402-b5e2-4a5d-af6b-58898d84c493',
                # '20bef995-b386-46bf-a88e-a675f3b244d0',
                # '20c613d4-40ed-4596-a24c-a5ab0730b519',
                # '210b02e4-a2cc-48e9-99cc-11bce77aded7',
                # '233cbe1f-1624-4631-9ad8-53530d0ee7c2',
                # '235d2e2a-a3ba-4fca-b996-c92db7c34696'

                '24418f60-fd29-4309-9d96-b595f47f42a9',
                '24c0668f-b2cd-4764-91fb-695929d25a88',
                '2640e414-c868-460c-a671-14487f1f8828',
                '268acf01-c75d-4cf1-988c-ebf618e4b61d',
                '26d8c5a6-c91f-4a26-b3db-89d00fd22e36',
                '279a5f74-dd12-4609-a9e5-54e8b86329b4',
                '27c46671-ec24-4859-9e0b-3474294548ba',
                '280a7bac-5dfd-4d19-b21e-5bc1ec2d0064',
                '28210745-e873-48f7-840c-3b64365ea722',
                '2832903d-ef7f-480c-94b0-af10678480bc',
                '2852c32a-7f99-49a6-8816-b58d9cfeb7c0',
                '2967ac7d-4012-4e04-ad6a-15494cb3fa1a',
                '29770760-03f4-4654-8f53-a469a467b92b',
                '2a7db873-2637-4dfb-b2c8-5f6e0930e225',
                '2a8a118c-dfd2-4835-b213-eb5d518daed8'
                
                # '2b0f89dc-2e4a-4153-8d41-59e7b7d03607',
                # '2b5893fa-3e84-4991-8a66-708b826c71f8',
                # '2b9fe566-63d7-4bd3-ac65-b3373087e7c4',
                # '2bbbc621-582d-4e4d-8f49-3ddb79959c07',
                # '2c091ecd-64c6-4449-a424-e2506f46c66f',
                # '2c5eb906-aba3-4678-a302-0928e5345651',
                # '2dcf7ae7-940f-4ba0-80c8-afcee0f22605',
                # '2e09f6d6-01bb-4b48-aa4f-d6df25b7b680',
                # '2e5d1539-ca3e-4b27-ad63-50df132fce65',
                # '2ed3107c-e15e-4f27-976e-22b31bf6af03',
                # '2f4b6c01-479b-49f6-a850-a6516668b125',
                # '2f7dce18-7ee0-4c41-a751-7df392e49dea',
                # '2fe2e78f-83d9-4f4f-83fa-9e51c6374d26',
                # '30112e1f-f2b7-4770-8f7b-1a8908235f2f',
                # '3045320d-181b-4387-b97f-c376f49c4ca7',
                # '304e0687-a293-4876-84a5-d14201e17934',
                # '3199c71b-856e-494f-8173-d2f2104105bb',
                # '327fe4e3-60bf-4433-a85a-eaf3557e6b41',
                # '330910ff-a1a8-4b16-995a-8285cda77596',
                # '331fc834-4304-4a00-ac7a-345cc37f90d3',
                # '345457a9-1c1a-41c4-87bc-a04638d86d77',
                # '34cb9230-9a25-416a-a5da-f23b66ee4633',
                # '3562b393-b7cc-4b30-8de9-5c76e4bd37f0',
                # '35cd0ffb-01a2-4ea5-9165-1626cd4c5f61',
                # '3655d9de-d58e-4b6f-9262-1b89143b6e82',
                # '36e3f38b-9c24-454a-b3f9-11b4c1060a67',
                # '37085e9e-9b4d-4df2-9198-0e3f8829fe5b',
                # '37b7e7e4-16a5-4cd1-a703-f8637f116121',
                # '389b931b-d8d1-49eb-a310-78c44bddc689',
                # '38ee1e99-a6b0-4101-9bf5-b43d76a605f8',
                # '3995c563-4305-497b-ba8c-ee84342ef4de',
                # '3c27c9af-bf13-428d-a516-4e7d65ed6842',
                # '3cb5af82-7a44-45c7-bbe4-a5779d6a9310',
                # '3ce2dcbd-63ca-4aea-ae4e-ab89f8fa6801',
                # '3d169244-bd98-407c-b4c4-e99cf51fb79e',
                # '3d41028a-7a20-46b1-9d46-30d562d627a3',
                # '3d9b75f1-0c39-44b6-baa9-ca6d45cb83fa',
                # '3ed102bd-d8dc-460d-8bdc-56370dc1a99f',
                # '3f4eac04-2827-4cf6-8e3c-05c5c47bd860',
                # '3f9a5a46-06b9-4c16-8cb0-c7a5b877ee89',
                # '4010442a-72d1-4944-86ba-b33ac91a5164',
                # '4158911c-92e0-4b62-bf42-304c622488ce',
                # '417abe60-75cc-42ab-962a-29b9e0d5b736',
                # '419dc65d-43d4-454b-adf1-c64d38f819ca',
                # '42c53e5b-9b8b-44ff-ba96-4d2f9286fa92',
                # '4432bd46-53c1-45e5-b363-d2f0fc4e7f80',
                # '45a51433-27e2-4360-90b4-671983156257',
                # '45a7ced6-99be-457a-928f-bd2eee2ff8b4',
                # '45c18d4b-235e-4eef-8780-4261927687ba',
                # '45c4e6ba-975c-4a1b-9e8e-f8b0348a31ca',
                # '45d4f276-629e-40e4-9785-d13cd16f6f9d',
                # '468fa93c-c952-47fb-b90c-000142395993',
                # '4784aadc-e622-4c17-a82e-744434c5d19a',
                # '47e195f8-7a9b-4d12-8051-b2e86c000a5c',
                # '480bbd4a-ec32-4ec1-ba2a-b6216fa34dc1',
                # '4839f22e-4372-4eb6-9d6c-ba2db672a72e',
                # '4845504e-9002-42ab-9bc6-45da23e05a1e',
                # '4859550c-5a4f-44ae-89ec-ba5993e6337f',
                # '492447eb-a713-4861-8c18-31177ccd7b12',
                # '49fbe78c-03db-4f10-8b68-000dc0e98f06',
                # '4b41c9e4-f859-420e-a9c0-59199c08d217',
                # '4c4e16ac-2499-4e57-987b-255996da0a70',
                # '4d3ff077-2014-4450-882c-8b3314a2a21d',
                # '4d5b09e0-f485-4c64-96d8-8019302f1af5',
                # '4dd0962f-4ebf-4ca7-b8e7-a1ac49aa5d71',
                # '4eff35d8-6f83-49f8-8ad0-1d70b2e0a10b',
                # '4f2e4945-1c08-4ad6-9410-0855831ce501',
                # '4fb5ecf9-0ce5-4b15-88fd-168430375019',
                # '50aef584-6f7f-49d4-8c32-c758d4479ebb',
                # '51a9766b-8e23-425e-8720-4d71a491b6ba',
                # '5238ca01-4c2d-471e-a5f8-7e2e366c62ee',
                # '5357f7d6-8f0a-4833-afef-7b77d1b21331',
                # '54225702-6624-460e-9735-6259275cf18e',
                # '548b6dae-3295-495e-9864-7d96c6dde6b9',
                # '5490a5d9-0438-4fc3-adbe-993308e6b3aa',
                # '554e066b-50bd-4e6a-bff0-aea287a342e8',
                # '55a1b62f-9682-4503-8a6f-794b2e92f582',
                # '575d6b23-b10b-472c-a3af-c3c62926654d',
                # '57761988-866b-4ae6-81d8-70abafbb29b5',
                # '58bc9682-a465-4d0c-adf5-1dfc915c7c90',
                # '59ba8d74-a5fa-4fed-898d-32af677598b9',
                # '5a888b2c-d468-43a9-bd7b-4d5334f99465',
                # '5b1e8f35-3eee-437e-9a37-dd814ed56044',
                # '5b614130-1a74-413c-a823-d7aec8daf517',
                # '5b8716bc-fbde-4121-b0fd-8fd52e6756a9',
                # '5c247987-ae95-434f-8286-ab84827b6de2',
                # '5c5dc1b4-438e-4549-99f3-814ea138c9ea',
                # '5d836f46-c238-4282-b14c-b68d4d1c02ae',
                # '5f1c12a2-4263-45d3-a7ad-dc04ea29be51',
                # '5f8bd14b-d8bb-40bc-9c54-4bfa3f52abdc',
                # '5f9337ed-f0f4-4d33-b6d7-c1357ad7aeaa',
                # '60de0c5d-1e81-43ce-9cba-656635a4dc12',
                # '614f5157-6ea1-4e0a-b709-a4b9a9da5e20',
                # '6367a482-415f-4431-a85c-7f36d535d9cc',
                # '6381e7ac-096b-4b1b-8a4d-cef9d535c786',
                # '63c4c1b6-1330-4c19-8629-26bc930e4ab9',
                # '63d71722-3efe-45e8-8000-3d23314fff55',
                # '645149f3-2742-4acd-8978-cfe5e591cb7c',
                # '658de78d-a49c-439a-967e-538c962bad57',
                # '65a746bf-02b7-48f4-9d5b-8a68797ff1c3',
                # '65e3ab52-d7ee-4a8d-b1ca-468376888085',
                # '662ae5c3-56b4-41af-aede-58120c5cac91',
                # '678ab3e7-c260-44b3-ab83-c44899734941',
                # '68a1da13-9d07-4f62-908b-8c7e53e8e6d5',
                # '68ac9e0a-a79e-4a64-8b98-e6a88a27f273',
                # '68d47e48-9ca5-4d6a-9073-aeb044ced3c6',
                # '6ae817ce-264f-4f6a-a51e-39341dd0a049',
                # '6bd92127-859b-442b-a9d6-c83e309ba528',
                # '6c9128a7-f1ae-4e85-b1fb-cdd78f78ba52',
                # '6d4e4b91-5fbc-481a-9200-2a6f7f114a20',
                # '6e1f4436-8a4c-4697-82fa-e50375ac192a',
                # '6e3e675a-bed9-4b78-a535-1fcd9824d2e1',
                # '6ea0a04c-adbb-4ef1-ae39-d7a2e185f1b1',
                # '6f2593fe-2e59-4758-ab39-076ca618b52e',
                # '6f3d6f9e-b039-49b8-aa50-8ab961cb4b68',
                # '6fdd3d72-21d2-4fe4-91e1-1cb4496e994a',
                # '70582d7f-3eb5-496a-859c-19cfeccc00d9',
                # '71103629-0a02-4f5f-9d0a-be3c7cd5cb54',
                # '71191adb-adbc-4d96-aabc-b4f4201a717e',
                # '71268f19-cc68-4eaa-8be5-64e8480771ed',
                # '713ae243-9466-4884-ac4c-5324cc37e6c6',
                # '714bbceb-c3b2-464d-8d16-50fcfac307ad',
                # '73aed128-d73a-4439-a4ea-b755da42cf2e',
                # '74183b16-0426-4c4a-a754-e2758dd201c7',
                # '76e68f2b-1ecb-43d2-8317-53cebff6b95a',
                # '78a88a1f-f9fc-443a-a454-f6c27648a2d7',
                # '7a4ee1c6-03d5-412e-b933-94ca0a2c1933',
                # '7a5a4744-d999-402a-acfe-118312f7b4db',
                # '7b3348aa-cad6-40a3-8a4a-eb0332742e3c',
                # '7b5e89e5-b7fc-493d-92ee-940bae66ed3a',
                # '7c1325d4-6366-4640-bd09-654a5271ec67',
                # '7c14ce9e-35bb-4cce-8818-2c01dab8091d',
                # '7c32107a-f7d6-40cd-83e0-7aae7595d16b',
                # '7c3b89fd-45af-470a-9551-02381a57491c',
                # '7c3eb695-a9a4-413b-ba66-1b55a7cd8ce9',
                # '7cbef44a-df23-415a-b41d-48ce15e77bf5',
                # '7e1dc9c7-bed9-4960-9460-fe90b82358a3',
                # '7e927303-bf4d-4fd0-8df4-b14a2c1b7cec',
                # '7f16ccb5-317f-4428-a919-a412694fa4dc',
                # '7f6ace45-b38f-47a5-b40b-7cc488880175',
                # '7fab0c67-363b-4a10-9938-264d44b65171',
                # '8053b1e0-ca98-481d-a7d9-a34c79fe1556',
                # '80b4e63a-a1a3-4c1b-8af0-f1c86851d78f',
                # '82074084-3f84-4ca8-86eb-a282854cd7a8',
                # '820f86e4-8eb2-402c-9533-5c7832e412ec',
                # '822e4878-f4d6-4d42-a853-5d305e5ba9cc',
                # '8243edd7-a393-45a1-b964-f3cbd94a9614',
                # '83df4124-e2f2-48f4-8e40-c116fa110741',
                # '844c53b7-769c-49fc-b034-8b2ff8a10189',
                # '845fa03e-6d45-42e9-8bc8-1bc3b2d352ff',
                # '848f3d2f-4dbf-4f17-a1cc-6872ec5644a5',
                # '8559b0f6-1f13-4896-9dd8-69b91593d2fe',
                # '85ccd501-a7f0-4baa-b029-385b876d4498',
                # '85ffc8df-6125-4d16-9339-73b70b09f9c5',
                # '86295c52-514e-4845-9da9-312d5ce66cab',
                # '86a60f97-b9e7-455d-a9a9-3400fa2ae5e4',
                # '872c5615-2754-4f25-bab0-d8531a4f2cff',
                # '874db85f-65d9-4f60-86b1-7358f38edc04',
                # '8785efaa-42c5-48ba-8b57-06958aa4e718',
                # '87efac21-21fc-40f3-8302-90a4c7a50f61',
                # '885c42f3-e161-4ff5-a41b-965438b1120c',
                # '88bb5810-ae5c-4079-813e-3400a77f53cf',
                # '89775f74-772d-468e-911f-05cdee81d472',
                # '89857644-69f9-4f71-a35c-84cac539fae0',
                # '8bb995cb-22f1-4a93-9f20-5e9dec72b6d1',
                # '8bcd8dba-a07d-43cd-b276-0fa92b136a3a',
                # '8bd0cd2c-82fa-44c8-8965-5064156da71f',
                # '8be093e0-87fe-450f-8330-65d11d1aa2f2',
                # '8cde1cec-9801-442a-84cc-31dbc8133827',
                # '8d4777d4-f135-4ff6-92b6-9adbbcb9b219',
                # '8f8ef14b-0287-4917-925c-07c4d61f20cc',
                # '91356cbd-ff21-40f6-a82d-f6e312ea7f14',
                # '91ff63b2-cf8f-433c-b8a1-6127667c074c',
                # '929ab762-0bef-49b0-a523-2462116b1097',
                # '937ad2b8-018f-4455-a1ce-2cd5bfc1f119',
                # '93956bd8-e11b-4b38-b31d-6b5478af703c',
                # '9398abad-8e02-4f17-9646-92432c1e4a67',
                # '9471abc3-17af-4282-97e9-93ab1a30cb89',
                # '952a1fd4-48b8-4e6a-adde-171ac1c7a791',
                # '954a58de-9a4f-40d3-9d92-59e2dc943260',
                # '9559823e-3eb9-4629-b407-c983356c5237',
                # '9794cad7-c852-4b45-b962-6770e9ce5a1c',
                # '97efbc29-8e66-470e-bdfd-ef7dead0c3d4',
                # '9944fee4-1c55-4cb8-9b52-4abe2eea8e17',
                # '9a489809-e9b4-4297-887e-3f9c1a9fbe1c',
                # '9a6f5d2f-a0a3-4d8a-bc54-7dab59d79fa5',
                # '9b0fc0df-5cfb-4ef3-83d6-67e8fc8f6b99',
                # '9bc1e7f2-95cd-4cbc-ab29-b3a4cd894dfd',
                # '9ca6617a-c1e0-4443-8654-891184864f20',
                # '9df70521-f9d8-4110-813d-2ec59819b7d3',
                # '9e07a09f-8bc1-4933-95ac-e90ee6a4f4dd',
                # '9e2027ea-c223-4baf-b258-567a8ada0a73',
                # '9ede1965-8a84-4ee9-b989-291d70f5cc49',
                # '9f16a682-be49-48c4-8315-c227d133fff2',
                # '9f2a605b-b1e5-4702-92c4-8afa91025a1e',
                # '9f8d396f-8139-4ecb-91db-8d3eb11b2ece',
                # '9fda5a86-1adb-482f-88ad-19c321c19ecf',
                # '9ffae82b-76cd-421d-8856-2fb39b459596',
                # 'a0617033-328e-4f68-96f1-733f27cc8c1e',
                # 'a1728647-bdf0-49d6-a999-f9643d9c4723',
                # 'a2756db1-4b53-482f-b6c0-5259ce4e88e7',
                # 'a3c3c53d-baca-437e-a301-1c38b17d6dc2',
                # 'a511bff8-25ea-4f57-bb29-3c16229ce6d9',
                # 'a517f16f-daed-451c-b1cc-a667689ac4a6',
                # 'a557503f-22b3-4729-b8ac-4d5ba034c213',
                # 'a5d5b244-8932-4690-8ed7-22e971873c5f',
                # 'a69717cd-7ae7-48cd-a08b-44918e67ac9f',
                # 'a6bd0e57-63d2-4338-a0c5-62a9ef3a41cd',
                # 'a7a04c30-7a92-412a-8669-310cf8777424',
                # 'a7f56c74-c463-4458-a5c7-22edec394ec6',
                # 'a90a66df-51cf-4c5f-93a8-38191c359ac3',
                # 'a95549a3-0a28-4ca8-94ce-854ba87e3356',
                # 'aa34b283-7dca-4ff6-82c7-09926a0d8b0d',
                # 'aa80baab-eaac-4042-88f9-33b57a9ebad1',
                # 'ab0cca97-f873-4c22-9b71-b1217bef75f4',
                # 'ab84811d-fbdc-47d9-bd66-3a0720d30626',
                # 'abc35673-ab6e-46e6-a7d7-416ac1c20809',
                # 'ac24ffa3-fb04-416e-a1fa-254a756c9d5d',
                # 'ad983104-b8ef-44fe-89f5-4d1f08db8457',
                # 'ae064d7b-6ed6-4245-9b79-cc34f1fc2db8',
                # 'ae536878-537c-44e2-843c-cf59cd4876b1',
                # 'b14524f5-20ec-4fb0-87be-f0ca2708c5e5',
                # 'b16e13c2-999c-44cf-9d45-e6c249751471',
                # 'b1f70d09-1e04-43a3-9bc3-516af25bcb68',
                # 'b25e2cf3-023d-4dd0-ad6f-d6191ef6673a',
                # 'b26b543c-c364-4f54-97ae-1688abc74eeb',
                # 'b2975dbc-e56c-4257-aafd-42c9ff4642a8',
                # 'b32edc95-5049-44a6-8a77-741819140f66',
                # 'b3e40c1d-a2d1-46b4-9ac8-ba6dd9d55016',
                # 'b43e8f22-6955-4599-aea9-c209eab9ebaa',
                # 'b4651d94-5cb9-44de-a1dd-e5003ee4532c',
                # 'b716bb24-5873-4d99-b553-3fc15b793c0e',
                # 'b8ebd810-36ba-4063-833d-3932ee41abdb',
                # 'ba1fbddb-a3b2-49ca-93ad-bcbfd0f90725',
                # 'baa34dc3-a335-452a-a159-e00acfb449ef',
                # 'bac45641-eef4-40bc-9b27-9e573f6abe36',
                # 'bb5ab6f5-ebe9-43b7-b669-362b48bbb493',
                # 'bc2195bf-171f-4862-b811-612afb43aa15',
                # 'bccb2e5c-b63c-4f98-a27f-c35638268cfe',
                # 'bcd8a583-d772-4f5e-bbd6-35d2f9a8029a',
                # 'bce036a4-29f6-47b0-af81-8883d01e6163',
                # 'bd119f37-7ffc-4331-ae80-106982918030',
                # 'bd39a6b7-1994-4392-a585-921f7ec78c54',
                # 'bd839115-299e-4667-8fab-86692cf46fba',
                # 'bd877b52-28d0-458b-8a3e-6e3c688c2bf4',
                # 'be74e855-25eb-4491-883f-8f1608883a4f',
                # 'be76ca36-9eb0-4fc9-9200-0a3e92e5fffe',
                # 'bed2d2bf-b014-48ac-92c1-a475cb95333e',
                # 'bf5a9de7-1662-46f3-b5b9-d117b501f734',
                # 'bf7098ff-0881-4919-b1bd-615ccd4b5572',
                # 'bf826c60-819d-4619-9385-1c8c2523b885',
                # 'bfa0b1b5-43fd-4722-b0cf-f8b78a45b224',
                # 'bfbcc178-2626-4b4d-bfe2-209e18dd960c',
                # 'c2b848d8-90ca-4b34-9d95-9068ca454609',
                # 'c3109a9c-db2c-43b5-b9a0-cc3105866420',
                # 'c4186fe2-6ee1-4106-b76a-76c802438f3d',
                # 'c49c72d9-1c40-4666-b31d-f18440d66363',
                # 'c57754ba-1462-4c3a-8a44-638f3051fe8c',
                # 'c593624b-a6a5-4982-a2de-0e5c094741e5',
                # 'c63080b2-b212-4b4b-b38d-ebfba1bd92cb',
                # 'c68a0616-b749-4562-a240-0443f4e2b029',
                # 'c6a14849-1144-4928-a688-18afdd2c7f3f',
                # 'c705dfb7-91fc-47d7-b881-9b740360c680',
                # 'c74434bc-cc36-4ca1-af22-f2f899015443',
                # 'c75ac571-8a56-41ca-8e17-c98b6da4a1b0',
                # 'c76c6fca-cf7f-46f8-99e9-999530ff174e',
                # 'c886799e-4cec-4b44-bdd9-ac87dc286055',
                # 'c8f56099-8796-4a6c-b729-3237f220bb32',
                # 'c9e4aa02-9398-41ae-914d-4a4d37d74c76',
                # 'ca0c27c4-2846-4768-8196-cbf9a65d314d',
                # 'ca14ea62-251f-40b1-8457-fc6a6964b6b4',
                # 'cbcd3186-0834-4ad7-8ad1-5fc99060ab57',
                # 'cdd6d5cd-5b44-41a5-ab5b-a9bf4a4b0573',
                # 'cef09e7e-d376-4db2-ae68-d4786c9694a0',
                # 'cf9d01d0-1163-47b0-acd7-65bc9244d23f',
                # 'd0b3bf0f-8ea2-4b24-81e2-605bc1a9602b',
                # 'd0f82b0c-b389-4215-bff0-8327eb2676cf',
                # 'd1963d7a-d16b-4cb8-9911-01c42bc38c84',
                # 'd19ba343-6437-47fd-9b10-e289d5a6cb7d',
                # 'd2197384-d71e-47ed-8108-64e82b54ab6c',
                # 'd266f870-844c-4404-939f-5b1836861152',
                # 'd314db04-c60e-41ec-9550-3f176d5e2eb3',
                # 'd3820c3b-51f2-4aa9-9fe6-863ef064e1ab',
                # 'd39a7d54-fa1e-4732-91f8-a7cb552fb5b2',
                # 'd5104879-84f6-4a14-96f6-42025bbd77f0',
                # 'd52f7d62-823f-431e-8df6-b9ab97094fc1',
                # 'd53e15f8-12b1-4220-ab28-e8295428912e',
                # 'd5c986ca-584f-42b0-a3f4-53df6d2e6df7',
                # 'd687c2aa-09f9-478c-879f-5510015aa89b',
                # 'd6bb78b0-4a03-4076-b0f5-2e7c8dedac11',
                # 'd783d817-8910-4f64-9871-c1f8071ac990',
                # 'd82a3b01-17ab-4b27-8076-a83a17dbbb74',
                # 'd87df77d-440f-48d5-9174-affca31612fe',
                # 'd8a259c5-bebb-4423-952c-d4aa8b871617',
                # 'd9ec2f2f-51d1-475f-8073-f489ef365c4f',
                # 'dac96e83-4d3f-40cb-9d94-53c00bd2b7f3',
                # 'db43a30b-9bb5-4290-b602-24f941b08a63',
                # 'db5763e4-c716-4a02-b39d-8035bd200434',
                # 'dbae66a3-aa98-4816-91e9-144bd8ab0755',
                # 'dc6e2a4c-cfa1-4d11-9ea4-b00f29b8622b',
                # 'ddf6b167-b025-4c56-8aeb-1b6637f811ad',
                # 'de0a4543-35cd-4158-b13d-0ef3201eb125',
                # 'de74984a-e339-4fcb-9c55-586dfa8b96f1',
                # 'df621e3f-0ca4-4243-b3ca-b594e2448bf6',
                # 'e0b98a64-81dd-4165-bcd5-0650bfa0c7a0',
                # 'e0e6de6b-034d-4644-b821-7e29a1ce87ff',
                # 'e14207a3-9173-4bd9-9a11-c9f51b418d86',
                # 'e1c64a11-49c2-47e9-bd38-9fb24ebc71bb',
                # 'e1dac566-b8fb-4254-ae31-531376126ed1',
                # 'e1eb91f7-fb67-4410-ae71-3626f5e67b61',
                # 'e2626cc8-e549-4310-b0b5-26971ad77dec',
                # 'e2da35c0-dbe9-4c8e-8e1f-d82b0c8660c1',
                # 'e39d58dc-d184-47fc-8d4d-85f2dbe08fec',
                # 'e51ae647-983d-41e1-9df1-167fa2ecee80',
                # 'e53365b6-37bf-4dc1-af81-0267f263d166',
                # 'e611c3a3-5e21-4bbc-8b65-f09dbc4ea2be',
                # 'e663d3a6-a8a4-40e9-ba81-47cde610831b',
                # 'e6734439-bba3-4359-b176-89a4c0c048ea',
                # 'e72954fc-3295-43c3-8a51-43a6bc3d5e3d',
                # 'e7528d04-4eda-4353-801c-8514e8e5f85b',
                # 'e76ebe71-3995-453a-bab0-4526ab0f0df4',
                # 'e7cb7630-93ef-4ba7-9f34-a8e281ec18a7',
                # 'e7fa09f7-85bb-4e3e-ae34-fa01a5aec7d7',
                # 'e81854e2-d868-4a90-8d42-17e6568c2798',
                # 'e8698a52-d08b-47ee-8d79-6220e5b5eb35',
                # 'e981c9c9-a514-4b57-bab5-2eb41f69c01b',
                # 'eae170d2-03b9-4287-bd89-7bbf17f16f35',
                # 'eb4c3347-5e4b-47d4-93ad-49462b62f3d4',
                # 'eea57352-5259-45e0-8ce7-dd06e80a032f',
                # 'ef5ddba7-a16e-4a49-94e4-9f9b24032360',
                # 'ef63d98d-2256-4c6c-9cca-64bf8f051688',
                # 'f10fc830-be24-47f5-9893-e71c65da6ada',
                # 'f1221d7b-f801-4567-baf5-9a7d1aac01d3',
                # 'f2239821-2597-4c59-bc8f-81d2a1138cd8',
                # 'f2e71a01-cdcf-4d96-900c-d91b9663b3c5',
                # 'f40ab5d6-cd38-4c8f-a85e-92b412a542fa',
                # 'f4143acb-5d19-4c62-aa98-742e58ae1bb8',
                # 'f5654cb1-7943-44fd-8168-8f8835e14f2d',
                # 'f571e97c-b0be-48a8-9d82-a84f4b127e43',
                # 'f583018f-e90c-43a4-a7ee-939a4a7e90fb',
                # 'f635dcc9-c528-43b8-896f-23db1cf82724',
                # 'f7e63c72-1ea7-452d-af1d-e27bae1ed8dd',
                # 'f83bba6a-6417-4ec7-911d-566fe082087e',
                # 'f83f5e22-f34e-4ded-b7dd-a34069d0db14',
                # 'f8506019-2d48-4091-992d-f669492d7392',
                # 'f874a811-9f71-485e-b753-568777eb9ea2',
                # 'f8a5df3d-666e-4989-bfe0-9ee7996d86d1',
                # 'f96a0638-d3f7-4300-92f8-0a21405a0399',
                # 'f9ad4960-cb60-4e81-96c4-f5a8d1124da1',
                # 'f9b6a696-3178-45ac-addb-efffe6560b3b',
                # 'fa85f696-b030-495f-b576-5e840053e3ab',
                # 'fb10863f-a883-46b6-b114-bb772ded2e8f',
                # 'fb8ffe70-ac87-45d1-a8e6-2896ea2b4eb8',
                # 'fc94e6b0-4f34-4fa2-9357-e3b8abea88f0',
                # 'fcb313cb-eec3-489d-acc2-e44056b92a8e',
                # 'fe39430e-3f8e-4dae-9c74-8c4965bddb2d',
                # 'fe8bdd35-3f10-4aeb-a447-9d670ca8f20a',
                # 'fea0faf2-b73d-4654-9fe9-da91d96b6522',
                # 'ffd63f69-2682-4237-b0d9-ad6bc8ddea45'
                ]
    for book in books:
        create_up_chapter_by_book_id(book)

run_all_book()