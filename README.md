# 餐饮数据 · 快速掌握刷题网站

一个本地/在线都能跑的 Flask 小站，按"正确答案"做成互动刷题，
帮助短短几天里快速掌握这份作业，重点练好**数据获取与处理**。

## 三大模块
1. **① 数据库运行维护**（基础简单）：建库建表、COUNT/GROUP BY、存表、UPDATE/DELETE、易错日期。
2. **② 数据获取与处理**（⭐ 重点）：read_excel→拆列→删列→缺失填充→算综合评分→emoji/繁转简→分词→存csv 的整套流水线。
3. **③ 数据可视化**（简单可试）：直方图、双Y轴折柱、雷达图、词云 的模板题。
另外有「技巧方法」页（口诀、做题顺序、变题应对、易错点）。

## 功能
- 用户注册 / 登录，**答题进度按用户保存**（数据库 SQLite，文件 `users.db`）。
- 每模块有「知识速记卡」+ 逐题作答：选中立即判对错，显示**解析**和**记忆技巧**。
- 进度条实时刷新，可一键重置某模块进度。

## 本地运行
```bash
cd website
pip install flask
python app.py
# 浏览器打开 http://127.0.0.1:5000
```
> 未登录也能刷题，但登录后才记录并累计进度。

## 在线部署（任选一种）
- **Render / Railway**：项目里用 `python app.py`(或 gunicorn)启动，暴露 5000 端口即可。
- **PythonAnywhere**：上传本文件夹，用 WSGI 指向 `app`(app.py里的 Flask 实例)。
- **Replit**：Run `python app.py` → 得到公网地址，加群操作即可给别人刷。

## 目录
```
website/
├── app.py            # Flask 主程序（路由+登录+进度存储）
├── content.py        # 全部题目与知识卡（改这里加题/改题）
├── users.db          # 自动生成：用户+进度
├── templates/        # base/index/auth/module/tips
└── static/           # style.css + app.js
```
> 想加题/改考点：编辑 `content.py` 里的 `MODULES`（每模块 cards=速记卡、questions=题目）。
