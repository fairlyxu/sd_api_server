import json
import uuid
from qiniu import Auth, put_file
import time
from threading import Thread
import webuiapi
import requests
from PIL import Image

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


def design(img_url, prompt):
    # create API client with custom host, port
    api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
    # api = webuiapi.WebUIApi(sampler='Euler a', steps=20)

    t1 = time.time()
    picture_name = img_url.split('/')[-1]  # 提取图片url后缀
    reponse = requests.get(img_url)
    with open(ORIGIN_FILE_PATH + '/' + picture_name, 'wb') as f:
        f.write(reponse.content)
    img = Image.open(ORIGIN_FILE_PATH + '/' + picture_name)
    unit1 = webuiapi.ControlNetUnit(input_image=img, module='canny', model='control_sd15_canny [fef5e48e]')
    result = api.img2img(images=[img],
                         resize_mode=0,
                         denoising_strength=0.75,
                         mask_blur=4,
                         inpainting_fill=0,
                         inpaint_full_res=False,
                         inpaint_full_res_padding=0,
                         inpainting_mask_invert=False,
                         styles=[],
                         subseed=-1,
                         subseed_strength=0,
                         seed_resize_from_h=-1,
                         seed_resize_from_w=-1,
                         batch_size=1,
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
                         sampler_index="Euler a",# "DPM++ SDE Karras",
                         include_init_images=False,
                         prompt="((%s)),best quality, extremely detailed, photo from Pinterest, interior,"
                                " cinematic photo, ultra-detailed, ultra-realistic, award-winning" % (prompt),
                         negative_prompt="longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality,ugly,poorly designed,amateur,bad bad proportions",
                         width=512,
                         height=512,
                         seed=-1,controlnet_units=[unit1])
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
        time.sleep(2)
        task_request = requests.request("GET", task_url, headers=headers)
        response = json.loads(task_request.text)
        res = True
        if response["code"] == 200:
            task = response["data"]
            if task is not None:
                image = task["image"]
                prompt = task["prompt"]
                print(image, prompt)
                # 调用画图
                res_img_list = design(task['image'], prompt)
                """
                for i in range(2):
                    t = Thread(target=task, args=(i,))
                    t.start()
                    time.sleep(2)
                """
                # 上传七牛云并且更新数据库
                if res:
                    task['status'] = 2
                    task['res_img2'] = ','.join(res_img_list)
                else:
                    task['status'] = 1
                update_response = requests.request("POST", update_task_url, json=task, headers=headers)
                print("update_task:", update_response)
        # print(num, "--->", res)

    dbtool.close_connect()


if __name__ == "__main__":
    for i in range(2):
        t = Thread(target=task, args=(i,))
        t.start()
        time.sleep(2)

