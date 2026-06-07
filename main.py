# -*- coding: utf-8 -*-
import argparse
import concurrent.futures
import json
import math
import os
import random
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock

import pytz
import requests

from util.aes_help import decrypt_data, encrypt_data
import util.zepp_helper as zeppHelper


LOCAL_CONFIG_PATH = Path("config.local.json")
TOKEN_DATA_PATH = Path("encrypted_tokens.data")
TRUE_VALUES = {"1", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off", ""}
SIMPLE_ENV_KEYS = {
    "USER": "ZEPP_USER",
    "PWD": "ZEPP_PASSWORD",
    "MIN_STEP": "MIN_STEP",
    "MAX_STEP": "MAX_STEP",
    "STEP_MODE": "STEP_MODE",
    "FIXED_STEP": "FIXED_STEP",
    "PUSH_PLUS_TOKEN": "PUSH_PLUS_TOKEN",
    "PUSH_PLUS_HOUR": "PUSH_PLUS_HOUR",
    "PUSH_PLUS_MAX": "PUSH_PLUS_MAX",
    "SLEEP_GAP": "SLEEP_GAP",
    "USE_CONCURRENT": "USE_CONCURRENT",
    "DRY_RUN": "DRY_RUN",
}

time_bj = None
config = {}
aes_key = None
encrypt_support = False
user_tokens = {}
user_tokens_lock = Lock()

PUSH_PLUS_TOKEN = ""
PUSH_PLUS_HOUR = ""
PUSH_PLUS_MAX = 30
sleep_seconds = 5.0
users = ""
passwords = ""
min_step = 0
max_step = 0
use_concurrent = False
dry_run = False
step_mode = "random"
fixed_step = None


def get_int_value_default(_config: dict, _key, default):
    _config.setdefault(_key, default)
    return int(_config.get(_key))


def get_bool_value(_config: dict, key: str, default: bool = False) -> bool:
    raw = _config.get(key, default)
    return parse_bool(raw, key)


def parse_bool(raw, label: str) -> bool:
    if isinstance(raw, bool):
        return raw
    value = str(raw).strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f"{label} 必须是布尔值，例如 True/False")


def get_min_max_by_time(hour=None, minute=None):
    if hour is None:
        hour = time_bj.hour
    if minute is None:
        minute = time_bj.minute
    time_rate = min((hour * 60 + minute) / (22 * 60), 1)
    min_config_step = get_int_value_default(config, "MIN_STEP", 18000)
    max_config_step = get_int_value_default(config, "MAX_STEP", 25000)
    return int(time_rate * min_config_step), int(time_rate * max_config_step)


def resolve_step_plan(_config: dict):
    mode = str(_config.get("STEP_MODE", "random")).strip().lower()
    if mode not in ("random", "fixed"):
        raise ValueError("STEP_MODE 只支持 random 或 fixed")

    if mode == "fixed":
        raw_step = _config.get("FIXED_STEP", _config.get("STEP"))
        if raw_step in (None, ""):
            raise ValueError("STEP_MODE=fixed 时必须配置 FIXED_STEP")
        step = int(raw_step)
        if step < 0:
            raise ValueError("FIXED_STEP 必须是非负整数")
        return mode, step, step, step

    min_value, max_value = get_min_max_by_time()
    if min_value > max_value:
        raise ValueError("当前计算出的步数范围不正确，请检查 MIN_STEP/MAX_STEP")
    return mode, None, min_value, max_value


def generate_step(min_step_value, max_step_value):
    if step_mode == "fixed":
        return str(fixed_step)
    return str(random.randint(min_step_value, max_step_value))


def desensitize_user_name(user):
    if len(user) <= 8:
        ln = max(math.floor(len(user) / 3), 1)
        return f"{user[:ln]}***{user[-ln:]}"
    return f"{user[:3]}****{user[-4:]}"


def get_beijing_time():
    target_timezone = pytz.timezone("Asia/Shanghai")
    return datetime.now().astimezone(target_timezone)


def format_now():
    return get_beijing_time().strftime("%Y-%m-%d %H:%M:%S")


def get_time():
    current_time = get_beijing_time()
    return "%.0f" % (current_time.timestamp() * 1000)


def push_plus(title, content):
    request_url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSH_PLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html",
        "channel": "wechat",
    }
    try:
        response = requests.post(request_url, data=data, timeout=10)
        if response.status_code == 200:
            json_res = response.json()
            print(f"pushplus 推送完成：{json_res.get('code')}-{json_res.get('msg')}")
        else:
            print(f"pushplus 推送失败，status: {response.status_code}")
    except requests.RequestException as err:
        print(f"pushplus 推送异常：{err}")


