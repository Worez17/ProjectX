
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import render
import doComment

# 表单
def search_form(request):
    return render_to_response('search_form.html')



# 接收请求数据
def search_commodity(request):
    request.encoding = 'utf-8'
    if 'q' in request.GET:
        list_commodity_name = doComment.do_search_commodity(request.GET['q'].encode('utf-8'))
        message = list_commodity_name
    else:
        message = '你提交了空表单'
    return HttpResponse(message)

# 查询具体某个商品的评论
def search_comment(request):
     request.encoding = 'utf-8'
     if 'q' in request.GET:
        # print 'search comment is going'
        list_comment = doComment.search_comment(request.GET['q'].encode('utf-8'))
        # message = list_comment
        return render(request, 'comment.html', {'data': list_comment})
     else:
        message = '没有查询条件'
        return HttpResponse(message)

# 分词
def phrase(request):
    request.encoding = 'utf-8'
    if 'comment' in request.GET:
        # print 'phrase is going'
        comment_phrase = doComment.phrase(request.GET['comment'].encode('utf-8'))
        # message = list_comment
        return render(request, 'phrase.html', {'data': comment_phrase})
        # return HttpResponse(comment_phrase)
    else:
        return HttpResponse('没有接收到相应信息')