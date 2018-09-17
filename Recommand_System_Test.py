# coding=utf-8

#推荐系统主要后台代码

import Init_SQL 
import math 
import pymysql

#功能：1.从数据库中生成User_Tags与Food_Tags的字典	2.计算User与Food的两个相似矩阵   3.针对用户喜爱的食物来调整其拥有的标签的权重   4.根据用户ID来返回推荐列表

user_name = Init_SQL.user_name
pw = Init_SQL.pw

class RSystem:
	def __init__(self):
		self.Food_ID_List  = ['947232','947623']	#在使用前在此处初始化
		self.User_ID_List = ['13342','34221','15564']	
		self.UserCF_Matrix = dict() 
		self.ItemCF_Matrix = dict()	
		self.Food_AveScore = dict() 
		self.Food_AveScore_List= dict() 
		self.RS_Tags_List = Init_SQL.Tags_List
		for food_id in self.Food_ID_List:
			self.Food_AveScore[food_id] = dict()
			self.Food_AveScore[food_id]['AveScore'] = 0	#avescore
			self.Food_AveScore[food_id]['Times'] = 0	#times

		DB_conn =  pymysql.connect(host = 'localhost',user = user_name,password = pw,db = 'db', charset = 'utf8mb4',cursorclass = pymysql.cursors.DictCursor)
		Get_F_AveS = DB_conn.cursor()
		Get_F_AveS.execute("select * from F_AveS")
		rows = Get_F_AveS.fetchall()

		for row in rows:
			self.Food_AveScore[row['Food_ID']]['AveScore'] = row['Ave_Score']
			self.Food_AveScore[row['Food_ID']]['Times'] = row['times']
		Get_F_AveS.close()
		DB_conn.close()


		self.User_Fav_Food_List = dict() 
		for user_id in self.User_ID_List:
			self.User_Fav_Food_List[user_id] = set()

	def Insert_NewFoodID(self,food_id):
		self.Food_ID_List.append(food_id)

	def Insert_NewUserID(self,user_id):
		self.User_ID_List.append(user_id)
		
	def Up_Tags_Weight(self,user_id,Fav_Food_ID):	#将特定用户喜欢的食物所具有的标签在UT表格中进行权重增加
		#权重增加百分比依据该用户对其有过行为的食物的数量，当该用户吃过更多食物的时候（评分行为越多），该行为对其的影响越小
		DB_conn = pymysql.connect(host = 'localhost',user  = user_name,password = pw,db ='db', charset = 'utf8mb4', cursorclass = pymysql.cursors.DictCursor)
		get_food_tags_cursor = DB_conn.cursor()
		get_food_tags_cursor.execute('select * from FTs where Food_ID = %s' %Fav_Food_ID)


		row = get_food_tags_cursor.fetchone()		#这里需要修改 使得其可以提出该食品对应的所有标签向量
		fav_tag_list = set()
		for tag in self.RS_Tags_List:
			if(row[tag] != 0 ):
				fav_tag_list.add(tag)

		get_food_tags_cursor.close()

		Get_U_CT_cursor = DB_conn.cursor()
		Get_U_CT_cursor.execute("select Comment_Times from User_CT where User_ID = %s" %user_id)
		temp_dict = Get_U_CT_cursor.fetchone()
		if(temp_dict['Comment_Times'] == 0):
			commmet_time = 1
		else:
			commmet_time = temp_dict['Comment_Times']

		for tag in fav_tag_list:
			Up_User_Tags_Weight = DB_conn.cursor()
			Up_User_Tags_Weight.execute('update UTs set %s  = %s + %s where User_ID = %s' %(tag,tag,1 + math.log(commmet_time/5) ,user_id))		
			DB_conn.commit()
			Up_User_Tags_Weight.close()

		self.User_Fav_Food_List[user_id].add(Fav_Food_ID)
    
    
	def DOWN_Tags_Weight(self,user_id,Dislike_Food):
		DB_conn = pymysql.connect(host = 'localhost',user = user_name,password = pw,db ='db', charset = 'utf8mb4', cursorclass = pymysql.cursors.DictCursor)
		get_food_tags_cursor = DB_conn.cursor()
        
		Unlike_tag_set = set()
		get_food_tags = 'select * from FTs where Food_ID = %s'  %(Dislike_Food)
		get_food_tags_cursor.execute(get_food_tags)
		Dislike_Tags_row = get_food_tags_cursor.fetchone()
        
		for tag in self.RS_Tags_List:
			if(Dislike_Tags_row[tag] != 0):
				Unlike_tag_set.add(tag)
    
		get_food_tags_cursor.close()
        
		for down_tag_index in Unlike_tag_set:
			Down_User_Tags_Weight = DB_conn.cursor()
			Down_User_Tags_Weight.execute(' update UTs set %s =  %s * 0.8 where User_ID = %s' %(tag,tag,user_id))
			DB_conn.commit()
			Down_User_Tags_Weight.close()
		self.User_Fav_Food_List[user_id].remove(Dislike_Food)


	def Cal_ItemCF(self):    #计算物品相似度
    #Point: 如何给向量字典顺序加入物品各个标签的行为点数
		Item_Tags = dict()
		DB_conn = pymysql.connect(host = 'localhost',user = user_name,password = pw,db = 'db', charset = 'utf8mb4',cursorclass = pymysql.cursors.DictCursor)
    	#生成各食物的标签向量
    	#（后面可以增加用标签占比来计算物品标签向量提高准确度）
		for i in range(0,len(self.Food_ID_List)):
			Item_Tags[self.Food_ID_List[i]] = dict() 
			get_food_tags_cursor = DB_conn.cursor()

			get_food_tags = " select * from FTs where Food_ID = %s" %self.Food_ID_List[i]
			get_food_tags_cursor.execute(get_food_tags)
			Food_Tags_row = get_food_tags_cursor.fetchone()
    		
			for j in range(0,len(self.RS_Tags_List)):
				Item_Tags[self.Food_ID_List[i]][self.RS_Tags_List[j]] = Food_Tags_row[self.RS_Tags_List[j]]
			get_food_tags_cursor.close()

    	#计算相似矩阵
		for food_i in self.Food_ID_List:
			self.ItemCF_Matrix[food_i] = dict()
			vector_i = Item_Tags[food_i].items()
			len_vi = 0
			for key, value in vector_i:
				len_vi += value*value 
			len_vi = math.sqrt(len_vi)
			for food_j in self.Food_ID_List:
				if (food_i == food_j):
					self.ItemCF_Matrix[food_i][food_j] = 0
				else:
					vector_j = Item_Tags[food_j].items()
					part_result = 0
					len_vj = 0
					for key, value in vector_j:
						len_vj += value*value 
					len_vj = math.sqrt(len_vj)
					for i in range(0,len(vector_i)):
						part_result += Item_Tags[food_i][self.RS_Tags_List[i]] * Item_Tags[food_j][self.RS_Tags_List[i]]
					self.ItemCF_Matrix[food_i][food_j] = part_result/(len_vi * len_vj)	
		DB_conn.close()

    		


	def Cal_UserCF(self):    #计算用户相似度
    	#后期可采用皮尔逊相似度
		DB_conn = pymysql.connect(host = 'localhost',user = user_name,password = pw, db = 'db', charset = 'utf8mb4',cursorclass = pymysql.cursors.DictCursor)
		User_Tags = dict() 

		for i in range(0,len(self.User_ID_List)):
			User_Tags[self.User_ID_List[i]] = dict() 
			get_User_tags_cursor = DB_conn.cursor() 

			get_user_tags = " select * from UTs where User_ID = %s" %self.User_ID_List[i]
			get_User_tags_cursor.execute(get_user_tags)
			User_Tags_row = get_User_tags_cursor.fetchone() 

			for j in range(0,len(self.RS_Tags_List)):
				User_Tags[self.User_ID_List[i]][self.RS_Tags_List[j]] = User_Tags_row[self.RS_Tags_List[j]]
			get_User_tags_cursor.close() 

    	#计算相似矩阵
		for user_i in self.User_ID_List:
			self.UserCF_Matrix[user_i] = dict() 
			vector_i = User_Tags[user_i].items() 
			len_vi = 0
			for key, value in vector_i:
				len_vi += value*value 
			len_vi = math.sqrt(len_vi)
			for user_j in self.User_ID_List:
				if(user_i == user_j):
					self.UserCF_Matrix[user_i][user_j] = 0 
				else :
					vector_j = User_Tags[user_j].items()
					len_vj = 0
					for key, value in vector_j:
						len_vj += value*value 
					len_vj = math.sqrt(len_vj)
					part_result = 0
					for i in range(0,len(self.RS_Tags_List)):
						part_result += User_Tags[user_i][self.RS_Tags_List[i]] * User_Tags[user_j][self.RS_Tags_List[i]]
					self.UserCF_Matrix[user_i][user_j] = part_result/(len_vi * len_vj)	
		DB_conn.close()
