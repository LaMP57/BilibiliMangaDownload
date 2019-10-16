from selenium import webdriver
from PIL import Image
from time import sleep
import os

def get_cookies():
    print('请在稍后打开的浏览器窗口中完成登录')
    fireFoxOptions = webdriver.FirefoxOptions()
    driver = webdriver.Firefox(options=fireFoxOptions)
    driver.get('https://manga.bilibili.com')

    sleep(10)
    actionButton = driver.find_element_by_class_name('action-button')
    while actionButton.text != '历史':
        sleep(5)
        actionButton = driver.find_element_by_class_name('action-button')

    cookies = driver.get_cookies()
    print('登陆成功！')

    driver.quit()
    return cookies

def optimize_webp(mangaTitle, chPath):
    pics = os.listdir('Download/%s/%s' % (mangaTitle, chPath))
    for pic in pics:
        picPath = 'Download/%s/%s/%s' % (mangaTitle, chPath, pic)
        im = Image.open(picPath)
        im.save(picPath[:-4]+'.webp', 'WEBP')
        os.remove(picPath)

def download_manga(mcNum, chNum, isFull, arrowDirection, needLogin):
    print('正在启动...')
    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.headless = True
    browser = webdriver.Firefox(options=fireFoxOptions)

    if needLogin:
        cookies = get_cookies()
        browser.get('https://manga.bilibili.com')
        for cookie in cookies:
            browser.add_cookie(cookie)

    url = 'https://manga.bilibili.com/mc%s/%s' % (mcNum, chNum)
    browser.get(url)
    browser.set_window_size(3840, 1080)
    while browser.title == '漫画全集在线观看 - 哔哩哔哩漫画':
        sleep(1)
    sleep(3)
    chTitle = browser.title
    pageTitle = chTitle
    chPath = pageTitle.split(' - ')[0]
    mangaTitle = browser.title.split(' - ')[1]
    if not(os.path.exists('Download/%s' % mangaTitle)):
        os.mkdir('Download/%s' % mangaTitle)

    i = 1
    print('%s - %s 开始下载...' % (mangaTitle, chPath))
    while pageTitle == chTitle:
        chPath = pageTitle.split(' - ')[0]
        if not(os.path.exists('Download/%s/%s' % (mangaTitle, chPath))):
            os.mkdir('Download/%s/%s' % (mangaTitle, chPath))

        pics = browser.find_elements_by_tag_name('canvas')

        if len(pics) == 3:
            pic1 = pics[0]
            pic1.screenshot('Download/%s/%s/%s.png' % (mangaTitle, chPath, str(i*2)))
            pic2 = pics[1]
            pic2.screenshot('Download/%s/%s/%s.png' % (mangaTitle, chPath, str(i*2-1)))

        if len(pics) == 2:
            pic1 = pics[0]
            pic1.screenshot('Download/%s/%s/%s.png' % (mangaTitle, chPath, str(i*2-1)))

        nextBottom = browser.find_element_by_class_name(arrowDirection)
        nextBottom.click()
        i += 1

        try:
            browser.find_element_by_class_name('toast-content')
        except:
            pass
        else:
            chTitle = 'END'

        while browser.title == '漫画全集在线观看 - 哔哩哔哩漫画':
            sleep(1)
        sleep(3)

        pageTitle = browser.title
        if chTitle != pageTitle:
            print('%s - %s 下载完成！开始压缩...' % (mangaTitle, chPath))
            optimize_webp(mangaTitle, chPath)
            print('压缩完成！')

            if isFull:
                i = 1
                chTitle = pageTitle
                chPath = pageTitle.split(' - ')[0]
                print('%s - %s 开始下载...' % (mangaTitle, chPath))

    browser.quit()

if __name__ == "__main__":
    if not(os.path.exists('Download')):
        os.mkdir('Download')
    print('请输入mc号：(漫画详情页url中mc后的数字)')
    mcNum = input()

    print('1.日漫模式(自右向左翻页)\n2.普通模式(自左向右翻页)')
    arrowDirection = input()
    if arrowDirection == '1':
        arrowDirection = 'arrow-left'
    else:
        arrowDirection = 'arrow-right'

    print('1.下载单章\n2.下载全本')
    isFull = input()
    if isFull == '1':
        isFull = False
        print('请输入要下载的章节号：(章节页url中在mc号后面的一组数字)')
        chNum = input()
    else:
        isFull = True
        print('请输入第一章的章节号：(章节页url中在mc号后面的一组数字)')
        chNum = input()

    print('1.直接下载\n2.需要登录')
    needLogin = input()
    if needLogin == '1':
        needLogin = False
    else:
        needLogin = True
    
    download_manga(mcNum, chNum, isFull, arrowDirection, needLogin)