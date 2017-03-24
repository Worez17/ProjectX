# -*- coding: utf-8 -*-
import requests as rq
import re
from pymongo import MongoClient
import json
import threading

def get_mongo():
    client = MongoClient('127.0.0.1', 27017)
    db_name = 'MyTest'
    db = client[db_name]
    collection_useraction = db['MyTable']
    return collection_useraction

def do_search_commodity(antistop):
    # print 'get commit is going'
    # mongo = get_mongo()
    list_seller_id = list()
    list_commodity_name = list()

    search_url = 'https://s.taobao.com/search?data-key=sort&data-value=sale-desc&ajax=true&_ksTS=1489401770411_976&callback=jsonp977&q=' \
                 + antistop + '&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20170313&ie=utf8&sort=sale-desc'
    search_web = rq.get(search_url)

    page_size = re.findall('\"pageSize\":(\d+),', search_web.text)[0]
    total_page = re.findall('\"totalPage\":(\d+),', search_web.text)[0]
    # current_page = re.findall('\"currentPage\":(\d+)', search_web.text)[0]
    # total_count = re.findall('\"totalCount\":(\d+)', search_web.text)[0]

    need_page_size = (109 + int(page_size)) / int(page_size)
    if need_page_size >= total_page:
        need_page_size = total_page
    # print need_page_size

    for i in range(0, need_page_size):
        if i != 0:
            search_url = 'https://s.taobao.com/search?data-key=sort&data-value=sale-desc&ajax=true&_ksTS=1489401770411_976&callback=jsonp977' \
                         '&q=%E7%93%9C%E5%AD%90&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20170313&ie=utf8&sort=sale-desc&s='\
                         + (page_size * i)
            search_web = rq.get(search_url)

        seller_ids = re.findall('\"nid\":\"(.\d+)\"', search_web.text)
        commodity_names = re.findall('\"raw_title\":\"(.*?)\"', search_web.text)
        for seller_id in seller_ids:
            list_seller_id.append(seller_id)
        for commodity_name in commodity_names:
            list_commodity_name.append(commodity_name + '<br>')

        # 本来打算每一页启动一个线程去抓取数据，但是现在出现一些莫名问题，暂时未能解决
        # 记录，后期有时间处理。看看是否要加入队列模式
        # t = threading.Thread(target=do_commit, args=(seller_ids,))
        # t.setDaemon(True)
        # t.start()

    t = threading.Thread(target=do_commit, args=(list_seller_id,))
    t.setDaemon(True)
    t.start()

    return list_commodity_name

def do_commit(seller_ids):
    print 'do commit is going'
    mongo = get_mongo()
    for seller_id in seller_ids:
        commit_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=' \
                     + seller_id + '&sellerId=130974249&order=3&currentPage=1'
        commit_web = rq.get(commit_url)

        last_page = re.findall('\"lastPage\":(.\d+)', commit_web.text)[0]
        for j in range(1, int(last_page) + 1):
            if j != 1:
                commit_url = re.sub('(?<=currentPage=)(\d+)', str(j), commit_url)
                commit_web = rq.get(commit_url)
                print commit_url
            commit_text = re.findall('\"rateList\":(\[.*?\])\,\"searchinfo\"', commit_web.text)[0]
            # commit_json = pd.read_json(commit_text)
            commit_json = json.loads(commit_text)
            # print commit_json["useful"]
            # print commit_text
            # print commit_json
            # print '----------------------------'

            mongo.insert(commit_json)
            # print 'once done'
