/* ============================================================
   PaperMind Learning Engine · 演示前端
   ============================================================ */

(function () {

  // ------------------------------------------------------------------
  // 标签页切换
  // ------------------------------------------------------------------
  document.querySelectorAll('.tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-content').forEach(function (t) { t.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });

  // ------------------------------------------------------------------
  // API 辅助
  // ------------------------------------------------------------------
  var API_BASE = '';

  function apiGet(path, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', API_BASE + path, true);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.onload = function () {
      try { cb(null, JSON.parse(xhr.responseText), xhr.status); }
      catch (e) { cb(e, null, xhr.status); }
    };
    xhr.onerror = function () { cb(new Error('网络错误')); };
    xhr.send();
  }

  function apiPost(path, body, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', API_BASE + path, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.onload = function () {
      try { cb(null, JSON.parse(xhr.responseText), xhr.status); }
      catch (e) { cb(e, null, xhr.status); }
    };
    xhr.onerror = function () { cb(new Error('网络错误')); };
    xhr.send(JSON.stringify(body));
  }

  // ------------------------------------------------------------------
  // 工具函数
  // ------------------------------------------------------------------
  function formatJSON(obj) {
    try { return JSON.stringify(obj, null, 2); }
    catch (e) { return String(obj); }
  }

  function escapeHTML(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  // ------------------------------------------------------------------
  // 可折叠区块
  // ------------------------------------------------------------------
  function makeCollapsible(title, bodyHTML, defaultOpen) {
    var block = document.createElement('div');
    block.className = 'section-block';

    var header = document.createElement('div');
    header.className = 'section-header' + (defaultOpen === false ? ' collapsed' : '');
    header.innerHTML = '<span>' + escapeHTML(title) + '</span><span class="collapse-icon">&#9660;</span>';

    var body = document.createElement('div');
    body.className = 'section-body';
    body.innerHTML = bodyHTML;

    header.addEventListener('click', function () {
      header.classList.toggle('collapsed');
    });

    block.appendChild(header);
    block.appendChild(body);
    return block;
  }

  function renderList(items, emptyMsg) {
    if (!items || items.length === 0) {
      return '<span class="empty-message">' + escapeHTML(emptyMsg || '无') + '</span>';
    }
    return items.map(function (item) {
      return '<div class="list-item">' + escapeHTML(String(item)) + '</div>';
    }).join('');
  }

  // ------------------------------------------------------------------
  // 摘要卡片
  // ------------------------------------------------------------------
  function renderSummaryCards(cards) {
    var container = document.createElement('div');
    container.className = 'summary-cards';
    cards.forEach(function (c) {
      var cls = 'summary-card' + (c.modifier ? ' ' + c.modifier : '');
      container.innerHTML +=
        '<div class="' + cls + '">' +
          '<div class="card-value">' + escapeHTML(String(c.value)) + '</div>' +
          '<div class="card-label">' + escapeHTML(c.label) + '</div>' +
        '</div>';
    });
    return container.outerHTML;
  }

  // ------------------------------------------------------------------
  // 警告渲染
  // ------------------------------------------------------------------
  function renderWarnings(warnings) {
    if (!warnings || warnings.length === 0) return '';
    var html = '<div class="warnings-bar">';
    warnings.forEach(function (w) {
      var isError = w.indexOf('FAIL') !== -1;
      html += '<div class="warning-item ' + (isError ? 'error' : 'warn') + '">' +
        '<span class="w-icon">' + (isError ? '&#10060;' : '&#9888;') + '</span>' +
        '<span>' + escapeHTML(w) + '</span></div>';
    });
    html += '</div>';
    return html;
  }

  // ------------------------------------------------------------------
  // 处理日志
  // ------------------------------------------------------------------
  function renderProcessingLog(log) {
    if (!log || log.length === 0) return '';
    return log.map(function (line) {
      return '<div class="log-line">' + escapeHTML(line) + '</div>';
    }).join('');
  }

  // ==================================================================
  // TAB 1: 文章学习
  // ==================================================================

  var paperEditor = document.getElementById('paper-json-editor');
  var paperResults = document.getElementById('paper-results');
  var paperStatus = document.getElementById('paper-status');
  var btnLearn = document.getElementById('btn-learn-paper');
  var btnExportPaper = document.getElementById('btn-export-paper');
  var paperProjectId = document.getElementById('paper-project-id');
  var paperProjectDesc = document.getElementById('paper-project-desc');

  var lastPaperResult = null;

  // ------------------------------------------------------------------
  // PDF 上传
  // ------------------------------------------------------------------
  var uploadArea = document.getElementById('pdf-upload-area');
  var uploadPlaceholder = document.getElementById('upload-placeholder');
  var uploadProgress = document.getElementById('upload-progress');
  var uploadResult = document.getElementById('upload-result');
  var uploadFilename = document.getElementById('upload-filename');
  var uploadFilesize = document.getElementById('upload-filesize');
  var pdfFileInput = document.getElementById('pdf-file-input');
  var clearUpload = document.getElementById('btn-clear-upload');
  var pdfSourceHint = document.getElementById('pdf-source-hint');

  // 点击上传区域触发文件选择
  uploadArea.addEventListener('click', function (e) {
    if (e.target === clearUpload) return;
    if (uploadResult.style.display !== 'none') return;
    pdfFileInput.click();
  });

  // 拖拽支持
  uploadArea.addEventListener('dragover', function (e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });
  uploadArea.addEventListener('dragleave', function () {
    uploadArea.classList.remove('drag-over');
  });
  uploadArea.addEventListener('drop', function (e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      handlePDFFile(e.dataTransfer.files[0]);
    }
  });

  // 文件选择
  pdfFileInput.addEventListener('change', function () {
    if (pdfFileInput.files.length > 0) {
      handlePDFFile(pdfFileInput.files[0]);
    }
  });

  // 清除上传
  clearUpload.addEventListener('click', function () {
    uploadResult.style.display = 'none';
    uploadPlaceholder.style.display = 'block';
    pdfFileInput.value = '';
    pdfSourceHint.textContent = '或上传 PDF 自动填充';
  });

  function handlePDFFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      paperStatus.textContent = '请选择 PDF 文件';
      return;
    }

    // 显示进度
    uploadPlaceholder.style.display = 'none';
    uploadProgress.style.display = 'flex';
    uploadResult.style.display = 'none';
    paperStatus.textContent = '正在上传 ' + file.name + '...';

    var reader = new FileReader();
    reader.onload = function (e) {
      var arrayBuffer = e.target.result;
      var bytes = new Uint8Array(arrayBuffer);
      var binary = '';
      for (var i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      var base64 = btoa(binary);

      apiPost('/api/paper/upload-pdf', {
        filename: file.name,
        data: base64
      }, function (err, data, status) {
        uploadProgress.style.display = 'none';
        if (err || data.error) {
          uploadPlaceholder.style.display = 'block';
          paperStatus.textContent = 'PDF 解析失败: ' + (data ? data.error : err);
          return;
        }

        // 显示上传结果
        uploadResult.style.display = 'flex';
        uploadFilename.textContent = file.name;
        uploadFilesize.textContent = formatFileSize(file.size);
        pdfSourceHint.textContent = '已从 PDF 提取文本（' + (data.text_length || 0) + ' 字符）';

        // 填充 JSON 编辑器
        var paperJson = {
          paper_id: data.paper_id,
          title: data.title || file.name.replace('.pdf', ''),
          full_text: data.full_text,
          authors: data.authors || [],
        };

        // 移除 article title 等无关前缀
        paperEditor.value = formatJSON(paperJson);
        paperStatus.textContent = 'PDF 解析完成，请检查并点击「学习文章」';
      });
    };
    reader.readAsArrayBuffer(file);
  }

  // ------------------------------------------------------------------
  // 学习按钮
  // ------------------------------------------------------------------
  btnLearn.addEventListener('click', function () {
    var jsonStr = paperEditor.value.trim();
    if (!jsonStr) {
      paperStatus.textContent = '请填入文章 JSON';
      return;
    }

    var paperObj;
    try { paperObj = JSON.parse(jsonStr); }
    catch (e) {
      paperStatus.textContent = 'JSON 格式错误: ' + e.message;
      return;
    }

    btnLearn.disabled = true;
    paperStatus.innerHTML = '<span class="spinner"></span> 正在学习...';

    var requestBody = {
      paper: paperObj,
      project_context: {
        project_id: paperProjectId.value || 'demo_project',
        project_description: paperProjectDesc.value || ''
      }
    };

    apiPost('/api/paper/learn', requestBody, function (err, data, status) {
      btnLearn.disabled = false;
      if (err) {
        paperStatus.textContent = '网络错误';
        paperResults.innerHTML = '<div class="placeholder">错误: ' + escapeHTML(err.message) + '</div>';
        return;
      }
      if (status !== 200 || data.error) {
        paperStatus.textContent = '出错';
        paperResults.innerHTML = '<div class="placeholder">' + escapeHTML(data.error || '未知错误') + '</div>';
        return;
      }

      paperStatus.textContent = '完成。';
      lastPaperResult = data;
      btnExportPaper.disabled = false;
      renderPaperResults(data);
    });
  });

  function renderPaperResults(r) {
    var html = '';

    // 警告
    html += renderWarnings(r.warnings || []);

    // 摘要卡片
    html += renderSummaryCards([
      { label: '质量分', value: (r.quality_score || 0).toFixed(3), modifier: r.quality_score >= 0.5 ? 'success' : 'warn' },
      { label: '相关分', value: (r.project_relevance_score || 0).toFixed(3), modifier: 'neutral' },
      { label: '实验设计', value: (r.experiment_design_patterns || []).length, modifier: 'success' },
      { label: '信号机制', value: (r.mechanism_patterns || []).length, modifier: 'success' },
      { label: '图表逻辑', value: (r.figure_logic_patterns || []).length, modifier: 'neutral' },
      { label: '写作模式', value: (r.writing_patterns || []).length, modifier: 'neutral' },
      { label: '可复用洞察', value: (r.reusable_insights || []).length, modifier: 'success' },
      { label: '警告数', value: (r.warnings || []).length, modifier: (r.warnings || []).length > 0 ? 'warn' : 'success' },
    ]);

    // 实验设计模式
    html += makeCollapsible('实验设计模式（' + (r.experiment_design_patterns || []).length + '）', renderPatternsTable(r.experiment_design_patterns || [], [
      'research_question', 'hypothesis', 'experimental_models', 'groups', 'interventions',
      'doses_or_concentrations', 'timepoints', 'assays', 'controls', 'statistical_methods',
      'validation_chain', 'strengths', 'limitations'
    ])).outerHTML;

    // 信号机制
    html += makeCollapsible('信号机制模式（' + (r.mechanism_patterns || []).length + '）', renderPatternsTable(r.mechanism_patterns || [], [
      'pathway', 'targets', 'upstream_factors', 'downstream_readouts',
      'evidence_types', 'claim_strength', 'limitations'
    ])).outerHTML;

    // 图表逻辑
    html += makeCollapsible('图表逻辑模式（' + (r.figure_logic_patterns || []).length + '）', renderPatternsTable(r.figure_logic_patterns || [], [
      'figure_id', 'figure_role', 'data_type', 'key_message', 'supports_which_claim', 'reusable_figure_idea'
    ])).outerHTML;

    // 写作模式
    html += makeCollapsible('写作模式（' + (r.writing_patterns || []).length + '）', renderPatternsTable(r.writing_patterns || [], [
      'introduction_logic', 'result_narrative', 'discussion_logic',
      'novelty_framing', 'limitation_framing', 'application_framing', 'reusable_sentences_or_templates'
    ])).outerHTML;

    // 可复用洞察
    html += makeCollapsible('可复用研究洞察（' + (r.reusable_insights || []).length + '）', renderInsightsTable(r.reusable_insights || []), true).outerHTML;

    // 推荐记忆记录
    html += makeCollapsible('推荐记忆记录（' + (r.recommended_memory_records || []).length + '）',
      '<pre class="raw-json">' + escapeHTML(formatJSON(r.recommended_memory_records || [])) + '</pre>', false).outerHTML;

    // 推荐证据边
    html += makeCollapsible('推荐证据边（' + (r.recommended_evidence_edges || []).length + '）',
      '<pre class="raw-json">' + escapeHTML(formatJSON(r.recommended_evidence_edges || [])) + '</pre>', false).outerHTML;

    // 处理日志
    html += makeCollapsible('处理日志', renderProcessingLog(r.processing_log || []), false).outerHTML;

    // 原始 JSON
    html += makeCollapsible('原始 JSON', '<pre class="raw-json">' + escapeHTML(formatJSON(r)) + '</pre>', false).outerHTML;

    paperResults.innerHTML = html;
  }

  function renderPatternsTable(patterns, fields) {
    if (!patterns || patterns.length === 0) {
      return '<span class="empty-message">未提取到模式。</span>';
    }
    var html = '';
    patterns.forEach(function (p, idx) {
      if (idx > 0) html += '<hr style="border:none;border-top:1px solid var(--c-border);margin:8px 0;">';
      html += '<table>';
      fields.forEach(function (f) {
        var val = p[f];
        if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) return;
        html += '<tr><td class="field-label">' + escapeHTML(f.replace(/_/g, ' ')) + '</td><td>';
        if (Array.isArray(val)) {
          html += renderList(val);
        } else {
          html += escapeHTML(String(val));
        }
        html += '</td></tr>';
      });
      html += '</table>';
    });
    return html;
  }

  function renderInsightsTable(insights) {
    if (!insights || insights.length === 0) {
      return '<span class="empty-message">未生成洞察。</span>';
    }
    var html = '<table><thead><tr><th>类型</th><th>内容</th><th>意义</th><th>适用分</th></tr></thead><tbody>';
    insights.forEach(function (ins) {
      html += '<tr>' +
        '<td>' + escapeHTML(ins.insight_type || '—') + '</td>' +
        '<td>' + escapeHTML((ins.content || '').substring(0, 150)) + '</td>' +
        '<td>' + escapeHTML((ins.why_it_matters || '').substring(0, 80)) + '</td>' +
        '<td>' + escapeHTML((ins.applicability_score || 0).toFixed(2)) + '</td>' +
        '</tr>';
    });
    html += '</tbody></table>';
    return html;
  }

  // 导出
  btnExportPaper.addEventListener('click', function () {
    if (!lastPaperResult) return;
    apiPost('/api/export', {
      name: 'paper_learning_result.json',
      content: lastPaperResult
    }, function (err, data) {
      if (err || data.error) {
        paperStatus.textContent = '导出失败: ' + (data ? data.error : err);
        return;
      }
      paperStatus.textContent = '已导出: ' + data.path;
    });
  });

  // ==================================================================
  // TAB 2: 记忆巩固
  // ==================================================================

  var sleepEditor = document.getElementById('sleep-json-editor');
  var sleepResults = document.getElementById('sleep-results');
  var sleepStatus = document.getElementById('sleep-status');
  var btnSleep = document.getElementById('btn-run-sleep');
  var btnExportSleep = document.getElementById('btn-export-sleep');

  var lastSleepResult = null;

  btnSleep.addEventListener('click', function () {
    var jsonStr = sleepEditor.value.trim();
    if (!jsonStr) {
      sleepStatus.textContent = '请填入 ConsolidationInput JSON';
      return;
    }

    var inputObj;
    try { inputObj = JSON.parse(jsonStr); }
    catch (e) {
      sleepStatus.textContent = 'JSON 格式错误: ' + e.message;
      return;
    }

    btnSleep.disabled = true;
    sleepStatus.innerHTML = '<span class="spinner"></span> 正在运行记忆巩固...';

    apiPost('/api/sleep-cycle', inputObj, function (err, data, status) {
      btnSleep.disabled = false;
      if (err) {
        sleepStatus.textContent = '网络错误';
        sleepResults.innerHTML = '<div class="placeholder">错误: ' + escapeHTML(err.message) + '</div>';
        return;
      }
      if (status !== 200 || data.error) {
        sleepStatus.textContent = '出错';
        sleepResults.innerHTML = '<div class="placeholder">' + escapeHTML(data.error || '未知错误') + '</div>';
        return;
      }

      sleepStatus.textContent = '完成。';
      lastSleepResult = data;
      btnExportSleep.disabled = false;
      renderSleepResults(data);
    });
  });

  function renderSleepResults(r) {
    var html = '';

    // 警告
    html += renderWarnings(r.warnings || []);

    // 摘要卡片
    var promoted = (r.promoted_memories || []).length;
    var archived = (r.archived_memories || []).length;
    var superseded = (r.superseded_memories || []).length;
    var patterns = (r.new_research_patterns || []).length;
    var edges = (r.new_evidence_edges || []).length;
    var queries = (r.recommended_literature_queries || []).length;

    html += renderSummaryCards([
      { label: '提升记忆', value: promoted, modifier: 'success' },
      { label: '归档记忆', value: archived, modifier: 'warn' },
      { label: '取代记忆', value: superseded, modifier: 'danger' },
      { label: '新模式', value: patterns, modifier: 'success' },
      { label: '证据边', value: edges, modifier: 'neutral' },
      { label: '文献查询', value: queries, modifier: 'neutral' },
    ]);

    // 提升记忆
    html += makeCollapsible('提升记忆（' + promoted + '）', renderMemoryTable(r.promoted_memories || []), true).outerHTML;

    // 归档记忆
    html += makeCollapsible('归档记忆（' + archived + '）', renderMemoryTable(r.archived_memories || []), false).outerHTML;

    // 取代记忆
    html += makeCollapsible('取代记忆（' + superseded + '）', renderMemoryTable(r.superseded_memories || []), false).outerHTML;

    // 更新后的项目摘要
    html += makeCollapsible('更新后的项目摘要',
      '<div style="white-space:pre-wrap;font-size:13px;">' + escapeHTML(r.updated_project_summary || '未生成摘要。') + '</div>', true).outerHTML;

    // 推荐文献查询
    if (queries > 0) {
      html += makeCollapsible('推荐文献查询（' + queries + '）',
        renderList(r.recommended_literature_queries), true).outerHTML;
    }

    // 推荐用户操作
    var actions = r.recommended_user_actions || [];
    if (actions.length > 0) {
      html += makeCollapsible('推荐用户操作（' + actions.length + '）',
        renderList(actions), true).outerHTML;
    }

    // 处理日志
    html += makeCollapsible('处理日志', renderProcessingLog(r.processing_log || []), false).outerHTML;

    // 原始 JSON
    html += makeCollapsible('原始 JSON', '<pre class="raw-json">' + escapeHTML(formatJSON(r)) + '</pre>', false).outerHTML;

    sleepResults.innerHTML = html;
  }

  function renderMemoryTable(memories) {
    if (!memories || memories.length === 0) {
      return '<span class="empty-message">无记忆记录。</span>';
    }
    var html = '<table><thead><tr><th>ID</th><th>内容</th><th>类型</th><th>评分</th><th>状态</th></tr></thead><tbody>';
    memories.forEach(function (m) {
      html += '<tr>' +
        '<td style="font-family:var(--font-mono);font-size:11px;">' + escapeHTML(m.memory_id || '—') + '</td>' +
        '<td>' + escapeHTML((m.content || '').substring(0, 100)) + '</td>' +
        '<td>' + escapeHTML(m.memory_type || '—') + '</td>' +
        '<td>' + escapeHTML((m.health_score || 0).toFixed(3)) + '</td>' +
        '<td>' + escapeHTML(m.status || '—') + '</td>' +
        '</tr>';
    });
    html += '</tbody></table>';
    return html;
  }

  // 导出
  btnExportSleep.addEventListener('click', function () {
    if (!lastSleepResult) return;
    apiPost('/api/export', {
      name: 'sleep_cycle_result.json',
      content: lastSleepResult
    }, function (err, data) {
      if (err || data.error) {
        sleepStatus.textContent = '导出失败: ' + (data ? data.error : err);
        return;
      }
      sleepStatus.textContent = '已导出: ' + data.path;
    });
  });

})();
