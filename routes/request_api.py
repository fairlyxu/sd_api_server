"""The Endpoints to manage the BOOK_REQUESTS"""
import uuid
import requests
import json
import time
from datetime import datetime, timedelta
from flask import jsonify, abort, request, Blueprint

from validate_email import validate_email
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
    """Create a book request record
    @param email: post : the requesters email address
    @param title: post : the title of the book requested
    @return: 201: a new_uuid as a flask/response object \
    with application/json mimetype.
    @raise 400: misunderstood request
    """
    if not request.get_json():
        abort(400)
    data = request.get_json(force=True)

    if not data.get('input'):
        abort(400)
    if not data.get('input').get('image'):
        abort(400)
    if not data.get('input').get('prompt'):
        abort(400)

    print("request:",data['input'])

    imgs_res_list = generate_img(data['input'])

    res_data = {
        "code": 200,
         "msg": "生成成功",
        "data": {
            "output": imgs_res_list
        }
    }


    # HTTP 201 Created
    return jsonify(res_data), 200