class MiMotionRunner:
    def __init__(self, _user, _passwd):
        self.user_id = None
        self.device_id = str(uuid.uuid4())
        user = str(_user).strip()
        password = str(_passwd).strip()
        self.invalid = False
        self.log_str = ""
        if user == "" or password == "":
            self.error = "用户名或密码为空"
            self.invalid = True
        self.password = password
        if not ((user.startswith("+86")) or "@" in user):
            user = "+86" + user
        self.is_phone = user.startswith("+86")
        self.user = user

    def login(self):
        with user_tokens_lock:
            user_token_info = user_tokens.get(self.user)

        if user_token_info is not None:
            access_token = user_token_info.get("access_token")
            login_token = user_token_info.get("login_token")
            app_token = user_token_info.get("app_token")
            self.device_id = user_token_info.get("device_id") or str(uuid.uuid4())
            self.user_id = user_token_info.get("user_id")
            user_token_info["device_id"] = self.device_id

            ok, msg = zeppHelper.check_app_token(app_token)
            if ok:
                self.log_str += "使用已加密保存的 app_token\n"
                return app_token

            self.log_str += f"app_token 失效，尝试重新获取，last grant time: {user_token_info.get('app_token_time')}，原因：{msg}\n"
            app_token, msg = zeppHelper.grant_app_token(login_token)
            if app_token is None:
                self.log_str += f"login_token 失效，尝试重新获取，last grant time: {user_token_info.get('login_token_time')}，原因：{msg}\n"
                login_token, app_token, user_id, msg = zeppHelper.grant_login_tokens(access_token, self.device_id, self.is_phone)
                if login_token is None:
                    self.log_str += f"access_token 已失效：{msg}，last grant time: {user_token_info.get('access_token_time')}\n"
                else:
                    user_token_info["login_token"] = login_token
                    user_token_info["app_token"] = app_token
                    user_token_info["user_id"] = user_id
                    user_token_info["login_token_time"] = get_time()
                    user_token_info["app_token_time"] = get_time()
                    self.user_id = user_id
                    with user_tokens_lock:
                        user_tokens[self.user] = user_token_info
                    return app_token
            else:
                self.log_str += "重新获取 app_token 成功\n"
                user_token_info["app_token"] = app_token
                user_token_info["app_token_time"] = get_time()
                with user_tokens_lock:
                    user_tokens[self.user] = user_token_info
                return app_token

        access_token, msg = zeppHelper.login_access_token(self.user, self.password)
        if access_token is None:
            self.log_str += f"登录获取 access_token 失败：{msg}\n"
            return None

        login_token, app_token, user_id, msg = zeppHelper.grant_login_tokens(access_token, self.device_id, self.is_phone)
        if login_token is None:
            self.log_str += f"access_token 换取 login_token 失败：{msg}\n"
            return None

        user_token_info = {
            "access_token": access_token,
            "login_token": login_token,
            "app_token": app_token,
            "user_id": user_id,
            "access_token_time": get_time(),
            "login_token_time": get_time(),
            "app_token_time": get_time(),
            "device_id": self.device_id,
        }
        self.user_id = user_id
        with user_tokens_lock:
            user_tokens[self.user] = user_token_info
        return app_token

    def login_and_post_step(self, min_step_value, max_step_value):
        if self.invalid:
            return "账号或密码配置有误", False

        app_token = self.login()
        if app_token is None:
            return "登录失败", False

        step = generate_step(min_step_value, max_step_value)
        self.log_str += f"步数模式：{step_mode}，范围：{min_step_value}~{max_step_value}，本次步数：{step}\n"
        if dry_run:
            return f"DRY_RUN 已开启，仅验证登录，不提交步数：{step}", True

        ok, msg = zeppHelper.post_fake_brand_data(step, app_token, self.user_id)
        return f"修改步数：{step}，接口返回：{msg}", ok


def push_to_push_plus(exec_results, summary):
    if PUSH_PLUS_TOKEN is None or PUSH_PLUS_TOKEN in ("", "NO"):
        return
    if PUSH_PLUS_HOUR is not None and str(PUSH_PLUS_HOUR).isdigit():
        if time_bj.hour != int(PUSH_PLUS_HOUR):
            print(f"当前设置 pushplus 推送整点为：{PUSH_PLUS_HOUR}，当前整点为：{time_bj.hour}，跳过推送")
            return

    html = f"<div>{summary}</div>"
    if len(exec_results) >= PUSH_PLUS_MAX:
        html += "<div>账号数量过多，详细情况请前往 GitHub Actions 查看。</div>"
    else:
        html += "<ul>"
        for exec_result in exec_results:
            result_word = "成功" if exec_result["success"] is True else "失败"
            html += (
                f"<li><span>账号：{desensitize_user_name(exec_result['user'])}</span>"
                f" 刷步数{result_word}，结果：{exec_result['msg']}</li>"
            )
        html += "</ul>"
    push_plus(f"{format_now()} 刷步数通知", html)


