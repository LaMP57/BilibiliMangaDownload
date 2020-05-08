import os, sys, getopt, zipfile, json, requests
from io import BytesIO

URL_DETAIL = "https://manga.bilibili.com/twirp/comic.v2.Comic/ComicDetail?device=pc&platform=web"
URL_IMAGE_INDEX = "https://manga.bilibili.com/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web"
URL_MANGA_HOST = "https://manga.hdslb.com"
URL_IMAGE_TOKEN = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"

def downloadImage(url, path):
    r = requests.get(url, stream=True, cookies = cookies)
    f = open(path, 'wb')
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
    f.close()

def getMangaInfo(mcNum):
    data = requests.post(URL_DETAIL, data={'comic_id': mcNum}).json()['data']
    data['ep_list'].reverse()
    return data['title'], data['ep_list']

def getImages(mcNum, chNum):
    data = requests.post(URL_IMAGE_INDEX, data = {'ep_id': chNum}, cookies = cookies).json()['data']
    data = bytearray(requests.get(data['host'] + data['path']).content[9:])
    key = [chNum&0xff, chNum>>8&0xff, chNum>>16&0xff, chNum>>24&0xff, mcNum&0xff, mcNum>>8&0xff, mcNum>>16&0xff, mcNum>>24&0xff]
    for i in range(len(data)):
        data[i]^=key[i%8]
    file = BytesIO(data)
    zf = zipfile.ZipFile(file)
    data = json.loads(zf.read('index.dat'))
    zf.close()
    file.close()
    return data['pics']

def getToken(url):
    data = requests.post(URL_IMAGE_TOKEN, data = {"urls": "[\""+url+"\"]"}, cookies = cookies).json()["data"][0]
    return '%s?token=%s' % (data["url"], data["token"])

def getChName(chList, chNum):
    for i in chList:
        if i['id'] == chNum:
            return i['short_title'] + i['title']
    return None

def downloadCh(mcNum, chNum, chName):
    if not(os.path.exists('Download/%s/%s' % (mangaTitle, chName))):
        os.mkdir('Download/%s/%s' % (mangaTitle, chName))
    print('[INFO]', chName, '开始下载')
    imagesURL = getImages(mcNum, chNum)
    for idx, url in enumerate(imagesURL, 1):
        fullURL = getToken(url)
        path = 'Download/%s/%s/%s.jpg' % (mangaTitle, chName, str(idx))
        downloadImage(fullURL, path)
    print('[INFO]', chName, '下载完成')

if __name__ == "__main__":
    if not(os.path.exists('Download')):
        os.mkdir('Download')

    print('请输入mc号：')
    mcNum = int(input())
    mangaTitle, chList = getMangaInfo(mcNum)
    print('[INFO]', mangaTitle)

    if not(os.path.exists('Download/%s' % mangaTitle)):
        os.mkdir('Download/%s' % mangaTitle)

    print('1.下载单章\n2.下载全本')
    isFull = input()
    if isFull == '1':
        isFull = False
        print('请输入要下载的章节号：')
        chNum = int(input())
    else:
        isFull = True

    print('1.均为免费章节\n2.包含付费章节')
    needCookies = input()
    if needCookies == '1':
        needCookies = False
    else:
        needCookies = True

    cookies = {}
    if needCookies:
        print('请按说明粘贴cookies：')
        cookiesStr = input()
        for line in cookiesStr.split(';'):
            key, value = line.strip().split('=', 1)
            cookies[key] = value

    if isFull:
        for ch in chList:
            chName = ch['short_title'] + ch['title']
            downloadCh(mcNum, ch['id'], chName)
    else:
        chName = getChName(chList, chNum)
        downloadCh(mcNum, chNum, chName)