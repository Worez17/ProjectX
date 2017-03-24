
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
import doCommit
import threading

# 表单
def search_form(request):
    return render_to_response('search_form.html')



# 接收请求数据
def search(request):
    request.encoding = 'utf-8'
    if 'q' in request.GET:
        # print 111
        # t = threading.Thread(target=getCommit.get_commit, args=(request.GET['q'].encode('utf-8'),))
        # t.start()
        list_commodity_name = doCommit.do_search_commodity(request.GET['q'].encode('utf-8'))
        message = list_commodity_name
    else:
        message = '你提交了空表单'
    return HttpResponse(message)
