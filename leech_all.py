import requests
from bs4 import BeautifulSoup
import asyncio
import nest_asyncio
from urllib.parse import urlparse, parse_qs, urlunparse

nest_asyncio.apply()

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
        print(response.status_code)
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


def get_book_details(book_link):
    response = requests.get(book_link)
    soup = BeautifulSoup(response.content, "html.parser")

    # Lấy thông tin tiêu đề, tác giả, thể loại và nội dung tóm tắt
    title_tag = soup.find('h1')
    book_title = title_tag.find('a').text

    detail_info_tags = soup.find_all(class_="detail-info")
    a_info_tags = detail_info_tags[0].find_all('a')
    author_name = a_info_tags[0].text.strip()
    genre = a_info_tags[1].text.strip()
    li_status_tag = detail_info_tags[0].find_all('li')
    status_name =  li_status_tag[2].find('span').text
    if status_name == 'Full':
        status = '1'
    else:
        status = '0'

    summary_tags = [element.text.strip()
                    for element in soup.find_all(class_="summary")]
    # Gộp tất cả các đoạn tóm tắt thành một chuỗi
    full_summary = ' '.join(summary_tags)

    div_tab_tag = soup.find(id="divtab")
    first_chapter_tag = div_tab_tag.find_all('a')[0]
    first_chapter_link = first_chapter_tag.get('href')

    return {
        'Booknm': book_title,
        'author_name': author_name,
        'genre': genre,
        'summary': full_summary,  # Trả về chuỗi đơn về nội dung tóm tắt
        'first_chapter_link': first_chapter_link,
        'status': status
    }


def get_next_chapter_link(chapter_link):
    response = requests.get(chapter_link)
    soup = BeautifulSoup(response.content, "html.parser")
    next_chapter_tag = soup.find(id="nextchap")
    next_chapter_link = next_chapter_tag.get(
        'href') if next_chapter_tag else None

    return next_chapter_link


def get_chapter_details(Bookid, chapter_link, Seq, success_count_max):
    list_chapter = []
    success_count = 0
    while chapter_link and success_count < success_count_max:
        empty_content_count = 0
        while empty_content_count < 5:
            response = requests.get(chapter_link)
            soup = BeautifulSoup(response.content, "html.parser")

            title_tag = soup.find('h1')
            chapter_title = title_tag.find('a').text

            # Tìm và loại bỏ các phần tử có id là 'setting-box' hoặc 'list-drop' và class 'comments' hoặc 'chapter-notification'
            elements_to_remove = soup.find_all(lambda tag: (tag.has_attr('id') and (tag['id'] == 'setting-box' or tag['id'] == 'list-drop')) or (tag.has_attr('class') and ('chapter-header' in tag['class'] or 'comments' in tag['class'] or 'chapter-notification' in tag['class'])))

            # Loại bỏ các phần tử tìm thấy
            for element in elements_to_remove:
                element.extract()  # hoặc element.decompose()

            content_tag = soup.find(id="reading")
            
            if content_tag:
                for tag in content_tag.find_all(['a', 'div']):
                    if tag.name == 'a' or tag.name == 'div':
                        # Check if it's a 'div' tag and its class doesn't contain certain values
                        if tag.name == 'div' and 'content' not in tag.get('class', []) and 'c-c' not in tag.get('class', []):
                            # Check if it's a 'div' with id 'content'
                            if 'content' in tag.get('id', []):
                                continue  # Skip this 'div' as it has id 'content'
                            tag.extract()
                        # Check if it's an 'a' tag and its class doesn't contain certain values
                        elif tag.name == 'a' and 'content' not in tag.get('class', []) and 'c-c' not in tag.get('class', []):
                            tag.extract()


            full_text = "\n\n\n".join(content_tag.stripped_strings)

            chapter_content = full_text

            if not chapter_content:
                empty_content_count += 1
                if empty_content_count == 5:

                    return list_chapter
            else:
                new_chapter = {
                    "Name": chapter_title,
                    "Content": chapter_content,
                    "Seq": Seq,
                    "Url": chapter_link,
                    "Status": "0",
                    "Bookid": Bookid
                }

                # Kiểm tra xem chapter đã tồn tại trong list_chapter hay chưa
                exists = any(item["Name"] == new_chapter["Name"] and item["Content"]
                             == new_chapter["Content"] for item in list_chapter)

                if not exists:
                    #print(chapter_link)
                    list_chapter.append(new_chapter)
                    Seq += 1
                    success_count += 1

                    if success_count >= success_count_max:
                        return list_chapter

                next_chapter_tag = soup.find(id="nextchap")
                next_chapter_link = next_chapter_tag.get(
                    'href') if next_chapter_tag else None

                if not next_chapter_link:
                    return list_chapter

                chapter_link = next_chapter_link

    return list_chapter

