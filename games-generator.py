import os, sys
import shutil
import requests
import json
import requests
from lxml import etree
from utils import renderStar, createLogger, composeImages

logger = createLogger('books-generator')

def resolve(url, timeout):
    try:
        headers = {
          'Accept': '',
          'User-Agent': 'apifox/1.0.0 (https://www.apifox.cn)'
        }

        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return parseContent(url, response.content)
    except Exception as e:
        logger.error(f'resolve data from {url} fails due to offline', exc_info=True)
        return None

def parseContent(url, content):
    html = etree.HTML(content)
    items = html.xpath('//div[@class="game-list"]/div[@class="common-item"]')
    next = html.xpath('string(//span[@class="next"]/a/@href)')
    next = str(next)
    if next.startswith('?'):
        next = f'https://movie.douban.com{next}'
        next = url[0:url.rindex('?')] + next

    list = []
    for item in items:
        parser = etree.HTML(etree.tostring(item, pretty_print=True))
        title = parser.xpath('string(//div[@class="title"]/a)')
        alt = parser.xpath('string(//div[@class="title"]/a/@href)')
        image = parser.xpath('string(//div[@class="pic"]/a/img/@src)')

        tags = parser.xpath('string(//div[@class="rating-info"]/span[@class="tags"])')
        tags = str(tags)
        tags = tags[3] if  tags  != '' and len(tags) > 3 else ''
        date = parser.xpath('string(//div[@class="rating-info"]/span[@class="date"])')
        date = date if date != None else ''

        recommend = parser.xpath('string(//div[@class="rating-info"]/span[contains(@class,"allstar")]/@class)')
        recommend = str(recommend)
        recommend = renderStar(recommend[19]) if recommend != '' and len(recommend) > 19 else ''

        comment = parser.xpath('string(//div[@class="content"]/div[not(@class)])')
        comment = comment if comment != None else ''

        info = parser.xpath('string(//div[@class="desc"]/text())')
        info =  info if info != None else  ''
        # info = info.replace(/(^\s*)|(\s*$)/g, '');
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
        });
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    # 在玩
    playing = []
    logger.info(f"resolve playing games for {uid}...")
    url = f'https://www.douban.com/people/{uid}/games?action=do'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        playing.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 玩过
    played = []
    logger.info(f"resolve played games for {uid}...")
    url = f'https://www.douban.com/people/{uid}/games?action=collect'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        played.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 想玩
    wishing = []
    logger.info(f"resolve wishing games for {uid}...")
    url = f'https://www.douban.com/people/{uid}/games?action=wish'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        wishing.extend(result['list'])
        result = resolve(result['next'], timeout)
    
    return {
        'playing': playing, 
        'played': played,
        'wishing': wishing
    }

def merge():
    if os.path.exists('./images'):
        shutil.rmtree('./images')
    os.mkdir('./images')

    movies = []
    with open('./data/games.json','rt',encoding='utf-8') as fp:
        data = json.load(fp)
        movies.extend(data["wishing"])
        movies.extend(data["playing"])
        movies.extend(data["played"])
        urls = list(map(lambda x:x['image'], movies))
        for i in range(len(urls)):
            response = requests.get(urls[i])
            with open(f'./images/{i}.jpg','wb') as fw:
                fw.write(response.content)

        images = []
        for file in os.listdir('./images'):
            images.append(f'./images/{file}')

        composeImages(images, 15, 27,'./data/games.jpg')
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        logger.info("a uid of douban.com is required.")
        sys.exit(0)

    # uid = sys.argv[1]
    # result = crawl(uid)
    # with open('./data/games.json', 'wt', encoding='utf-8') as fp:
    #      json.dump(result, fp)
    # logger.info(f"resolve games data for {uid} is done")
    merge()
    