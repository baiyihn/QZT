import logging
import sys
import json
import time
import requests
import schedule
import random
from pathlib import Path
import uuid
import base64
import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import datetime


# 配置日志
def setup_logging():
    logger = logging.getLogger("MyLogger")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logging()


class CaptchaHandler:
    def __init__(self, phone, password):
        self.phone = phone
        self.passwd = password
        self.base_url = "http://gwsxapp.gzzjzhy.com"  # 请确保URL是正确的

    def encrypt_aes_ecb(self, plaintext, key):
        aes = AES.new(key, AES.MODE_ECB)
        padded_data = pad(plaintext, AES.block_size)
        ciphertext = aes.encrypt(padded_data)
        return base64.b64encode(ciphertext).decode('utf-8')

    def request_post(self, url, data):
        headers = {
            "user-agent": "Mozilla/5.0 ...",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, data=json.dumps(data), headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"请求错误: {e}")
            return None

    def captcha_get(self):
        url = f"{self.base_url}/captcha/get"
        data = {
            "captchaType": "blockPuzzle",
            "clientUid": f"slider-{uuid.uuid4()}",
            "ts": int(time.time() * 1000)
        }
        return self.request_post(url, data)

    def calculate_offset(self, original_img_base64, jigsaw_img_base64):
        original_edge = cv2.Canny(
            cv2.imdecode(np.frombuffer(base64.b64decode(original_img_base64), np.uint8), cv2.IMREAD_UNCHANGED), 100,
            200)
        jigsaw_edge = cv2.Canny(
            cv2.imdecode(np.frombuffer(base64.b64decode(jigsaw_img_base64), np.uint8), cv2.IMREAD_UNCHANGED), 100, 200)
        _, _, _, offset = cv2.minMaxLoc(cv2.matchTemplate(original_edge, jigsaw_edge, cv2.TM_CCOEFF_NORMED))
        return f"{offset[0]:.14f}"

    def handle_captcha(self):
        return_data = self.captcha_get()
        if return_data is None or "repData" not in return_data:
            logger.error("获取验证码数据失败")
            return None

        rep_data = return_data.get("repData", {})
        secret_key_bytes = rep_data.get("secretKey", "").encode('utf-8')
        token = rep_data.get("token", "").encode('utf-8')
        original_img_base64 = rep_data.get("originalImageBase64")
        jigsaw_img_base64 = rep_data.get("jigsawImageBase64")

        if not original_img_base64 or not jigsaw_img_base64:
            logger.error("图像数据获取失败")
            return None

        x_offset_result = self.calculate_offset(original_img_base64, jigsaw_img_base64)
        coordinate_bytes = json.dumps({"x": x_offset_result, "y": 5}, separators=(',', ':')).encode('utf-8')
        token_coordinate_bytes = (token.decode('utf-8') + "---" + coordinate_bytes.decode('utf-8')).encode('utf-8')

        encrypted_verification = self.encrypt_aes_ecb(coordinate_bytes, secret_key_bytes)
        captcha_verification = self.encrypt_aes_ecb(token_coordinate_bytes, secret_key_bytes)

        verification_data = {
            "captchaType": "blockPuzzle",
            "pointJson": encrypted_verification,
            "token": token.decode('utf-8')
        }
        verification_result = self.request_post(f"{self.base_url}/captcha/check", verification_data)
        if verification_result is None:
            logger.error("验证码验证失败")
            return None

        login_data = {
            "phonenumber": self.phone,
            "password": self.passwd,
            "captchaVerification": captcha_verification
        }
        login_result = self.request_post(f"{self.base_url}/api/user/login", login_data)

        if login_result is None:
            logger.error("登录请求失败，返回结果为 None")
            return None

        if "data" not in login_result or login_result["data"] is None or "token" not in login_result["data"]:
            logger.error("登录成功，但返回结果中没有token")
            return None

        return login_result["data"].get("token")


