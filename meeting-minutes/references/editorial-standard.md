# 会议纪要编辑与排版标准

## 内容依据

参照 [Meetily Standard Meeting Notes](https://github.com/Zackriya-Solutions/meetily/blob/main/frontend/src-tauri/templates/standard_meeting.json) 的四段结构：摘要、关键决策、行动项、讨论要点。2026-10-20复核时，Meetily在 `topic:meeting-minutes archived:false` 的stars排序中居首。关注度不等于质量认证；该模板规定内容组织，不规定字体、纸张或国际标准。下列版式为本技能的独立设计，不声称获得认证。

## 正文结构

1. 标题与元信息：主题、日期、形式、交流单位。仅列获授权的个人信息，不猜会议实际起止时间。
2. 会议摘要：一段说明目的、核心结果与下一步，不重复参会名单。
3. 关键决策或交流结论：决策前置；探索性交流使用“交流结论”，不将倾向性表态升级为决议。
4. 行动事项：每行一项，至少列ID、任务、责任方和期限；已分配与建议待办分开。缺失值统一写“待确认”“未约定”，交付物可写进任务描述。
5. 讨论要点：按主题归纳问题、回应与必要限制，不转储逐字稿。较长内容可从新页开始。

时间戳、笔记段落、原话对照、技术检查及详细待核项保留在内部依据文件。沿用上游的可追溯原则，但公开交流稿不默认显示转写片段及个人信息。

## 版式

- A4纵向，左右边距约20–23mm、上下18–22mm；不使用装饰性封面占满一页。
- 正文10.5–11pt，行距约1.35–1.5；标题20–25pt，一级标题12–14pt，层级不超过三级。
- 中文使用已安装且可嵌入PDF的清晰字体；显式设置东亚字体，不能仅相信文件中的字体声明。可用思源黑体等，字体由使用者另行提供。
- 深色正文、一种克制的强调色、浅色摘要卡片；采用统一栅格、段距、缩进和页码。中英文辅助标签须少量，不喧宾夺主。
- 行动表优先4列，任务列占约一半宽度；显式固定列宽、表头重复、整行不拆页。长行动项改用卡片，不压缩到难读的小字。
- 不让标题单独留在页末，不拆开一个行动项；不以空格对齐，不插入多余空段落凑版。按内容决定页数，不靠缩小字号强塞两页。
- 附录另册按时间排序，一张完整画面一页；只对获授权的对外副本去标识，原始证据不覆盖。

## 可编辑输出

已有 `docx` Node依赖时，可运行 `node scripts/render_minutes.js input.json new-output-directory`。脚本拒绝覆盖，输出DOCX和Markdown，正文由调用者编写，脚本不会自动转写或生成未经核对的事实。

输入字段：`title, subtitle, date, format, organizations, summary, conclusions, actions, discussions, next_steps`。`actions`项使用`id, task, owner, due`；`discussions`项使用`title, text`。可选`style.font`指定本地中文字体，`layout.discussion_new_page`用于长篇分区，`conclusion_heading`可设为“交流结论”。

本地实际纪要可增加`participants`数组，项含`name, organization, role`，以及`participant_note`。`appendices`数组项含`title, note, figures`；图片项含本地`file`、原图`width, height`及`caption`，渲染为一图一页的横向附录，并复制完整原图到输出目录。默认不去掉名单和附录；公开模板只保留此通用结构，不包含真实姓名、头像或截图。`classification`可加在页脚，`layout.conclusions_new_page`、`layout.discussion_page_break_before`可控制长篇分页。

## 交付检查

渲染DOCX至PDF后查看全部页面：字体真实嵌入、页边距、截断、表格、孤立标题、行拆分和留白；检查文本及任务未丢失、个人元数据未意外进入文件。模板通过不等于业务内容获确认，也不对审美质量作“世界第一”或认证承诺。
