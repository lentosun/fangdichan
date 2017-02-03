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


_FNAME_PREFIX = "/tmp/hangzhou_xiaoqu_"
_TIME = datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S')
_DATE = datetime.datetime.now().strftime('%Y%m%d')
_LOG_PATH = _FNAME_PREFIX + _TIME + ".csv"
_SQLITE_DB = "hangzhou.db"
_ITEM_PER_PAGE = 30
_TABLE_NAME = "xiaoqu_%s" % _TIME

os_type = platform.system().lower()
log_path = _LOG_PATH
index = 0
base_url = "http://hz.lianjia.com/xiaoqu/"
#sort = "cro11"
#total_page_number = 100
if "win" in os_type:
    _FNAME_PREFIX = "c:/tmp/hangzhou_xiaoqu_"


conn = sqlite3.connect(_SQLITE_DB)
sql_create_table = "CREATE TABLE [%s](\
                  [url] CHAR PRIMARY KEY ON CONFLICT REPLACE UNIQUE ON CONFLICT REPLACE,\
                  [name] CHAR, \
                  [district] CHAR,\
                  [businesscircle] CHAR,\
                  [period] INTEGER, \
                  [price] FLOAT, \
                  [insale] INTEGER, \
                  [subway] CHAR, \
                  [salein90] INTEGER, \
                  [inputdate] CHAR);" % _TABLE_NAME
conn.execute(sql_create_table)
conn.commit()


while os.path.exists(log_path):
    log_path = _LOG_PATH + "." + str(index)
    index = index + 1

log = open(log_path, 'a')

# 区县列表，遍历所有区县的小区，这样更完整
district_list = ["xihu", "xiacheng", "jianggan", "gongshu", "shangcheng", "binjiang", "yuhang", "xiaoshan"]


total_item_xpath = "//div[@class='content']//h2[@class='total fl']/span/text()"

dict_xpath = [
    {"name": "url",
     "header": "URL",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='info']//div[@class='title']//a/@href"},

    {"name": "title",
     "header": "Name",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='info']//div[@class='title']//a/text()"},

    {"name": "district",
     "header": "District",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//a[@class='district']/text()"},

    {"name": "bizcircle",
     "header": "BusinessCircle",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//a[@class='bizcircle']/text()"},

    {"name": "period",
     "header": "Period",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='positionInfo']/text()[last()]"},

    {"name": "price",
     "header": "Price",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='totalPrice']/span/text()"},

    {"name": "insale",
     "header": "Insale",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='xiaoquListItemSellCount']//span/text()"},

    {"name": "subway",
     "header": "Subway",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='tagList']//span/text()"},

    {"name": "salein90",
     "header": "SaleIn90",
     "xpath": "//li[@class='clear xiaoquListItem'][INDEX]//div[@class='houseInfo']/a[1]/text()"}
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


def fetch_number(input_str, index=0):
    output_list = []
    tmp_list = re.findall(r"\d+\.?\d*", input_str)
    if index < len(tmp_list):
        output_list.append(tmp_list[index])
    return output_list


def clear_utf8_str(input_str):
    output_str = input_str.encode("utf8").strip().replace(",", "").replace(" ", "")
    return output_str


def prepare_entry(input_list, number=False, index=0):
    entry = ""
    if input_list:
        if number:
            input_list = fetch_number(input_list[0], index)
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

seq = 1

for district in district_list:
    main_url = base_url + district + "/"
    try:
        dom = get_dom_by_url(main_url)
    except Exception, e:
        print "Failed to open URL: %s" % main_url
        continue
    total_item_number = int(get_element_by_xpath(dom, total_item_xpath)[0])
    total_page_number = (total_item_number+_ITEM_PER_PAGE-1)//_ITEM_PER_PAGE
    print total_page_number
    for i in range(1, total_page_number + 1):
        page_url = main_url + "pg" + str(i) + "/"
        print page_url
        try:
            dom = get_dom_by_url(page_url)
        except Exception, e:
            print "Failed to open URL: %s" % page_url
            continue
        item_number = 0
        if total_item_number/i < _ITEM_PER_PAGE:
            item_number = total_item_number-(_ITEM_PER_PAGE*(i-1))
        else:
            item_number = _ITEM_PER_PAGE
        for i in range(1, item_number + 1):
            entry = str(seq) + ","
            for name_xpath in dict_xpath:
                xpath = name_xpath['xpath'].replace("INDEX", str(i))
                elements = get_element_by_xpath(dom, xpath)
                if name_xpath['name'] in to_number_list:
                    entry += prepare_entry(elements, number=True)
                elif name_xpath['name'] in ['salein90']:
                    entry += prepare_entry(elements, number=True, index=1)
                else:
                    entry += prepare_entry(elements)
            entry += _DATE
            if entry[-1:] == ",":
                entry = entry[:-1]
            entry += "\n"
            log.write(entry)
            sql_entry = prepare_sql_entry(entry)
            sql = "REPLACE INTO %s (url, name, district, businesscircle, period, price, insale, subway, salein90, inputdate) VALUES (%s)" % (_TABLE_NAME, sql_entry)
            conn.execute(sql)
            conn.commit()
            print entry
            seq += 1
        time.sleep(random.uniform(30, 120))
conn.close()
