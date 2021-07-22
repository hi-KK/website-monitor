from django.db import models

# Create your models here.

class tokenStr(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.CharField(max_length=100,null=False)
    token=models.CharField(max_length=100,null=False)
    time=models.CharField(max_length=100,null=False)

class Sacntask(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100,null=False)
    domain=models.CharField(max_length=100,null=False)
    status = models.CharField(max_length=10,null=False)
    mail = models.CharField(max_length=100, null=False)
    gjlx= models.CharField(max_length=100, null=False)

    gjfz= models.CharField(max_length=100, null=False)
    time=models.DateField(auto_now=True)

class StatusList(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=100,null=False)
    title=models.CharField(max_length=100,null=False)
    md5 = models.CharField(max_length=1000,null=False)
    md5_jc=models.CharField(max_length=1000,null=False)
    lt_status=models.CharField(max_length=100,null=False)
    wz_status=models.CharField(max_length=100,null=False)
    header=models.CharField(max_length=1000,null=False)
    img=models.CharField(max_length=100,null=False)
    xsd=models.CharField(max_length=100,null=False)

class report(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=100,null=False)
    one_md5 = models.CharField(max_length=1000,null=False)
    two_md5=models.CharField(max_length=1000,null=False)
    page_error=models.CharField(max_length=100,null=False)
    code_error=models.CharField(max_length=100,null=False)
    ky_count=models.CharField(max_length=100,null=False)
    wz_count=models.CharField(max_length=100,null=False)

class dsretime(models.Model):

    id = models.AutoField(primary_key=True)
    name= models.CharField(max_length=100,null=False)
    time=models.CharField(max_length=100,null=False)

class mail(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=100, null=False)
    username = models.CharField(max_length=100, null=False)
    password = models.CharField(max_length=100, null=False)
    server= models.CharField(max_length=100,null=False)
    port=models.CharField(max_length=100,null=False)
    protype= models.CharField(max_length=100,null=False)

class username(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, null=False)
    password = models.CharField(max_length=100, null=False)
    alisname = models.CharField(max_length=100, null=True)
    time = models.DateField(auto_now=True,null=True)
