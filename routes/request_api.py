"""The Endpoints to manage the BOOK_REQUESTS"""
import pymysql
import requests
import json
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
            password='mysql123456',  # 数据库密码
            database='sd_task',  # 数据库名称
            charset='utf8mb4'  # 数据库字符集
        )

REQUEST_API = Blueprint('request_api', __name__)

def get_blueprint():
    """Return the blueprint for the main app module"""
    return REQUEST_API

def generate_img(data):
        imgurl = data["image"] #"https://img2.baidu.com/it/u=200748940,4153827508&fm=253&app=138&size=w931&n=0&f=JPEG&fmt=auto?sec=1680454800&t=e6333e4f52cb066037ebd88a5256c299"
        prompt = data["prompt"] #"a modern bedroom"
        url = "https://api.replicate.com/v1/predictions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Token 80f708014de97c0aaf851c5f72e4116b8810695b"
        }
        payload = {
            "version": "854e8727697a057c525cdb45ab037f64ecca770a1769cc52287c2e56472a247b",
            "input": {
                "image": imgurl,
                "prompt": prompt,
                "a_prompt": "best quality, extremely detailed, photo from Pinterest, interior, cinematic photo, ultra-detailed, ultra-realistic, award-winning",
                "n_prompt": "longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality"
            }
        }


        response = requests.request("POST", url, json=payload, headers=headers)
        resdata = response.text
        #resdata = '{"completed_at":null,"created_at":"2023-04-01T11:08:28.825710Z","error":null,"id":"e52vxqib7neires54ieiba4cge","input":{"image":"https://img2.baidu.com/it/u=200748940,4153827508&fm=253&app=138&size=w931&n=0&f=JPEG&fmt=auto?sec=1680454800&t=e6333e4f52cb066037ebd88a5256c299","prompt":"a modern bedroom","a_prompt":"best quality, extremely detailed, photo from Pinterest, interior, cinematic photo, ultra-detailed, ultra-realistic, award-winning","n_prompt":"longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality"},"logs":null,"metrics":{},"output":null,"started_at":null,"status":"starting","urls":{"get":"https://api.replicate.com/v1/predictions/e52vxqib7neires54ieiba4cge","cancel":"https://api.replicate.com/v1/predictions/e52vxqib7neires54ieiba4cge/cancel"},"version":"854e8727697a057c525cdb45ab037f64ecca770a1769cc52287c2e56472a247b","webhook_completed":null}'
        print("resdata:",resdata)
        resdict = json.loads(resdata)
        result_img_url = str(resdict["urls"]["get"])
        # https://api.replicate.com/v1/predictions/e52vxqib7neires54ieiba4cge

        #headers = {"Authorization": "Token 80f708014de97c0aaf851c5f72e4116b8810695b"}
        #result_img_url = "https://api.replicate.com/v1/predictions/aggckwxvkfgsxmjijsmr42j6fi"
        print("result_img_url：", result_img_url)
        time.sleep(10)
        img_response = requests.request("GET", str(result_img_url), headers=headers)
        print("this is post request", img_response, img_response.text)
        if img_response is not None:
            imgs_res_dict = json.loads(img_response.text)
            imgs_res_list = imgs_res_dict["output"]
        print("imgs_res_list",imgs_res_list)

        return imgs_res_list




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

    sqltool = MysqlTool(pool)
    print("request:",data['input'])
    obj = sqltool.get_task(data.get('requestid'))
    if (obj is None):
        new_task = {}
        new_task["requestid"] = data.get('requestid')
        new_task["image"] = data.get('input').get('image') #data.get('image')
        new_task["prompt"] = data.get('input').get('prompt')#data.get('','')
        new_task["a_prompt"] = data.get('input').get('a_prompt','')
        new_task["n_prompt"] = data.get('input').get('n_prompt', '')
        sqltool.create_task(new_task)
        time.sleep(5)
        tmp_obj = sqltool.get_task_by_requestid(data.get('requestid'))
        print("tmp_obj",tmp_obj)
        obj = tmp_obj

    if (obj["res_img1"] and obj["res_img2"]):
        if (obj["res_img1"] != "" and obj["res_img2"]):
            output = [obj["res_img1"], obj["res_img2"]]
            msg = "生成成功"
    else:
        code = 100
        msg = "排队中"

    res_data = {
        "code": code,
        "msg": msg,
        "data": {
            "output": output
        }
    }


    # HTTP 201 Created
    return jsonify(res_data), 200



