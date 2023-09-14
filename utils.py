import logging
from PIL import Image
import os
import requests
import json

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

def composeImages(images, rows, columns, output='output.jpg'):
    index = 0
    width = int(columns * 136 * 0.75)
    height = int(rows * 192 * 0.75)
    newImage = Image.new('RGB', (width, height))
    srcImage = None
    for x in range(0, columns):
        for y in range(0, rows):
            try:
                srcImage = Image.open(images[index])
            except Exception as e:
                srcImage = Image.open(images[0])
            srcImage = srcImage.resize((int(136 * 0.75), int(192 * 0.75)), Image.ANTIALIAS)
            x_position = int(x * 136 * 0.75)
            y_position = int(y * 192 * 0.75)
            newImage.paste(srcImage, (x_position, y_position))
            index += 1
            if index >= len(images):
                index = 0
    return newImage.save(output)