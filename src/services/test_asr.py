import os
import base64
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

import dashscope
from dashscope.audio.qwen_tts_realtime import *

qwen_tts_realtime: QwenTtsRealtime = None
text_to_synthesize = [
    '对吧~我就特别喜欢这种超市，',
    '尤其是过年的时候',
    '去逛超市',
    '就会觉得',
    '超级超级开心！',
    '想买好多好多的东西呢！'
]

DO_VIDEO_TEST = False

def init_dashscope_api_key():
    """
    从 .env 文件中加载 DashScope API Key
    """
    script_dir = Path(__file__).parent
    env_path = script_dir / '.env'
    
    print(f"查找 .env 文件: {env_path}")
    print(f".env 文件存在: {env_path.exists()}")
    
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=True)
        print(".env 文件已加载")
    
    api_key = os.environ.get('DASHSCOPE_API_KEY', '')
    
    if not api_key or api_key in ('', 'your-dashscope-api-key'):
        print(f"环境变量值: '{api_key}'")
        raise ValueError(
            "未找到有效的 DashScope API Key！\n"
            f"请检查 {env_path} 文件是否正确配置。"
        )
    
    dashscope.api_key = api_key
    print(f"✓ API Key 已设置（长度: {len(api_key)}）")


def play_pcm_audio(file_path, sample_rate=24000, channels=1, bits_per_sample=16):
    """
    播放 PCM 音频文件
    
    参数:
        file_path: PCM 文件路径
        sample_rate: 采样率（默认 24000 Hz）
        channels: 声道数（默认 1 单声道）
        bits_per_sample: 位深度（默认 16 bit）
    """
    try:
        import pyaudio
        import wave
        
        # 打开 PCM 文件
        with open(file_path, 'rb') as pcm_file:
            pcm_data = pcm_file.read()
        
        # 初始化 PyAudio
        p = pyaudio.PyAudio()
        
        # 设置音频格式
        format_map = {
            8: pyaudio.paUInt8,
            16: pyaudio.paInt16,
            32: pyaudio.paInt32,
        }
        audio_format = format_map.get(bits_per_sample, pyaudio.paInt16)
        
        # 打开音频流
        stream = p.open(
            format=audio_format,
            channels=channels,
            rate=sample_rate,
            output=True
        )
        
        # 播放音频
        print(f"🔊 正在播放音频...")
        stream.write(pcm_data)
        
        # 等待播放完成
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("✓ 播放完成")
        
    except ImportError:
        print("⚠️  未安装 pyaudio，请运行: pip install pyaudio")
        print("   或者使用以下命令（Windows）:")
        print("   pip install pipwin")
        print("   pipwin install pyaudio")
    except Exception as e:
        print(f"⚠️  播放失败: {e}")


class MyCallback(QwenTtsRealtimeCallback):
    def __init__(self):
        self.complete_event = threading.Event()
        self.audio_file_path = 'voicefile/result_24k.pcm'
        self.file = open(self.audio_file_path, 'wb')
        self.audio_data_size = 0

    def on_open(self) -> None:
        print('connection opened')
        print('💡 提示: 音频将保存到文件，播放功能需要安装 pyaudio')

    def on_close(self, close_status_code, close_msg) -> None:
        self.file.close()
        print('connection closed with code: {}, msg: {}'.format(
            close_status_code, close_msg))

    def on_event(self, response: str) -> None:
        try:
            global qwen_tts_realtime
            type = response['type']
            if 'session.created' == type:
                print('start session: {}'.format(response['session']['id']))
            if 'response.audio.delta' == type:
                recv_audio_b64 = response['delta']
                audio_data = base64.b64decode(recv_audio_b64)
                self.file.write(audio_data)
                self.audio_data_size += len(audio_data)
            if 'response.done' == type:
                print('response {} done'.format(qwen_tts_realtime.get_last_response_id()))
            if 'session.finished' == type:
                print('session finished')
                print(f"📁 音频数据大小: {self.audio_data_size} bytes")
                self.complete_event.set()
        except Exception as e:
            print('[Error] {}'.format(e))
            return

    def wait_for_finished(self):
        self.complete_event.wait()


if __name__ == '__main__':
    init_dashscope_api_key()

    print('Initializing ...')

    callback = MyCallback()

    qwen_tts_realtime = QwenTtsRealtime(
        model='qwen3-tts-flash-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )

    qwen_tts_realtime.connect()
    qwen_tts_realtime.update_session(
        voice='Cherry',
        response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
        mode='server_commit'        
    )
    
    for text_chunk in text_to_synthesize:
        print('send text: {}'.format(text_chunk))
        qwen_tts_realtime.append_text(text_chunk)
        time.sleep(0.1)
    
    qwen_tts_realtime.finish()
    callback.wait_for_finished()
    
    print('[Metric] session: {}, first audio delay: {}'.format(
        qwen_tts_realtime.get_session_id(), 
        qwen_tts_realtime.get_first_audio_delay()
    ))
    
    # 播放音频
    print("\n" + "="*50)
    print("尝试播放音频...")
    play_pcm_audio(
        file_path=callback.audio_file_path,
        sample_rate=24000,
        channels=1,
        bits_per_sample=16
    )