import json
import os
import re
import requests
import zipfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

URL_DETAIL = "https://manga.bilibili.com/twirp/comic.v2.Comic/ComicDetail?device=pc&platform=web"
URL_IMAGE_INDEX = "https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web"
URL_MANGA_HOST = "https://manga.hdslb.com"
URL_IMAGE_TOKEN = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"

def downloadImage(url, path, retry = 0):
    r = requests.get(url, stream = True, cookies = cookies)
    if r.content.endswith(b'\xff\xd9') or retry > 9:
        f = open(path, 'wb')
        for chunk in r.iter_content(chunk_size = 1024):
            if chunk:
                f.write(chunk)
        f.close()
    else:
        downloadImage(url, path, retry + 1)

def getMangaInfo(mcNum):
    data = requests.post(URL_DETAIL, data = {'comic_id': mcNum}).json()['data']
    data['ep_list'].reverse()
    return filterStr(data['title']), data['ep_list']

def getImages(mcNum, chNum):
    data = requests.post(URL_IMAGE_INDEX, data = {'ep_id': chNum}, cookies = cookies).json()['data']
    data = bytearray(requests.get(data['host'] + data['path']).content[9:])
    key = [chNum&0xff, chNum>>8&0xff, chNum>>16&0xff, chNum>>24&0xff, mcNum&0xff, mcNum>>8&0xff, mcNum>>16&0xff, mcNum>>24&0xff]
    for i in range(len(data)):
        data[i] ^= key[i%8]
    file = BytesIO(data)
    zf = zipfile.ZipFile(file)
    data = json.loads(zf.read('index.dat'))
    zf.close()
    file.close()
    return data['pics']

def getURLwithToken(url):
    data = requests.post(URL_IMAGE_TOKEN, data = {"urls": "[\""+url+"\"]"}, cookies = cookies).json()["data"][0]
    return '%s?token=%s' % (data["url"], data["token"])

def getChapterName(chapterList, chapterID):
    for chapte in chapterList:
        if chapte['id'] == chapterID:
            return filterStr(chapte['short_title'] + ' ' + chapte['title'])
    return None

def downloadChapter(mcNum, chapterID, chapterName):
    if not(os.path.exists('downloads/%s/%s' % (mangaTitle, chapterName))):
        os.mkdir('downloads/%s/%s' % (mangaTitle, chapterName))
    print('[INFO]%s开始下载' % chapterName)
    try:
        imagesURLs = getImages(mcNum, chapterID)
        imagesIndexLength = len(str(len(imagesURLs)))
        tasks = list()
        for idx, url in enumerate(imagesURLs, 1):
            fullURL = getURLwithToken(url)
            path = 'downloads/%s/%s/%s.jpg' % (mangaTitle, chapterName, str(idx).zfill(imagesIndexLength))
            tasks.append(pool.submit(downloadImage, fullURL, path))
        wait(tasks, return_when = ALL_COMPLETED)
        print('[INFO]%s下载完成' % chapterName)
    except:
        print('[ERROR]%s下载失败' % chapterName)

def filterStr(name):
    return re.sub(r'[\\\/:*?"<>|]', '', name).strip().rstrip('.')

if __name__ == "__main__":
    pool = ThreadPoolExecutor(max_workers=4)
    if not(os.path.exists('downloads')):
        os.mkdir('downloads')

    print('请输入mc号：')
    print('mc', end='')
    mcNum = int(input())
    mangaTitle, chapterList = getMangaInfo(mcNum)
    print('[INFO]', mangaTitle)

    if not(os.path.exists('downloads/%s' % mangaTitle)):
        os.mkdir('downloads/%s' % mangaTitle)

    print('1.下载单章\n2.下载全本')
    downloadAll = input()
    if downloadAll == '1':
        downloadAll = False
        print('请输入要下载的章节号：')
        chapterID = int(input())
    else:
        downloadAll = True

    print('1.均为免费章节\n2.包含付费章节')
    needsLogin = input()
    cookies = dict()
    if needsLogin == '2':
        print('请按说明粘贴SESSDATA：')
        cookies['SESSDATA'] = input().strip()

    if downloadAll:
        for chapter in chapterList:
            chapterName = filterStr(chapter['short_title'] + ' ' + chapter['title'])
            downloadChapter(mcNum, chapter['id'], chapterName)
    else:
        chapterName = getChapterName(chapterList, chapterID)
        downloadChapter(mcNum, chapterID, chapterName)
