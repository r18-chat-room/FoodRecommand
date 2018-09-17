# coding=utf-8
import json 
from flask import Flask 
from flask import request 
from flask import redirect 
from flask import jsonify
#from flask.ext.sqlalchemy import SQLAlchemy
import pymysql
import gzip
import msgpack
import urllib
import tarfile
import requests



def Post_Data_Test():	
	url = '/'	#http://127.0.0.1:5000/
	values = {'id':'15564','num':'123','tags' : ['甜','辣','苦'],'food':'947623','detail':"这个菜很辣，超级甜，我很喜欢",'CommentId':'1','rate':1}
	d = json.dumps(values)
	headers =  {'Content-Type':'application/json'}
	req = requests.post(url,headers = headers,data = d)
	#res_data = urllib.urlopen(req)
	#res = res_data.read()
	print(req.text)


if __name__ == '__main__':
	Post_Data_Test()