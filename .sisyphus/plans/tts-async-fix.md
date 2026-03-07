# TTS 异步播放修复计划

## 问题描述
用户反馈：一次对话后需要停顿很久才可以输出下一个问题

## 根本原因
`src/core/agent.py` 中 TTS 音频播放使用同步阻塞模式：
- `_play_audio_sync` 调用 `sd.wait()` 阻塞等待音频播放完成
- `TTSTask.finish()` 等待所有音频播放完毕才能返回
- 导致 `process()` 必须等待音频播放完毕才能处理下一轮对话

## 修复方案
实现 TTS 异步播放：合成和播放都在后台执行，不阻塞主流程

## 修改内容

### 1. 修改 `_play_audio_sync` → `_play_audio_async`
- 位置：`src/core/agent.py` 第 41-75 行
- 修改：移除 `sd.wait()` 和 `sd.stop()`，实现异步播放

### 2. 修改 `AudioPlayer._play_loop`
- 位置：`src/core/agent.py` 第 97-106 行
- 修改：调用 `_play_audio_async` 替代 `_play_audio_sync`

### 3. 修改 `TTSTask.finish()`
- 位置：`src/core/agent.py` 第 228-248 行
- 修改：不等待 `audio_player.wait_finish()`，直接返回

### 4. 修改主流程调用
- 位置：`src/core/agent.py` 第 509-511 行
- 修改：不调用 `await tts_task.finish()`，或者快速返回

## 预期效果
- TTS 合成和播放完全异步化
- `process()` 调用后立即返回
- 用户可以立即输入下一条消息
- 音频在后台播放

## 验证方式
运行 `python decoupled_agent.py`，连续输入两条消息，观察：
1. 第一条消息回复后是否立即可以输入第二条
2. 音频是否正常播放
