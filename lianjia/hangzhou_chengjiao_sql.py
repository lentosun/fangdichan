#!/usr/bin/python
# coding:utf-8

# author: Yi Sun (lentosun@163.com)

import platform
import os
import urllib2
import lxml.html.soupparser as soupparser
import datetime
import time
import random
import re
import sqlite3

_FNAME_PREFIX = "/tmp/hangzhou_chengjiao_"
_TIME = datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S')
_DATE = datetime.datetime.now().strftime('%Y%m%d')
_LOG_PATH = _FNAME_PREFIX + _TIME + ".csv"

os_type = platform.system().lower()
log_path = _LOG_PATH
index = 0
base_url = "http://hz.lianjia.com/chengjiao/"
page = "pg"
sort = ""
total_page_number = 100
_SQLITE_DB = "hangzhou.db"
_ITEM_PER_PAGE = 30
_TABLE_NAME = "deal_%s" % _TIME

if "win" in os_type:
    _FNAME_PREFIX = "c:/tmp/hangzhou_chengjiao_"

while os.path.exists(log_path):
    log_path = _LOG_PATH + "." + str(index)
    index = index + 1

log = open(log_path, 'a')

conn = sqlite3.connect(_SQLITE_DB)
sql_create_table = "CREATE TABLE [%s](\
                  [URL] CHAR PRIMARY KEY ON CONFLICT REPLACE, \
                  [name] CHAR, \
                  [xiaoqu] CHAR, \
                  [huxing] CHAR, \
                  [area] FLOAT, \
                  [dealDate] CHAR, \
                  [info] CHAR, \
                  [totalPrice] FLOAT, \
                  [unitPrice] FLOAT, \
                  [inputDate]);" % _TABLE_NAME
conn.execute(sql_create_table)
conn.commit()

dict_xpath = [
    {"name": "url",
     "header": "URL",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='title']/a/@href"},

    {"name": "title",
     "header": "Name",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='title']/a/text()"},

    {"name": "detail",
     "header": "Xiaoqu,Huxing,Area",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='title']/a/text()"},

    {"name": "deal_date",
     "header": "DealDate",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='dealDate']/text()"},

    {"name": "info",
     "header": "Info",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='houseInfo']/text()"},

    {"name": "total_price",
     "header": "TotalPrice",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='totalPrice']/span/text()"},

    {"name": "unit_price",
     "header": "UnitPrice",
     "xpath": "//ul[@class='listContent']/li[INDEX]//div[@class='unitPrice']/span/text()"}
]


tmp_str = ""
for ele in dict_xpath:
    tmp_str += ele['header'] + ","
log.write("序号," + tmp_str + "input_date\n")

to_number_list = ["total_price", "unit_price", "area"]


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


def devide_details(input, sep="|", to_number_indice=[], del_first=False):
    output_list = []
    input_list = input[0].split(sep)
    if input_list:
        for i in range(len(input_list)):
            tmp_str = ""
            if i in to_number_indice:
                tmp_str = fetch_number(input_list[i])[0]
            else:
                tmp_str = input_list[i]
            tmp_str = clear_utf8_str(tmp_str)
            output_list.append(tmp_str)
    if del_first:
        del output_list[0]
    return output_list


def format_list(input_list, length):
    ret = []
    input_list_len = len(input_list)
    if input_list_len == length:
        ret = input_list
    elif input_list_len < length:
        ret = input_list
        for i in range(length - input_list_len):
            ret.append("")
    else:
        last_ele = ""
        for i in range(length -1):
            ret.append(input_list[i])
        for i in range(length -1 , input_list_len):
            last_ele += input_list[i]
        ret.append(last_ele)
    return ret


def conv_l2s(input_list, sep=","):
    ret = ""
    for tmp_str in input_list:
        ret += tmp_str + ","
    return ret


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
            elif name_xpath['name'] in ['detail']:
                tmp_list = devide_details(elements, " ", [2])
                tmp_list = format_list(tmp_list, 3)
                tmp_str = conv_l2s(tmp_list)
                entry += tmp_str
            else:
                entry += prepare_entry(elements)
        entry += _DATE # 把当前日期作为录入时间写入数据库
        if entry[-1:] == ",":
            entry = entry[:-1]
        entry += "\n"
        log.write(entry)
        sql_entry = prepare_sql_entry(entry)
        sql = "REPLACE INTO %s (URL, name, xiaoqu, huxing, area, dealDate, info, totalPrice, unitPrice, inputDate) VALUES (%s)" % (_TABLE_NAME, sql_entry)
        conn.execute(sql)
        conn.commit()
        print entry
        seq += 1
    time.sleep(random.uniform(30, 120))
conn.close()
