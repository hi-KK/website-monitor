import hashlib
import time

from django.contrib import auth
from django.db.models import Q
from django.http import JsonResponse, HttpResponse

from django.shortcuts import render, redirect


# Create your views here.
from api.settings import spnshot, source_code,spnshot_error,source_code_error,compare_code
from system.alert import kySendMail
from system.models import tokenStr, Sacntask, StatusList, report, dsretime, mail, username
from .compare import compare
from .alert import kySendMail,WzSendMail

#定时任务
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job

job_defaults = { 'max_instances': 2 }

scheduler = BackgroundScheduler(job_defaults=job_defaults)
scheduler.add_jobstore(DjangoJobStore(), "default")
#读取数据库中设置的时间频率
jc_time=dsretime.objects.filter(name='jc').first().time
wz_time=dsretime.objects.filter(name='wz').first().time

#
@register_job(scheduler, "interval", seconds=int(jc_time), id='jc_web',replace_existing=True)
def jc():
    import requests,re
    url_all = Sacntask.objects.all()
    url=[]
    for i in url_all:
        url.append(i.domain)
    for i in url:
        result_status = Sacntask.objects.filter(domain=i).first().status
        if int(result_status) == 1:
            headers={
                'Referer':'www.venustech.com.cn',
                'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0',

            }
            try:
                result = requests.get(i,headers=headers,timeout=20)
                status = result.status_code
                title = result.content.decode('utf-8')
                title = re.findall('<title>([^\<]+)</title>', title)[0]
                header=''
                for x in result.headers.items():
                    header += x[0] + ':' + x[1] + '\r\n'


                if status==200:
                    StatusList.objects.filter(url=i).update(
                        lt_status='可用',
                        header=header,
                        title=title,

                    )
                else:
                    StatusList.objects.filter(url=i).update(
                        lt_status='不可用')
                    kySendMail(i)
            except Exception as e:
                StatusList.objects.filter(url=i).update(
                    lt_status='不可用')
                kySendMail(i)


        else:
            pass
###################
##########网页快照##########

@register_job(scheduler, "interval", minutes=int(wz_time), id='screenshot_web',replace_existing=True)
def screenshot():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import hashlib

    chrome_options = Options()

    chrome_options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错

    chrome_options.add_argument('window-size=1920x1500')  # 指定浏览器分辨率
    chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    chrome_options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
    # chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
    chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    # chrome_options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"  # 手动指定使用的浏览器位置
    # 依据系统类型如MAC，LINUX下载对应浏览器驱动包

    url = Sacntask.objects.all()
    for i in url:
        result_status = Sacntask.objects.filter(domain=i.domain).first().status
        if int(result_status) == 1:

            driver = webdriver.Chrome(chrome_options=chrome_options,
                                      executable_path='/Users/nols/Documents/个人/chrome/bin/chromedriver')

            driver.get(i.domain)
            # 路径设置
            img_lj = spnshot + '{}'.format(i.id) + '.png'
            file_code = source_code + '{}'.format(i.id) + '.txt'
            error_tp = spnshot_error + '_'+'{}'.format(i.id) + '.png'
            error_code = source_code_error + '{}'.format(i.id) + '.txt'
            source_data = driver.page_source
            # 计算源码MD5
            md5 = hashlib.md5()
            md5.update(source_data.encode("utf8"))
            md5_str = md5.hexdigest()



            import os
            if not os.path.exists(img_lj):
                driver.save_screenshot(img_lj)
            if not os.path.exists(file_code):
                StatusList.objects.filter(url=i.domain).update(
                    img=i.id,
                    md5=md5_str,
                    wz_status='完整',

                )
                report.objects.filter(url=i.domain).update(
                    one_md5=md5_str,
                )

                # 留存第一次源码指纹和MD5
                with open(file_code, 'w+') as f:
                    f.write(source_data)


            # 留存后续源码MD5指纹

            StatusList.objects.filter(url=i.domain).update(
                img=i.id,
                md5_jc=md5_str
            )
            report.objects.filter(url=i.domain).update(

                two_md5=md5_str,
            )

            one_md5 = StatusList.objects.filter(url=i.domain).first().md5
            if len(one_md5) > 0:
                if one_md5 != md5_str:
                    #对比相似度

                    StatusList.objects.filter(url=i.domain).update(
                        wz_status='篡改'
                    )
                    # 留存篡改后error的快照
                    driver.save_screenshot(error_tp)

                    #静态资源存放
                    report.objects.filter(url=i.domain).update(
                        page_error = "/static/img_error/" + '_' + '{}'.format(i.id) + '.png'
                    )
                    # 留存篡改后源码
                    error_data = driver.page_source
                    with open(error_code, 'w+') as f:
                        f.write(source_data)

                    report.objects.filter(url=i.domain).update(
                        code_error = "/static/source_code_error/" + '{}'.format(i.id) + '.txt'
                    )
                    # 对比文件相似度，和生成对比文件
                    num = compare.string_similar(file_code,error_code)
                    StatusList.objects.filter(url=i.domain).update(
                        xsd=num
                    )
                    compare.compare_file(file_code, error_code, i.id)


                    report.objects.filter(url=i.domain).update(

                        ky_count = "/static/compare_code/" + '{}'.format(i.id) + '.html'
                    )
                    WzSendMail(i.domain)
                else:
                    StatusList.objects.filter(url=i.domain).update(
                        wz_status='完整'
                    )
            #关闭单个标签
            driver.close()
            #关闭浏览器
            # driver.quit()