def create_authors(name, Authors):
    for author in Authors:
        if author["Name"] == name:
            return author["Id"]
    put_response = put_request(f'https://leech.audiotruyencv.org/api/authors', json={
                               "Id": "", "Name": name, "Created": "2023-11-01T02:18:08.419Z", "Biography": "", "Updated": "2023-11-01T02:18:08.419Z"})
    if put_response is None:
        return False
    return put_response["Id"]


def create_genres(name, Genres):
    for genre in Genres:
        if genre["Name"] == name:
            return [genre]
    return []


def process_chapters(Bookid, Seq, initial_link):
    next_chapter_link = get_next_chapter_link(initial_link)
    if next_chapter_link != None:
        list_chapter_ = get_chapter_details(
            Bookid, next_chapter_link, Seq + 1, 100)
        while len(list_chapter_) > 0:
            chapter_put_request = put_request(
                f'https://leech.audiotruyencv.org/api/leech/insert-chapter-by-bookid/{Bookid}', json=list_chapter_)
            list_chapter_ = []
            if chapter_put_request != False and chapter_put_request:
                next_chapter_link = get_next_chapter_link(
                    chapter_put_request["Url"])
                if next_chapter_link != None:
                    list_chapter_ = get_chapter_details(
                        Bookid, next_chapter_link, chapter_put_request["Seq"] + 1, 100)

def process_book(book_link):
    Genres = get_request(f'https://leech.audiotruyencv.org/api/genres')
    Authors = get_request(f'https://leech.audiotruyencv.org/api/authors')
    book_details = get_book_details(book_link)
    ListChapters = get_chapter_details("", book_details["first_chapter_link"], 1, 100)
    Book = {
        "Booknm": book_details["Booknm"],
        "AuthorsId": create_authors(book_details["author_name"], Authors),
        "Status": book_details['status'],
        "Description": book_details["summary"],
        "ListGenres": create_genres(book_details["genre"], Genres),
        "ListChapters": ListChapters
    }
    book_post_request = post_request('https://leech.audiotruyencv.org/api/leech/insert-book', json=Book)
    
    if book_post_request and book_post_request != False:
        last_item = book_post_request[-1]
        process_chapters(last_item["Bookid"], last_item["Seq"], last_item["Url"])

def get_link_books_in_page(page_link):
    list_books = []

    response = requests.get(page_link)
    soup = BeautifulSoup(response.content, "html.parser")
    content_tag = soup.find_all(class_="list-content")
    book_tag = content_tag[0].find_all('h3')

    chapter_tags = soup.find_all('span', class_="row-chapter")

    for book in book_tag:
        chapter_count = chapter_tags[book_tag.index(book)].text.split('.')[1]

        book_link_tag = book.find('a')
        book_nm = book_link_tag.text.split('-')[0].strip()
        if not check_book_exists(book_nm) and int(chapter_count) > 0:
            book_link = book_link_tag.get('href')
            list_books.append(book_link)
    
    return list_books

def check_book_exists(book_nm):
    book = get_request(f'https://leech.audiotruyencv.org/api/book/paginated-app?Keyword={book_nm}')
    rows = book['Rows']
    if len(rows) > 0:
        for b in rows:
            if b['Booknm'].strip().lower() == book_nm.lower():
                return True
    return False

def get_next_page(page_link):
    parsed_url = urlparse(page_link)
    query_parameters = parse_qs(parsed_url.query)
    
    next_page = query_parameters.get('trang', ['0'])
    next_page_value = int(next_page[0]) + 1
    query_parameters['trang'] = [str(next_page_value)]
    
    next_page_link = urlunparse(parsed_url._replace(query="&".join([f"{k}={v[0]}" for k, v in query_parameters.items()])))
    
    return next_page_link

