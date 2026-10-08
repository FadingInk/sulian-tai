// 考试模拟：渲染随机试卷、选择题点选、代码题关键词判分、提交算分
(function(){
  const P = window.__PAPER__ || [];
  if(!P.length) return;
  const answers = P.map(() => ({ choice: null, code: '', checked: false }));
  const wrap = document.getElementById('paper');

  const esc = s => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  function render(){
    wrap.innerHTML = P.map((it, i) => {
      const [mid, qid, q] = it;
      const isCode = q.type === 'code';
      const opts = isCode ? '' :
        '<div class="ex-opts" data-i="'+i+'">' +
        q.options.map((o, oi) =>
          '<div class="opt" data-oi="'+oi+'" onclick="pickOpt('+i+','+oi+',this)">'+esc(o)+'</div>'
        ).join('') + '</div>';
      const codebox = isCode ?
        '<div class="code-hint">📁 数据路径：' + esc(q.datapath||'') + '</div>' +
        '<textarea id="cin-'+i+'" rows="4" spellcheck="false" placeholder="在这里写代码…"></textarea>' +
        '<button class="btn small" onclick="checkCode('+i+')">▶ 记分</button>' +
        '<span class="ex-check" id="chk-'+i+'"></span>' : '';
      return '<div class="exam-q" id="eq-'+i+'">' +
        '<div class="q-top"><span class="q-no">'+(i+1)+'</span>' +
        '<span class="q-type">'+(isCode?'【写代码】':'【选择】')+'</span></div>' +
        '<p class="q-text">'+esc(q.q)+'</p>' + opts + codebox +
        '<div class="ex-fb" id="fb-'+i+'"></div></div>';
    }).join('');
  }

  // 选择题
  window.pickOpt = function(i, oi, el){
    const box = el.parentElement;
    [...box.children].forEach(c=>c.classList.remove('correct','wrong'));
    box.children[oi].classList.add('correct');
    answers[i].choice = oi;
    answers[i].checked = true;
    updateDone();
  };

  // 代码题记分（关键词核对）
  window.checkCode = function(i){
    const [mid, qid, q] = P[i];
    const code = document.getElementById('cin-'+i).value;
    const missing = q.check_kw.filter(kw => code.indexOf(kw) < 0);
    const passed = !missing.length;
    answers[i].code = code;
    answers[i].checked = true;
    const fb = document.getElementById('fb-'+i);
    const chk = document.getElementById('chk-'+i);
    if(passed){
      chk.textContent = '✅ 已判定通过';
      fb.innerHTML = '<p class="x">通过</p>';
    } else {
      chk.textContent = '❌ 待补充';
      fb.innerHTML = '<p class="t">还缺：' + missing.map(m=>'<code>'+esc(m)+'</code>').join(' ') +
        '</p><details class="ans"><summary>参考答案</summary><pre>'+esc(q.answer)+'</pre></details>';
    }
    updateDone();
  };

  function updateDone(){
    const n = answers.filter(a=>a.checked).length;
    document.getElementById('exDone').textContent = '已答 ' + n + ' / ' + P.length;
  }

  // 判分：选择题比对 answer；代码题比对 check_kw
  window.grade = function(){
    let correct = 0;
    const lines = [];
    P.forEach((it, i) => {
      const [mid, qid, q] = it;
      const a = answers[i];
      let ok = false;
      if(q.type === 'choice'){
        ok = a.choice === q.answer;
      } else {
        ok = !q.check_kw.filter(kw => a.code.indexOf(kw) < 0).length;
      }
      if(ok) correct++;
      lines.push((ok?'✅':'❌') + ' 第'+(i+1)+'题' + (q.type==='choice' ? '' : ok?'':' · 参考见上方'));
    });
    const pct = Math.round(correct / P.length * 100);
    document.getElementById('result').classList.remove('hidden');
    document.getElementById('result').innerHTML =
      '<h2>得分：' + correct + ' / ' + P.length + '（' + pct + '%）</h2>' +
      '<div class="rv-item"><pre class="plain">' + lines.join('\n') + '</pre></div>' +
      '<p class="warn">' + (pct>=80?'🎉 掌握得不错，进错题本把没对的再刷一刷。' :
        pct>=60?'还可以，把做错的题标记进错题本重点复习。' :
        '别灰心，返回模块把写代码题亲手多敲几遍再重测。') + '</p>';
    document.getElementById('result').scrollIntoView({behavior:'smooth'});
  };

  render();
})();