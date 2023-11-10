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
            next_chapter_tag = soup.find(id="nextchap")
            next_chapter_link = next_chapter_tag.get(
                    'href') if next_chapter_tag else None
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

                #print(next_chapter_link)
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

    book_links =['https://truyenconvert.net/truyen/van-dao-long-hoang-14480',
                'https://truyenconvert.net/truyen/dinh-phong-vo-thuat-duong-khai-full',
                'https://truyenconvert.net/truyen/ta-di-roi-linh-ha-bat-bat-bat-bat-do',
                'https://truyenconvert.net/truyen/tu-tien-tu-trong-thay-ky-ngo-bat-dau-36506',
                'https://truyenconvert.net/truyen/ong-xa-phuc-hac-lua-tinh-kieu-kien-bang-full',
                'https://truyenconvert.net/truyen/ba-xa-ngoan-ngoan-de-anh-sung-em-to-can-nhi-full',
                'https://truyenconvert.net/truyen/sau-khi-ca-man-the-ga-full',
                'https://truyenconvert.net/truyen/hao-mon-kinh-mong-3-dung-de-lo-nhau-an-tam-full',
                'https://truyenconvert.net/truyen/me-17-tuoi-con-trai-thien-tai-cha-phuc-hac-trinh-ninh-tinh-full',
                'https://truyenconvert.net/truyen/quan-thuat-tac-gia-cau-bao-tu-full',
                'https://truyenconvert.net/truyen/linh-chi-hoa-ne-mo-ngoc',
                'https://truyenconvert.net/truyen/anh-hung-menh-van-1864',
                'https://truyenconvert.net/truyen/sau-trong-dem-toi-tac-gia-ciara',
                'https://truyenconvert.net/truyen/tu-dung-phat-hien-em-trai-rat-dang-yeu-full',
                'https://truyenconvert.net/truyen/nhu-giac-mong-ban-dau-tu-mong-so-giac',
                'https://truyenconvert.net/truyen/giai-ma-trai-tim-em-yen-dan-amber',
                'https://truyenconvert.net/truyen/than-chu-o-re-vuong-bac-than-trieu-thanh-ha-truyen-full',
                'https://truyenconvert.net/truyen/che-ngu-nam-than-tham-dinh-full',
                'https://truyenconvert.net/truyen/tong-tai-tan-khoc-chiem-huu-dien-cuong-mong-ai',
                'https://truyenconvert.net/truyen/nu-dong-nghiep-tra-xanh-co-quy-mang-qua-toan-nai',
                'https://truyenconvert.net/truyen/pha-quan-menh-chang-re-bat-pham-diep-pham-tac-gia-tu-pham',
                'https://truyenconvert.net/truyen/bac-si-giup-em-luong-dien-chieu-full',
                'https://truyenconvert.net/truyen/cuoi-cung-van-bo-lo-nhau-tranh-ca',
                'https://truyenconvert.net/truyen/ta-linh-the-gioi-ta-lay-nhuc-than-quet-ngang-the-nay-32072',
                'https://truyenconvert.net/truyen/ban-hoc-tu-hoi-cam-mieng-di-deu-dung-khoac-lac-37398',
                'https://truyenconvert.net/truyen/not-ruoi-son-noi-day-mat-qua-qua',
                'https://truyenconvert.net/truyen/a-thanh-ca-nho-thien-tai-full',
                'https://truyenconvert.net/truyen/o-dai-hoc-bi-hoa-khoi-chan-cua-tan-lang',
                'https://truyenconvert.net/truyen/van-co-chi-ton-giang-lam-full',
                'https://truyenconvert.net/truyen/ve-sau-mua-ha-trieu-lo-ha-kho-full',
                'https://truyenconvert.net/truyen/trong-em-tu-thuo-con-tho-full',
                'https://truyenconvert.net/truyen/linh-canh-hanh-gia-32858',
                'https://truyenconvert.net/truyen/cong-cuoc-theo-duoi-cua-lang-tong-lang-tuan-hao',
                'https://truyenconvert.net/truyen/thien-dao-huu-khuyet-truong-huyen-full',
                'https://truyenconvert.net/truyen/trach-nhat-phi-thang-32985',
                'https://truyenconvert.net/truyen/dinh-phong-thien-ha-luc-lam-thien-full',
                'https://truyenconvert.net/truyen/dau-canh-treo-mot-manh-trang-xanh-be-con-say-xin',
                'https://truyenconvert.net/truyen/ngai-vuong-ket-hon-nhe-tac-gia-qua-dao-vi-tieu-tien-nu',
                'https://truyenconvert.net/truyen/hoan-tuong-the-gioi-37175',
                'https://truyenconvert.net/truyen/mot-kiep-van-vuong-hieu-y-lam',
                'https://truyenconvert.net/truyen/em-dung-mong-thoat-khoi-toi-tieu-my-a-full',
                'https://truyenconvert.net/truyen/be-alpha-nay-co-chut-ngot-ngao-dieu-dieu-tho',
                'https://truyenconvert.net/truyen/lop-truong-lanh-lung-duoc-y',
                'https://truyenconvert.net/truyen/tinh-hoan-su-menh-36344',
                'https://truyenconvert.net/truyen/gia-bat-thi-quai-dam-35805',
                'https://truyenconvert.net/truyen/bat-dau-lam-nam-vung-buc-ta-lat-ban-37248',
                'https://truyenconvert.net/truyen/dau-den-may-van-yeu-huynh-thien-ky-full',
                'https://truyenconvert.net/truyen/va-vao-anh-mat-em-hoa-tieu-le',
                'https://truyenconvert.net/truyen/vo-cuc-ma-dao-dinh-hao-full',
                'https://truyenconvert.net/truyen/quan-lam-binh-vuong-ss-ha-than-full',
                'https://truyenconvert.net/truyen/be-thich-khach-toi-am-sat-anh-di-ne-full',
                'https://truyenconvert.net/truyen/dich-nu-cuong-phi-cuc-pham-bao-boi-vo-lai-nuong-ma-duyet-duyet-full',
                'https://truyenconvert.net/truyen/cao-thu-tu-chan-diep-thien-truyen-full-tac-gia-phong-hoa',
                'https://truyenconvert.net/truyen/ta-doat-xa-chinh-minh-36285',
                'https://truyenconvert.net/truyen/trong-sinh-quat-khoi-huong-giang-37369',
                'https://truyenconvert.net/truyen/reconvert-than-thanh-la-ma-de-quoc-37286',
                'https://truyenconvert.net/truyen/xuyen-thanh-ban-trai-cu-cua-hotboy-truong-lien-soc',
                'https://truyenconvert.net/truyen/ta-o-tuy-duong-bat-nui-nang-dinh-doa-so-duong-quang-37424',
                'https://truyenconvert.net/truyen/co-be-tho-ngay-dung-hong-tron-da-chi-thuong-lang-full',
                'https://truyenconvert.net/truyen/khoet-vach-treo-tuong-leo-giuong-deo-em',
                'https://truyenconvert.net/truyen/chi-muon-quay-lai-thoi-gian-de-yeu-anh-than-gia-ngon',
                'https://truyenconvert.net/truyen/tong-giam-doc-hang-ty-cuop-lai-vo-truoc-da-sinh-con-minh-chau-hoan-full',
                'https://truyenconvert.net/truyen/tong-tai-my-nhan-yeu-can-ve-ly-tien-nguyen-truyen-full',
                'https://truyenconvert.net/truyen/toc-nhan-dau-tu-ta-san-xuat-hang-loat-dai-de-36904',
                'https://truyenconvert.net/truyen/chang-soi-hap-dan-phong-van-tieu-yeu-full',
                'https://truyenconvert.net/truyen/long-huyet-chien-than-phong-thanh-duong-full',
                'https://truyenconvert.net/truyen/quang-minh-32302',
                'https://truyenconvert.net/truyen/hoa-kiep-nhan-sinh-thuy-linh-znghi-full',
                'https://truyenconvert.net/truyen/co-qua-nhieu-dieu-anh-khong-biet-chung-tieu-nhac',
                'https://truyenconvert.net/truyen/co-vo-yeu-nghiet-cua-dai-boss-mafia-mac-ai-ly',
                'https://truyenconvert.net/truyen/trong-phan-1995-37463',
                'https://truyenconvert.net/truyen/ca-man-tu-tien-sieu-vui-suong-trach-lan-full',
                'https://truyenconvert.net/truyen/hong-hoang-thong-thien-di-chuc-thuc-ta-co-cai-nghia-huynh-37349',
                'https://truyenconvert.net/truyen/chu-gia-em-yeu-nhuoc-giai-full',
                'https://truyenconvert.net/truyen/bay-ngay-an-ai-an-tam-full',
                'https://truyenconvert.net/truyen/cong-tu-khuynh-thanh-duy-hoa-tong-tu',
                'https://truyenconvert.net/truyen/thien-kim-tro-ve-cha-but-tieu-tuu-full',
                'https://truyenconvert.net/truyen/lo-mot-buoc-dau-thuong-ca-doi-thien-nguyet-phung',
                'https://truyenconvert.net/truyen/giai-tri-vua-ra-nguc-lien-cung-thien-hau-nhao-tai-tieng-35440',
                'https://truyenconvert.net/truyen/tu-la-vo-than-1178',
                'https://truyenconvert.net/truyen/truyen-co-nguyet-vuong-lac-kha-han',
                'https://truyenconvert.net/truyen/ket-hon-am-duong-0-gio-sang-full',
                'https://truyenconvert.net/truyen/bat-hu-kiem-than-lam-dich-full',
                'https://truyenconvert.net/truyen/thien-menh-chi-ton-tran-khiem-truyen-full',
                'https://truyenconvert.net/truyen/di-the-ta-quan-phong-lang-thien-ha-full',
                'https://truyenconvert.net/truyen/em-khong-muon-lam-nguoi-thay-the-chi-full',
                'https://truyenconvert.net/truyen/doan-sat-thu-tien-hoa-than-cap-lam-lang-full',
                'https://truyenconvert.net/truyen/co-hau-cam-cua-cong-tuoc-tieu-cam-cam',
                'https://truyenconvert.net/truyen/em-la-tat-ca-cua-toi-co-gai-a-nhuoc-hi-full',
                'https://truyenconvert.net/truyen/truyen-12-nu-than-slaydark',
                'https://truyenconvert.net/truyen/chu-nho-vy-thao-full',
                'https://truyenconvert.net/truyen/hoi-han-muon-mang-hoang-man-huyen',
                'https://truyenconvert.net/truyen/hang-xom-cua-ta-la-nghe-si-34385',
                'https://truyenconvert.net/truyen/lac-nhau-mot-doi-duong-thien-y-full',
                'https://truyenconvert.net/truyen/bo-bo-kinh-tam-dong-hoa-full',
                'https://truyenconvert.net/truyen/thua-lo-thanh-thu-phu-tu-tro-choi-101812',
                'https://truyenconvert.net/truyen/weibo-cua-toi-co-the-doan-so-menh-full',
                'https://truyenconvert.net/truyen/tong-man-ta-tai-yeu-quai-thoi-dai-lam-ninja-37382',
                'https://truyenconvert.net/truyen/hoan-hoan-ai-cach-yeu-cua-chu-tich-phong-tieu-cam-cam',
                'https://truyenconvert.net/truyen/ke-khung-nguoi-dien-chau-thanh-full',
                'https://truyenconvert.net/truyen/tieu-tong-xin-tha-cho-toi',
                'https://truyenconvert.net/truyen/chu-gioi-de-nhat-nhan-33966',
                'https://truyenconvert.net/truyen/ta-bat-coc-dong-thoi-gian-nga-bang-gia-lieu-thi-gian-tuyen-33782',
                'https://truyenconvert.net/truyen/tinh-chien-phong-bao-kho-lau-tinh-tinh-full',
                'https://truyenconvert.net/truyen/chi-co-rinnegan-sao-duoc-ta-con-muon-tenseigan-37299',
                'https://truyenconvert.net/truyen/khong-he-dang-yeu-tay-phong-chuoc-chuoc',
                'https://truyenconvert.net/truyen/hom-nay-thien-kim-lai-di-va-mat-full-bf529f68-4ee1-4c5f-acd9-f467ac14b5eb',
                'https://truyenconvert.net/truyen/nga-dich-su-pho-moi-dao-dai-han-tai-dot-pha-33140',
                'https://truyenconvert.net/truyen/thong-doc-dai-nhan-em-xin-anh-man-linh-full',
                'https://truyenconvert.net/truyen/trung-sinh-de-gap-nguoi-da-bach-vo-nha',
                'https://truyenconvert.net/truyen/truyen-ma-bay-nang-dau-full-85-chap-ngoai-truyen-nang-dau-thu-7-nha-ho-hoang-thien-yet',
                'https://truyenconvert.net/truyen/me-doc-than-tuoi-18-co-thuy-linh-full',
                'https://truyenconvert.net/truyen/quy-de-cuong-the-dai-tieu-thu-an-choi-trac-tang-tieu-that-gia-full',
                'https://truyenconvert.net/truyen/than-y-xuat-chung-hoang-hach-truyen-full-tac-gia-luc-thuy',
                'https://truyenconvert.net/truyen/da-cong-tien-tri-36103',
                'https://truyenconvert.net/truyen/thay-bach-dung-lam-loan-dan-tieu-nghien',
                'https://truyenconvert.net/truyen/kiep-truoc-thanh-that-kiep-truoc-cua-ta-bi-moc-ra-36025',
                'https://truyenconvert.net/truyen/em-khong-can-lai-co-don-gian-moc-tu-on-duong',
                'https://truyenconvert.net/truyen/cong-phap-bi-pha-mat-ta-cang-manh-hon-35366',
                'https://truyenconvert.net/truyen/tro-choi-nguy-hiem-tong-tai-toi-ac-tay-troi-an-tam-full',
                'https://truyenconvert.net/truyen/khung-bo-phuc-to-than-bi-phuc-to-28080',
                'https://truyenconvert.net/truyen/tuyet-sac-dan-duoc-su-quy-vuong-yeu-phi-tieu-that-gia-full',
                'https://truyenconvert.net/truyen/mua-he-mang-ten-em-nham-bang-chu-full',
                'https://truyenconvert.net/truyen/can-cu-so-7-33115',
                'https://truyenconvert.net/truyen/thu-linh-am-ve-xuat-dao-o-c-vi-xuan-vu-hanh-hoa-bach',
                'https://truyenconvert.net/truyen/bao-thu-cua-re-phe-vat-lam-hien-full',
                'https://truyenconvert.net/truyen/tam-quoc-khai-cuc-tram-quan-vu-tam-quoc-khai-cuoc-chem-quan-vu-37437',
                'https://truyenconvert.net/truyen/long-de-bat-diet-luc-ly-full',
                'https://truyenconvert.net/truyen/hoa-vu-yeu-dong-lieu-dich-hoc-thuat-tu-hoi-37094',
                'https://truyenconvert.net/truyen/mot-giay-sua-chua-dai-de-tu-vi-bat-dau-tuc-vo-dich-37275',
                'https://truyenconvert.net/truyen/nga-trach-lap-tu-am-anh-quy-tich-azeroth-bong-ma-quy-dao-36143',
                'https://truyenconvert.net/truyen/xin-goi-ta-quy-sai-dai-nhan-112942',
                'https://truyenconvert.net/truyen/tong-tai-cuong-the-phu-nhan-da-tro-ve-full',
                'https://truyenconvert.net/truyen/nga-tai-lieu-thien-quan-mo-nhi-truong-sinh-lo-37119',
                'https://truyenconvert.net/truyen/thu-phi-thien-ha-than-y-dai-tieu-thu-ngu-tieu-dong',
                'https://truyenconvert.net/truyen/hoac-cach-oc-ty-chi-hoi-vu-su-hogwarts-chi-phu-thuy-xam-37329',
                'https://truyenconvert.net/truyen/phe-sai-muon-nghich-thien-ma-de-cuong-phi-tieu-that-gia-full',
                'https://truyenconvert.net/truyen/vo-yeu-la-me-don-than-thuan-khiet-nhat-kieu-le-full',
                'https://truyenconvert.net/truyen/tam-quoc-tran-thu-bien-cuong-muoi-nam-bat-dau-danh-dau-ly-nguyen-ba-37240',
                'https://truyenconvert.net/truyen/co-dau-thay-the-cua-pho-tong-nham-huan-full',
                'https://truyenconvert.net/truyen/nga-than-thuong-huu-dieu-long-34260',
                'https://truyenconvert.net/truyen/ve-si-than-cap-cua-nu-tong-giam-doc',
                'https://truyenconvert.net/truyen/toi-cuong-than-thoai-de-hoang-full-tac-gia-nham-nga-tieu',
                'https://truyenconvert.net/truyen/toan-dan-dao-quan-day-hoc-tro-gap-boi-phan-hoi-112696',
                'https://truyenconvert.net/truyen/bi-mat-nguy-hiem-xin-anh-tha-thu-huynh-thien-ky',
                'https://truyenconvert.net/truyen/duoc-than-am-ma-su-full',
                'https://truyenconvert.net/truyen/ep-yeu-100-ngay-diep-phi-da-full',
                'https://truyenconvert.net/truyen/mi-anh-anh-giai-ngay-tho-full',
                'https://truyenconvert.net/truyen/o-dai-hoc-bi-hoa-khoi-chan-cua',
                'https://truyenconvert.net/truyen/vo-oi-ve-nhanh-le-pham-kim-hue-full',
                'https://truyenconvert.net/truyen/oan-gia-thoi-de-thue-cho-tong-tai-huong-ngoc-lani-full',
                'https://truyenconvert.net/truyen/song-lai-lam-tiep-thi-vuong-35243',
                'https://truyenconvert.net/truyen/tu-hong-mong-thanh-the-bat-dau-vo-dich-32314',
                'https://truyenconvert.net/truyen/truyen-linh-vuc-nghich-thuong-thien-full',
                'https://truyenconvert.net/truyen/vu-cuc-thien-ha-lam-minh-full',
                'https://truyenconvert.net/truyen/quang-minh-37086',
                'https://truyenconvert.net/truyen/truyen-gia-thien-full',
                'https://truyenconvert.net/truyen/bao-ho-ben-ta-toc-truong-29534',
                'https://truyenconvert.net/truyen/buc-ta-cuoi-cao-duong-ta-do-ca-nha-nguoi-35192',
                'https://truyenconvert.net/truyen/tham-hai-du-tan-33910',
                'https://truyenconvert.net/truyen/than-de-trong-sinh-diep-tran-truyen-full',
                'https://truyenconvert.net/truyen/y-dao-quan-do',
                'https://truyenconvert.net/truyen/bi-mat-noi-goc-toi-nhi-dong-tho-tu',
                'https://truyenconvert.net/truyen/hao-nhat-tam-diem-can-tranh',
                'https://truyenconvert.net/truyen/ba-xa-nen-ngoan-ngoan-yeu-anh-hoang-da-thanh-tuyet-truyen-full',
                'https://truyenconvert.net/truyen/ta-da-tai-luyen-ai-tro-choi-106541',
                'https://truyenconvert.net/truyen/thieu-soai-dai-nhan-cua-nang-tong-nguyen-nhiem',
                'https://truyenconvert.net/truyen/mot-cham-la-say-dam-hai-cham-la-dam-ngay-full',
                'https://truyenconvert.net/truyen/tro-choi-nay-cung-qua-chan-that-31102',
                'https://truyenconvert.net/truyen/anh-de-than-bi-trom-cuoi-vo-yeu-toi-pk-cong-tu-dien',
                'https://truyenconvert.net/truyen/phong-tong-sung-the-tron-kiep-hoang-hon-tren-bien',
                'https://truyenconvert.net/truyen/garfield-bao-thu-ky-kim-cuong-quyen-full',
                'https://truyenconvert.net/truyen/so-phan-an-bai-me-bim',
                'https://truyenconvert.net/truyen/mink-duong-pho-so-13-31766',
                'https://truyenconvert.net/truyen/yeu-duong-doan-chinh-tay-tay-dac',
                'https://truyenconvert.net/truyen/cho-nguoi-noi-yeu-toi-full',
                'https://truyenconvert.net/truyen/nhung-yeu-quai-nay-lam-sao-deu-co-thanh-mau-gia-ta-yeu-quai-cham-yeu-do-huu-huyet-dieu-34349',
                'https://truyenconvert.net/truyen/phong-cach-yeu-tham-cua-nha-giau-moi-noi-hoa-li-tam-hoan',
                'https://truyenconvert.net/truyen/my-man-the-gioi-le-minh-quy-tich-37494',
                'https://truyenconvert.net/truyen/cam-ai-tinh-nhan-sugar-thu-cach-full',
                'https://truyenconvert.net/truyen/bon-vuong-muon-thanh-tinh-hoa-li-tam-hoan',
                'https://truyenconvert.net/truyen/dan-tuc-tong-tuong-tay-huyet-than-khai-thuy-dan-toc-theo-tuong-tay-huyet-than-bat-dau-37072',
                'https://truyenconvert.net/truyen/hop-dong-hon-nhan-bat-dac-di-tham-hao-quan-full',
                'https://truyenconvert.net/truyen/nga-tai-dien-tong-kiem-dao-thanh-tien-37546',
                'https://truyenconvert.net/truyen/hoa-trong-mong-ca-doi-vi-em-hani-hai-nguyen',
                'https://truyenconvert.net/truyen/bat-dau-max-cap-bao-xa-messi-cau-ta-nhap-argentina-34406',
                'https://truyenconvert.net/truyen/trong-mat-chi-co-troi-xanh-nha-dau',
                'https://truyenconvert.net/truyen/game-of-thrones-thuy-long-chi-no-108034',
                'https://truyenconvert.net/truyen/vo-tan-dan-dien-nhiep-van-full',
                'https://truyenconvert.net/truyen/tu-hai-quan-dai-tuong-den-gotei-13-37413',
                'https://truyenconvert.net/truyen/nghe-noi-thua-tuong-quyen-the-muon-hoan-luong-luu-cau-hoa',
                'https://truyenconvert.net/truyen/de-hoang-manh-nhat-tan-quan-full',
                'https://truyenconvert.net/truyen/quoc-vuong-34654',
                'https://truyenconvert.net/truyen/no-le-cua-ceo-selinapheobe',
                'https://truyenconvert.net/truyen/quan-tau-nguoi-khac-khong-can-thi-toi-lay-nguyet-cam-y-mong',
                'https://truyenconvert.net/truyen/ta-tai-huyen-huyen-the-gioi-them-diem-tu-hanh-37218',
                'https://truyenconvert.net/truyen/ngai-anh-de-dang-hot-va-cau-nghe-si-het-thoi-khai-tam-thi-phuc-ma',
                'https://truyenconvert.net/truyen/nhip-tim-sang-som-manh-ngu-nguyet',
                'https://truyenconvert.net/truyen/vo-cu-toi-khong-muon-lam-nguoi-thay-the-full',
                'https://truyenconvert.net/truyen/sau-khi-ly-hon-mot-ca-khuc-cua-ta-hoa-khap-ca-nuoc-37355',
                'https://truyenconvert.net/truyen/huyen-thoai-tro-ve-full',
                'https://truyenconvert.net/truyen/tan-lua-trong-dem-dai-105842',
                'https://truyenconvert.net/truyen/toi-cuong-than-thoai-de-hoang-nham-nga-tieu-full',
                'https://truyenconvert.net/truyen/ta-chinh-la-than-31031',
                'https://truyenconvert.net/truyen/quy-nhap-mong-luc-nua-dem-lu-thanh-full',
                'https://truyenconvert.net/truyen/hao-lai-o-hoi-che-hollywood-hoi-che-37127',
                'https://truyenconvert.net/truyen/em-la-vi-sao-chieu-sang-cuoc-doi-anh-chu-duong-em-se-ngoan-ngoan-ma-full',
                'https://truyenconvert.net/truyen/do-thi-tang-kieu-tam-duong-tru-tru-full',
                'https://truyenconvert.net/truyen/vo-han-buu-soa-nguoi-dua-thu-vo-han-35645',
                'https://truyenconvert.net/truyen/thai-tu-bui-doi-diep-hoan-full',
                'https://truyenconvert.net/truyen/mang-vo-ve-nuoi-hoang-chi-full',
                'https://truyenconvert.net/truyen/choc-phai-dien-ha-hac-am-lee-sam',
                'https://truyenconvert.net/truyen/doc-y-than-nu-phuc-hac-lanh-de-cuong-sung-the-nguyet-ha-khuynh-ca',
                'https://truyenconvert.net/truyen/ta-that-khong-co-nghi-toi-the-tu-la-nu-de-a-nga-chan-mot-tuong-qua-the-tu-thi-nu-de-a-37059',
                'https://truyenconvert.net/truyen/ve-si-than-cap-cua-nu-tong-giam-doc-lam-phi-full']
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
