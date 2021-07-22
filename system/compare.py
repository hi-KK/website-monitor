#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Author: nols
import difflib
import sys

from api.settings import compare_code



class compare():
    def read_file(self,file_name):
        try:
            file_desc = open(file_name, 'r')
            # 读取后按行分割
            text = file_desc.read().splitlines()

            file_desc.close()
            return text
        except IOError as error:
            sys.exit()


    # 比较两个文件并把结果生成一份html文本
    def compare_file(self,file1, file2,id):
        if file1 == "" or file2 == "":
            print('文件路径不能为空：第一个文件的路径：{0}, 第二个文件的路径：{1} .'.format(file1, file2))
            sys.exit()
        else:
            print("正在比较文件{0} 和 {1}".format(file1, file2))
        text1_lines = self.read_file(file1)
        text2_lines = self.read_file(file2)
        diff = difflib.HtmlDiff()    # 创建HtmlDiff 对象
        result = diff.make_file(text1_lines, text2_lines)  # 通过make_file 方法输出 html 格式的对比结果
        # 将结果写入到result_comparation.html文件中
        try:
            with open(compare_code + '{}'.format(id)+'.html', 'w') as result_file:
                result_file.write(result)
                print("0============> Successfully Finished\n")
        except IOError as error:
            print('写入html文件错误：{0}'.format(error))
    #比较文件相似度
    def string_similar(self,s1, s2):
        #返回整数
        return int(difflib.SequenceMatcher(None, s1, s2).quick_ratio()*100)

compare = compare()