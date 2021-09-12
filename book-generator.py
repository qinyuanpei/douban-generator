import requests
from lxml import etree

def resolve(url, timeout):
    try:
        headers = {
          'Accept': '',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
        }

        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return parseContent(response.content)
    except Exception as e:
        print(e)
        return None

def renderStar(num):
    if num == '1':
        return '★☆☆☆☆ 很差';
    elif num == '2':
        return '★★☆☆☆ 较差';
    elif num == '3':
        return '★★★☆☆ 还行';
    elif num == '4':
        return '★★★★☆ 推荐';
    elif num == '5':
        return '★★★★★ 力荐';
    else:
       return ''

def parseContent(content):
    html = etree.HTML(content)
    items = html.xpath('//ul[@class="interest-list"]/li[@class="subject-item"]')
    next = html.xpath('string(//span[@class="next"]/a/@href)')
    next = str(next)
    if next.startswith('/'):
        next = f'https://book.douban.com{next}'

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
            title: str(title),
            alt: str(alt),
            image: str(image),
            pub: str(pub),
            updated: str(updated),
            tags: str(tags),
            recommend: str(recommend),
            comment: str(comment)
        })
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    # 在读
    reading = []
    url = f'https://book.douban.com/people/{uid}/do'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        reading.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 读过
    readed = []
    url = f'https://book.douban.com/people/{uid}/collect'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        readed.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 想读
    wishing = []
    url = f'https://book.douban.com/people/{uid}/wish'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        wishing.extend(result['list'])
        result = resolve(result['next'], timeout)
    
    return {
        'reading': reading, 
        'readed': readed,
        'wishing': wishing
    }

if __name__ == '__main__':
    uid = '60029335'
    print(crawl(uid))

    