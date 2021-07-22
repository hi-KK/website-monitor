#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Author: nols

from system.models import Sacntask, StatusList
from system.smtp import send


def kySendMail(domain):
    #告警类型
    AlertType=Sacntask.objects.filter(domain=domain).first().gjlx
    # 收件人
    RecMail = Sacntask.objects.filter(domain=domain).first().mail

    if '可用性' in AlertType:
        send(RecMail,'jc',domain)
    else:
        pass

def WzSendMail(domain):
    # 告警类型
    AlertType = Sacntask.objects.filter(domain=domain).first().gjlx
    # 收件人
    RecMail = Sacntask.objects.filter(domain=domain).first().mail
    #阀值
    gjfz = Sacntask.objects.filter(domain=domain).first().gjfz
    #相似度
    xsd = StatusList.objects.filter(url=domain).first().xsd

    if '完整性' in AlertType:
        #判定相似度<设定阀值触发告警
        if int(xsd) < int(gjfz):
            send(RecMail, 'wz', domain)

