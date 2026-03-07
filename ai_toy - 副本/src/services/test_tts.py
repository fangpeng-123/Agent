# -*- coding: utf-8 -*-
"""Dashscope ASR 本地音频识别测试"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")


def upload_file(file_path: str) -> str:
    """上传音频文件到 Dashscope OSS"""
    url = "https://dashscope.aliyuncs.com/api/v1/files"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "audio/wav")}
        data = {"purpose": "file-transcribe"}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        file_id = result["data"]["uploaded_files"][0]["file_id"]

        # 获取可下载的 URL
        detail_resp = requests.get(
            f"https://dashscope.aliyuncs.com/api/v1/files/{file_id}", headers=headers
        )
        return detail_resp.json()["data"]["url"]
    else:
        raise Exception(f"上传失败: {response.text}")


def submit_task(file_url: str) -> str:
    """提交异步转写任务"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": "qwen3-asr-flash-realtime",
        "input": {"file_urls": [file_url]},
        "parameters": {"channel_id": [0]},
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["output"]["task_id"]
    raise Exception(f"任务提交失败: {response.text}")


def get_result(task_id: str) -> str:
    """获取转写结果"""
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    for _ in range(60):
        resp = requests.get(url, headers=headers)
        result = resp.json()
        status = result["output"]["task_status"]

        if status == "SUCCEEDED":
            text_url = result["output"]["results"][0]["transcription_url"]
            text_resp = requests.get(text_url)
            text_result = text_resp.json()
            return text_result["transcripts"][0]["sentences"][0]["text"]
        elif status == "FAILED":
            raise Exception(f"转写失败: {result['output'].get('message')}")

        print(f"  状态: {status}, 等待中...")
        time.sleep(1)
    raise Exception("转写超时")


def main():
    audio_file_path = (
        r"F:\code\Agent\ai_toy\src\services\voicefile\儿童说话你好呀.wav"
    )

    if not os.path.exists(audio_file_path):
        print(f"[ERROR] 文件不存在: {audio_file_path}")
        return

    print(f"开始识别音频: {audio_file_path}\n")

    try:
        print("步骤1: 上传文件...")
        file_url = upload_file(audio_file_path)
        print(f"  [OK] 文件上传成功\n")

        print("步骤2: 提交转写任务...")
        task_id = submit_task(file_url)
        print(f"  [OK] 任务已提交\n")

        print("步骤3: 等待转写完成...")
        result = get_result(task_id)
        print(f"\n[OK] 识别结果: {result}")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
