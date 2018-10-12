# -- coding: UTF-8
from django.shortcuts import redirect
import hashlib
import uuid
import os

#md5加密方法
def mymd5(pwd):
    mymd5 = hashlib.md5()
    mymd5.update(pwd.encode('utf-8'))
    return mymd5.hexdigest()


#登录使用的装饰器
def login(func):
    def wrapper(request,*args,**kwargs):
        if request.session.get('login_info'):
            return func(request, *args, **kwargs)
        else:
            return redirect('/user/login_ui')
    return wrapper



def do_file_name(file_name):
    return  str(uuid.uuid1())+os.path.splitext(file_name)[1]