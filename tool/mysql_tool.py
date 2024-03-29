# 导入pymysql模块import pymysql
import traceback

import pymysql

# 创建连接MYSQL的类
class MysqlTool:
    # 初始化变量
    def __init__(self, pool, dbname="SD_TASK"):
        # 创建数据库连接
        self.connect = pool.connection()
        self.dbname = dbname

    # 查询数据库的版本
    def find_version(self):
        # 使用 cursor() 方法创建一个游标对象 cursor
        cursor = self.connect.cursor()

        # 使用 execute()  方法执行 SQL 查询
        cursor.execute("SELECT VERSION()")

        # 使用 fetchone() 方法获取单条数据.
        data = cursor.fetchone()
        print("Database version : %s " % data)

    # 数据库的查询操作
    def get_task_by_requestid(self, requestid):
        # 使用cursor()方法获取操作游标
        cursor = self.connect.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            cursor.execute("select * from %s where requestid='%s'" %(self.dbname,requestid))

            print("get_task_by_requestid 查询成功！！！！")
            return cursor.fetchall()[0]
        except:
            # 如果发生错误则回滚
            self.connect.rollback()

    # 数据库的查询操作
    def get_task_by_status(self, status):
        # 使用cursor()方法获取操作游标
        cursor = self.connect.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            sql= "select * from %s where status=%d" % (self.dbname, status)
            #print("###"*10,sql)
            cursor.execute(sql)
            res = cursor.fetchone()
            #print("get_task_by_status 查询成功！！！！", res)
            if res:
                return res
        except Exception as e:
            traceback.print_exc()
            print("get_task_by_status error~:", e)



    # 数据库的插入操作
    def create_task(self, obj):
        # 使用cursor()方法获取操作游标
        cursor = self.connect.cursor()
        #print("obj:", obj)

        # SQL 插入语句
        sql = """INSERT INTO SD_TASK(requestid,image, prompt, a_prompt, n_prompt,status)
                 VALUES('%s', '%s','%s', '%s', '%s',1)""" % (
            obj['requestid'], obj['image'], obj['prompt'], obj['a_prompt'], obj['n_prompt'])
        #print(sql)
        try:
            # 执行sql语句
            cursor.execute(sql)
            # 提交到数据库执行
            self.connect.commit()
        except:
            # 如果发生错误则回滚
            self.connect.rollback()
        print("插入成功！！！！")

    def create_task_v2(self, obj):
        # 使用cursor()方法获取操作游标
        cursor = self.connect.cursor()
        #print("obj:", obj)

        # SQL 插入语句
        sql = """INSERT INTO %s (requestid,image, normal_param, control_param,status)
                    VALUES('%s', '%s','%s', '%s',1)""" % (self.dbname, obj['requestid'], obj['image'], obj['normal_param'], obj['control_param'])
        #print(sql)
        try:
            # 执行sql语句
            cursor.execute(sql)
            # 提交到数据库执行
            self.connect.commit()
        except:
            # 如果发生错误则回滚
            self.connect.rollback()
        print("插入成功！！！！")

    # 数据库更新操作
    def update_task(self, obj):
        print("sql update_task :",obj)
        if ('status' not in obj or obj['status'] is None):
            print(" status is null" )
            return
        if ('requestid' not in obj or obj['requestid'] is None):
            print(" requestid is null")
            return
        # 使用cursor()方法获取操作游标
        cursor = self.connect.cursor()
        sql_con = 'status = %d ' %(obj['status'])
        print("**"*20,sql_con)
        if ('res_img1' in obj and obj['res_img1'] is not None):
            sql_con += ", res_img1 = '" + obj['res_img1'] + "'"
        if ('res_img2' in obj and obj['res_img2'] is not None):
            sql_con += ", res_img2 = '" + obj['res_img2'] + "'"
        #print("@@"*20,sql_con)
        # SQL 更新语句
        sql = "UPDATE " + self.dbname  +  " SET " + sql_con + " WHERE requestid = '%s'" %(obj['requestid'])
        #sql = "UPDATE '%s' SET " + sql_con + " WHERE requestid = '%s'" % (self.dbname,obj['requestid'])
        print("update sql: ",sql)
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 提交到数据库执行
            self.connect.commit()
        except:
            # 发生错误时回滚
            self.connect.rollback()

        print("更新成功！！！")

    # 关闭数据库的提示信息
    def close_connect(self):
        # 关闭数据库连接
        self.connect.close()
        print("MySQL connection closed.")


if __name__ == "__main__":
    # 定义变量
    try:
        obj = {'requestid': '1234567ddd', 'image': 'https://img2.baidu.com/it/u=4251773486,3026766425&fm=253&app=138&size=w931&n=0&f=JPEG&fmt=auto?sec=1680454800&t=97c57b5295b3a0bb8ae66e95e4e442d3', 'prompt': 'a modern bedroom', 'a_prompt': 'best quality, extremely detailed, photo from Pinterest, interior, cinematic photo, ultra-detailed, ultra-realistic, award-winning', 'n_prompt': 'longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality'}
        db = MysqlTool()
        print("MySQL connection finished.")
        db.find_version()
        db.create_task(obj)
    except Exception as e:
        print("Error connecting to MySQL: " + str(e))
    except pymysql.err.OperationalError as e:
        print("连接意外断开、 数据库名未找到: " + str(e))

