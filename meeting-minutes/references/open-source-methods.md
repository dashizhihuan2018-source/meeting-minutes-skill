# 开源方法参考

检索快照：2026-10-20。Stars 只表示检索时的社区关注度，不证明准确率、隐私或会议内容完整性。以下为方法学习，不是安装或产品实测。

## 直接相关会议应用

- [Meetily](https://github.com/Zackriya-Solutions/meetily)：在 `topic:meeting-minutes archived:false` 按 stars 排序的结果中居首（31,958）。社区版 MIT；PRO 是另一代码库。借鉴原始转写与结构化总结分离、摘要/决策/行动项/讨论的结构。其 `frontend/src-tauri/templates/standard_meeting.json` 要求行动项附责任人、期限和转写时间；`backend/app/transcript_processor.py` 展示分块和重叠处理。技能增加了缺失责任人不猜测、全部材料交叉核验和截图证据。
- [Anarlog，原 Hyprnote](https://github.com/fastrepl/anarlog)：9,535 stars；社区应用 MIT，企业目录另有商业许可。借鉴“转写+人工 memo”融合、Markdown 可移植性、转写与总结 provider 分离。是否本地处理取决于所选 provider，不因产品称 local-first 就认定所有路径本地。
- [Vexa](https://github.com/Vexa-ai/vexa)：2,892 stars，Apache-2.0；会议机器人/转写 API 方向。仅在确有在线会议接入需要且获授权时考虑，离线文件纪要无需自动加入会议。

## 转写基础组件

- [WhisperX](https://github.com/m-bain/whisperX)：24,693 stars，BSD-2-Clause。借鉴时间对齐、说话人分离与摘要分层；说话人聚类不等于真实姓名识别，不应从画面位置自动归属发言。
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)：支持使用已有本地模型转写，不把模型输出视为人工校对。输入 16kHz 单声道 PCM 可通过 `wave` + NumPy 读取，避免某些 PyAV 环境的 `metadata_errors` 参数不兼容；不要为解决此问题修改全局环境。

技能的截图附录和证据分层是独立工作流设计，不宣称这些应用已经提供相同功能。没有复制以上项目的程序实现。
