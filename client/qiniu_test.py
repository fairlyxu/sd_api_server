from qiniu import Auth, put_file, etag

import uuid


def qiniu_token(bucked_name):
    q = Auth(access_key='vh7avAFMeC1WefXJjiU11Hzb90ZyLi_YM5cE88uw',
             secret_key='STOqHj_jpEjG01_Q-YfH8eGpLqtE3s3gBQMP7n6A')

    token = q.upload_token(bucked_name)

    return token


def upload_img(bucked_name, file_path, domain_name):
    """
    收集本地信息到云服务器上
    参考地址：https://developer.qiniu.com/kodo/sdk/1242/python
    """
    # 指定上传空间，获取token
    token = qiniu_token(bucked_name)
    # 指定图片名称
    file_name = '{}.png'.format(uuid.uuid4())
    ret, info = put_file(token,  file_name, file_path)
    print(  info.status_code == 200 )
    img_url = domain_name + '/' + ret.get('key')
    return img_url


if __name__ == '__main__':
    bucked_name = 'aigcute'
    file_path = '../img/WechatIMG193.jpeg'
    domain_name = 'qiniu.aigcute.com'
    print(upload_img(bucked_name, file_path, domain_name))