def get_all_link_books(page_link, max_page=10):
    page_count = 1
    list_books = get_link_books_in_page(page_link)
    next_page_link = get_next_page(page_link)
    while next_page_link:
        list_books.extend(get_link_books_in_page(next_page_link))
        page_count += 1
        if page_count > max_page:
            break
        next_page_link = get_next_page(next_page_link)
    return list_books

async def async_process_book(book_link):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, process_book, book_link)

async def main():

    book_links = ['https://truyenconvert.net/truyen/than-y-tro-lai-ngo-binh-full', 'https://truyenconvert.net/truyen/de-nhat-kiem-than-diep-huyen-full-truyen-tac-gia-thanh-phong', 'https://truyenconvert.net/truyen/phong-than-chau-tan-ninh-vo-thuong-than-de-truyen-full', 'https://truyenconvert.net/truyen/do-de-xuong-nui-vo-dich-thien-ha-diep-bac-minh-full', 'https://truyenconvert.net/truyen/vo-thuong-luan-hoi-chi-mon-trieu-ban-truyen-full-tac-gia-ban-ban', 'https://truyenconvert.net/truyen/chien-than-bat-bai-tieu-chinh-van-truyen-full-tac-gia-hac-long', 'https://truyenconvert.net/truyen/hau-due-kiem-than-diep-quan-full', 'https://truyenconvert.net/truyen/dinh-phong-thien-ha-luc-lam-thien-full', 'https://truyenconvert.net/truyen/chien-than-thanh-y-duong-tuan-truyen-full', 'https://truyenconvert.net/truyen/yeu-long-co-de-17099', 'https://truyenconvert.net/truyen/doc-ton-truyen-ky-thanh-van-mon-lam-nhat-truyen-full', 'https://truyenconvert.net/truyen/tu-la-vo-than-1178', 'https://truyenconvert.net/truyen/van-co-than-de-4295', 'https://truyenconvert.net/truyen/nguoi-chong-vo-dung-cua-nu-than-lam-chinh', 'https://truyenconvert.net/truyen/to-than-chi-ton-diep-van-full', 'https://truyenconvert.net/truyen/thai-co-long-tuong-quyet-9424', 'https://truyenconvert.net/truyen/vu-than-chua-te-8208', 'https://truyenconvert.net/truyen/chang-re-quyen-the-bui-nguyen-minh-full-truyen-tac-gia-n-h', 'https://truyenconvert.net/truyen/than-y-tro-lai-ngo-binh-full', 'https://truyenconvert.net/truyen/de-nhat-kiem-than-diep-huyen-full-truyen-tac-gia-thanh-phong', 'https://truyenconvert.net/truyen/phong-than-chau-tan-ninh-vo-thuong-than-de-truyen-full', 'https://truyenconvert.net/truyen/do-de-xuong-nui-vo-dich-thien-ha-diep-bac-minh-full', 'https://truyenconvert.net/truyen/vo-thuong-luan-hoi-chi-mon-trieu-ban-truyen-full-tac-gia-ban-ban', 'https://truyenconvert.net/truyen/chien-than-bat-bai-tieu-chinh-van-truyen-full-tac-gia-hac-long', 'https://truyenconvert.net/truyen/hau-due-kiem-than-diep-quan-full', 'https://truyenconvert.net/truyen/dinh-phong-thien-ha-luc-lam-thien-full', 'https://truyenconvert.net/truyen/chien-than-thanh-y-duong-tuan-truyen-full', 'https://truyenconvert.net/truyen/yeu-long-co-de-17099', 'https://truyenconvert.net/truyen/doc-ton-truyen-ky-thanh-van-mon-lam-nhat-truyen-full', 'https://truyenconvert.net/truyen/tu-la-vo-than-1178', 'https://truyenconvert.net/truyen/van-co-than-de-4295', 'https://truyenconvert.net/truyen/nguoi-chong-vo-dung-cua-nu-than-lam-chinh', 'https://truyenconvert.net/truyen/to-than-chi-ton-diep-van-full', 'https://truyenconvert.net/truyen/thai-co-long-tuong-quyet-9424', 'https://truyenconvert.net/truyen/vu-than-chua-te-8208', 'https://truyenconvert.net/truyen/chang-re-quyen-the-bui-nguyen-minh-full-truyen-tac-gia-n-h', 'https://truyenconvert.net/truyen/dao-gioi-thien-ha-29110', 'https://truyenconvert.net/truyen/lac-mat-co-dau-xung-hi-chien-le-xuyen-canh-thien-full-0e930621-6f6b-4d5f-8c90-3299e168e1c7', 'https://truyenconvert.net/truyen/vo-anh-tam-thien-dao-26146', 'https://truyenconvert.net/truyen/tieu-tong-xin-tha-cho-toi', 'https://truyenconvert.net/truyen/ta-mo-th-t-s-khong-la-hac-diem-35722', 'https://truyenconvert.net/truyen/bat-diet-ba-the-quyet-29150', 'https://truyenconvert.net/truyen/than-y-o-re-phan-lam-convert-truyen-full', 'https://truyenconvert.net/truyen/tung-thien-than-de-9361', 'https://truyenconvert.net/truyen/do-thi-cuc-pham-y-than-22494', 'https://truyenconvert.net/truyen/xuyen-khong-toi-vuong-trieu-dai-khang-kim-phi-full-574f3710-1f15-44c8-96e5-910b514d3557', 'https://truyenconvert.net/truyen/binh-vuong-va-bay-chi-gai-cuc-pham', 'https://truyenconvert.net/truyen/than-chu-o-re-vuong-bac-than-trieu-thanh-ha-truyen-full', 'https://truyenconvert.net/truyen/than-thoai-cam-khu-101379', 'https://truyenconvert.net/truyen/van-dao-long-hoang-14480', 'https://truyenconvert.net/truyen/ta-co-mot-than-bi-dong-k-28326', 'https://truyenconvert.net/truyen/thau-thi-ta-y-hon-hoa-do-25656', 'https://truyenconvert.net/truyen/su-ty-xin-giup-ta-tu-hanh-39123', 'https://truyenconvert.net/truyen/thien-dao-huu-khuyet-truong-huyen-full', 'https://truyenconvert.net/truyen/hoan-nghenh-di-vao-dia-nguc-cua-ta-37317', 'https://truyenconvert.net/truyen/chan-kinh-dem-dong-phong-suu-the-bien-tuyet-my-nu-de-chan-kinh-dong-phong-da-suu-the-bien-tuyet-my-nu-de-34935', 'https://truyenconvert.net/truyen/tien-ma-dong-tu-29575', 'https://truyenconvert.net/truyen/chien-than-bac-canh-duong-than-full', 'https://truyenconvert.net/truyen/kinh-thien-kiem-de-14670', 'https://truyenconvert.net/truyen/dan-dao-tong-su-117491', 'https://truyenconvert.net/truyen/toan-dan-chuyen-chuc-tu-linh-phap-su-ta-tuc-la-thien-tai-34809', 'https://truyenconvert.net/truyen/song-bang-tan-the-ta-tru-hang-chuc-ty-vat-tu-36060', 'https://truyenconvert.net/truyen/van-dao-kiem-ton-6716', 'https://truyenconvert.net/truyen/sau-nguoi-chi-gai-cuc-pham-cua-toi-truong-minh-vu-lam-kieu-han-truyen-full', 'https://truyenconvert.net/truyen/nghich-thien-ta-than-2707', 'https://truyenconvert.net/truyen/cao-thu-tu-chan-diep-thien-truyen-full-tac-gia-phong-hoa', 'https://truyenconvert.net/truyen/than-long-chien-9983', 'https://truyenconvert.net/truyen/van-minh-chi-van-gioi-linh-chu-22804', 'https://truyenconvert.net/truyen/toi-o-thanh-pho-bat-dau-tu-tien-tieu-tieu', 'https://truyenconvert.net/truyen/truyen-chien-than-o-re-duong-thanh-tan-thanh-tam-truyen-full-tac-gia-tieu-tieu', 'https://truyenconvert.net/truyen/ta-tai-huong-giang-lam-than-toan-huyen-hoc-37058', 'https://truyenconvert.net/truyen/vo-nghich-cuu-thien-gioi-33313', 'https://truyenconvert.net/truyen/bo-chau-la-chien-than-so-pham-tac-gia-mat-bac-full', 'https://truyenconvert.net/truyen/nay-nhan-vat-chinh-rat-manh-lai-can-than-27611', 'https://truyenconvert.net/truyen/ngoai-that-khong-de-lam-37455', 'https://truyenconvert.net/truyen/van-co-de-te-29867', 'https://truyenconvert.net/truyen/ren-sat-lien-co-the-truong-sinh-bat-tu-36103', 'https://truyenconvert.net/truyen/linh-canh-hanh-gia-32858', 'https://truyenconvert.net/truyen/cuu-vuc-kiem-de-10740', 'https://truyenconvert.net/truyen/nghich-thien-dan-de-29355', 'https://truyenconvert.net/truyen/toan-dan-tro-choi-tu-zombie-tan-the-bat-dau-treo-may-31219', 'https://truyenconvert.net/truyen/60-trong-sinh-cam-nham-kich-ban-nu-phu-muon-lam-giau-38482', 'https://truyenconvert.net/truyen/de-tu-cua-ta-tat-ca-deu-la-dai-de-chi-tu-34318', 'https://truyenconvert.net/truyen/trach-nhat-phi-thang-32985', 'https://truyenconvert.net/truyen/kiem-trung-tien-100569', 'https://truyenconvert.net/truyen/toan-dan-thuc-tinh-bat-dau-than-thoai-cap-thien-phu-37151', 'https://truyenconvert.net/truyen/ta-tai-tu-tien-gioi-van-co-truong-thanh-35214', 'https://truyenconvert.net/truyen/dinh-phong-thien-ha-luc-lam-thien-full-3b18d62b-0494-4e0a-be38-bc9b6c323740', 'https://truyenconvert.net/truyen/luc-dia-kien-tien-28542', 'https://truyenconvert.net/truyen/thon-phe-co-de-32427', 'https://truyenconvert.net/truyen/tro-choi-nay-cung-qua-chan-that-31102', 'https://truyenconvert.net/truyen/bi-doat-tat-thay-sau-nang-phong-than-tro-ve-32908', 'https://truyenconvert.net/truyen/bao-thu-cua-re-phe-vat-lam-hien-full', 'https://truyenconvert.net/truyen/ba-vu-33145', 'https://truyenconvert.net/truyen/van-co-toi-cuong-tong-23003', 'https://truyenconvert.net/truyen/ca-nha-nhan-vat-phan-dien-dien-phe-chi-co-su-muoi-dau-bi-37374', 'https://truyenconvert.net/truyen/bat-diet-chien-than-7388', 'https://truyenconvert.net/truyen/tien-gia-34950', 'https://truyenconvert.net/truyen/ta-tru-than-tong-mon-tren-duoi-bi-them-khoc-roi-35162', 'https://truyenconvert.net/truyen/kiem-dao-de-nhat-tien-27843', 'https://truyenconvert.net/truyen/phu-nhan-nang-ao-choang-lai-nao-dong-toan-thanh-31623', 'https://truyenconvert.net/truyen/huyen-huyen-ta-thien-menh-dai-nhan-vat-phan-phai-28132', 'https://truyenconvert.net/truyen/nga-dich-te-bao-giam-nguc-26684', 'https://truyenconvert.net/truyen/cuc-pham-than-y-tran-gia-bao-lieu-ngoc-anh-truyen-full', 'https://truyenconvert.net/truyen/de-hoang-manh-nhat-tan-quan-full', 'https://truyenconvert.net/truyen/trung-sinh-nien-dai-phao-hoi-truong-ty-mang-muoi-phan-cong-32925', 'https://truyenconvert.net/truyen/van-tuong-chi-vuong-30362', 'https://truyenconvert.net/truyen/toan-cau-cao-vo-cay-quai-thanh-than-ta-danh-xuyen-qua-nhan-loai-cam-khu-34037', 'https://truyenconvert.net/truyen/du-hi-giang-lam-di-the-gioi-19896', 'https://truyenconvert.net/truyen/luan-hoi-nhac-vien-29658', 'https://truyenconvert.net/truyen/linh-khi-khoi-phuc-ta-cua-lon-di-thong-mini-vu-tru-31746', 'https://truyenconvert.net/truyen/can-cu-so-7-33115', 'https://truyenconvert.net/truyen/tro-ve-84-tu-thu-dong-nat-bat-dau-lam-giau-32256', 'https://truyenconvert.net/truyen/do-thi-co-tien-y-33711', 'https://truyenconvert.net/truyen/ngao-the-dan-than-tram-tuong-truyen-full', 'https://truyenconvert.net/truyen/ta-de-tu-tat-ca-deu-la-sa-dieu-nguoi-choi-29832', 'https://truyenconvert.net/truyen/ba-son-kiem-truong-20647', 'https://truyenconvert.net/truyen/di-gioi-he-thong-cua-hang-33201', 'https://truyenconvert.net/truyen/do-thi-cuc-pham-y-than-24736', 'https://truyenconvert.net/truyen/bao-ho-ben-ta-toc-truong-29534', 'https://truyenconvert.net/truyen/xuyen-khong-song-mot-cuoc-doi-khac-du-ky-full', 'https://truyenconvert.net/truyen/hon-don-thien-de-quyet-17290', 'https://truyenconvert.net/truyen/van-co-thien-de-6450', 'https://truyenconvert.net/truyen/con-duong-ba-chu-akay-hau-truyen-full-dai-cuc-hay-59e24ef7-5fbb-47d0-8147-a8e1f8192cfd', 'https://truyenconvert.net/truyen/cuu-tinh-ba-the-quyet-6209', 'https://truyenconvert.net/truyen/de-quoc-dai-phan-tac-37262', 'https://truyenconvert.net/truyen/su-phu-toi-la-than-tien-duong-bach-xuyen-full', 'https://truyenconvert.net/truyen/cac-su-de-deu-la-dai-lao-vay-ta-chi-co-the-bat-hack-35805', 'https://truyenconvert.net/truyen/ta-co-9-trieu-ty-liem-cau-tien-32251', 'https://truyenconvert.net/truyen/nhan-dao-dai-thanh-31494', 'https://truyenconvert.net/truyen/do-thi-tu-chan-y-thanh-7545', 'https://truyenconvert.net/truyen/mink-duong-pho-so-13-31766', 'https://truyenconvert.net/truyen/toan-cau-lanh-chua-bat-dau-tro-thanh-sa-mac-lanh-chua-32231', 'https://truyenconvert.net/truyen/hom-nay-ta-co-the-thua-ke-phu-quan-di-san-sao-35592', 'https://truyenconvert.net/truyen/cao-thu-ha-son-ta-la-tien-nhan-ly-duc-than-full', 'https://truyenconvert.net/truyen/hac-lien-hoa-cong-luoc-so-tay-37036', 'https://truyenconvert.net/truyen/tien-vo-de-ton-106532', 'https://truyenconvert.net/truyen/quoc-vuong-34654', 'https://truyenconvert.net/truyen/nhung-ngay-o-comic-lam-nguoi-co-van-tinh-than-tai-my-man-duong-tam-linh-dao-su-dich-nhat-tu-36409', 'https://truyenconvert.net/truyen/huan-luyen-quan-su-ngay-thu-nhat-cao-lanh-giao-hoa-dua-nuoc-cho-ta-33731', 'https://truyenconvert.net/truyen/toan-dan-linh-chu-bat-dau-che-tao-bat-hu-tien-vuc-31403', 'https://truyenconvert.net/truyen/tot-nhat-con-re-25014', 'https://truyenconvert.net/truyen/70-tieu-kieu-the-me-ke-37356', 'https://truyenconvert.net/truyen/mang-theo-khong-kho-hang-hoi-80-37040', 'https://truyenconvert.net/truyen/hai-duong-cau-sinh-vo-han-thang-cap-tien-hoa-36873', 'https://truyenconvert.net/truyen/van-minh-chi-van-gioi-lanh-chua-26280', 'https://truyenconvert.net/truyen/hong-mong-thien-de-25733', 'https://truyenconvert.net/truyen/pha-quan-menh-chang-re-bat-pham-diep-pham-tac-gia-tu-pham', 'https://truyenconvert.net/truyen/ta-tai-pham-nhan-khoa-hoc-tu-tien-29748', 'https://truyenconvert.net/truyen/chien-than-vo-dich-thien-ha-sieu-cap-chien-than-lam-thieu-huy-truyen-full', 'https://truyenconvert.net/truyen/cong-phap-bi-pha-mat-ta-cang-manh-hon-35366', 'https://truyenconvert.net/truyen/than-hao-tu-so-0-buoc-len-the-gioi-dinh-phong-104418', 'https://truyenconvert.net/truyen/ta-tai-quy-di-the-gioi-can-than-tu-tien-35123', 'https://truyenconvert.net/truyen/tao-hoa-chi-vuong-101111', 'https://truyenconvert.net/truyen/thai-co-than-vuong-101274', 'https://truyenconvert.net/truyen/nien-dai-van-nam-phu-cuc-pham-vo-truoc-trong-sinh-35024', 'https://truyenconvert.net/truyen/luan-hoi-dan-de-28665', 'https://truyenconvert.net/truyen/linh-vo-de-ton-14674', 'https://truyenconvert.net/truyen/xuyen-nhanh-khong-phuc-toi-chien-30452', 'https://truyenconvert.net/truyen/than-hao-tu-thi-d-i-h-c-sau-bat-dau-28911', 'https://truyenconvert.net/truyen/vut-bo-chang-re-ngoc-so-tran-truyen-full', 'https://truyenconvert.net/truyen/than-kiem-vo-dich-35584', 'https://truyenconvert.net/truyen/ly-tri-nguoi-cho-kinh-so-31907', 'https://truyenconvert.net/truyen/khai-truong-nguoi-tai-trong-cua-hang-lao-ban-co-uc-diem-cuong-31302', 'https://truyenconvert.net/truyen/ta-phat-song-truc-tiep-thong-thanh-trieu-37429', 'https://truyenconvert.net/truyen/cuc-pham-toan-nang-cao-thu-103294', 'https://truyenconvert.net/truyen/tuan-thien-yeu-bo-31693', 'https://truyenconvert.net/truyen/cai-the-de-ton-100558', 'https://truyenconvert.net/truyen/dai-duong-de-nhat-nghich-tu-30404', 'https://truyenconvert.net/truyen/cac-nguoi-tu-tien-ta-lam-ruong-37446', 'https://truyenconvert.net/truyen/vo-dao-than-ma-ly-tan-full', 'https://truyenconvert.net/truyen/thien-dao-do-thu-quan-14540', 'https://truyenconvert.net/truyen/thai-hoang-thon-thien-quyet-32503', 'https://truyenconvert.net/truyen/ta-dua-vao-danh-dau-vo-dich-bat-dau-trieu-hoan-than-ma-37080', 'https://truyenconvert.net/truyen/ta-moi-tuan-tuy-co-mot-cai-moi-chuc-nghiep-28958', 'https://truyenconvert.net/truyen/than-thoai-ky-nguyen-ta-tien-hoa-thanh-hang-tinh-cap-cu-thu-37624', 'https://truyenconvert.net/truyen/vo-thuong-sat-than-100358', 'https://truyenconvert.net/truyen/chien-ham-cua-ta-co-the-thang-cap-29431', 'https://truyenconvert.net/truyen/tuyet-the-than-hoang-107356', 'https://truyenconvert.net/truyen/tu-han-che-ta-don-gian-vo-dich-33860', 'https://truyenconvert.net/truyen/thi-than-chien-de-100006', 'https://truyenconvert.net/truyen/thien-kieu-tu-hon-ta-rut-ra-tien-to-tu-hanh-37488', 'https://truyenconvert.net/truyen/vu-than-thien-ha-101271', 'https://truyenconvert.net/truyen/tu-dai-thu-bat-dau-tien-hoa-101213', 'https://truyenconvert.net/truyen/phe-sai-muon-nghich-thien-ma-de-cuong-phi-tieu-that-gia-full', 'https://truyenconvert.net/truyen/toan-bo-vi-dien-deu-quy-cau-nhan-vat-phan-dien-nu-chinh-lam-nguoi-30429', 'https://truyenconvert.net/truyen/nu-tong-tai-toan-nang-binh-vuong-12161', 'https://truyenconvert.net/truyen/ta-o-huyen-vu-tren-lung-xay-gia-vien-29810', 'https://truyenconvert.net/truyen/kiem-lai-17186', 'https://truyenconvert.net/truyen/uyen-thien-ton-35873', 'https://truyenconvert.net/truyen/khai-cuoc-kim-phong-te-vu-lau-ch-mot-dao-kinh-thien-ha-33411', 'https://truyenconvert.net/truyen/tu-tien-bac-si-106196', 'https://truyenconvert.net/truyen/than-ma-thien-ton-ly-phong-full', 'https://truyenconvert.net/truyen/metaverse-xuyen-viet-hau-tu-ky-to-he-thong-36334', 'https://truyenconvert.net/truyen/theo-dai-thu-bat-dau-tien-hoa-25385', 'https://truyenconvert.net/truyen/giao-chu-ve-huu-thuong-ngay-29542', 'https://truyenconvert.net/truyen/sieu-cap-bao-an-tai-do-thi-7221', 'https://truyenconvert.net/truyen/cuc-pham-van-tue-gia-32693', 'https://truyenconvert.net/truyen/tong-vo-ta-lay-giang-ho-dong-trieu-dinh-35063', 'https://truyenconvert.net/truyen/de-nguoi-cau-ca-nguoi-lai-cau-len-tau-ngam-nguyen-tu-37035', 'https://truyenconvert.net/truyen/cu-long-thuc-tinh-luc-hi-truyen-full', 'https://truyenconvert.net/truyen/van-lan-tra-ve-vi-su-cu-the-vo-dich-37303', 'https://truyenconvert.net/truyen/hac-thach-mat-ma-29286', 'https://truyenconvert.net/truyen/cuu-long-thanh-to-13506', 'https://truyenconvert.net/truyen/nha-ta-dap-chua-nuoc-that-khong-co-cu-mang-a-30792', 'https://truyenconvert.net/truyen/nghe-trom-tieng-long-bat-dau-van-tieu-nang-kiem-chem-dinh-quang-tien-33202', 'https://truyenconvert.net/truyen/chien-than-tu-la-giang-nghia-truyen-full', 'https://truyenconvert.net/truyen/tai-nha-tre-lam-dau-bep-nuoi-tre-my-thuc-37747', 'https://truyenconvert.net/truyen/thien-dao-thu-can-mot-phan-cay-cay-phan-tram-thu-hoach-37304', 'https://truyenconvert.net/truyen/than-cap-phuc-che-he-thong-34018', 'https://truyenconvert.net/truyen/ta-tu-tien-toan-bo-nho-bi-dong-31095', 'https://truyenconvert.net/truyen/dan-dai-chi-ton-khuong-pham-fulll', 'https://truyenconvert.net/truyen/tien-moc-ky-duyen-31243', 'https://truyenconvert.net/truyen/dinh-phong-vo-thuat-duong-khai-full', 'https://truyenconvert.net/truyen/thai-at-30379', 'https://truyenconvert.net/truyen/thien-hoang-vo-dich-21719', 'https://truyenconvert.net/truyen/dau-la-dai-luc-iv-chung-cuc-dau-la-101403', 'https://truyenconvert.net/truyen/ta-co-mot-toa-nha-ma-nga-huu-nhat-toa-khung-bo-oc-21918', 'https://truyenconvert.net/truyen/de-nguoi-mo-tiem-sua-chua-nguoi-nhac-len-co-chien-phong-bao-37370', 'https://truyenconvert.net/truyen/kiem-den-11011', 'https://truyenconvert.net/truyen/de-de-ta-la-thien-tuyen-chi-tu-33826', 'https://truyenconvert.net/truyen/ta-theo-tu-trong-bung-me-lien-bat-dau-tu-luyen-38451', 'https://truyenconvert.net/truyen/dieu-thap-tai-tu-tien-gioi-34243', 'https://truyenconvert.net/truyen/khung-bo-song-lai-19738']
    # Limit the number of concurrent tasks to 10
    concurrency = 10
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_task(link):
        async with semaphore:
            await async_process_book(link)

    # Create tasks in batches of 10
    for i in range(0, len(book_links), concurrency):
        batch = book_links[i:i + concurrency]
        tasks = [limited_task(link) for link in batch]
        await asyncio.gather(*tasks)

# Chạy main() bất đồng bộ
asyncio.run(main())
