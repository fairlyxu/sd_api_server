import pymysql
from dbutils.pooled_db import PooledDB
pool = PooledDB(
            creator=pymysql,  # 使用pymysql作为连接的创建者
            maxconnections=20,  # 连接池中最大连接数
            mincached=2,  # 连接池中最小空闲连接数
            maxcached=20,  # 连接池中最大空闲连接数
            maxshared=20,  # 连接池中最大共享连接数
            blocking=True,  # 如果连接池达到最大连接数，是否等待连接释放后再获取新连接
            host='localhost',  # 数据库主机名
            port=3306,  # 数据库端口号
            user='root',  # 数据库用户名
            password='mysql123456',  # 数据库密码
            database='sd_task',  # 数据库名称
            charset='utf8mb4'  # 数据库字符集
        )

