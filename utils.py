import logging

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

def createLogger(category):
    logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(category)