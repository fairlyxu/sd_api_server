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
import html

AD_CONFIG = {1: ["https://imggc.aigcute.com/8f00b204e9800998.jpeg",
                 "https://imggc.aigcute.com/87d72c88ccfa4190.jpeg",
                 "https://imggc.aigcute.com/0c2a049c8735a640.jpeg"]}

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
    if query == None or query == "" or query == "null" or len(query) < 1:
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

    try:
        # Send request
        r = requests.post(url, params=payload, headers=headers)
        result = r.json()
        if "trans_result" in result and "dst" in result["trans_result"][0]:
            return result["trans_result"][0]["dst"]
    except Exception as e:
        print(e)
        return translate_res


def design(img_url, normal_param, control_param):



    prompt, n_prompt, a_prompt = "", "", ""
    sampler_index = "DPM++ 2M Karras"
    size_width = 512
    size_height = 720
    steps = 20
    num = 4
    pid = 0

    if "pid" in normal_param:
        pid = int(normal_param["pid"])

    if pid != 0:
        ad_img_list = AD_CONFIG.get(pid, []).split(",")
        num = 4 - len(ad_img_list)


    if "prompt" in normal_param:
        prompt = html.unescape(normal_param["prompt"])
    if "a_prompt" in normal_param:
        translate_res = translate(normal_param["a_prompt"])
        if translate_res != None:
            a_prompt = " " + translate_res
    if "n_prompt" in normal_param:
        n_prompt = html.unescape(normal_param["n_prompt"])
    if "sampler_index" in normal_param:
        sampler_index = html.unescape(normal_param["sampler_index"])
    if "size_width" in normal_param:
        size_width = int(normal_param["size_width"])
    if "size_width" in normal_param:
        size_height = int(normal_param["size_height"])
    if "step" in normal_param:
        steps = int(normal_param["step"])

    control_model = "control_v11f1p_sd15_depth_fp16 [4b72d323]"
    control_resize_mode = "Crop and Resize"
    control_module = "invert"
    weight = 0.8
    guidance_start = 0.0,
    guidance_end = 1.0,

    if "control_model" in control_param:
        control_model = html.unescape(control_param["model"])
    if "module" in control_param:
        control_module = html.unescape(control_param["module"])
    if "resize_mode" in control_param:
        control_resize_mode = control_param["resize_mode"]
    if "weight" in control_param:
        weight = control_param["weight"]
    if "guidance_start" in control_param:
        guidance_start = float(control_param["guidance_start"])
    if "guidance_end" in control_param:
        guidance_end = float(control_param["guidance_end"])

    """
      normal_param: {"sampler_index":"DPM++ 2M Karra","prompt":"mas   ","a_prompt":" ","n_prompt":"  digit, fewer digits, cropped, worst quality, low quality, normal quality,",
      "clip":2,"steps":20,"size_width":512,"size_height":720}
      control_param: {"module":"invert","model":"control_v11f1p_sd15_depth_fp16 [4b72d323]","weight":"0.8","guidance_start":0,"guidance_end":1}
      """

    # create API client with custom host, port
    t_host = '101.43.28.24'
    t_port = 6061
    api = webuiapi.WebUIApi(host=t_host, port=t_port)

    t1 = time.time()
    picture_name = img_url.split('/')[-1]  # 提取图片url后缀
    reponse = requests.get(img_url)
    with open(ORIGIN_FILE_PATH + picture_name, 'wb') as f:
        f.write(reponse.content)
    img_url = ORIGIN_FILE_PATH + picture_name
    img = Image.open(img_url)

    unit1 = webuiapi.ControlNetUnit(input_image=img, module=control_module, model=control_model,
                                    guidance_start=guidance_start, guidance_end=guidance_end,
                                    weight=float(weight), resize_mode=control_resize_mode, pixel_perfect="true")

    result = api.txt2img(batch_size=1,
                         n_iter=num,
                         steps=steps,
                         cfg_scale=7,
                         restore_faces=False,
                         tiling=False,
                         eta=0,
                         s_churn=0,
                         s_tmax=0,
                         s_tmin=0,
                         s_noise=1,
                         override_settings={},
                         sampler_index=sampler_index,  # "DPM++ 2M Karras",
                         prompt=prompt + a_prompt,
                         negative_prompt=n_prompt,
                         width=size_width,
                         height=size_height, controlnet_units=[unit1])

    res_img = result.images
    img_list = []
    for tmp_img in res_img:  # [0:-1]:
        des_img = '{}.png'.format(uuid.uuid4())
        tmp_img.save(FILE_PATH + str(des_img))
        res, des_img_url = upload_img(des_img)
        if res:
            img_list.append("https://" + des_img_url)
            os.remove(FILE_PATH + str(des_img))

        else:
            print("上传七牛云失败，文件名：", des_img)

    if len(img_list) < 4 and pid !=0 :
        img_list += ad_img_list

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


def ee_test_ee():
    image = "https://qiniu.aigcute.com/o_1hdih8it75796pdf7c199ul8e9.jpg"
    normal_param = {"sampler_index": "DPM++ 2M Karra",
                    "prompt": "Wandering Earth,Planetary Accelerator,Space Background,Cybertron Similar,Dreams,Illusions,Bold Colors,High Quality,Very Detailed,Master Masterpiece Award-winning,Bertil Nilsson,",
                    "a_prompt": "",
                    "n_prompt": "NSFW,EasyNegative, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
                    "clip": "2", "steps": "20", "size_width": "512", "size_height": "720"}
    control_param = {"module": "invert (from white bg &amp; black line)",
                     "model": "control_v11p_sd15_seg_fp16 [ab613144]", "weight": "0.8", "guidance_start": 0,
                     "guidance_end": "1"}

    print(image, normal_param, control_param)
    if image != None and image != "null":
        # 调用画图
        res_img_list = design(image, normal_param, control_param)
        print(res_img_list)


def task(num):
    while True:
        try:
            # time.sleep(2)
            task_request = requests.request("GET", task_url, headers=headers)
            response = json.loads(task_request.text)
            res = True
            if response["code"] == 200:
                task = response["data"]
                print("TASK:",task)
                if task is not None:
                    image = task["image"]
                    normal_param = task["normal_param"]
                    control_param = task["control_param"] 
                    print(image, normal_param, control_param )
                    if image != None and image != "null":
                        # 调用画图
                        res_img_list = design(image, json.loads(normal_param), json.loads(control_param))
                        if len(res_img_list) > 0:
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
            print("~~~" ,e)


if __name__ == "__main__":
    task(1)
    """
    for i in range(1):
        t = Thread(target=task, args=(i,))
        t.start()
        time.sleep(2)
    """
