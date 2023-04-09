import uuid
from qiniu import Auth, put_file, etag
from tool.mysql_tool import MysqlTool
from dbutils.pooled_db import PooledDB
import time
from threading import Thread
import webuiapi
import base64
from PIL import Image

import pymysql
BUCKED_NAME = "aigcute"
FILE_PATH = "./result/"
DOMAIN_NAME = 'qiniu.aigcute.com'

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
def design(img_url,prompt):
    # create API client
    api = webuiapi.WebUIApi()

    # create API client with custom host, port
    api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
    #api = webuiapi.WebUIApi(sampler='Euler a', steps=20)

    t1 = time.time()
    img = Image.open(img_url)
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
                         n_iter=1,
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
                         sampler_index="DPM++ SDE Karras",
                         include_init_images=False,
                         prompt="(%s),best quality, extremely detailed, photo from Pinterest, interior,"
                                " cinematic photo, ultra-detailed, ultra-realistic, award-winning" %(prompt),
                         negative_prompt="longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality",
                         width=512,
                         height=512,
                         seed=-1,controlnet_units=[unit1])
    print(result.images)
    res_img = result.images[0]
    # save_encoded_image(result['images'][0], 'result/result/'+ str(int(time.time())) + '.png')
    des_img = '{}.png'.format(uuid.uuid4())
    res_img.save(FILE_PATH + str(des_img))
    print("cost time:", int(time.time() - t1))
    cn = webuiapi.ControlNetInterface(api)
    print(cn.model_list())
    print("cost time:", int(time.time() - t1))
    return des_img

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
    ret, info = put_file(token, file_name, FILE_PATH)
    if info.status_code == 200:
        img_url = DOMAIN_NAME + '/' + ret.get('key')
        return True, img_url
    else:
        return False,None



def task(num):
    dbtool = MysqlTool(pool)
    while True:
        task = dbtool.get_task_by_status(1)
        if task is None:
            return
        task['status'] = 0
        dbtool.update_task(task)
        #调用画图
        res_img = design(task['image'])
        res, des_img_url = upload_img(res_img)
        # 上传七牛云并且更新数据库
        if res:
            task['status'] = 2
            task['res_img1'] = des_img_url
            task['res_img2'] = des_img_url
        else:
            task['status'] = 1
        dbtool.update_task(task)
        print(num, "--->", res)

    dbtool.close_connect()



if __name__ == "__main__":
    for i in range(3):
        t = Thread(target=task, args=(i,))
        t.start()
        time.sleep(1)