def run_single_account(total, idx, user_mi, passwd_mi):
    idx_info = f"[{idx + 1}/{total}]" if idx is not None else ""
    log_str = f"[{format_now()}]\n{idx_info}账号：{desensitize_user_name(user_mi)}\n"
    try:
        runner = MiMotionRunner(user_mi, passwd_mi)
        exec_msg, success = runner.login_and_post_step(min_step, max_step)
        log_str += runner.log_str
        log_str += f"{exec_msg}\n"
        exec_result = {"user": user_mi, "success": success, "msg": exec_msg}
    except Exception:
        error = traceback.format_exc()
        log_str += f"执行异常：{error}\n"
        exec_result = {"user": user_mi, "success": False, "msg": f"执行异常：{error}"}
    print(log_str)
    return exec_result


def execute():
    user_list = users.split("#")
    passwd_list = passwords.split("#")
    exec_results = []
    idx, total = 0, len(user_list)

    if use_concurrent:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 8)) as executor:
            exec_results = list(
                executor.map(
                    lambda x: run_single_account(total, x[0], *x[1]),
                    enumerate(zip(user_list, passwd_list)),
                )
            )
    else:
        for user_mi, passwd_mi in zip(user_list, passwd_list):
            exec_results.append(run_single_account(total, idx, user_mi, passwd_mi))
            idx += 1
            if idx < total:
                time.sleep(sleep_seconds)

    if encrypt_support:
        persist_user_tokens()

    success_count = sum(1 for result in exec_results if result["success"] is True)
    summary = f"\n执行账号总数：{total}，成功：{success_count}，失败：{total - success_count}"
    print(summary)
    push_to_push_plus(exec_results, summary)


def prepare_user_tokens() -> dict:
    if TOKEN_DATA_PATH.exists():
        data = TOKEN_DATA_PATH.read_bytes()
        try:
            decrypted_data = decrypt_data(data, aes_key, None)
            return json.loads(decrypted_data.decode("utf-8", errors="strict"))
        except Exception:
            print("密钥不正确或者加密内容损坏，放弃已缓存 token")
            return {}
    return {}


def persist_user_tokens():
    origin_str = json.dumps(user_tokens, ensure_ascii=False)
    cipher_data = encrypt_data(origin_str.encode("utf-8"), aes_key, None)
    TOKEN_DATA_PATH.write_bytes(cipher_data)