# per-execution monitoring, call register_events on your scheduler
register_events(scheduler)
scheduler.start()
print("Scheduler started!")









# 路由保护
def LoginQuery(func):
    def url(request):
        print(request.headers)
        body=request.body.decode()
        if not body:
            return JsonResponse({'status': 'fail'})
        else:
            token = eval(body)
            token = body['token']
            if token:
                #还需对token进行数据库比对，这里省略
                is_token=tokenStr.objects.all().filter(token=token).first()
                if is_token:
                    return func(request)
            else:
                return JsonResponse({'status':'fail'})
    return url




def login(request):
    if request.method =='POST':
        data = request.body.decode()
        data=eval(data)
        user = data['username']
        passwd=data['password']

        #加密密码字符串
        md5 = hashlib.md5()
        md5.update(passwd.encode())
        jm_password = md5.hexdigest()

        data_username = username.objects.filter(username=user).first()
        data_passwd = username.objects.filter(password=jm_password).first()
        if data_username and data_passwd:
            from system.sigin_token import Token
            token_value =  Token()
            value = token_value.create_token(user, passwd)
            tokenStr.objects.create(
                user=user,
                time=time.time(),
                token=value
            )
            return JsonResponse({'status':'success','token':value,'user':user})

        else:
            return JsonResponse({'status': 'fail'})




def token_add(request):
    if request.method=='POST':
        print(request.body)
        data = request.body.decode()
        data=eval(data)
        print(data)
        name = data['name']
        domain=data['domain']
        status = data['scan']
        mail = data['mail']
        gjfz=data['gjfz']
        gjlx=data['gjlx']
        Sacntask.objects.create(
            name=name,
            domain=domain,
            status=status,
            mail=mail,
            gjfz=gjfz,
            gjlx=gjlx
        )
        StatusList.objects.create(
            url=domain,
        )
        report.objects.create(
            url=domain,
        )
        return JsonResponse({'status': 'success'})

    else:

        task_all = Sacntask.objects.all()
        data= []
        task_data={}
        for i in task_all:
            task_data['id']=i.pk
            task_data['name'] = i.name
            task_data['domain'] = i.domain
            task_data['status']=i.status
            task_data['mail'] = i.mail
            task_data['gjfz'] = i.gjfz
            task_data['gjlx'] = i.gjlx
            data.append(task_data)
            task_data = {}

        return JsonResponse({'res':data,'total':len(data)})


def token_edit(request):
    if request.method=='POST':
        body=eval(request.body.decode())
        print(body)
        id=body['id']
        name=body['name']
        domain=body['domain']
        mail=body['mail']
        gjfz = body['gjfz']
        gjlx = body['gjlx']

        #查询原先url
        url = Sacntask.objects.filter(id=int(id)).first()
        url=url.domain
        #更新

        Sacntask.objects.filter(id=int(id)).update(
            name=name,
            domain=domain,
            mail=mail,
            gjfz=gjfz,
            gjlx=gjlx

        )

       #更新
        StatusList.objects.filter(url=url).update(
            url=domain)
        report.objects.filter(url=url).update(
            url=domain)
        return JsonResponse({'status':'success'})


def scan_status(request):
    if request.method=="POST":
        body = eval(request.body.decode())
        id = body['id']
        status = body['status']
        print(body)
        Sacntask.objects.filter(id=int(id)).update(
            status=status
        )
        return JsonResponse({'status': 'success'} )


