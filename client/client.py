import json
import uuid
from qiniu import Auth, put_file
import time
from threading import Thread
import webuiapi
import requests
from PIL import Image
import html 



BUCKED_NAME = "aigcute"
FILE_PATH = './result/'
DOMAIN_NAME = 'qiniu.aigcute.com'
ORIGIN_FILE_PATH = './origin/'
SERVER_HOST = "http://101.132.254.70:5001/"
task_url = SERVER_HOST + "v1/get_task"
update_task_url = SERVER_HOST + "v1/update_task"
headers = {
    "Content-Type": "application/json"
}

import logging
import traceback

# 在这里设置记录的是什么等级以上的日志
logging.basicConfig(filename='run.log', format='%(asctime)s - %(name)s - %(levelname)s -%(module)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=20)



def design(img_url, prompt):
    print("prompt，文件名：", prompt)
    
    # create API client with custom host, port
    api = webuiapi.WebUIApi(host='127.0.0.1', port=7862)
    # api = webuiapi.WebUIApi(sampler='Euler a', steps=20)

    t1 = time.time()
    picture_name = img_url.split('/')[-1]  # 提取图片url后缀
    reponse = requests.get(img_url)
    with open(ORIGIN_FILE_PATH + '/' + picture_name, 'wb') as f:
        f.write(reponse.content)
    img = Image.open(ORIGIN_FILE_PATH + '/' + picture_name)

    unit1 = webuiapi.ControlNetUnit(input_image=img, module='depth_leres', model='control_v11f1p_sd15_depth [cfd03158]', guidance_start= 0.0, guidance_end = 0.3,) ##control_v11p_sd15_mlsd [aca30ff0]
    result = api.txt2img(n_iter=4,
                         sampler_index="Euler a",
                         prompt="%s, an extremely delicat, 8k wallpaper, {{{masterpiece}}},Sense of design, interior design,dvArchModern, interior, interior door, 85mm, f1.8, portrait, photo realistic, hyperrealistic, orante, super detailed, intricate, dramatic, sunset lighting, shadows, high dynamic range" % (prompt),
                         negative_prompt="lowres, text, error, worst quality, low quality, normal quality, jpeg artifacts, watermark, username, blurry,signature, soft, blurry, drawing, sketch, poor quality, ugly, text, type, word, logo, pixelated, low resolution, saturated, high contrast, oversharpened",
                         width=512,
                         height=512,
                         seed=-1,
                         controlnet_units=[unit1])

    #print(result.images)
    res_img = result.images
    img_list = []
    for tmp_img in res_img:
        des_img = '{}.png'.format(uuid.uuid4())
        tmp_img.save(FILE_PATH + str(des_img))
        res, des_img_url = upload_img(des_img)
        if res:
            img_list.append("https://" + des_img_url)
        else:
            print("上传七牛云失败，文件名：", tmp_img)


    print("cost time:", int(time.time() - t1))
    return img_list


def upload_img(file_name):
    """
    收集本地信息到云服务器上
    参考地址：https://developer.qiniu.com/kodo/sdk/1242/python
    """

    # 指定上传空间，获取token
    q = Auth(access_key='vh7avAFMeC1WefXJjiU11Hzb90ZyLi_YM5cE88uw',
             secret_key='STOqHj_jpEjG01_Q-YfH8eGpLqtE3s3gBQMP7n6A')
    token = q.upload_token(BUCKED_NAME)
    # 指定图片名称
    ret, info = put_file(token, 'res_' + file_name, FILE_PATH + file_name, )
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
                    #image = task["image"]
                    prompt = html.unescape(task["prompt"]) 
                    # 调用画图
                    res_img_list = design(task['image'], prompt) 
                    # 上传七牛云并且更新数据库
                    if res:
                        task['status'] = 2
                        task['res_img2'] = ','.join(res_img_list)
                    else:
                        task['status'] = 1
                    update_response = requests.request("POST", update_task_url, json=task, headers=headers)
                    print("update_task:", update_response)
                    #logging.info("运行结果为: {}".format(update_response))
        except Exception as e:
            s = traceback.format_exc() 
            logging.info(u"使用 traceback 输出异常: {}".format(s)) 
            logging.error(u"使用 logging error 参数 exc_info=True 输出异常", exc_info=True) 
            logging.exception(u"使用logging exception 函数直接输出异常堆栈 {}".format(e))  

    


if __name__ == "__main__":
    i = 1
    t = Thread(target=task, args=(i,))
    t.start() 

