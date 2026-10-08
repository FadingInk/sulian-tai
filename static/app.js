// 刷题交互逻辑：选择题点选判对 / 代码题输入判分 + 收藏/错题 + 进度
(function(){
  const Q = window.__QUESTIONS__;
  if(!Q || !Q.length) return;
  const MOD = window.__MODULE__;
  const FAV_ERR = window.__FAVERR__ || {};
  const LOGGED = !!window.__LOGIN__;
  let cur = 0, answered = false;

  const esc = s => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                          .replace(/"/g,'&quot;');

  function setActBtn(kind, on){
    const b = document.getElementById(kind==='fav'?'actFav':'actErr');
    if(!b) return;
    if(on){ b.classList.add('on'); b.textContent = kind==='fav' ? '⭐ 已收藏' : '✅ 已标记错题'; }
    else { b.classList.remove('on'); b.textContent = kind==='fav' ? '⭐ 收藏' : '❌ 错题'; }
  }

  function renderActions(){
    const s = (FAV_ERR[cur] || {});
    setActBtn('fav', !!s.fav);
    setActBtn('err', !!s.err);
  }

  const render = () => {
    const q = Q[cur];
    const fid = cur;
    document.getElementById('qNo').textContent = cur + 1;
    document.getElementById('qCount').textContent = (cur + 1) + ' / ' + Q.length;
    document.getElementById('qText').textContent = q.q;
    const box = document.getElementById('qOpts');
    const codeArea = document.getElementById('qCode');
    const isCode = q.type === 'code';
    document.getElementById('qType').textContent = isCode ? '【写代码】' : '【选择】';
    // 选择 / 代码输入区切换
    box.classList.toggle('hidden', isCode);
    codeArea.classList.toggle('hidden', !isCode);
    if(isCode){
      document.getElementById('datapath').textContent =
        '📁 数据路径：' + (q.datapath || 'D:\\dai_ma\\泰迪\\3 数据获取与处理\\shops_review');
      document.getElementById('codeInput').value = '';
    } else {
      box.innerHTML = '';
      q.options.forEach((opt, i) => {
        const el = document.createElement('div');
        el.className = 'opt';
        el.textContent = opt;
        el.onclick = () => pick(i, el, fid);
        box.appendChild(el);
      });
    }
    document.getElementById('feedback').innerHTML = '';
    document.getElementById('prev').disabled = cur === 0;
    document.getElementById('next').disabled = false;
    answered = false;
    renderActions();
  };

  // ---------- 选择题 ----------
  function pick(i, el, fid){
    if(answered) return;
    answered = true;
    const q = Q[fid];
    const opts = document.querySelectorAll('.opt');
    opts[i].classList.add(q.answer === i ? 'correct' : 'wrong');
    if(q.answer !== i){ opts[q.answer].classList.add('correct'); }
    const ok = q.answer === i;
    const fb = document.getElementById('feedback');
    fb.innerHTML =
      `<p class="${ok?'x':'t'}">${ok?'✅ 回答正确':'❌ 回答错误（绿色为正确答案）'}</p>` +
      `<p>🧾 解析：${esc(q.explain)}</p>` +
      `<p>💡 记忆技巧：${esc(q.tip)}</p>`;
    // 答错自动标记错题
    if(LOGGED && !ok){
      flip_remote('err', cur, true); FAV_ERR[cur]=Object.assign(FAV_ERR[cur]||{}, {err:true}); renderActions();
    }
    save(qid=fid, ok);
    refreshProgress();
  }

  // ---------- 代码题 ----------
  window.submitCode = function(){
    const q = Q[cur];
    const code = document.getElementById('codeInput').value;
    const fb = document.getElementById('feedback');
    fetch('/check_code', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({module: MOD, qid: cur, code: code})
    }).then(r=>r.json()).then(d=>{
      if(d.ok){
        if(d.passed){
          fb.innerHTML = `<p class="x">✅ 判分通过！关键 API 全写对了。</p>
            <p>💡 记忆技巧：${esc(d.tip)}</p>`;
          answered = true;
          refreshProgress();
        } else {
          const miss = d.missing.map(m=>'<code>'+esc(m)+'</code>').join(' ');
          fb.innerHTML = `<p class="t">❌ 还缺这些关键点（一个都不能少）：</p><p class="miss">${miss}</p>
            <details class="ans"><summary>查看参考答案</summary><pre>${esc(d.answer)}</pre>
            <p>🧾 解析：${esc(d.explain)}</p></details>`;
        }
      } else {
        fb.innerHTML = `<p class="t">${esc(d.msg||'出错了')}</p>`;
      }
    }).catch(e=>{
      fb.innerHTML = `<p class="t">提交失败，请重试。</p>`;
    });
  };

  // ---------- 收藏 / 错题 ----------
  function flip_remote(kind, fid, on){
    return fetch(`/flip/${MOD}/${fid}/${kind}`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({on: on})
    }).then(r=>r.json());
  }
  window.flip = function(kind){
    const s = FAV_ERR[cur] || (FAV_ERR[cur] = {});
    const now = !s[kind];
    if(!LOGGED){ alert('请先登录，才能收藏/标记错题'); return; }
    flip_remote(kind, cur, now).then(d=>{
      if(d.ok){ s[kind]=now; setActBtn(kind, now); }
      else alert(d.msg||'操作失败');
    });
  };

  function save(qid, ok){
    fetch('/submit', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({module: MOD, qid: qid, correct: ok})
    }).catch(()=>{});
  }

  function refreshProgress(){
    fetch('/progress/'+MOD).then(r=>r.json()).then(d=>{
      if(d.ok){
        const pct = Math.round(d.done/d.total*100)||0;
        const bar=document.querySelector('.prog-inner');
        if(bar){ bar.style.width = pct+'%'; }
        const t=document.getElementById('progTxt');
        if(t){ t.textContent = '已答对 '+d.done+' / '+d.total+'（'+pct+'%）'; }
      }
    }).catch(()=>{});
  }

  window.nav = (d) => {
    const nn = cur + d;
    if(nn<0 || nn>=Q.length) return;
    cur = nn;
    render();
  };
  render();
})();