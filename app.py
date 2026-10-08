# -*- coding: utf-8 -*-
"""
刷题平台（Flask）· 通用架构
==========================================
分层：落地方案(landing/ `/`) → 平台主页分类(hub/ `/hub`) → 分类详情(category)
      → 题集(set) → 模块刷题(module)。

平台层完全通用，不出现任何具体题目内容；每一份题目(题集)连同它的模块、
技巧方法、提升拓展、考试模拟都封装在题集内部。

运行：python app.py → 浏览器打开 http://127.0.0.1:5000
"""
import sqlite3, os, random
from flask import Flask, request, redirect, url_for, render_template, session, jsonify
from content import CATEGORIES, SETS

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "users.db")
app = Flask(__name__)
app.secret_key = "restaurant-quiz-2026"

# ---------- 通用索引 ----------
MODULES = []            # 全部模块
MOD_INDEX = {}          # mid -> module
QUESTION_INDEX = {}     # (mid, qid) -> question
ASSIGN = {}             # mid -> 所属题集
SET_INDEX = {}          # sid -> set
for s in SETS:
    SET_INDEX[s["id"]] = s
    for m in s["modules"]:
        MODULES.append(m)
        MOD_INDEX[m["id"]] = m
        ASSIGN[m["id"]] = s
        for i, q in enumerate(m["questions"]):
            QUESTION_INDEX[(m["id"], i)] = q
CAT_INDEX = {c["id"]: c for c in CATEGORIES}


