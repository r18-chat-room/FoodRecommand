# coding=utf-8

from flask import Flask 
import pymysql 
import requests
import json

#初始化三个表格且值均为0：1.用户标签表   2.食物标签表    3.用户食物评分表    
print("User_Name:")
user_name = input()
print("Password:")
pw = input()



#标签要从那个接口获取并在此初始化 
Tags_List = list()	#存储标签列表	
Food_List = list()
#两者均要为string

url = 'https://gd.delbertbeta.cc/v1/internel/food/get-all-info'		
req = requests.get(url)
all_info = req.json()
all_food_info = all_info

for each_info in all_food_info:
	Food_List.append(each_info['_id'])		

tag_url = 'https://gd.delbertbeta.cc/v1/app/food/tag/random'
d = {"count": 20}
req = requests.post(tag_url,json = d)
tag_list = req.json()
for i in range(len(tag_list)):
	Tags_List.append(tag_list[i]['name'])

############################################ under is the code needed to be disabled after first usage #############################	
	
db = pymysql.connect(host = 'localhost',user = user_name,password = pw,db = 'db', charset = 'utf8mb4',cursorclass = pymysql.cursors.DictCursor)	#doubts			数据库权限初始化：grant all  on *.* to 'user_name'@'localhost' identified by password;

#1.用户标签表

#先构建好整个表格
cursor_1 = db.cursor()	#cursor作为数据库操作单位

DataL_Init_1 = """Create Table UTs(		
	User_ID  varChar(30)  NOT NULL primary key,
	%s    double(5,2) null default 0	
	)"""%(Tags_List[0])		#创建表格关于用户及其标签。
cursor_1.execute(DataL_Init_1)
db.commit()
cursor_1.close()

cursor_2 = db.cursor()
for i in range(1,len(Tags_List)):
	cursor_2.execute("alter table UTs add %s double(5,2) null default 0"%(Tags_List[i]))
	db.commit()
cursor_2.close()


#2.食物标签表


#先构建好整个表格
cursor_3 = db.cursor()

DataL_Init_2 = """Create Table FTs(
				Food_ID  varChar(30)  NOT NULL primary key,
				%s  	 double(5,2)   NULL default 0
				)"""	%(Tags_List[0])
cursor_3.execute(DataL_Init_2)
db.commit()
cursor_3.close()

cursor_4 = db.cursor()
for i in range(1,len(Tags_List)):
	Action_2 = """
				alter table FTs add %s double(5,2) null default 0 
				"""	%Tags_List[i]

	cursor_4.execute(Action_2)
	db.commit()
cursor_4.close()


#3.用户食物分数表

cursor_5 = db.cursor() 
DataL_Init_3 = """Create Table UFS_0(
				  User_ID	varChar(30)  NOT NULL,
				  Food_ID   varChar(30)  NOT NULL,
				  Score		varChar(20)	 NULL
				 )"""

cursor_5.execute(DataL_Init_3)
db.commit()
cursor_5.close()


#4.食物平均分表		insert时需要(id,0,0)这样插入
cursor_6 = db.cursor()

DataL_Init_4 = """Create Table F_AveS(
				Food_ID  varChar(30) NOT NULL primary key,
				Ave_Score	double(5,2) NULL default 0,
				times	INT(4)  NULL default 0
				)"""
cursor_6.execute(DataL_Init_4)
db.commit()
cursor_6.close() 


#创建用户评论次数表		User_CT
cursor_7 = db.cursor() 
cursor_7.execute("""Create Table User_CT(
				User_ID varChar(30) NOT NULL primary key,
				Comment_Times int(4) NULL default 0
				)""")
db.commit() 
cursor_7.close()

#创建用户FavFood表

cursor_8 = db.cursor()
cursor_8.execute("""Create Table User_FavFood(
				User_ID varChar(30) NOT NULL,
				Fav_Food varChar(30) NOT NULL
				)""")
db.commit()
cursor_8.close()

#创建评论信息表
cursor_9 = db.cursor()
cursor_9.execute("""Create Table Comment_Info(
				Comm_ID varchar(50) NOT NULL primary key,
				Context varchar(500) NOT NULL,
				User_ID varchar(30) NOT NULL,
				Score double(5,2) NOT NULL,
				Food_ID varchar(30) NOT NULL
				)""")
