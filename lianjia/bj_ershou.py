#!/usr/bin/python
#coding:utf-8

# author: Yi Sun (lentosun@163.com)

import sys
import os
import urllib2
import lxml.html.soupparser as soupparser
import datetime
import time
import random
import re


_FNAME_PREFIX = "/tmp/beijing_ershou_"
_TIME = datetime.datetime.now().strftime('%Y_%m_%d') 
_LOG_PATH = _FNAME_PREFIX + _TIME + ".cvs"

log_path = _LOG_PATH
index = 0
base_url = "http://bj.lianjia.com/ershoufang/"
page = "pg"
sort = "co32"
total_page_number = 100
#total_page_number = 10


def get_dom_by_url(url):
    page_content = urllib2.urlopen(url).read()
    page_dom = soupparser.fromstring(page_content)
    return page_dom


def get_element_by_xpath(dom, xpath):
    element_list = []
    element_list = dom.xpath(xpath)
    return element_list


def fetch_number(input_str):
    output_str = re.findall(r"\d+\.?\d*",input_str)
    return output_str


def clear_utf8_str(input_str):
    output_str = input_str.encode("utf8").strip().replace(",", "").replace(" ","")
    return output_str


def prepare_entry(input_list, number=False):
    entry = ""
    if input_list:
        if number:
            input_list = fetch_number(input_list[0])
        entry = clear_utf8_str(input_list[0]) + ","
    else:
        entry = ","
    return entry

while os.path.exists(log_path):
    log_path = _LOG_PATH + "." + str(index)
    index = index + 1

log = open(log_path, 'a')

xpath_room_link = "//div[@class='info clear']//div[@class='title']/a/@href"

dict_xpath = [
        {"name": "title",
         "header": "名称",
         "xpath": "//div[@class='sellDetailHeader']//h1/text()"},

        {"name": "trans_time",
         "header": "挂牌时间",
         "xpath": "//div[@class='transaction']/div[@class='content']//li[1]/text()"},

        {"name": "xiaoqu",
         "header": "小区",
         "xpath": "//div[@class='aroundInfo']//div[@class='communityName']//a[@class='info']/text()"},

        {"name": "district",
         "header": "区县",
         "xpath": "//div[@class='areaName']//span[@class='info']/a[1]/text()"},

        {"name": "district_detail_1",
         "header": "街区",
         "xpath": "//div[@class='areaName']//span[@class='info']/a[2]/text()"},

        {"name": "district_detail_2",
         "header": "街道",
         "xpath": "//div[@class='areaName']//span[@class='info']/a[3]/text()"},

        {"name": "ring_road",
         "header": "环路",
         "xpath": "//div[@class='areaName']//span[@class='info']/text()[last()]"},

        {"name": "subway",
         "header": "地铁",
         "xpath": "//div[@class='areaName']//a[@class='supplement']/text()"},

        {"name": "total_price",
         "header": "总价",
         "xpath": "//div[@class='overview']//span[@class='total']/text()"},

        {"name": "unit_price",
         "header": "单价",
         "xpath": "//div[@class='unitPrice']/span[@class='unitPriceValue']/text()"},

        {"name": "area",
         "header": "面积",
         "xpath": "//div[@class='houseInfo']/div[@class='area']/div[@class='mainInfo']/text()"},

        {"name": "period",
         "header": "建筑类型及年代",
         "xpath": "//div[@class='houseInfo']/div[@class='area']/div[@class='subInfo']/text()"},

        {"name": "rooms",
         "header": "户型",
         "xpath": "//div[@class='houseInfo']/div[@class='room']/div[@class='mainInfo']/text()"},

        {"name": "building_type",
         "header": "楼型",
         "xpath": "//div[@class='houseInfo']/div[@class='room']/div[@class='subInfo']/text()"},

        {"name": "direction",
         "header": "朝向",
         "xpath": "//div[@class='houseInfo']/div[@class='type']/div[@class='mainInfo']/text()"},

        {"name": "room_type",
         "header": "装修",
         "xpath": "//div[@class='houseInfo']/div[@class='type']/div[@class='subInfo']/text()"}
        ]

tmp_str = ""
for ele in dict_xpath:
    tmp_str += ele['header'] + ","
log.write("序号," + tmp_str + "URL\n")


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
    output_str = re.findall(r"\d+\.?\d*",input_str)
    return output_str


def clear_utf8_str(input_str):
    output_str = input_str.encode("utf8").strip().replace(",", "").replace(" ","")
    return output_str


def prepare_entry(input_list, number=False):
    entry = ""
    if input_list:
        if number:
            input_list = fetch_number(input_list[0])
        entry = clear_utf8_str(input_list[0]) + ","
    else:
        entry = ","
    return entry


page_urls = []
for i in range(1, total_page_number + 1):
    page_url = base_url + "pg" + str(i) + sort + "/"
    page_urls.append(page_url)

seq = 1

for page_url in page_urls:
    print page_url
    try:
        dom = get_dom_by_url(page_url)
        room_urls = get_element_by_xpath(dom, xpath_room_link)
    except Exception, e:
        print "Failed to open URL: %s" % page_url
        continue
    for room_url in room_urls:
        try:
            dom = get_dom_by_url(room_url)
        except Exception, e:
            print "Failed to open URL: %s" % room_url
            continue
        entry = str(seq) + ","
        for name_xpath in dict_xpath:
            elements = get_element_by_xpath(dom, name_xpath['xpath'])
            if name_xpath['name'] in to_number_list:
                entry += prepare_entry(elements, number=True)
            else:
                entry += prepare_entry(elements)
        entry += room_url + "\n"
        log.write(entry)
        print entry
        seq += 1
        time.sleep(random.uniform(2,3))