'''
	def Feature_Connection_Mining(self):
		#根据用户的喜爱食物对其进行关联搜索，对每个用户的喜欢模式找出最频繁项
'''


	

    #推荐算法中用USerCF来线下计算并定时提供好推荐列表，再用ItemCF来进行当用户收藏了食物之后的实时计算

	def Renew_Food_Rank_List(self):
		print(self.Food_AveScore)
		temp = sorted(self.Food_AveScore.items(),key = lambda item : item[0], reverse = True)
		self.Food_AveScore_List = temp 
		self.Food_AveScore = dict(temp)
		print(temp)

	def Recommand(self,user_id):    #根据用户ID返回其推荐列表		
        #先根据用户相似度抽取相似度高的用户收藏的食物用于推荐
        UserCF_Recommand_List = list()
        if user_id in self.UserCF_Matrix: 
			Top_Sim_User_List = sorted(self.UserCF_Matrix[user_id],key = lambda item:item[1],reverse = True)		#结果为['34221', '13342']	
        	#删掉top_list中用户自身
			Top_Sim_User_List.remove(user_id)	

			for top_sim_user in Top_Sim_User_List:
				for food in self.User_Fav_Food_List[top_sim_user]:
					if food not in UserCF_Recommand_List:
						UserCF_Recommand_List.append(food)
					else :
						continue



        #再根据物品相似度进行实时推荐
		Sim_Items_List = list() 
		Sim_Items_Set = set()
		for Fav_Food_ID in self.User_Fav_Food_List[user_id]:
			part_Sim_Items_List = sorted(self.ItemCF_Matrix[Fav_Food_ID],key = lambda item: item[1], reverse = True)
			Sim_Items_List.extend(part_Sim_Items_List)

		Sim_Items_Recommand_List = list(set(Sim_Items_List))
		Sim_Items_List.sort(key = Sim_Items_List.index)

		#然后再根据用户自身edit的标签来推荐 
		DB_conn = pymysql.connect(host = 'localhost', user = user_name,password = pw, db = 'db', charset = 'utf8mb4',cursorclass = pymysql.cursors.DictCursor)
		get_User_tags_cursor = DB_conn.cursor() 
		get_user_tags = " select * from UTs where User_ID = %s" %user_id
		get_User_tags_cursor.execute(get_user_tags)
		User_Tags_row = get_User_tags_cursor.fetchone() 
		del User_Tags_row['User_ID']
		#先得出用户标签权重排名
		Tag_Rank_List = sorted(User_Tags_row.items(),key = lambda item:item[1], reverse = True)	#tag标签依据权重从高至下排列	返回结果如[('辣', 2.0), ('甜', 1.2), ('咸', 1.0), ('苦', 1.0)]
		RecommandList_EditedTag = list()
		counter = 0
		tag_value_sum = 0
		for tag,value in Tag_Rank_List:
			if (value != 0):
				counter += 1 
				tag_value_sum += value 
		mid_tag_value = tag_value_sum/counter
		#筛选出值得依据的标签 
		EditedTags_RecommendList = list()
		for tag,value in Tag_Rank_List:
			if(value >= mid_tag_value):
				Tag_To_Foods_cursor = DB_conn.cursor() 
				Tag_To_Foods_cursor.execute("select Food_ID,%s from FTs"%tag)
				rows = Tag_To_Foods_cursor.fetchall()
				Top_ChosenTag_Rank_DictList = sorted(rows,key = lambda item : item["%s"%tag],reverse = True)
				#从值得推荐的标签的字典列表中获取前几个食品加入列表中
				for i in range(2):		#'2'后期可加入学习因子且要视记录多少而定
					EditedTags_RecommendList.append(Top_ChosenTag_Rank_DictList[i]['Food_ID'])

		get_User_tags_cursor.close() 

        #下一步先融合二表再进行根据平均分数排列
		All_Item_Recommend_List = Sim_Items_List + UserCF_Recommand_List + EditedTags_RecommendList
		self.Renew_Food_Rank_List()
		Food_AveScore_Rank_List = list() 
		for key,value in self.Food_AveScore_List:
			Food_AveScore_Rank_List.append(key)

		self.Food_AveScore = dict(self.Food_AveScore)
		Final_Item_Recommend_List = [item for item in Food_AveScore_Rank_List if item in All_Item_Recommend_List]
		return Final_Item_Recommend_List