# 发送POST请求的函数
def send_post_request(url, token, data, config_path, config):
    headers = {
        "User-Agent": "Mozilla/5.0 ...",
        "Content-Type": "application/json",
        "token": token
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        logger.info(f"请求成功，响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        response_json = response.json()

        if response_json.get("code") == 402:
            logger.warning("检测到 402 错误，尝试更新 token...")
            ensure_token_validity(config_path, config, force_update=True)
            return None

        return response_json
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None


# 检查或创建配置文件
def check_or_create_config(config_path):
    if not config_path.exists():
        default_config = {
            "tokens": [
                {
                    "token": "",
                    "first_entry_time": "09:00",
                    "punch_clock_time": "18:00",
                    "last_updated": None,
                    "messages": [
                        {
                            "name": "用户1",
                            "content": "上班打卡成功",
                            "uid": "用户1的uid"
                        }
                    ],
                    "punch_clock_data": {},
                    "phone": "your_phone1",
                    "password": "your_password1"
                }
            ],
            "pushplus": {
                "token": "cadfb817896a449cb8b89c63b8ff10b6",  # 你的 PushPlus token
                "topic": "2024"  # 你的 PushPlus topic
            }
        }
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(default_config, config_file, ensure_ascii=False, indent=4)
        logger.info(f"创建默认配置文件: {config_path}")
    else:
        logger.info(f"配置文件已存在: {config_path}")


# 加载配置文件
def load_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"加载配置文件时发生错误: {e}")
        check_or_create_config(config_path)
        sys.exit(1)


def ensure_token_validity(config_path, config, force_update=False):
    failed_users = []

    for user in config['tokens']:
        if force_update or 'token' not in user or not user['token']:
            handler = CaptchaHandler(user['phone'], user['password'])
            new_token = handler.handle_captcha()
            if new_token:
                user['token'] = new_token
                user['last_updated'] = datetime.datetime.now().isoformat()
                logger.info(f"用户 {user['phone']} 成功获取新 token")
                # 发送通知
                send_notification([{
                    "name": user['messages'][0]['name'],
                    "content": "token 更新成功了"
                }], config)
            else:
                logger.error(f"用户 {user['phone']} 登录失败，无法获取新 token，将在2分钟后重试")
                # 发送通知
                send_notification([{
                    "name": user['messages'][0]['name'],
                    "content": "token 获取失败，请注意获取间隔时间"
                }], config)
                failed_users.append(user)
                continue
            # 每次更新 token 后延迟 10 秒
            time.sleep(10)

        if user['last_updated']:
            last_updated_date = datetime.datetime.fromisoformat(user['last_updated'])
            if (datetime.datetime.now() - last_updated_date).days >= 6:
                handler = CaptchaHandler(user['phone'], user['password'])
                new_token = handler.handle_captcha()
                if new_token:
                    user['token'] = new_token
                    user['last_updated'] = datetime.datetime.now().isoformat()
                    logger.info(f"用户 {user['phone']} 强制更新新 token")
                    # 发送通知
                    send_notification([{
                        "name": user['messages'][0]['name'],
                        "content": "token 强制更新成功"
                    }], config)
                else:
                    logger.error(f"用户 {user['phone']} 强制更新 token 失败，将在2分钟后重试")
                    # 发送通知
                    send_notification([{
                        "name": user['messages'][0]['name'],
                        "content": "token 强制更新失败，请注意获取间隔时间"
                    }], config)
                    failed_users.append(user)
                    continue
                # 每次强制更新 token 后延迟 10 秒
                time.sleep(10)

    # 尝试重新更新失败的用户
    if failed_users:
        logger.info("等待2分钟后重新尝试更新失败的用户...")
        time.sleep(120)
        for user in failed_users:
            handler = CaptchaHandler(user['phone'], user['password'])
            new_token = handler.handle_captcha()
            if new_token:
                user['token'] = new_token
                user['last_updated'] = datetime.datetime.now().isoformat()
                logger.info(f"用户 {user['phone']} 再次尝试成功获取新 token")
                # 发送通知
                send_notification([{
                    "name": user['messages'][0]['name'],
                    "content": "再次尝试 token 更新成功"
                }], config)
            else:
                logger.error(f"用户 {user['phone']} 再次尝试登录失败，无法获取新 token")
                # 发送通知
                send_notification([{
                    "name": user['messages'][0]['name'],
                    "content": "再次尝试 token 获取失败，请注意获取间隔时间"
                }], config)
                continue

    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    logger.info("配置文件中的 token 已更新")


# 发送通知的函数
def send_notification(messages, config):
    pushplus_token = config["pushplus"]["token"]
    pushplus_topic = config["pushplus"]["topic"]
    url = "https://www.pushplus.plus/send"
    for message in messages:
        # 生成最新的时间戳
        timestamp = datetime.datetime.now().timestamp() * 1000000 + datetime.datetime.now().microsecond
        timestamp_str = str(int(timestamp))  # 转换为整数并转换为字符串

        data = {
            "token": pushplus_token,
            "title": message['name'],
            "content": message['content'],
            "topic": pushplus_topic,
            "timestamp": timestamp_str,
            "template": "html"
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            logger.info(f"通知发送成功: {response.json()}")
            # 延迟避免频率过快
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            logger.error(f"通知发送失败: {e}")


# 定义定时任务（上班打卡）
def job_first_entry(user, config_path, config):
    token = user['token']
    user_name = user['messages'][0]['name']
    delay = random.randint(0, 500)
    time.sleep(delay)
    logger.info(f"开始上班打卡任务: {user_name}")
    response = send_post_request('http://gwsxapp.gzzjzhy.com/api/workClock/punchClock', token, user['punch_clock_data'],
                                 config_path, config)
    if response is not None and response.get("code") == 0:
        logger.info(f"{user_name} 要每天开心呀！今天已经打卡成功了！")
        success_message = [
            {
                "name": user_name,
                "content": "今天已经打卡成功了！",
            }
        ]
        send_notification(success_message, config)
    else:
        if response is None or 'code' not in response:
            logger.error(f"{user_name} 上班打卡失败，请检查网络")
            error_message = [
                {
                    "name": user_name,
                    "content": "上班打卡失败，请检查网络",
                }
            ]
            send_notification(error_message, config)
        else:
            logger.error(f"{user_name} 上班打卡失败，要自己打卡哦，错误码: {response.get('code')}")
            error_code_message = [
                {
                    "name": user_name,
                    "content": f"上班打卡失败，要自己打卡哦，错误码: {response.get('code')}",
                }
            ]
            send_notification(error_code_message, config)


# 定义定时任务（下班打卡）
def job_punch_clock(user, config_path, config):
    token = user['token']
    user_name = user['messages'][0]['name']
    delay = random.randint(0, 500)
    time.sleep(delay)
    logger.info(f"开始下班打卡任务: {user_name}")
    response = send_post_request('http://gwsxapp.gzzjzhy.com/api/workClock/punchClock', token, user['punch_clock_data'],
                                 config_path, config)
    if response is not None and response.get("code") == 0:
        logger.info(f"{user_name} 好好休息，属于自己的时间已经成功到来！")
        success_message = [
            {
                "name": user_name,
                "content": "好好休息，属于自己的时间已经成功到来！",
            }
        ]
        send_notification(success_message, config)
    else:
        if response is None or 'code' not in response:
            logger.error(f"{user_name} 下班打卡失败，请检查网络")
            error_message = [
                {
                    "name": user_name,
                    "content": "下班打卡失败，请检查网络",
                }
            ]
            send_notification(error_message, config)
        else:
            logger.error(f"{user_name} 下班打卡失败，错误码: {response.get('code')}, 自动更新token...")
            handler = CaptchaHandler(user['phone'], user['password'])
            new_token = handler.handle_captcha()
            if new_token:
                user['token'] = new_token
                user['last_updated'] = datetime.datetime.now().isoformat()
                logger.info(f"用户 {user_name} 更新 token 成功")
                # 发送通知
                send_notification([{
                    "name": user_name,
                    "content": "下班打卡失败后，token 更新成功"
                }], config)
            else:
                logger.error(f"用户 {user_name} 更新 token 失败")
                # 发送通知
                send_notification([{
                    "name": user_name,
                    "content": "token 更新失败，请注意获取间隔时间"
                }], config)
            error_code_message = [
                {
                    "name": user_name,
                    "content": f"下班打卡失败，手动打卡，错误码: {response.get('code')}",
                }
            ]
            send_notification(error_code_message, config)


# 主程序入口
if __name__ == "__main__":
    config_path = Path("config.json")#配置文件路径和文件名称

    # 输出当前用户配置文件路径
    logger.info(f"当前用户配置文件路径: {config_path.resolve()}")

    check_or_create_config(config_path)
    config = load_config(config_path)

    # 询问用户是否需要在程序启动时更新 token
    initial_user_input = input("程序启动时是否需要更新 token? (y/n): ")
    if initial_user_input.lower() == 'y':
        ensure_token_validity(config_path, config, force_update=True)

    # 定义定时任务
    for user in config['tokens']:
        schedule.every().day.at(user['first_entry_time']).do(job_first_entry, user, config_path, config)
        schedule.every().day.at(user['punch_clock_time']).do(job_punch_clock, user, config_path, config)

    logger.info("定时任务设置完成，程序开始运行...")

    while True:
        schedule.run_pending()
        time.sleep(1)
