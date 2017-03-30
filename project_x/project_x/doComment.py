# -*- coding: utf-8 -*-
import requests as rq
import re
from pymongo import MongoClient
import json
import threading
import logging
import logging.config
import jieba.posseg as pseg
import sys
import myUtil

reload(sys)
sys.setdefaultencoding('utf8')

logging.config.fileConfig("logger.conf")
# create logger
logger = logging.getLogger("example")

with open('config/jieba.json', 'r') as f:
    jieba_phrase = json.load(f)

def get_mongo():
    client = MongoClient('127.0.0.1', 27017)
    db_name = 'MyTest'
    db = client[db_name]
    collection_useraction = db['MyTable']
    return collection_useraction

def do_search_commodity(antistop):
    # print 'get comment is going'
    # mongo = get_mongo()
    list_item_id = list()
    list_commodity_name = list()

    search_url = 'https://s.taobao.com/search?data-key=sort&data-value=sale-desc&ajax=true&_ksTS=1489401770411_976&callback=jsonp977&q=' \
                 + antistop + '&imgfile=&js=1&stats_click=search_radio_all%3A1&initiative_id=staobaoz_20170313&ie=utf8&sort=sale-desc'
    search_web = rq.get(search_url, headers=myUtil.randHeader())

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
            search_web = rq.get(search_url, headers=myUtil.randHeader())

        item_ids = re.findall('\"nid\":\"(.\d+)\"', search_web.text)
        commodity_names = re.findall('\"raw_title\":\"(.*?)\"', search_web.text)
        for index, item_id in enumerate(item_ids):
            list_item_id.append(item_id)
            list_commodity_name.append('<a href="http://127.0.0.1:8000/search-comment?q=' + item_id + '">' + commodity_names[index] + '<br>')

        # t = threading.Thread(target=do_comment, args=(seller_ids,))
        # t.setDaemon(True)
        # t.start()

    t = threading.Thread(target=do_comment, args=(list_item_id,))
    t.setDaemon(True)
    t.start()

    return list_commodity_name

def do_comment(list_item_id):

    # print 'do comment is going'
    mongo = get_mongo()

    for item_id in list_item_id:
        comment_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=' \
                     + item_id + '&sellerId=130974249&order=1&content=2&append=0&currentPage=1'
        comment_web = rq.get(comment_url, headers=myUtil.randHeader())
        # print comment_url
        last_page = re.findall('\"lastPage\":(.\d+)', comment_web.text)[0]
        # 获取本次获取数据时countTotal
        count_total = re.findall('\"total\":(.\d+)', comment_web.text)[0]

        last_count_comment = 0
        if mongo.find_one({"typeId": "item_count", "itemId": item_id}) == None :
            item_count = {"typeId": "item_count", "itemId": item_id, "count_tatal": count_total}
            mongo.insert(item_count)
        elif int(mongo.find_one({"typeId": "item_count", "itemId": item_id})['count_tatal']) < int(count_total):
            last_item_count = mongo.find_one({"typeId": "item_count", "itemId": item_id})
            count_minus = int(count_total) - int(last_item_count['count_tatal'])
            mongo.update({"typeId": "item_count", "itemId": item_id}, {"$set": {"count_tatal": count_total}})
            last_page = (count_minus + 19) / 20
            last_count_comment = count_minus % 20
        else:
            continue

        for j in range(1, int(last_page) + 1):
            if j != 1:
                comment_url = re.sub('(?<=currentPage=)(\d+)', str(j), comment_url)
                comment_web = rq.get(comment_url, headers=myUtil.randHeader())
                # print comment_url
            try:
                comment_text = re.findall('\"rateList\":(\[.*?\])\,\"searchinfo\"', comment_web.text)[0]
                comment_text = re.sub('"(?=aliMallSeller)', '"typeId":"comment", "itemId":"' + item_id + '","', comment_text)

                if int(last_page) == j and last_count_comment != 0:
                    comment_text_dump = '[{"'
                    comment_text_dumps = re.findall('(.*?){"', comment_text)
                    for i in range(1, last_count_comment+1):
                        comment_text_dump = comment_text_dump + comment_text_dumps[i]
                    comment_text_dump = comment_text_dump[0: len(comment_text_dump) - 1] + ']'
                    comment_text = comment_text_dump
                    print comment_text

                comment_json = json.loads(comment_text)
                mongo.insert(comment_json)
            except:
                print 'Exception'

def search_comment(item_id):
    print 'search comment is going'
    mongo = get_mongo()
    list_content = list()
    for u in mongo.find({"typeId":"comment", "itemId": item_id}):
        list_content.append(u['rateContent'] )

    return list_content

def phrase(comment):
    # print comment

    list_word = list()
    words = pseg.cut(comment)

    list_word.append(comment)
    for w in words:
        if jieba_phrase.has_key(w.flag):
            list_word.append(w.word + '(' + jieba_phrase[w.flag] + ')')
        elif jieba_phrase.has_key(w.flag[0:1]):
            list_word.append(w.word + '(' + jieba_phrase[w.flag[0:1]] + ')')
        else:
            list_word.append(w.word + w.flag + '(没有找到该词词性)')
    return list_word

if __name__ == "__main__":
    print 'main is going'
    # mongo = get_mongo()
    # print mongo.find({"itemId": "43199049035"}).count()
    list_word = list()
    words = pseg.cut("张三去清华大学")

    for w in words:
        print w.word + w.flag[0:1]

    # with open('jieba.json', 'r') as f:
    #     data = json.load(f)
    # print data['qwe']
    # search_comment()
    # logger.info('sdfgh')