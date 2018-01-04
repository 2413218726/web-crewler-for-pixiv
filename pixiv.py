# -*- coding: utf-8 -*-
__author__ = 'f1sh'

import requests
import re
import os
import threading
import argparse

s = requests.session()
proxies = {
    "http": "http://127.0.0.1:1080",
    "https": "http://127.0.0.1:1080"
}
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
}

#登录P站
def login(email, password):
    r = s.get("https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index", proxies = proxies)
    pattern = re.compile('<input type="hidden" name="post_key" value="(.*?)">', re.S)
    post_key = re.search(pattern, r.content).group(1)
    data = {
        "pixiv_id": email,
        "password": password,
        "captcha": "",
        "g_recaptcha_response": "",
        "post_key": post_key,
        "source": "pc",
        "ref": "wwwtop_accounts_index",
        "return_to": "https://www.pixiv.net/"
    }
    s.post("https://accounts.pixiv.net/api/login?lang=zh", data = data, headers = header, proxies = proxies)

#获取图片pid
def getPids():
    url = 'https://www.pixiv.net/ranking_area.php?type=detail&no=6'
    page = s.get(url, headers = header, proxies = proxies).content
    pattern = re.compile('<a href="member_illust\.php\?mode=medium&amp;illust_id=(.*?)">', re.S)
    pids = re.findall(pattern, page)
    return pids

#爬取图片
def getImg(pid):
    try:
        mediumUrl = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=" + pid
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Referer": mediumUrl
        }
        r = s.get(mediumUrl, headers = header, proxies = proxies)
        pattern = re.compile('<img src="https://i.pximg.net/c/600x600/img-master/(.*?)_master1200.jpg" ', re.S)
        imgPath = re.search(pattern, r.content).group(1)
        pattern = re.compile('<span>(\d*)</span>', re.S)
        mangaCount = re.search(pattern, r.content)
        imgUrl = "https://i.pximg.net/img-original/" + imgPath + ".jpg"
        r = s.get(imgUrl, headers = header, proxies = proxies)
        filename = 'pixiv/' + pid + ".jpg"
        if r.status_code == 404:
            imgUrl = "https://i.pximg.net/img-original/" + imgPath + ".png"
            r = s.get(imgUrl, headers = header, proxies = proxies)
            filename = 'pixiv/' + pid + ".png"
        if r.status_code == 404:
            imgUrl = "https://i.pximg.net/img-original/" + imgPath + ".gif"
            r = s.get(imgUrl, headers = header, proxies = proxies)
            filename = 'pixiv/' + pid + ".gif"
        if r.status_code == 502:
            raise Exception("HTTP 502")
        data = r.content
        f = open(filename, 'wb')
        f.write(data)
        f.close()
        if mangaCount:
            mangaCount = int(mangaCount.group(1))
            i = 1
            while i < mangaCount:
                imgUrl = "https://i.pximg.net/img-original/" + imgPath[0:-1] + str(i) + ".jpg"
                r = s.get(imgUrl, headers = header, proxies = proxies)
                filename = 'pixiv/' + pid + '_p' + str(i) + ".jpg"
                if r.status_code == 404:
                    imgUrl = "https://i.pximg.net/img-original/" + imgPath[0:-1] + str(i) + ".png"
                    r = s.get(imgUrl, headers = header, proxies = proxies)
                    filename = 'pixiv/' + pid + '_p' + str(i) + ".png"
                if r.status_code == 404:
                    imgUrl = "https://i.pximg.net/img-original/" + imgPath[0:-1] + str(i) + ".gif"
                    r = s.get(imgUrl, headers = header, proxies = proxies)
                    filename = 'pixiv/' + pid + '_p' + str(i) + ".gif"
                if r.status_code == 502:
                    raise Exception("HTTP 502")
                data = r.content
                f = open(filename, 'wb')
                f.write(data)
                f.close()
                i += 1
    except:
        pass

#创建目录
def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
    else:
        return False

#主函数
def main():
    ts = []
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--email", type = str)
    parser.add_argument("-p", "--password", type = str)
    parser.add_argument("-i", "--id", type = str ,nargs = "?", default = "")
    arg = parser.parse_args()
    login(arg.email, arg.password)
    mkdir('pixiv')
    if arg.id != "":
        getImg(arg.id)
    else:
        pids = getPids()
        for pid in pids:
            t = threading.Thread(target = getImg, args = (pid, ))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

if __name__ == '__main__':
    main()