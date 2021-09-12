import requests
from lxml import etree

def resolve(url, timeout):
    try:
        headers = {
          'Accept': '',
          'User-Agent': 'apifox/1.0.0 (https://www.apifox.cn)'
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
    items = html.xpath('//div[@class="grid-view"]/div[@class="item"]')
    next = html.xpath('string(//span[@class="next"]/a/@href)')
    next = str(next)
    if next.startswith('/'):
        next = f'https://movie.douban.com{next}'

    list = []
    for item in items:
        parser = etree.HTML(etree.tostring(item, pretty_print=True))
        title = parser.xpath('string(//li[@class="title"]/a/em)')
        alt = parser.xpath('string(//li[@class="title"]/a/@href)')
        image = parser.xpath('string(//div[@class="item"]/div[@class="pic"]/a/img/@src)').replace('ipst', 'spst')

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
            title: str(title),
            alt: str(alt),
            image: str(image),
            tags: str(tags),
            date: str(date),
            recommend: str(recommend),
            comment: str(comment),
            info: str(info)
        })
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    # 在看
    watching = []
    url = f'https://movie.douban.com/people/{uid}/do'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        watching.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 看过
    watched = []
    url = f'https://movie.douban.com/people/{uid}/collect'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        watched.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 想看
    wishing = []
    url = f'https://movie.douban.com/people/{uid}/wish'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        wishing.extend(result['list'])
        result = resolve(result['next'], timeout)
    
    return {
        'watching': watching, 
        'watched': watched,
        'wishing': wishing
    }

if __name__ == '__main__':
    uid = '60029335'
    print(crawl(uid))

    