db.commit()
cursor_9.close()

# put all initial food info in the table includng the comment 			 
#分函数处理各个信息插入不同表中的行为
def insert_into_FTs(info):	#info includes 	[{'food_id':..., 'tags':[{'name':...},...]},{...},]	 
	Init_FT_cursor = db.cursor()
	for i in info:
		sql_action = 'insert into FTs(Food_ID) values(\'%s\')' %i['food_id']
		Init_FT_cursor.execute(sql_action)
	db.commit()
	for i in info:
		for tag in i['tags']:
			sql_action = 'update FTs set %s = 3 where Food_ID = \'%s\''%(tag,i['food_id'])
			Init_FT_cursor.execute(sql_action)
	db.commit()
	Init_FT_cursor.close()

def insert_into_Comment_Info(info):    #info includes [{'food_id‘:, 'rate':, 'tags':[],'detail':[],'user_id':,}]
	CI_cursor = db.cursor()
	for comment in info:
		sql_action = 'insert into Comment_Info(Comm_ID,Context,User_ID,Score,Food_ID) values(\'%s\',\'%s\',\'%s\',%s,\'%s\')'%(comment['comment_id'],comment['detail'],comment['user_id'],comment['rate'],comment['food_id'])
		CI_cursor.execute(sql_action)
	db.commit()
	CI_cursor.close()
	
def insert_into_F_Aves(info):   #info is [{'food_id':,'rate':,'time':},...]
	FA_cursor = db.cursor()
	for fs in info:
		sql_action = 'insert into F_AveS(Food_ID,Ave_Score,times) values(\'%s\',%s,%s)'%(fs['food_id'],fs['rate'],fs['time'])
		FA_cursor.execute(sql_action)
	db.commit()
	
def insert_into_User_CT(info):   #info is [{'user_id':,'comm_times':},...]
	UCT_cursor = db.cursor()
	for uct in info:
		sql_action = "insert into User_CT(User_ID,Comment_Times) values(\'%s\',%s)"%(uct['user_id'],uct['comm_times'])
		UCT_cursor.execute(sql_action)
	db.commit()
	UCT_cursor.close()

def insert_into_UFS_0(info):    #info is [{'user_id':,'food_id':,'rate':}]
	UFS_cursor = db.cursor()
	for ufs in info:
		sql_action = "insert into UFS_0(User_ID,Food_ID,Score) values(\'%s\',\'%s\',%s)"%(ufs['user_id'],ufs['food_id'],ufs['rate'])
		UFS_cursor.execute(sql_action)
	db.commit()
	UFS_cursor.close()
		
#roll over all_info dict and store data	
all_food_tags = []	
all_comment_info = []
all_food_score = []
all_user_ct = []
all_user_foodscore = []
for food_info in all_food_info:
	all_food_tags.append({'food_id':food_info['_id'],'tags':[x['name'] for x in food_info['tags']]})
	for comment in food_info['comment']:
		all_comment_info.append({'comment_id':comment['_id'],'food_id':food_info['_id'],'rate':comment['rate'],'tags':[x['name'] for x in comment['tags']],'detail':comment['detail'],'user_id':comment['userId']})
		
		if len(all_user_ct) == 0:
			all_user_ct.append({'user_id':comment['userId'],'comm_times':1})
		else:
			if comment['userId'] in [x['user_id'] for x in all_user_ct]:
				all_user_ct[comment['userId']]['comm_times'] += 1
			else:
				all_user_ct.append({'user_id':comment['userId'],'comm_times':1})
		
		all_user_foodscore.append({'user_id':comment['userId'],'rate':comment['rate'],'food_id':comment['food']})
			
	all_food_score.append({'food_id':food_info['_id'],'rate':food_info['rating'],'time':len(food_info['comment'])})
		
insert_into_FTs(all_food_tags)		
insert_into_Comment_Info(all_comment_info)		
insert_into_F_Aves(all_food_score)		
insert_into_User_CT(all_user_ct)
insert_into_UFS_0(all_user_foodscore)		
		
db.close()		
		
			 
#######################  above is the code needed to be disabled after first usage ###################################
