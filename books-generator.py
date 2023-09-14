import os
import sys
import time
import shutil
import requests
import json
from lxml import etree
from requests.sessions import session
from utils import renderStar, createLogger, composeImages
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright
import datetime

logger = createLogger('books-generator')

def resolve(session, url, timeout):
    try:
        headers = {
          'Accept': 'text/html; charset=utf-8',
          'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
          'Referer': 'https://book.douban.com/mine?status=wish'
        }

        response = session.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return parseContent(response.text)
    except Exception as e:
        logger.error(f'resolve data from {url} fails due to offline', exc_info=True)
        return None

def parseContent(content):
    html = etree.HTML(content)
    items = html.xpath('//ul[@class="interest-list"]/li[@class="subject-item"]')
    next = html.xpath('string(//span[@class="next"]/a/@href)')
    next = str(next)
    if next.startswith('/'):
        next = f'http://book.douban.com{next}'

    list = []
    for item in items:
        parser = etree.HTML(etree.tostring(item, pretty_print=True))
        title = parser.xpath('string(//div[@class="info"]/h2/a/@title)')
        alt = parser.xpath('string(//div[@class="info"]/h2/a/@href)')
        image = parser.xpath('string(//div[@class="pic"]/a/img/@src)')

        pub = parser.xpath('string(//div[@class="pub"])')

        updated = parser.xpath('string(//span[@class="date"])')
        
        tags = parser.xpath('string(//span[@class="tags"])')
        tags = str(tags)
        tags = tags[3] if tags != '' and len(tags) > 3 else ''

        recommend = parser.xpath('string(//div[@class="short-note"]/div/span[contains(@class,"rating")]/@class)')
        recommend = str(recommend)
        recommend = renderStar(recommend[6])  if recommend != '' and len(recommend) > 6 else ''
        comment = parser.xpath('string(//p[@class="comment"])')
        comment = comment if comment != None else ''

        list.append({
            'title': str(title),
            'alt': str(alt),
            'image': str(image),
            'pub': str(pub),
            'updated': str(updated),
            'tags': str(tags),
            'recommend': str(recommend),
            'comment': str(comment)
        })
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    session = requests.session()

    # 读过
    readed = []
    logger.info(f"resolve readed books for {uid}...")
    url = f'http://book.douban.com/people/{uid}/collect'
    result = resolve(session, url, timeout)
    while result != None and result['next'] != '':
        readed.extend(result['list'])
        result = resolve(session, result['next'], timeout)

    # 在读
    reading = []
    logger.info(f"resolve reading books for {uid}...")
    url = f'http://book.douban.com/people/{uid}/do'
    result = resolve(session, url, timeout)
    while result != None and result['next'] != '':
        reading.extend(result['list'])
        result = resolve(session, result['next'], timeout)

    # 想读
    wishing = []
    logger.info(f"resolve wishing books for {uid}...")
    url = f'http://book.douban.com/people/{uid}/wish'
    result = resolve(session, url, timeout)
    while result != None and result['next'] != '':
        wishing.extend(result['list'])
        result = resolve(session, result['next'], timeout)

    # 统计
    statics = [ 0 for i in  range(12)]
    currrent = datetime.datetime.now()
    for book in readed:
        updated = book['updated'][:10]
        updated = datetime.datetime.strptime(updated, '%Y-%m-%d')
        if updated.year == currrent.year:
            statics[updated.month - 1] += 1
        else:
            continue
    for book in reading:
        updated = book['updated'][:10]
        updated = datetime.datetime.strptime(updated, '%Y-%m-%d')
        if updated.year == currrent.year:
            statics[updated.month - 1] += 1
        else:
            continue

    
    return {
        'reading': reading, 
        'readed': readed,
        'wishing': wishing,
        'statics': statics
    }

def merge():
    if os.path.exists('./images'):
        shutil.rmtree('./images')
    else:
        os.mkdir('./images')

    movies = []
    with open('./data/books.json','rt',encoding='utf-8') as fp:
        data = json.load(fp)
        movies.extend(data["wishing"])
        movies.extend(data["reading"])
        movies.extend(data["readed"])
        urls = list(map(lambda x:x['image'], movies))
        for i in range(len(urls)):
            response = requests.get(urls[i])
            with open(f'./images/{i}.jpg','wb') as fw:
                fw.write(response.content)

        images = []
        for file in os.listdir('./images/'):
            images.append(f'./images/{file}')

        composeImages(images, 15, 27, './data/books.jpg')

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        logger.info("a uid of douban.com is required.")
        sys.exit(0)

    uid = sys.argv[1]
    result = crawl(uid)
    with open('./data/books.json', 'wt', encoding='utf-8') as fp:
         json.dump(result, fp)
    logger.info(f"resolve books data for {uid} is done")
    merge()