def load_config_from_env_or_file(config_path=None) -> dict:
    raw_config = os.environ.get("CONFIG")
    if raw_config:
        try:
            return dict(json.loads(raw_config))
        except json.JSONDecodeError as err:
            raise ValueError(f"CONFIG 格式不正确：{err}") from err

    simple_config = load_simple_config_from_env()
    if simple_config:
        print("未检测到 CONFIG，改用新手模式 Secrets/Variables")
        return simple_config

    local_config_path = Path(config_path) if config_path else LOCAL_CONFIG_PATH
    if local_config_path.exists():
        try:
            print(f"未检测到环境变量 CONFIG，改用本地配置：{local_config_path}")
            return dict(json.loads(local_config_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as err:
            raise ValueError(f"{local_config_path} 格式不正确：{err}") from err

    raise ValueError(f"未配置 CONFIG 环境变量，也未找到 {local_config_path}")


def load_simple_config_from_env() -> dict:
    if not os.environ.get("ZEPP_USER") and not os.environ.get("ZEPP_PASSWORD"):
        return {}
    simple_config = {}
    for config_key, env_key in SIMPLE_ENV_KEYS.items():
        value = os.environ.get(env_key)
        if value not in (None, ""):
            simple_config[config_key] = value
    return simple_config


def validate_config(_config: dict):
    required = ["USER", "PWD"]
    missing = [key for key in required if not str(_config.get(key, "")).strip()]
    if missing:
        raise ValueError(f"缺少必要配置：{', '.join(missing)}")

    user_list = str(_config["USER"]).split("#")
    passwd_list = str(_config["PWD"]).split("#")
    if len(user_list) != len(passwd_list):
        raise ValueError(f"账号数量[{len(user_list)}]和密码数量[{len(passwd_list)}]不匹配")
    if any(not item.strip() for item in user_list) or any(not item.strip() for item in passwd_list):
        raise ValueError("USER/PWD 中存在空账号或空密码，请检查 # 分隔内容")

    min_config_step = get_int_value_default(_config, "MIN_STEP", 18000)
    max_config_step = get_int_value_default(_config, "MAX_STEP", 25000)
    if min_config_step < 0 or max_config_step < 0:
        raise ValueError("MIN_STEP 和 MAX_STEP 必须是非负整数")
    if min_config_step > max_config_step:
        raise ValueError("MIN_STEP 不能大于 MAX_STEP")

    push_plus_max = get_int_value_default(_config, "PUSH_PLUS_MAX", 30)
    if push_plus_max <= 0:
        raise ValueError("PUSH_PLUS_MAX 必须大于 0")

    sleep_gap = _config.get("SLEEP_GAP", 5)
    if sleep_gap in (None, ""):
        sleep_gap = 5
    if float(sleep_gap) < 0:
        raise ValueError("SLEEP_GAP 必须是非负数字")

    get_bool_value(_config, "USE_CONCURRENT", False)
    get_bool_value(_config, "DRY_RUN", False)

    step_mode_value = str(_config.get("STEP_MODE", "random")).strip().lower()
    if step_mode_value not in ("random", "fixed"):
        raise ValueError("STEP_MODE 只支持 random 或 fixed")
    if step_mode_value == "fixed":
        raw_fixed_step = _config.get("FIXED_STEP", _config.get("STEP"))
        if raw_fixed_step in (None, ""):
            raise ValueError("STEP_MODE=fixed 时必须配置 FIXED_STEP")
        fixed_step_value = int(raw_fixed_step)
        if fixed_step_value < 0:
            raise ValueError("FIXED_STEP 必须是非负整数")


def init_runtime(args=None):
    global time_bj, config, aes_key, encrypt_support, user_tokens
    global PUSH_PLUS_TOKEN, PUSH_PLUS_HOUR, PUSH_PLUS_MAX, sleep_seconds
    global users, passwords, min_step, max_step, use_concurrent, dry_run
    global step_mode, fixed_step

    time_bj = get_beijing_time()
    config = load_config_from_env_or_file(args.config if args else None)
    validate_config(config)

    raw_aes_key = os.environ.get("AES_KEY") or str(config.get("AES_KEY", ""))
    if raw_aes_key:
        aes_key = raw_aes_key.encode("utf-8")
        if len(aes_key) == 16:
            encrypt_support = True
            user_tokens = prepare_user_tokens()
        else:
            print("AES_KEY 长度不是 16 字节，无法使用加密 token 缓存")
    else:
        print("未设置 AES_KEY，跳过加密 token 缓存")

    PUSH_PLUS_TOKEN = config.get("PUSH_PLUS_TOKEN", "")
    PUSH_PLUS_HOUR = config.get("PUSH_PLUS_HOUR", "")
    PUSH_PLUS_MAX = get_int_value_default(config, "PUSH_PLUS_MAX", 30)
    sleep_seconds = config.get("SLEEP_GAP", 5)
    if sleep_seconds in (None, ""):
        sleep_seconds = 5
    sleep_seconds = float(sleep_seconds)
    users = str(config.get("USER"))
    passwords = str(config.get("PWD"))
    step_mode, fixed_step, min_step, max_step = resolve_step_plan(config)
    use_concurrent = get_bool_value(config, "USE_CONCURRENT", False)
    dry_run = get_bool_value(config, "DRY_RUN", False)
    force_dry_run = os.environ.get("FORCE_DRY_RUN")
    if force_dry_run not in (None, ""):
        dry_run = parse_bool(force_dry_run, "FORCE_DRY_RUN")
    if args and args.dry_run:
        dry_run = True

    if use_concurrent:
        print("已开启多账号并发执行")
    else:
        print(f"多账号执行间隔：{sleep_seconds} 秒")
    print(f"步数模式：{step_mode}，本次范围：{min_step}~{max_step}")
    if dry_run:
        print("DRY_RUN 已开启：会验证登录并计算步数，但不会提交步数")


def parse_args():
    parser = argparse.ArgumentParser(description="Run MiMotion step sync.")
    parser.add_argument("--config", help="本地配置文件路径，默认 config.local.json")
    parser.add_argument("--check-config", action="store_true", help="只检查配置，不登录、不提交步数")
    parser.add_argument("--dry-run", action="store_true", help="强制试运行，只登录和计算步数，不提交步数")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        init_runtime(cli_args)
        if cli_args.check_config:
            print("配置检查通过")
            raise SystemExit(0)
        execute()
    except ValueError as err:
        print(f"启动失败：{err}")
        raise SystemExit(1)
    except Exception as err:
        print(f"启动失败：{err}")
        traceback.print_exc()
        raise SystemExit(1)
