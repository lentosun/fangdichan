#!/usr/bin/python
# coding:utf-8

# author: Yi Sun (lentosun@163.com)

import sys
import os
import urllib2
import lxml.html.soupparser as soupparser
import datetime
import time
import random
import re
import sqlite3


_FNAME_PREFIX = "c:/tmp/wuhan_xiaoqu_"
_TIME = datetime.datetime.now().strftime('%Y_%m_%d')
_LOG_PATH = _FNAME_PREFIX + _TIME + ".csv"
_SQLITE_DB = "wuhan.db"
_ITEM_PER_PAGE = 30


log_path = _LOG_PATH
index = 0
base_url = "http://wh.lianjia.com/xiaoqu/"
page = "pg"
sort = "cro11"
total_page_number = 100


conn = sqlite3.connect(_SQLITE_DB)


while os.path.exists(log_path):
    log_path = _LOG_PATH + "." + str(index)
    index = index + 1

log = open(log_path, 'a')


dict_xpath = [
    {"name": "url",
     "header": "URL",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//div[@class='info']//div[@class='title']//a/@href"},

    {"name": "title",
     "header": "Name",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//div[@class='info']//div[@class='title']//a/text()"},

    {"name": "district",
     "header": "District",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//a[@class='district']/text()"},

    {"name": "bizcircle",
     "header": "BusinessCircle",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//a[@class='bizcircle']/text()"},

    {"name": "period",
     "header": "Period",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//div[@class='positionInfo']/text()[last()]"},

    {"name": "price",
     "header": "Price",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//div[@class='totalPrice']/span/text()"},

    {"name": "subway",
     "header": "Subway",
     "xpath": "//li[INDEX][@class='clear xiaoquListItem']//div[@class='tagList']//span/text()"}
    ]

tmp_str = ""
for ele in dict_xpath:
    tmp_str += ele['header'] + ","
if tmp_str[-1:] == ",":
    tmp_str = tmp_str[:-1]
log.write("ID," + tmp_str + "\n")

to_number_list = ["period", "price"]


def get_dom_by_url(url):
    page_content = urllib2.urlopen(url).read()
    page_dom = soupparser.fromstring(page_content)
    return page_dom


def get_element_by_xpath(dom, xpath):
    element_list = []
    element_list = dom.xpath(xpath)
    return element_list


def fetch_number(input_str):
    output_str = re.findall(r"\d+\.?\d*", input_str)
    return output_str


def clear_utf8_str(input_str):
    output_str = input_str.encode("utf8").strip().replace(",", "").replace(" ", "")
    return output_str


def prepare_entry(input_list, number=False):
    entry = ""
    if input_list:
        if number:
            input_list = fetch_number(input_list[0])
        if input_list:
            entry = clear_utf8_str(input_list[0]) + ","
        else:
            entry =  ","
    else:
        entry = ","
    return entry

def prepare_sql_entry(entry):
    tmp_list = entry.split(",")
    del tmp_list[0] #删除csv的id，用sql默认的rowid
    ret = ""
    for s in tmp_list:
        ret += "\"" + s + "\"" + ","
    if ret[-1:] == ",":
        ret = ret[:-1]
    return ret

page_urls = []
for i in range(1, total_page_number + 1):
    page_url = base_url + "pg" + str(i) + sort + "/"
    page_urls.append(page_url)

seq = 1

for page_url in page_urls:
    print page_url
    try:
        dom = get_dom_by_url(page_url)
    except Exception, e:
        print "Failed to open URL: %s" % page_url
        continue
    for i in range(1, _ITEM_PER_PAGE + 1):
        entry = str(seq) + ","
        for name_xpath in dict_xpath:
            xpath = name_xpath['xpath'].replace("INDEX", str(i))
            elements = get_element_by_xpath(dom, xpath)
            if name_xpath['name'] in to_number_list:
                entry += prepare_entry(elements, number=True)
            else:
                entry += prepare_entry(elements)
        if entry[-1:] == ",":
            entry = entry[:-1]
        entry += "\n"
        log.write(entry)
        sql_entry = prepare_sql_entry(entry)
        sql = "REPLACE INTO xiaoqu (url, name, district, businesscircle, period, price, subway) VALUES (%s)" % sql_entry
        print sql
        conn.execute(sql)
        conn.commit()
        print entry
        seq += 1
    time.sleep(random.uniform(30, 120))

conn.close()
