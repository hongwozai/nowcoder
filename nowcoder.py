#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import bs4
import sys
import time
import json
import urllib
import cPickle
import urllib2
import argparse
import cookielib

reload(sys)

sys.setdefaultencoding('utf-8')


nowcoderUrl = "https://www.nowcoder.com"
userAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"

nowcoderLang = {"c": 2,
                "java": 4,
                "python": 5}


def initCookie():

    cj = cookielib.CookieJar()
    opener = urllib2.build_opener()
    opener.add_handler(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    return


def getProblems(bs, urllist):
    # 题目链接
    all_tr = bs.find(class_="offer-body")
    if all_tr is None:
        return

    all_tr = all_tr.find_all("tr")
    for tr in all_tr:
        # 存储名字和链接
        a = tr.find("a")
        try:
            if a.string is not None:
                urllist.append((unicode(a.string), a["href"]))
                # print a.string, a["href"]
        except IndexError as e:
            print e
            pass
    return


def getCourse(path):
    "获取专题下面的所有题目"

    urllist = []

    s = urllib.urlencode([("query", ""),
                          ("asc", "true"),
                          ("order", ""),
                          ("page", 1)])
    req = urllib2.Request("%s/ta/%s?%s" % (nowcoderUrl, path, s),
                          headers={"User-Agent": userAgent})
    print req.get_full_url()
    res = urllib2.urlopen(req)

    print "[*] first request"
    bs = bs4.BeautifulSoup(res.read())
    # print bs
    if u"页面不存在" in bs.title.string:
        return

    ul = bs.find(lambda x: x.name == "ul" and x.has_attr("data-total"))
    if ul is None:
        return

    getProblems(bs, urllist)

    # 总共有几页
    for i in range(2, int(ul["data-total"]) + 1):
        print "[*] %d request" % i
        # 获取到所有的连接
        s = urllib.urlencode([("query", ""),
                              ("asc", "true"),
                              ("order", ""),
                              ("page", i)])
        req = urllib2.Request("%s/ta/%s?%s" % (nowcoderUrl, path, s),
                              headers={"User-Agent": userAgent})

        # print req.get_full_url()
        res = urllib2.urlopen(req)
        getProblems(bs4.BeautifulSoup(res.read()), urllist)
    return urllist


def writeDump(name, urllist):
    with open(name, "w") as f:
        cPickle.dump(urllist, f)
    return


class SwordOffer(object):

    def __init__(self, name):
        if name is not None:
            with open(name, "r") as f:
                self.urllist = cPickle.load(f)
            # 当前正在运行的编程题（拉过来的）
            self.tpId = 0
        return

    def show(self):
        i = 0
        for name, url in self.urllist:
            print "%d: %s" % (i, name.strip())
            i += 1
        return

    def getContent(self, order, lang):
        "获得题目内容，示例，提交的url,获得结果的url"
        if (len(self.urllist) < order) or (order < 1):
            return (None, None, None)
        name, url = self.urllist[order - 1]
        req = urllib2.Request("%s%s" % (nowcoderUrl, url),
                              headers={"User-Agent": userAgent})
        # print "[+] request %d's content, example" % order
        # print req.get_full_url()
        res = urllib2.urlopen(req)
        bs = bs4.BeautifulSoup(res.read(), "html5lib")

        # 获取题目内容
        content = ""
        for i in bs.find(class_="subject-describe").strings:
            content += i
        # content = bs.find(class_="subject-describe").contents[1].string
        # 获取示例代码
        example = bs.find("textarea", id="{}Tpl".format(lang)).string
        # 获取试题代号
        tpId = 0
        m = re.compile(r"questionId: '([0-9]+)'").search(str(bs))
        if m is not None:
            tpId = m.group(1)
        self.tpId = tpId
        return (content, example, tpId)

    def postContentAndResult(self, content, tpId=None, lang=2):
        # 提交的id
        submissionId = 0
        if tpId is None:
            tpId = self.tpId

        s = urllib.urlencode([("questionId", tpId),
                              ("content", content),
                              ("language", lang)])
        req = urllib2.Request("%s/submit_cd?stoken=" % (nowcoderUrl),
                              headers={"User-Agent": userAgent},
                              data=s)
        print "[+] post %d content and get result" % int(tpId)

        # print req.get_full_url()
        res = urllib2.urlopen(req).read()
        j = json.loads(res)
        if j["code"] != 0:
            print "[-] %s" % j["msg"]
            return
        print "[+] submitid: %d: %s" % (j["submissionId"], j["msg"])
        submissionId = j["submissionId"]

        # 用sumbissionId获取代码
        while True:
            print "[-] tpId: %s, submissionId: %s submit!" % (
                tpId, submissionId
            )
            s = urllib.urlencode([("token", ""),
                                  ("submissionId", submissionId)])
            res = urllib2.urlopen("%s/status?%s" % (nowcoderUrl, s)).read()
            j = json.loads(res)
            if j["status"] != 0:
                print "[*] result:\n %s\n[*] error:\n%s" % (
                    j["desc"],
                    urllib.unquote(j["memo"]).replace('<br/>', '\n')
                )
                break
            time.sleep(1)
        return


if __name__ == '__main__':
    initCookie()
    so = None

    p = argparse.ArgumentParser()
    p.add_argument("-v", "--version", help="version message")
    p.add_argument("-c", "--course", help="get course", type=str)
    p.add_argument("-i", "--input", help="input dump file name")
    p.add_argument("-g", "--get",  help="get problem", type=int)
    p.add_argument("-p", "--put",  help="put file to test", type=str)
    p.add_argument("-pi", "--putid",  help="put id", type=int)
    p.add_argument("-l", "--language",  help="use language", type=str,
                   default="c", choices=["c", "java", "python"])
    arg = p.parse_args()

    if len(sys.argv) == 1:
        p.print_help()
        sys.exit(-1)

    if arg.course is not None:
        urllist = getCourse(arg.course)
        writeDump(arg.course, urllist)
        so = SwordOffer(arg.course)
        so.show()
        sys.exit(0)

    # 加载
    if arg.input is not None and arg.put is None:
        so = SwordOffer(arg.input)
        if arg.get is None:
            so.show()

    # 获取题目
    if arg.get is not None:
        if arg.input is None:
            print "Usage: -i <file> -g <number>"
            sys.exit(-1)
        content, example, tpId = so.getContent(arg.get, arg.language)
        if content is None:
            sys.stderr.write("[-] content fetch error!\n")
            sys.exit(-1)

        print u"[-]tpId: %s" % tpId
        print u"[-]content: \n%s" % content.decode()
        print "==========="
        print example

    # 上传代码拉取测试用例
    if arg.put is not None and arg.putid is not None:
        so = SwordOffer(arg.input)
        with open(arg.put, "r") as f:
            so.postContentAndResult(f.read(), arg.putid, nowcoderLang[arg.language])
        print
