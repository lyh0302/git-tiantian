# -- coding: utf-8
import sys
import random
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from tiantiantest import myutil
from django.core.urlresolvers import reverse
from user.models import *
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.views.generic import View
from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,SignatureExpired,BadSignature
# from django.contrib.auth.models import AbstractUser
from tiantiantest import settings
import re

reload(sys)
sys.setdefaultencoding('utf-8')



# 跳转到登录页面

def index(request):
    return render(request, "./index.html")
# 注册界面
class RegisterView(View):
    def get(self,request):
        return render(request, 'register.html')
    def post(self,request):
        # 接收参数
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 运行数据检验
        if not all([username, password, cpwd, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验密码
        if password != cpwd:
            return render(request, 'register.html', {'errmsg': '两次密码不一致'})
            # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()


        serializer=Serializer(settings.SECRET_KEY,3600)
        info={"confirm":user.id}
        token=serializer.dumps(info).decode()
        encryption_url="http://192.168.12.212:8888/user/active/%s"%token

        #发邮件
        subject='天天生鲜欢迎信息'
        message=''
        sender=settings.EMAIL_FROM
        receiver=[email]
        html_message='<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="%s">%s</a>'%(username,encryption_url,encryption_url)

        send_mail(subject,message,sender,receiver,html_message=html_message)

        return redirect(reverse('user:login'))

class  ActiveView(View):
    def get(self,request,token):
        serializer =Serializer(settings.SECRET_KEY,3600)
        try:
            info=serializer.loads(token)
            user_id=info["confirm"]

            user=User.objects.get(id=user_id)
            user.is_active=1
            user.save()

            return redirect(reverse("user:login"))
        except SignatureExpired as e:
            return  HttpResponse("激活连接已过期")
        except BadSignature as e:
            return HttpResponse("激活连接非法")
# def register(request):
#     '''注册'''
#     if request.method=='GET':
#         return render(request, 'register.html')
#     elif request.method=='POST':
#         #接收数据
#         # 接收参数
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         cpwd = request.POST.get('cpwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#
#         # 运行数据检验
#         if not all([username, password, cpwd, email]):
#             # 数据不完整
#             return render(request, 'register.html', {'errmsg': '数据不完整'})
#         # 校验密码
#         if password != cpwd:
#             return render(request, 'register.html', {'errmsg': '两次密码不一致'})
#             # 校验邮箱
#         if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '请同意协议'})
#         # 校验用户名是否重复
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             # 用户名不存在
#             user = None
#
#         if user:
#             # 用户名存在
#             return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
#         user = User.objects.create_user(username, email, password)
#         user.is_active = 0
#         user.save()
#
#         return redirect(reverse('user:login'))
#
# # # 注册处理
# # def register_handler(request):


#登录页面
class LoginView(View):
    def get(self,request):
        context = {}

        # 判断是否存在记住用户名的cookie
        cookie_user_name = request.COOKIES.get('cookie_user_name')
        if cookie_user_name:
            context['cookie_user_name'] = cookie_user_name

        # 判断验证码
        verificationcode_error = request.COOKIES.get('verificationcode_error')
        if verificationcode_error:
            context['verificationcode_error'] = '验证码错误'

        # 判断用户名
        user_error = request.COOKIES.get('user_error')
        if user_error:
            context['user_error'] = '用户名错误'

        # 判断密码
        pwd_error = request.COOKIES.get('pwd_error')
        if pwd_error:
            context['pwd_error'] = '密码错误'

        # 判断验证码是否正确
        return render(request, 'login.html', context)
    def post(self,request):
        # 接收参数
        request_params = request.POST

        # 接收验证码并判断
        verificationcode = request_params.get('verificationcode')

        if request.session['verificationcode'].upper() != verificationcode.upper():
            response = redirect('/user/login_ui')
            response.set_cookie('verificationcode_error', 1)
            response.set_cookie('name_error', 1, -1)
            response.set_cookie('pwd_error', 1, -1)
            return response

        # 接收其他参数
        user_name = request_params.get('user_name')
        user_pwd = request_params.get('user_pwd')
        remember = request_params.get('remember')

        # 加密
        user_pwd = myutil.mymd5(user_pwd)

        # 判断
        if User.objects.filter(uname=user_name, upwd=user_pwd).exists():
            response = HttpResponseRedirect('/book/index')
            # 写cookie
            if remember:
                response.set_cookie('cookie_user_name', user_name, max_age=2 * 7 * 24 * 3600)

            # 写session
            request.session['login_info'] = user_name

            response.set_cookie('verificationcode_error', 1, -1)
            response.set_cookie('name_error', 1, -1)
            response.set_cookie('pwd_error', 1, -1)
        else:
            response = redirect('/user/login_ui')
            if not User.objects.filter(uname=user_name).exists():
                response.set_cookie('name_error', 1)
            else:
                response.set_cookie('name_error', 1, -1)
                response.set_cookie('pwd_error', 1)
            response.set_cookie('verificationcode_error', 1, -1)

            return redirect(reverse('user:index'))


# def login(request):
#
#     context = {}
#
#     # 判断是否存在记住用户名的cookie
#     cookie_user_name = request.COOKIES.get('cookie_user_name')
#     if cookie_user_name:
#         context['cookie_user_name'] = cookie_user_name
#
#     #判断验证码
#     verificationcode_error = request.COOKIES.get('verificationcode_error')
#     if verificationcode_error:
#         context['verificationcode_error'] = '验证码错误'
#
#     # 判断用户名
#     name_error = request.COOKIES.get('name_error')
#     if name_error:
#         context['name_error'] = '用户名错误'
#
#     # 判断密码
#     pwd_error = request.COOKIES.get('pwd_error')
#     if pwd_error:
#         context['pwd_error'] = '密码错误'
#
#
#     # 判断验证码是否正确
#     return render(request, 'login.html', context)
#
#
# # 登录的逻辑处理：1、登录成功，跳转到index页面，2、失败，调转到登录页面
# def login_handler(request):
#     # 接收参数
#     request_params = request.POST
#
#     #接收验证码并判断
#     verificationcode = request_params.get('verificationcode')
#
#     if request.session['verificationcode'].upper() != verificationcode.upper():
#         response = redirect('/user/login_ui')
#         response.set_cookie('verificationcode_error',1)
#         response.set_cookie('name_error', 1, -1)
#         response.set_cookie('pwd_error', 1, -1)
#         return response
#
#
#     #接收其他参数
#     user_name = request_params.get('user_name')
#     user_pwd = request_params.get('user_pwd')
#     remember = request_params.get('remember')
#
#     # 加密
#     user_pwd = myutil.mymd5(user_pwd)
#
#     # 判断
#     if User.objects.filter(uname=user_name,upwd=user_pwd).exists():
#         response = HttpResponseRedirect('/book/index')
#         # 写cookie
#         if remember:
#             response.set_cookie('cookie_user_name', user_name, max_age=2 * 7 * 24 * 3600)
#
#         # 写session
#         request.session['login_info'] = user_name
#
#         response.set_cookie('verificationcode_error', 1,-1)
#         response.set_cookie('name_error', 1,-1)
#         response.set_cookie('pwd_error', 1,-1)
#     else:
#         response = redirect('/user/login_ui')
#         if not User.objects.filter(uname=user_name).exists():
#             response.set_cookie('name_error', 1)
#         else:
#             response.set_cookie('name_error', 1, -1)
#             response.set_cookie('pwd_error', 1)
#         response.set_cookie('verificationcode_error', 1, -1)
#
#     return response



# 退出
def logout(request):
    request.session.flush()
    return redirect('/user/login')


'''
#验证码测试
def verificationcode(request):
    with open('/home/yong/c罗.jpg','rb') as file:
        return HttpResponse(file.read(),'image/jpeg')
'''


def verificationcode(request):
    bgcolor = (random.randrange(50, 100), random.randrange(50, 100), 150)
    width = 160
    height = 40
    # 创建画面对象
    # im = Image.new('RGB', (width, height), bgcolor)
    im = Image.new('RGB', (width, height), (200,230,200))
    # 创建画笔对象
    draw = ImageDraw.Draw(im)
    # 调用画笔的point()函数绘制噪点
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    # 定义验证码的备选值
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    # 随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += str1[random.randrange(0, len(str1))]
    # 构造字体对象
    font = ImageFont.truetype('FreeMono.ttf', 25)
    # 构造字体颜色
    fontcolor = (200, random.randrange(0, 200), random.randrange(0, 200))
    # 绘制4个字
    draw.text((20, 5), rand_str[0], font=font, fill=fontcolor)
    draw.text((55, 5), rand_str[1], font=font, fill=fontcolor)
    draw.text((90, 5), rand_str[2], font=font, fill=fontcolor)
    draw.text((125, 5), rand_str[3], font=font, fill=fontcolor)
    # 释放画笔
    del draw
    #创建内存读写的对象
    buf = BytesIO()
    # 将图片保存在内存中，文件类型为png
    im.save(buf, 'png')

    #放入session中
    request.session['verificationcode'] = rand_str
    request.session.set_expiry(0)

    return HttpResponse(buf.getvalue(), 'image/png')




#检查用户名是否存在，如果存在返回1,否则返回0
def checkusername(request):
    # time.sleep(5)
    user_name = request.GET.get('user_name')
    if User.objects.filter(uname=user_name).exists():
        return HttpResponse(1)
    else:
        return HttpResponse(0)