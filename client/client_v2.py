# -*- coding: utf-8 -*-
import os
import uuid
from qiniu import Auth, put_file
import time
from threading import Thread
import webuiapi
from PIL import Image
import requests
import random
import json
from hashlib import md5

BUCKED_NAME = "aigcute"
FILE_PATH = './result/'
DOMAIN_NAME = 'qiniu.aigcute.com'
ORIGIN_FILE_PATH = './origin/'
SERVER_HOST = "http://101.132.254.70:5001/"
task_url = SERVER_HOST + "v2/get_task"
update_task_url = SERVER_HOST + "v2/update_task"
headers = {
    "Content-Type": "application/json"
}



def translate(query):
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()

    translate_res = ""
    if query == None or query =="" or query =="null"  or len(query) < 1:
        return translate_res
    # Set your own appid/appkey.
    appid = '20231013001845675'
    appkey = 'FmseV6MYnw8gzQQV09Vv'
    from_lang = 'auto'
    to_lang = 'en'
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path
    # Generate salt and sign

    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    try :
        # Send request
        r = requests.post(url, params=payload, headers=headers)
        result = r.json()
        if "trans_result" in result and "dst" in result["trans_result"][0]:
            return result["trans_result"][0]["dst"]
    except Exception as e:
        print(e)
        return translate_res

def design(img_url, normal_param_str,control_param_str):
    try:
        normal_param = json.loads(normal_param_str)
        control_param = json.loads(control_param_str)
    except Exception as e:
        print(e)

    prompt, n_prompt = "", ""
    sampler_index = "DPM++ 2M Karras"
    if "prompt" in normal_param:
        prompt = normal_param["prompt"]
    if "a_prompt" in normal_param:
        a_prompt = " " + translate(normal_param["a_prompt"])
        prompt += a_prompt
    if "n_prompt" in normal_param:
        n_prompt = normal_param["n_prompt"]
    if "sampler_index" in normal_param:
        sampler_index = normal_param["sampler_index"]


    control_model = "control_v11f1p_sd15_depth_fp16 [4b72d323]"
    control_resize_mode = "Crop and Resize"
    control_module = "invert"
    weight = 0.8
    if "control_model" in control_param:
        control_model = control_param["model"]
    if "module" in control_param:
        control_module = control_param["module"]
    if "resize_mode" in control_param:
        control_resize_mode = control_param["resize_mode"]
    if "weight" in control_param:
        weight = control_param["weight"]

    # create API client with custom host, port
    api = webuiapi.WebUIApi(host='101.43.28.24', port=7860)


    t1 = time.time()
    picture_name = img_url.split('/')[-1]  # 提取图片url后缀
    reponse = requests.get(img_url)
    with open(ORIGIN_FILE_PATH + picture_name, 'wb') as f:
        f.write(reponse.content)
    img_url = ORIGIN_FILE_PATH + picture_name
    img = Image.open(img_url)

    unit1 = webuiapi.ControlNetUnit(input_image=img, module=control_module, model=control_model,
                                    weight=float(weight), resize_mode=control_resize_mode, pixel_perfect="true")

    result = api.txt2img(batch_size=1,
                         n_iter=4,
                         steps=20,
                         cfg_scale=7,
                         restore_faces=False,
                         tiling=False,
                         eta=0,
                         s_churn=0,
                         s_tmax=0,
                         s_tmin=0,
                         s_noise=1,
                         override_settings={},
                         sampler_index=sampler_index,#"DPM++ 2M Karras",
                         prompt= prompt,
                         negative_prompt= n_prompt,
                         width=512,
                         height=724,controlnet_units=[unit1])

    res_img = result.images
    img_list = []
    for tmp_img in res_img[0:-1]:
        des_img = '{}.png'.format(uuid.uuid4())
        tmp_img.save(FILE_PATH + str(des_img))
        res, des_img_url = upload_img(des_img)
        if res:
            img_list.append("https://" + des_img_url)
            os.remove(FILE_PATH + str(des_img))

        else:
            print("上传七牛云失败，文件名：", des_img)

    print("cost time:", int(time.time() - t1))
    return img_list

def upload_img(file_name):
    """
    收集本地信息到云服务器上
    参考地址：https://developer.qiniu.com/kodo/sdk/1242/python
    """
    print(type(file_name))
    t1 = time.time()
    # 指定上传空间，获取token
    q = Auth(access_key='vh7avAFMeC1WefXJjiU11Hzb90ZyLi_YM5cE88uw',
             secret_key='STOqHj_jpEjG01_Q-YfH8eGpLqtE3s3gBQMP7n6A')
    token = q.upload_token(BUCKED_NAME)
    # 指定图片名称

    ret, info = put_file(token, 'res_' + file_name, FILE_PATH + file_name, )
    print("upload_img cost:", time.time() - t1)
    if info.status_code == 200:
        img_url = DOMAIN_NAME + '/' + ret.get('key')
        return True, img_url
    else:
        return False, None


def task(num):
    while True:
        try:
            time.sleep(2)
            task_request = requests.request("GET", task_url, headers=headers)
            response = json.loads(task_request.text)
            res = True
            if response["code"] == 200:
                task = response["data"]
                if task is not None:
                    image = task["image"]
                    normal_param = task["normal_param"]
                    control_param = task["control_param"]
                    print(image, normal_param,control_param)
                    if image!= None and image!="null":
                        # 调用画图
                        res_img_list = design(task['image'],normal_param,control_param)
                        if len(res_img_list) > 0 :
                            # 上传七牛云并且更新数据库
                            if res:
                                task['status'] = 2
                                task['res_img2'] = ','.join(res_img_list)
                            else:
                                task['status'] = 1
                            update_response = requests.request("POST", update_task_url, json=task, headers=headers)
                            print("update_task:", update_response)
                # print(num, "--->", res)
        except Exception as e:
            print(e)




if __name__ == "__main__":
    task(1)
    """
    for i in range(1):
        t = Thread(target=task, args=(i,))
        t.start()
        time.sleep(2)
    """



