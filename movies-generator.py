import os
import sys
import shutil
import requests
import json
from lxml import etree
from utils import renderStar, createLogger, composeImages
import datetime

logger = createLogger('movies-generator')

def resolve(url, timeout):
    try:
        headers = {
          'Accept': '*/*',
          'Cookie': 'bid=yWp-BWCU5QE; dbcl2="60029335:nfTLxNRvjfM"; push_noty_num=0; push_doumail_num=0; __utma=30149280.877824136.1693788912.1694401825.1694670246.4; __utmz=30149280.1694670246.4.3.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmv=30149280.6002; ck=hb8a; ap_v=0,6.0; __utmb=30149280.5.10.1694670246; __utmc=30149280; __gads=ID=5865881b86059a47-22fb884ccce30022:T=1694670404:RT=1694670766:S=ALNI_Mb7aSCWzR6eswJxcuKNF7ewSVCmyQ; __gpi=UID=00000d929d3ff0c3:T=1694670404:RT=1694670766:S=ALNI_MbauFz6G2dSGCykKKV9QrK9G1VEJg; frodotk_db="f36356891bdfe508da2a039b539faf18"',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
        }

        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return parseContent(response.content)
    except Exception as e:
        logger.error(f'resolve data from {url} fails due to offline', exc_info=True)
        return None

def parseContent(content):
    html = etree.HTML(content)
    items = html.xpath('//div[@class="grid-view"]/div[@class="item comment-item"]')
    next = html.xpath('string(//span[@class="next"]/a/@href)')
    next = str(next)
    if next.startswith('/'):
        next = f'https://movie.douban.com{next}'

    list = []
    for item in items:
        parser = etree.HTML(etree.tostring(item, pretty_print=True))
        title = parser.xpath('string(//li[@class="title"]/a/em)')
        alt = parser.xpath('string(//li[@class="title"]/a/@href)')
        image = parser.xpath('string(//div[@class="item comment-item"]/div[@class="pic"]/a/img/@src)').replace('ipst', 'spst')

        tags = parser.xpath('string(//li/span[@class="tags"])')
        tags = str(tags)[0:3] if str(tags) != None  else ''
        date = parser.xpath('string(//li/span[@class="date"])')
        date = date if date != None else ''

        recommend = parser.xpath('string(//li/span[starts-with(@class,"rating")]/@class)')
        recommend = str(recommend)
        recommend = renderStar(str(recommend)[6]) if len(recommend) >= 6 else renderStar('3')
        comment = parser.xpath('string(//li/span[@class="comment"])')
        comment = comment if comment != None else ''

        info = parser.xpath('string(//li[@class="intro"])')
        info = info if info != None else ''

        # image = 'https://images.weserv.nl/?url=' + image.substr(8, image.length - 8) + '&w=100'

        list.append({
            'title': str(title),
            'alt': str(alt),
            'image': str(image),
            'tags': str(tags),
            'date': str(date),
            'recommend': str(recommend),
            'comment': str(comment),
            'info': str(info)
        })
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    # 在看
    watching = []
    logger.info(f"resolve watching movies for {uid}...")
    url = f'https://movie.douban.com/people/{uid}/do'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        watching.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 看过
    watched = []
    logger.info(f"resolve watched movies for {uid}...")
    url = f'https://movie.douban.com/people/{uid}/collect'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        watched.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 想看
    wishing = []
    logger.info(f"resolve wishing movies for {uid}...")
    url = f'https://movie.douban.com/people/{uid}/wish'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        wishing.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 统计
    statics = [ 0 for i in  range(12)]
    currrent = datetime.datetime.now()
    for movie in watched:
        updated = movie['date']
        updated = datetime.datetime.strptime(updated, '%Y-%m-%d')
        if updated.year == currrent.year:
            statics[updated.month - 1] += 1
        else:
            continue
    for movie in watching:
        updated = movie['date']
        updated = datetime.datetime.strptime(updated, '%Y-%m-%d')
        if updated.year == currrent.year:
            statics[updated.month - 1] += 1
        else:
            continue

    return {
        'watching': watching, 
        'watched': watched,
        'wishing': wishing,
        'statics': statics
    }

def merge():
    if os.path.exists('./images'):
        shutil.rmtree('./images')
    os.mkdir('./images')

    movies = []
    with open('./data/movies.json','rt',encoding='utf-8') as fp:
        data = json.load(fp)
        movies.extend(data["wishing"])
        movies.extend(data["watching"])
        movies.extend(data["watched"])
        urls = list(map(lambda x:x['image'], movies))
        for i in range(len(urls)):
            response = requests.get(urls[i])
            with open(f'./images/{i}.jpg','wb') as fw:
                fw.write(response.content)

        images = []
        for file in os.listdir('./images'):
            images.append(f'./images/{file}')

        composeImages(images, 15, 27,'./data/movies.jpg')

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        logger.info("a uid of douban.com is required.")
        sys.exit(0)

    uid = sys.argv[1]
    result = crawl(uid)
    with open('./data/movies.json', 'wt', encoding='utf-8') as fp:
         json.dump(result, fp)
    logger.info(f"resolve movies data for {uid} is done")

    merge()

    