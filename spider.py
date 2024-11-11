import requests
from bs4 import BeautifulSoup
import json
import time

# 文件路径
keyword_file = 'keywords.txt'
output_file = 'results.json'

# 读取关键字
with open(keyword_file, 'r') as f:
    keywords = [line.strip() for line in f.readlines()]

# 基础URL
search_url_template = "https://m.douban.com/search/?query={}"
book_url_base = "https://book.douban.com"

# 结果存储
results = []

# 创建一个 Session 对象
session = requests.Session()

# 设置 headers，模拟浏览器请求
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
}

for keyword in keywords:
    search_url = search_url_template.format(keyword)
    response = session.get(search_url, headers=headers)
    
    # 调试信息
    print(f"Searching for keyword: {keyword}")
    print(f"Search URL: {search_url}")
    print(f"Response status code: {response.status_code}")
    if response.status_code != 200:
        print(f"Failed to fetch search results for keyword: {keyword}")
        continue
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找书籍条目链接
    book_links = soup.find_all('a', href=True)
    book_suffixes = [link['href'] for link in book_links if '/subject/' in link['href']]
    
    # 调试信息
    if not book_suffixes:
        print(f"No book links found for keyword: {keyword}")
    
    for suffix in book_suffixes:
        # 修正 URL 拼接逻辑，确保去掉 /book
        book_url = book_url_base + suffix.replace('/book', '')
        book_response = session.get(book_url, headers=headers)
        
        # 调试信息
        print(f"Fetching book details from URL: {book_url}")
        print(f"Book response status code: {book_response.status_code}")
        if book_response.status_code != 200:
            print(f"Failed to fetch book details for URL: {book_url}")
            continue
        
        book_soup = BeautifulSoup(book_response.text, 'html.parser')

        # 获取书籍信息
        itemreviewed = book_soup.find('span', property='v:itemreviewed')
        # 搜索包含 "/search/" 的链接
        search_tag = book_soup.find('a', href=lambda href: href and "/search/" in href)
        # 如果 search_tag 不存在，则搜索包含 "/author/" 的链接
        if not search_tag:
            author_tag = book_soup.find('a', href=lambda href: href and "/author/" in href)
        else:
            author_tag = search_tag

        #获取出版社信息        
        publisher_tag = book_soup.find('a', href=lambda href: href and "/press/" in href)
        if not publisher_tag:
            publisher_tag = book_soup.find('span', string='出版社:').find_next_sibling(string=True)

        if author_tag:
            # 如果 author_tag 不为空
            if "编著" in author_tag:
                # 如果 author_tag 中包含 "编著" 字符串，去除 "编著"
                author = author_tag.text.replace("编著", "")
            else:
                # 如果 author_tag 存在，但是不包含 "编著" ，直接赋值
                author = author_tag.text
        else:
            # 如果 author_tag 为空，赋值为 "N/A"
            author = 'N/A'
      
        publisher = publisher_tag.text if publisher_tag else 'N/A'
        pub_year = book_soup.find('span', string='出版年:').find_next_sibling(string=True)
        pages = book_soup.find('span', string='页数:').find_next_sibling(string=True)
        isbn = book_soup.find('span', string='ISBN:').find_next_sibling(string=True)

        # 打印调试信息
        print(f"Title: {itemreviewed.text if itemreviewed else 'N/A'}")
        print(f"Author: {author}")
        print(f"Publisher: {publisher}")
        print(f"Publication Year: {pub_year.strip() if pub_year else 'N/A'}")
        print(f"Pages: {pages.strip() if pages else 'N/A'}")
        print(f"ISBN: {isbn.strip() if isbn else 'N/A'}")

        book_info = {
            'keyword': keyword,
            'title': itemreviewed.text if itemreviewed else 'N/A',
            'author': author,
            'publisher': publisher,
            'pub_year': pub_year.strip() if pub_year else 'N/A',
            'pages': pages.strip() if pages else 'N/A',
            'isbn': isbn.strip() if isbn else 'N/A'
        }

        results.append(book_info)
        
        # 只保留第一条结果，跳出循环
        break
    
    # 为了避免过于频繁请求，加入短暂的休眠
    time.sleep(1)

# 保存结果到文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f'信息已保存到 {output_file}')
