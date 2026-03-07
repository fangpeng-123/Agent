# -*- coding: utf-8 -*-
"""
诊断 get_weather_now 调用错误
"""

import sys
from pathlib import Path

# 添加父目录到路径
agent_root = Path(__file__).parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

print("=" * 80)
print("诊断 get_weather_now 调用")
print("=" * 80)

# 1. 检查环境变量
print("\n[1] 检查环境变量")
from dotenv import load_dotenv
import os

# 尝试从 agent_test 目录加载 .env
env_path = Path(__file__).parent / ".env"
print(f"  尝试加载: {env_path}")
print(f"  文件存在: {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path, override=True)
    print("  [OK] 已加载 .env 文件")

HEFENG_KEY = os.getenv("HEFENG_KEY")
HEFENG_API_HOST = os.getenv("HEFENG_API_HOST")

print(f"\n  HEFENG_KEY: {'已设置' if HEFENG_KEY else '未设置'}")
print(f"  HEFENG_API_HOST: {HEFENG_API_HOST or '未设置'}")

# 2. 导入函数
print("\n[2] 导入工具函数")
try:
    from Function_Call import ALL_FUNCTIONS

    print(f"  [OK] 成功导入 ALL_FUNCTIONS")
    print(f"  可用函数: {list(ALL_FUNCTIONS.keys())}")

    get_weather_now = ALL_FUNCTIONS.get("get_weather_now")
    if get_weather_now:
        print(f"  [OK] get_weather_now 函数存在: {get_weather_now}")
    else:
        print(f"  [ERROR] get_weather_now 函数不存在!")

except Exception as e:
    print(f"  [ERROR] 导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 3. 直接调用测试（不使用异步）
print("\n[3] 直接调用测试")
if get_weather_now:
    try:
        print("  调用: get_weather_now('北京')")
        result = get_weather_now("北京")
        print(f"  [OK] 调用成功!")
        print(f"  结果:\n{result}")
    except Exception as e:
        print(f"  [ERROR] 调用失败: {e}")
        import traceback

        traceback.print_exc()

# 4. 在异步上下文中调用测试
print("\n[4] 异步调用测试")
import asyncio


async def test_async():
    if get_weather_now:
        try:
            print("  在 async 函数中调用 get_weather_now")
            # 检查是否是异步函数
            import inspect

            if inspect.iscoroutinefunction(get_weather_now):
                print("  函数是 async，使用 await 调用")
                result = await get_weather_now("上海")
            else:
                print("  函数是同步的，直接调用")
                result = get_weather_now("上海")
            print(f"  [OK] 调用成功!")
            print(f"  结果前100字符:\n{result[:100]}...")
        except Exception as e:
            print(f"  [ERROR] 调用失败: {e}")
            import traceback

            traceback.print_exc()


asyncio.run(test_async())

# 5. 检查 Function_Call 模块中的环境变量状态
print("\n[5] 检查模块内部环境变量")
try:
    import Function_Call.Weather.weather_tools as weather_module

    print(
        f"  weather_tools.HEFENG_KEY: {'已设置' if weather_module.HEFENG_KEY else '未设置'}"
    )
    print(
        f"  weather_tools.HEFENG_API_HOST: {weather_module.HEFENG_API_HOST or '未设置'}"
    )
    print(f"  weather_modules.BASE_URL: {weather_module.BASE_URL}")
except Exception as e:
    print(f"  [ERROR] 检查失败: {e}")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