def current_uid():
    """返回当前登录用户 id；未登录或会话用户已被删除则返回 None。"""
    name = session.get("user")
    if not name:
        return None
    row = get_user(name)
    return row["id"] if row else None


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS progress(
        user_id INTEGER, module TEXT, qid INTEGER, correct INTEGER,
        PRIMARY KEY(user_id, module, qid))""")
    c.execute("""CREATE TABLE IF NOT EXISTS collections(
        user_id INTEGER, module TEXT, qid INTEGER, kind TEXT,
        PRIMARY KEY(user_id, module, qid, kind))""")
    c.commit(); c.close()


def get_user(username):
    c = db(); row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    c.close(); return row


def module_stats(user_id, mod_id):
    c = db()
    done = c.execute("SELECT qid, correct FROM progress WHERE user_id=? AND module=?",
                     (user_id, mod_id)).fetchall()
    c.close()
    return {r["qid"]: bool(r["correct"]) for r in done}


def set_stats(user_id, s):
    total = sum(len(m["questions"]) for m in s["modules"])
    done = 0
    if user_id:
        for m in s["modules"]:
            done += sum(1 for v in module_stats(user_id, m["id"]).values() if v)
    return done, total


def collection_set(user_id, mod_id, qid, kind, on):
    c = db()
    if on:
        c.execute("INSERT OR IGNORE INTO collections(user_id,module,qid,kind) VALUES(?,?,?,?)",
                  (user_id, mod_id, int(qid), kind))
    else:
        c.execute("DELETE FROM collections WHERE user_id=? AND module=? AND qid=? AND kind=?",
                  (user_id, mod_id, int(qid), kind))
    c.commit(); c.close()


def collection_list(user_id, kind):
    c = db()
    rows = c.execute("SELECT module,qid FROM collections WHERE user_id=? AND kind=? ORDER BY module,qid",
                     (user_id, kind)).fetchall()
    c.close()
    items = []
    for r in rows:
        q = QUESTION_INDEX.get((r["module"], r["qid"]))
        if q:
            items.append({"module": r["module"], "qid": r["qid"], "q": q,
                          "mname": MOD_INDEX[r["module"]]["name"]})
    return items


# ---------- ① 入口：简单介绍页 ----------
@app.route("/")
def home():
    return render_template("landing.html", total_sets=len(SETS),
                           total_modules=len(MODULES),
                           cats=CATEGORIES)


# ---------- ② 平台主页：大分类 ----------
@app.route("/hub")
def hub():
    uid = current_uid()
    cats = []
    for c in CATEGORIES:
        total_q = sum(len(m["questions"]) for sid in c["set_ids"] for m in SET_INDEX[sid]["modules"])
        cats.append({**c, "qcount": total_q,
                     "set_count": len(c["set_ids"])})
    return render_template("hub.html", cats=cats, uid=uid)


# ---------- ③ 分类详情：题集列表 ----------
@app.route("/category/<cid>")
def category(cid):
    c = CAT_INDEX.get(cid)
    if not c:
        return "分类不存在", 404
    uid = current_uid()
    sets = []
    for sid in c["set_ids"]:
        s = SET_INDEX[sid]
        done, total = set_stats(uid, s)
        sets.append({**s, "done": done, "total": total,
                     "pct": round(done / total * 100) if total else 0,
                     "ccat": c["name"]})
    return render_template("category.html", c=c, sets=sets)


# ---------- ④ 题集详情：模块 + 题集内专属功能 ----------
@app.route("/set/<sid>")
def set_page(sid):
    s = SET_INDEX.get(sid)
    if not s:
        return "题集不存在", 404
    uid = current_uid()
    mods = []
    for m in s["modules"]:
        total = len(m["questions"]); done = 0
        if uid:
            done = sum(1 for v in module_stats(uid, m["id"]).values() if v)
        mods.append({"mod": m, "total": total, "done": done,
                     "pct": round(done / total * 100) if total else 0})
    cat = CAT_INDEX.get(next((c["id"] for c in CATEGORIES if sid in c["set_ids"]), None)) \
          or {"id": None, "name": "全部"}
    return render_template("set.html", s=s, mods=mods, cat=cat)


# ---------- 题集内：技巧方法 ----------
@app.route("/set/<sid>/tips")
def set_tips(sid):
    s = SET_INDEX.get(sid)
    if not s:
        return "题集不存在", 404
    return render_template("tips.html", s=s, tip_sections=s.get("tips", []), modules=s["modules"])


# ---------- 题集内：提升拓展 ----------
@app.route("/set/<sid>/extensions")
def set_extensions(sid):
    s = SET_INDEX.get(sid)
    if not s:
        return "题集不存在", 404
    return render_template("extensions.html", s=s, ext=s.get("extensions", []), modules=s["modules"])


# ---------- 题集内：错题本 & 收藏（整题集范围） ----------
@app.route("/set/<sid>/review")
def set_review(sid):
    if not session.get("user"):
        return redirect(url_for("login"))
    s = SET_INDEX.get(sid)
    if not s:
        return "题集不存在", 404
    mset = set(m["id"] for m in s["modules"])
    uid = current_uid()
    errors = [it for it in collection_list(uid, "err") if it["module"] in mset]
    favs = [it for it in collection_list(uid, "fav") if it["module"] in mset]
    return render_template("review.html", s=s, errors=errors, favs=favs)


# ---------- 模块刷题页 ----------
@app.route("/module/<mid>")
def module(mid):
    mod = MOD_INDEX.get(mid)
    if not mod:
        return "模块不存在", 404
    s = ASSIGN[mid]
    uid = current_uid()
    stats = module_stats(uid, mid) if uid else {}
    fav_err = {}
    if uid:
        c = db()
        rows = c.execute("SELECT module,qid,kind FROM collections WHERE user_id=?", (uid,)).fetchall()
        c.close()
        for r in rows:
            if r["module"] == mid:
                fav_err.setdefault(r["qid"], {})[r["kind"]] = True
    done = sum(1 for v in stats.values() if v)
    total = len(mod["questions"])
    done_pct = round(done / total * 100) if total else 0
    return render_template("module.html", mod=mod, s=s, stats=stats, total=total,
                           done=done, done_pct=done_pct, fav_err=fav_err)


# ---------- 保存进度 ----------
@app.route("/submit", methods=["POST"])
def submit():
    if not session.get("user"):
        return jsonify(ok=False, msg="请先登录")
    data = request.get_json()
    uid = current_uid()
    c = db()
    c.execute("INSERT OR REPLACE INTO progress(user_id,module,qid,correct) VALUES(?,?,?,?)",
              (uid, data["module"], int(data["qid"]), 1 if data["correct"] else 0))
    c.commit(); c.close()
    return jsonify(ok=True)


# ---------- 写代码题：关键词判分 ----------
@app.route("/check_code", methods=["POST"])
def check_code():
    data = request.get_json()
    q = QUESTION_INDEX.get((data["module"], int(data["qid"])))
    if not q or q.get("type") != "code":
        return jsonify(ok=False, msg="题目不存在")
    code = data.get("code", "")
    missing = [kw for kw in q.get("check_kw", []) if kw not in code]
    passed = not missing
    uid = current_uid()
    if uid and passed:
        c = db()
        c.execute("INSERT OR REPLACE INTO progress(user_id,module,qid,correct) VALUES(?,?,?,1)",
                  (uid, data["module"], int(data["qid"])))
        c.commit(); c.close()
    return jsonify(ok=True, passed=passed, missing=missing,
                   answer=q["answer"], explain=q["explain"], tip=q["tip"])


# ---------- 收藏 / 错题 ----------
@app.route("/flip/<mid>/<int:qid>/<kind>", methods=["POST"])
def flip(mid, qid, kind):
    if not session.get("user"):
        return jsonify(ok=False, msg="请先登录")
    data = request.get_json(True) or {}
    collection_set(current_uid(), mid, qid, kind, bool(data.get("on")))
    return jsonify(ok=True)


# ---------- 进度 API ----------
@app.route("/progress/<mid>")
def progress(mid):
    uid = current_uid()
    if not uid:
        return jsonify(ok=False)
    stats = module_stats(uid, mid)
    total = len(MOD_INDEX[mid]["questions"])
    done = sum(1 for v in stats.values() if v)
    return jsonify(ok=True, done=done, total=total)


# ---------- 考试模拟：随机抽题 ----------
@app.route("/exam/<sid>")
def exam(sid):
    s = SET_INDEX.get(sid)
    if not s:
        return "题集不存在", 404
    all_q = []
    for m in s["modules"]:
        for i, q in enumerate(m["questions"]):
            all_q.append((m["id"], i, q))
    random.shuffle(all_q)
    paper = all_q[:min(40, len(all_q))]
    return render_template("exam.html", s=s, paper=paper)


# ---------- 重置模块进度 ----------
@app.route("/reset/<mid>")
def reset(mid):
    uid = current_uid()
    if uid:
        c = db(); c.execute("DELETE FROM progress WHERE user_id=? AND module=?", (uid, mid))
        c.commit(); c.close()
    return redirect(url_for("module", mid=mid))


# ---------- 认证 ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = None
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        if not u or not p:
            msg = "用户名和密码不能为空"
        elif get_user(u):
            msg = "用户名已存在"
        else:
            c = db(); c.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, p))
            c.commit(); c.close()
            session["user"] = u
            return redirect(url_for("hub"))
    return render_template("auth.html", mode="注册", msg=msg)


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = None
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        row = get_user(u)
        if row and row["password"] == p:
            session["user"] = u
            return redirect(url_for("hub"))
        msg = "用户名或密码错误"
    return render_template("auth.html", mode="登录", msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)