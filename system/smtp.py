#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Author: nols

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from system.models import mail


def send( to, status,domain):
    """

    :param username: 账户
    :param password: 密码
    :param server: 服务器
    :param port: 端口
    :param encrypt: 协议
    :param sender: 发件者
    :param to: 收件人
    :param status: jc任务还是篡改任务
    :param domain: 域名
    :return:
    """
    mailinfo = mail.objects.all()
    for i in mailinfo:
        username = i.username
        password = i.password
        server = i.server
        port = i.port
        encrypt = i.protype
        sender=i.username

    if status=='jc':
        text='''
            域名：{}无法访问可用性异常，请及时处理
        '''.format(domain)
        title='网站监测平台可用性告警'
    else:
        text = '''
                    域名：{}完整性异常，请及时处理
                '''.format(domain)
        title = '网站监测平台完整性告警'

    message = MIMEText(text, 'plain', 'utf-8')
    message['Subject'] = Header(title, 'utf-8')
    message['From'] = sender

    try:
        if encrypt == 'none':
            w5_smtp = smtplib.SMTP()
            w5_smtp.connect(server, int(port))
        elif encrypt == 'tsl':
            w5_smtp = smtplib.SMTP(server, int(port))
            w5_smtp.starttls()
        else:
            w5_smtp = smtplib.SMTP_SSL(server, int(port))

        w5_smtp.login(username, password)
        w5_smtp.sendmail(sender, str(to), message.as_string())
        print('"发送成功"')
        return {"status": 0, "result": "发送成功"}

    except Exception as e:
        print("邮件发送失败")
        return {"status": 2, "result": "邮件发送失败"}