def search(request):
    if request.method == "POST":
        body=eval(request.body.decode())
        print(body)
        content=body['content']
        q = Q(Q(name__contains=content)|Q(domain__contains=content))
        ret = Sacntask.objects.filter(q)
        data = []
        task_data = {}
        for i in ret:
            task_data['id'] = i.pk
            task_data['name'] = i.name
            task_data['domain'] = i.domain
            task_data['status'] = i.status
            data.append(task_data)
            task_data = {}
        print(data)
        return JsonResponse({'res': data, 'total': len(data),'status':'success'})


def liststatus(request):
    if request.method=="GET":
        status = StatusList.objects.all()
        data = []
        status_dict={}
        wz_lt=[]
        for i in status:
            status_dict['id'] = i.pk
            status_dict['url']=i.url
            status_dict['title'] = i.title
            status_dict['MD5'] = i.md5
            wz_lt.append(i.lt_status)
            wz_lt.append(i.wz_status)
            status_dict['status']=wz_lt
            status_dict['xsd'] = i.xsd
            data.append(status_dict)
            wz_lt=[]
            status_dict={}
        return JsonResponse({'res': data, 'status': 'success'})


def listxq(request):
    if request.method=="POST":
        body = eval(request.body.decode())
        id = body['id']
        print(id)
        url = StatusList.objects.filter(id=int(id))
        status_dict = {}
        wz_lt = []
        for i in url:
            status_dict['id'] = i.id
            status_dict['url']=i.url
            status_dict['title'] = i.title
            status_dict['MD5'] = i.md5
            status_dict['header'] = i.header
            status_dict['md5_jc'] = i.md5_jc
            wz_lt.append(i.lt_status)
            wz_lt.append(i.wz_status)
            status_dict['status']=wz_lt
            status_dict['img'] = '/static/img/'+'{}'.format(i.id)+'.png'
        return JsonResponse({'res': status_dict, 'status': 'success'})


def task_del(request):
    if request.method=="POST":
        body = eval(request.body.decode())
        id = body['id']

        url=Sacntask.objects.filter(id=id).first()

        Sacntask.objects.filter(id=int(id)).delete()
        StatusList.objects.filter(url=url.domain).delete()
        report.objects.filter(url=url.domain).delete()

        return JsonResponse({'status': 'success'})


def report_list(request):
    if request.method=="GET":

        all = report.objects.all()
        data={}
        data_dict=[]
        for i in all:
            data['id'] = i.id
            data['url']=i.url
            data['one_md5'] = i.one_md5
            data['two_md5'] = i.two_md5
            data['new_page'] = i.page_error
            data['code'] = i.code_error
            data['ky_count']=i.ky_count
            data['wz_count'] = i.wz_count
            data_dict.append(data)
            data = {}

        return JsonResponse({'res':data_dict,'status': 'success'})


