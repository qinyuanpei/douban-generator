from os import replace
import re
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
        return parseContent(url, response.content)
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
            title: str(title),
            alt: str(alt),
            image: str(image),
            tags: str(tags),
            date: str(date),
            recommend: str(recommend),
            comment: str(comment),
            info: str(info)
        });
    

    return {
        'list': list,
        'next': next
    }

def crawl(uid, timeout=180):
    # 在看
    playing = []
    url = f'https://www.douban.com/people/{uid}/games?action=do'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        playing.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 看过
    played = []
    url = f'https://www.douban.com/people/{uid}/games?action=collect'
    result = resolve(url, timeout)
    while result != None and result['next'] != '':
        played.extend(result['list'])
        result = resolve(result['next'], timeout)

    # 想看
    wishing = []
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

if __name__ == '__main__':
    uid = '60029335'
    print(crawl(uid))

    