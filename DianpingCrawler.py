import os
import random
import re
import time
import requests
from lxml import etree
import math
from selenium import webdriver
# webdriver下载地址:

class Crawler():
    def __init__(self,data_fold,info_url):
        self.data_fold = data_fold
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'Referer': 'http://www.dianping.com/beijing/ch50/g183',
            'Cookie':''
        }

        self.info_url = info_url
        self.store_id = self.info_url.split('/')[-1]
        self.fold_path = self.data_fold+'/'+self.store_id
        if not os.path.exists(self.fold_path):
            os.makedirs(self.fold_path)

    def get_pages_1(self,url):
        # 第一种获取页面内容方法--response
        response = requests.get(url = url,headers=self.headers).text
        return response


    def get_pages_2(self):
        '''
        获取店铺评论总数量（两种页面格式，对应两种方法）
        '''
        # 第二种获取页面内容方法--直接下载页面
        driver = webdriver.Chrome('/Users/bu/PycharmProject/MT比赛/DianpingCrawler/chromedriver')
        driver.get(self.info_url)
        time.sleep(30)
        # 暂停30s，在这个时间进行登陆操作

        url = self.info_url+'/review_more/p%s'
        # 获取店铺ID
        # 第一种解析页面方法
        try:
            # 美食店面格式
            driver.get(self.info_url)
            time.sleep(random.randint(5,10))
            response = driver.page_source
            tree = etree.HTML(response)
            assess_number = tree.xpath('//*[@id="defaultcomment-wrapper"]/a/span/text()')[0][1:-1]
        except:
            # 医美店面格式
            self.get_pages_1(url=self.info_url)
            tree = etree.HTML(response)
            d = {}
            d['index'] = self.info_url.split('/')[-1]
            d['name'] = tree.xpath('//*[@id="basic-info"]/h1/text()')[0].replace(' ','').replace('\n','')
            d['locality_region'] = tree.xpath('//*[@id="basic-info"]/div[2]/a/span/text()')[0]
            d['street_address'] = tree.xpath('//*[@id="basic-info"]/div[2]/span[2]/@title')[0]
            try:
                assess_number = tree.xpath('//*[@id="comment"]/h2/a/span/text()')[0][1:-1]
            except:
                assess_number =0
        pages = math.ceil(int(assess_number)/15)
        # 获取评论页数
        if pages==0:
            driver.close()
            return 0
        for page in range(1,pages+1):
            driver.get(url%str(page))
            time.sleep(random.randint(5,10))
            time.sleep(2)
            # 这里把渲染后的网页保存为文件，就不用进行多次爬虫
            html_page = driver.page_source
            with open(self.fold_path+'/page%s.html'%str(page),'w',encoding='utf-8') as f:
                f.write(html_page)
        driver.close()
        return 1

    def get_dictionary(self):
        with open(self.fold_path+'/page1.html','r') as f:
            html_page = f.read()
        # 第二种解析页面方法
        css_url = re.findall('<link rel="stylesheet" type="text/css" href="(//s3plus.meituan.*?)">', html_page)
        css_url = 'http:{}'.format(css_url[0])
        css_content = requests.get(css_url).text
        with open(self.fold_path+'/css.css', 'w', encoding='utf-8') as f:  # 保存css文件
            f.write(css_content)

        # 从中得到字体
        font = re.findall('background-image: url\((.*?)\);', css_content, re.S)  # 提取链接
        maxnum = 0

        for i in font:
            font_url = 'http:{}'.format(i)
            temp_font_content = requests.get(font_url).text
            if len(temp_font_content) > maxnum:
                font_content = temp_font_content
                maxnum = len(font_content)
        with open(self.fold_path+'/font.svg', 'w', encoding='utf-8') as f:  # 保存文件
            f.write(font_content)
        return

    def get_reply(self,html_page,font_content,css_content):
        # 变长
        y_dic = re.findall('<path id=("(\d+)") d="M0 (\d+) H600"/>',font_content)
        y_dic = [(int(idx),int(y)) for non,idx,y in y_dic]
        strategy =1
        if len(y_dic)==0:
            y_dic_2 = re.findall('<text x="0" y="(\d+)">.*?</text>',font_content)
            y_dic_2 = [int(y) for y in y_dic_2]
            strategy = 2
        inf = re.findall('<div class="review-words Hide">(.*?)<div class="less-words">', html_page, re.S)
        inf = inf + re.findall('<div class="review-words">(.*?)</div>',html_page, re.S)

        replylist=[]
        for record in inf:
            inf_copy = record
            svgmti = re.findall('<svgmtsi class="(.*?)">', record)
        # 对于每一个标签
            for class_name in svgmti:
                XY = re.findall('.%s{background:-(.*?)px -(.*?)px;}' % class_name, css_content, re.S)
                #获得坐标
                X = int(float(XY[0][0]) / 14)
                # X的转换两种策略都相同
                if strategy ==1:
                    for i in y_dic:
                        # print(XY[0][1])
                        # print(i)
                        if i[1]> int(float(XY[0][1])):
                            Y = i[0]
                            break
                    fo = re.findall('<textPath xlink:href="#%s" textLength=".*?">(.*?)</textPath>'%str(Y), font_content)
                    # print(fo)
                    inf_copy = re.sub(f'<svgmtsi class="{class_name}"></svgmtsi>', fo[0][X], inf_copy, count=0)
                    # 每得到一个字就把标签换掉
                else:
                    Y = int(float(XY[0][1]))
                    for i in y_dic_2:
                        if i>int(float(Y)):
                            Y=i
                            break
                    fo = re.findall('<text x="0" y="%s">(.*?)</text>'%str(Y), font_content)
                    inf_copy = re.sub(f'<svgmtsi class="{class_name}"></svgmtsi>', fo[0][X], inf_copy, count=0)

            # 删除干扰字符
            inf_copy = re.sub('<img .*? alt="">', '', inf_copy, count=0)
            inf_copy = re.sub('</div>.*?<div class="review-words', '', inf_copy, count=0, flags=re.S)
            inf_copy = inf_copy.replace('Hide">', '')
            inf_copy = inf_copy.replace('">', '')
            inf_copy = inf_copy.replace('\n', '')
            inf_copy = inf_copy.strip()
            replylist.append(inf_copy)
        return replylist


    def run(self):
        flag = self.get_pages_2()
        if flag == 1:
            self.get_dictionary()
            with open(self.fold_path+'/font.svg','r') as f:
                font_content = f.read()
            with open(self.fold_path + '/css.css','r') as f:
                css_content = f.read()
            htmllist = os.listdir(self.fold_path)
            replylist = []
            for html in htmllist:
                if 'page' in html:
                    with open(self.fold_path+'/'+html,'r') as f:
                        html_page = f.read()
                replylist = replylist + self.get_reply(html_page,font_content,css_content)
            return replylist
        else:
            return '无评论'

if __name__ == '__main__':
    c = Crawler('Datafold','http://www.dianping.com/shop/k67wZzWBOaEDUtTZ')
    reply_list = c.run()