def status_edit(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        id = body['id']
        print(id)
        url = StatusList.objects.filter(id=id).first()
        edit_md5=StatusList.objects.filter(id=id).first().md5_jc
        task = Sacntask.objects.filter(domain=url.url).first()

        #修改状态概览md5
        StatusList.objects.filter(id=int(id)).update(
            md5=edit_md5,
            wz_status='完整',
            xsd=''
        )

        # 修改监测md5
        report.objects.filter(url=url.url).update(
            one_md5=edit_md5
        )
        # 删除report报告中的源码路径和快照路径、对比路径
        report.objects.filter(url=url.url).update(
            page_error='',
            code_error='',
            ky_count=''
        )
        #删除源照片和源码
        import os
        os.remove(spnshot+str(task.id)+'.png')
        os.remove(source_code + str(task.id) + '.txt')


        return JsonResponse({ 'status': 'success'})


def data_del(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        id = body['id']
        print(id)
        """
        1、删除源码
        2、删除指纹
        3、篡改源码
        4、篡改快照
        5、对比报告
        """
        if id==1:
            import os
            list1 = os.listdir(source_code)
            for i in list1:
                c_path = os.path.join(source_code, i)
                os.remove(c_path)
            return JsonResponse({'status': 'success'})
        if id==2:
            import os
            list1 = os.listdir(spnshot)
            for i in list1:
                c_path = os.path.join(spnshot, i)
                os.remove(c_path)
            return JsonResponse({'status': 'success'})
        if id==3:
            import os
            list1 = os.listdir(source_code_error)
            for i in list1:
                c_path = os.path.join(source_code_error, i)
                os.remove(c_path)
            all = report.objects.all()
            alllist = []
            for i in all:
                alllist.append(i.id)
            for i in alllist:
                report.objects.filter(id=i).update(
                    page_error='',
                    code_error='',
                    ky_count=''
                )

            return JsonResponse({'status': 'success'})

        if id==4:
            import os
            list1 = os.listdir(spnshot_error)
            for i in list1:
                c_path = os.path.join(spnshot_error, i)
                os.remove(c_path)
            all = report.objects.all()
            alllist = []
            for i in all:
                alllist.append(i.id)
            for i in alllist:
                report.objects.filter(id=i).update(
                    page_error='',
                    code_error='',
                    ky_count=''
                )
            return JsonResponse({'status': 'success'})
        if id==5:
            import os
            list1 = os.listdir(compare_code)
            for i in list1:
                c_path = os.path.join(compare_code, i)
                os.remove(c_path)
            all = report.objects.all()
            alllist = []
            for i in all:
                alllist.append(i.id)

            for i in alllist:

                report.objects.filter(id=i).update(
                    page_error='',
                    code_error='',
                    ky_count=''
                )
            return JsonResponse({'status': 'success'})


# timlist=dsretime.objects.all()
# for i in timlist:
#     ky_time=i.jc_time
#     wz_time=wz_time


def time_update_jc(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        value = body['time']

        dsretime.objects.filter(name='jc').update(
            time=value
        )
        ky_time = int(value)
        scheduler.remove_job('jc_web')
        scheduler.add_job(jc, 'interval', seconds=ky_time, id='jc_web')
        return JsonResponse({'status': 'success'})





def time_update_wz(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        value = body['time']
        dsretime.objects.filter(name='wz').update(
            time=value
        )
        wz_time = int(value)
        scheduler.remove_job('screenshot_web')
        scheduler.add_job(jc,'interval', minutes=wz_time, id='screenshot_web')
        return JsonResponse({'status': 'success'})


def sj_time(request):
    jc_time=dsretime.objects.filter(name='jc').first().time
    wz_time=dsretime.objects.filter(name='wz').first().time
    time_list=[]
    time_list.append(jc_time)
    time_list.append(wz_time)
    print(time_list)
    return JsonResponse({'res':time_list,'status': 'success'})


def gjmail(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        username = body['email']
        password = body['password']
        server = body['server']
        port = body['port']
        protype = body['protype']

        mail.objects.filter(uuid='gjmail').update(
            username=username,
            password=password,
            server=server,
            port=port,
            protype=protype
        )
        return JsonResponse({'status': 'success'})
    else:
        maill = mail.objects.all()
        data = {}
        for i in maill:
            data['username']=i.username
            data['password'] = i.password
            data['server'] = i.server
            data['port'] = i.port
            data['protype'] = i.protype

        return JsonResponse({'status': 'success','res':data})


def status_search(request):
    if request.method == "POST":
        data = eval(request.body.decode())
        data = data['cxdata']
        if data == 'availability':
            res_data = []
            status = []
            res_data_dict={}
            all=StatusList.objects.filter(lt_status='不可用')
            for i in all :
                print(i.id)
                res_data_dict['id']=i.id
                res_data_dict['url'] = i.url
                res_data_dict['MD5'] = i.md5
                status.append(i.lt_status)
                status.append(i.wz_status)
                res_data_dict['status'] = status
                res_data_dict['xsd'] = i.xsd
                res_data.append(res_data_dict)
                res_data_dict={}
                status=[]

            return JsonResponse({'status': 'success', 'res': res_data})
        elif data =='integrity':
            res_data = []
            status = []
            res_data_dict = {}
            all = StatusList.objects.filter(lt_status='篡改')
            for i in all:
                print(i.id)
                res_data_dict['id'] = i.id
                res_data_dict['url'] = i.url
                res_data_dict['MD5'] = i.md5
                status.append(i.lt_status)
                status.append(i.wz_status)
                res_data_dict['status'] = status
                res_data_dict['xsd'] = i.xsd
                res_data.append(res_data_dict)
                res_data_dict = {}
                status = []

            return JsonResponse({'status': 'success', 'res': res_data})
        elif data =='all':
            res_data = []
            status = []
            res_data_dict = {}
            all = StatusList.objects.all()
            for i in all:
                res_data_dict['id'] = i.id
                res_data_dict['url'] = i.url
                res_data_dict['MD5'] = i.md5
                status.append(i.lt_status)
                status.append(i.wz_status)
                res_data_dict['status'] = status
                res_data_dict['xsd'] = i.xsd
                res_data.append(res_data_dict)
                res_data_dict = {}
                status = []

            return JsonResponse({'status': 'success', 'res': res_data})
        else:
            q = Q(Q(url__contains = data)|Q(xsd__contains=data)|Q(title__contains=data)|Q(lt_status__contains=data)|Q(wz_status__contains=data) )
            all_data = StatusList.objects.filter(q)
            res_data = []
            status = []
            res_data_dict = {}
            for i in all_data:
                res_data_dict['id'] = i.id
                res_data_dict['url'] = i.url
                res_data_dict['MD5'] = i.md5
                status.append(i.lt_status)
                status.append(i.wz_status)
                res_data_dict['status'] = status
                res_data_dict['xsd'] = i.xsd
                res_data.append(res_data_dict)
                res_data_dict = {}
                status = []

            return JsonResponse({'status': 'success', 'res': res_data})


def report_search(request):
    data = eval(request.body.decode())
    data = data['cxdata']
    q = Q(Q(url__contains=data))
    all_data = report.objects.filter(q)
    res_data = []
    res_data_dict = {}
    for i in all_data:
        res_data_dict['id'] = i.id
        res_data_dict['url'] = i.url
        res_data_dict['one_md5'] = i.one_md5
        res_data_dict['two_md5'] = i.two_md5
        res_data_dict['new_page'] = i.page_error
        res_data_dict['code'] = i.code_error
        res_data_dict['ky_count'] = i.ky_count
        res_data.append(res_data_dict)
        res_data_dict = {}

    return JsonResponse({'status': 'success', 'res': res_data})


def user_add(request):
    if request.method == "POST":
        body = eval(request.body.decode())

        user = body['username']
        alisname = body['alisname']
        password = body['password']
        old_name = username.objects.filter(username= user)
        if old_name :
            return JsonResponse({'msg':'账户已存在'})
        else:
            md5 = hashlib.md5()
            md5.update(password.encode())
            jm_password = md5.hexdigest()
            username.objects.create(
                username=user,
                password=jm_password,
                alisname=alisname
            )
            return JsonResponse({'status': 'success'})





def user_list(request):
    all = username.objects.all()
    data = []
    data_dict={}
    for i in all:
        data_dict['id']=i.id
        data_dict['name'] = i.username
        data_dict['alisname'] = i.alisname
        data.append(data_dict)
        data_dict={}
    return JsonResponse({'res': data})


def user_del(request):
    if request.method == "POST":
        body = eval(request.body.decode())
        print(body)
        id = body['id']
        user = username.objects.filter(id=int(id)).first().username
        if user=='admin':
            return JsonResponse({'status': 'fail'})
        else:
            username.objects.filter(id=int(id)).delete()
            return JsonResponse({'status': 'success'})


def user_edit(request):
    if request.method == "POST":
        body = eval(request.body.decode())

        if 'alisname' in body.keys():
            user = body['name']
            alisname = body['alisname']
            password = body['password']
            md5 = hashlib.md5()
            md5.update(password.encode())
            jm_password = md5.hexdigest()
            username.objects.filter(username=user).update(
                username=user,
                password=jm_password,
                alisname=alisname

            )
            return JsonResponse({'status': 'success'})
        else:
            user = body['name']
            password = body['password']
            md5 = hashlib.md5()
            md5.update(password.encode())
            jm_password = md5.hexdigest()
            username.objects.filter(username=user).update(
                username=user,
                password=jm_password,

            )
            return JsonResponse({'status': 'success'})



def user_search(request):
    if request.method == "POST":

        if eval(request.body.decode())['result']:
            body = eval(request.body.decode())
            user = body['result']
            userdata = username.objects.filter(username=user)
            data=[]
            data_dict={}
            for i in userdata:
                data_dict['name']=i.username
                data_dict['alisname']=i.alisname
                data_dict['id'] = i.id
                data.append(data_dict)
                data_dict={}
            return JsonResponse({'res': data})
        else:

            all = username.objects.all()
            data = []
            data_dict = {}
            for i in all:
                data_dict['id'] = i.id
                data_dict['name'] = i.username
                data_dict['alisname'] = i.alisname
                data.append(data_dict)
                data_dict = {}
            return JsonResponse({'res': data})

