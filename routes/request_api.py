
import pymysql
import time
from flask import jsonify, abort, request, Blueprint
from tool.mysql_tool import MysqlTool
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
            password='wangqiang123',  # 数据库密码
            database='AIGC_TASK',  # 数据库名称
            charset='utf8mb4'  # 数据库字符集
        )

REQUEST_API = Blueprint('request_api', __name__)

def get_blueprint():
    """Return the blueprint for the main app module"""
    return REQUEST_API


@REQUEST_API.route('/v1/generate', methods=['POST'])
def generate():
    msg = ""
    code = 200
    output = []

    if not request.get_json():
        abort(400)
    data = request.get_json(force=True)
    if not data.get('requestid'):
        abort(400)
    if not data.get('input'):
        abort(400)
    if not data.get('input').get('image'):
        abort(400)
    if not data.get('input').get('prompt'):
        abort(400)
    try:
        dbtool = MysqlTool(pool)
        obj = dbtool.get_task_by_requestid(data.get('requestid'))
        if (obj is None):
            new_task = {}
            new_task["requestid"] = data.get('requestid')
            new_task["image"] = data.get('input').get('image') #data.get('image')
            new_task["prompt"] = data.get('input').get('prompt')#data.get('','')
            new_task["a_prompt"] = data.get('input').get('a_prompt','')
            new_task["n_prompt"] = data.get('input').get('n_prompt', '')
            dbtool.create_task(new_task)
            time.sleep(5)
            tmp_obj = dbtool.get_task_by_requestid(data.get('requestid'))
            obj = tmp_obj

        if (obj["res_img2"] and len(obj["res_img2"]) >0):
                output = obj["res_img2"].split(',')
                msg = "生成成功"
        else:
            code = 100
            msg = "排队中"
    except:
        code = -1
        msg = "查询失败"

    res_data = {
        "code": code,
        "msg": msg,
        "data": {
            "output": output
        }
    }


    # HTTP 201 Created
    return jsonify(res_data), 200

@REQUEST_API.route('/v1/get_task')
def get_task():
    msg = "查询成功"
    code = 200
    try:
        dbtool = MysqlTool(pool)
        task = dbtool.get_task_by_status(1)
        if task is None:
            code = -1
            msg = "查询失败"
        else:
            task['status'] = 0
            dbtool.update_task(task)
    except:
        code = -1
        msg = "查询失败"
        task = None

    res_data = {
        "code": code,
        "msg": msg,
        "data": task
    }
    # HTTP 201 Created
    return jsonify(res_data), 200


@REQUEST_API.route('/v1/update_task', methods=['POST'])
def update_task():
    msg = "更新成功"
    code = 200
    if not request.get_json():
        abort(400)
    task = request.get_json(force=True)

    if not task.get('requestid'):
        abort(400)
    try:
        dbtool = MysqlTool(pool)
        dbtool.update_task(task)
    except:
        code = -1
        msg = "更新失败"


    res_data = {
        "code": code,
        "msg": msg,
        "data":""
    }
    # HTTP 201 Created
    return jsonify(res_data), 200



