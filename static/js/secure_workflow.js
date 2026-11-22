(function () {
  'use strict';

  function byId(id) { return document.getElementById(id); }

  var root = byId('secure-workflow');
  if (!root) return;

  var uploadUrl = root.getAttribute('data-upload-url') || '/api/app/upload-zip/';
  var demoUrl = root.getAttribute('data-demo-url') || '/api/app/upload-demo-zip/';
  var inspectUrl = root.getAttribute('data-inspect-url') || '/api/app/dataset-inspect/';
  var confirmUrl = root.getAttribute('data-confirm-url') || '/api/app/dataset-allocation-confirm/';
  var sceneHost = byId('dt3d-stage');
  var sceneUrl = sceneHost ? sceneHost.getAttribute('data-scene-url') : '/api/digital-twin/scene/';
  var operations = byId('dt3d-operations');

  var SCREENS = ['upload', 'analysis', 'dataset', 'allocation', 'network', 'scheduling', 'transfer', 'security', 'attack', 'failover', 'report'];
  var DEMO_STEPS = [
    { screen: 'upload', message: 'Dataset upload screen' },
    { screen: 'analysis', message: 'ZIP validation' },
    { screen: 'analysis', message: 'Extraction and dataset analysis' },
    { screen: 'dataset', message: 'Dataset tree visualization' },
    { screen: 'dataset', message: 'Dataset statistics' },
    { screen: 'allocation', message: 'Storage partitioning plan' },
    { screen: 'allocation', message: 'Storage allocation confirmation' },
    { screen: 'network', message: 'Return to 3D network' },
    { screen: 'scheduling', message: 'GA scheduling decision' },
    { screen: 'transfer', message: 'File-transfer state' },
    { screen: 'report', message: 'Storage confirmation' },
    { screen: 'security', message: 'Protection policy visualization' },
    { screen: 'attack', message: 'Simulated attack against one resource' },
    { screen: 'failover', message: 'Resource isolation and defensive response' },
    { screen: 'failover', message: 'Scheduler re-evaluation' },
    { screen: 'report', message: 'Final task and storage status' }
  ];

  var state = {
    step: 0,
    demoIndex: 0,
    demoPlaying: false,
    demoTimer: 0,
    demoSpeed: 1,
    reportId: '',
    inspect: null,
    scene: null,
    file: null,
    collapsed: {},
    selectedNode: null,
    graphSearch: '',
    graphScale: 1,
    graphOffset: { x: 0, y: 0 },
    graphPan: null
  };

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function text(value, fallback) {
    return value === null || value === undefined || value === '' ? (fallback || 'Unknown') : String(value);
  }

  function formatBytes(value) {
    if (value === null || value === undefined || value === '') return 'Unknown';
    var number = Number(value);
    if (!isFinite(number) || number < 0) return 'Unknown';
    var units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var index = 0;
    while (number >= 1024 && index < units.length - 1) {
      number /= 1024;
      index += 1;
    }
    var digits = index === 0 ? 0 : number >= 100 ? 0 : number >= 10 ? 1 : 2;
    return number.toFixed(digits) + ' ' + units[index];
  }

  function getCookie(name) {
    var parts = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < parts.length; i += 1) {
      var part = parts[i].trim();
      if (part.indexOf(name + '=') === 0) return decodeURIComponent(part.slice(name.length + 1));
    }
    return '';
  }

  function requestHeaders() {
    return {
      'Accept': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    };
  }

  function postForm(url, data) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: requestHeaders(),
      body: data
    }).then(function (response) {
      return response.json().catch(function () { throw new Error('HTTP ' + response.status); });
    });
  }

  function setStatus(id, message, isSimulated) {
    var node = byId(id);
    if (!node) return;
    node.textContent = message;
    if (id === 'swf-mode-badge') node.classList.toggle('is-simulated', !!isSimulated);
  }

  function showOperations(visible) {
    if (!operations) return;
    operations.hidden = !visible;
    if (visible) {
      window.requestAnimationFrame(function () { window.dispatchEvent(new Event('resize')); });
      operations.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
  }

  function showStep(index) {
    state.step = Math.max(0, Math.min(SCREENS.length - 1, index));
    Array.prototype.forEach.call(root.querySelectorAll('[data-swf-screen]'), function (screen) {
      screen.hidden = screen.getAttribute('data-swf-screen') !== SCREENS[state.step];
    });
    Array.prototype.forEach.call(root.querySelectorAll('[data-swf-step]'), function (button) {
      if (button.getAttribute('data-swf-step') === SCREENS[state.step]) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
    if (state.step >= 4) showOperations(true);
    if (state.step === 3) renderAllocation();
    if (state.step === 7) renderSecurityLayers();
    if (state.step === 8) populateAttackScenarios();
  }

  function showDemoStep(index) {
    state.demoIndex = Math.max(0, Math.min(DEMO_STEPS.length - 1, index));
    var definition = DEMO_STEPS[state.demoIndex];
    showStep(SCREENS.indexOf(definition.screen));
    var jump = byId('swf-step-jump');
    if (jump) jump.value = String(state.demoIndex);
    setStatus('swf-final-report', 'Demonstration step ' + (state.demoIndex + 1) + ' / ' + DEMO_STEPS.length + ': ' + definition.message);
  }

  function populateStepJump() {
    var jump = byId('swf-step-jump');
    if (!jump || jump.options.length) return;
    DEMO_STEPS.forEach(function (definition, index) {
      var option = document.createElement('option');
      option.value = String(index);
      option.textContent = String(index + 1).padStart(2, '0') + '. ' + definition.message;
      jump.appendChild(option);
    });
  }

  function startDemo() {
    stopDemoTimer();
    state.demoPlaying = true;
    var play = byId('swf-play');
    if (play) play.setAttribute('aria-pressed', 'true');
    showDemoStep(0);
  }

  function stopDemoTimer() {
    if (state.demoTimer) window.clearInterval(state.demoTimer);
    state.demoTimer = 0;
  }

  function pauseDemo() {
    state.demoPlaying = false;
    stopDemoTimer();
    var play = byId('swf-play');
    var pause = byId('swf-pause');
    if (play) play.setAttribute('aria-pressed', 'false');
    if (pause) pause.setAttribute('aria-pressed', 'true');
  }

  function scheduleDemoTimer() {
    stopDemoTimer();
    if (!state.demoPlaying) return;
    state.demoTimer = window.setInterval(function () {
      if (state.demoIndex >= DEMO_STEPS.length - 1) {
        pauseDemo();
        return;
      }
      showDemoStep(state.demoIndex + 1);
    }, 8000 / state.demoSpeed);
  }

  function updateFileSelection(file) {
    state.file = file || null;
    setStatus('swf-file-name', file ? file.name : 'None');
    setStatus('swf-file-size', file ? formatBytes(file.size) : 'Unknown');
    setStatus('swf-upload-status', file ? 'Ready to upload ' + file.name : 'Waiting for a ZIP archive.');
  }

  function uploadSelectedFile() {
    if (!state.file) {
      setStatus('swf-upload-status', 'Choose a .zip file first.');
      return;
    }
    var mode = byId('swf-mode').value;
    var form = new FormData();
    form.append('file', state.file);
    form.append('execution_mode', mode);
    var progress = byId('swf-progress');
    var fill = byId('swf-progress-fill');
    var button = byId('swf-upload');
    button.disabled = true;
    setStatus('swf-upload-status', 'Uploading and analyzing ' + state.file.name + '...');
    var xhr = new XMLHttpRequest();
    xhr.open('POST', uploadUrl, true);
    var headers = requestHeaders();
    delete headers['Content-Type'];
    Object.keys(headers).forEach(function (key) { xhr.setRequestHeader(key, headers[key]); });
    xhr.upload.onprogress = function (event) {
      if (!event.lengthComputable) return;
      var value = Math.round(event.loaded / event.total * 100);
      if (fill) fill.style.width = value + '%';
      if (progress) progress.setAttribute('aria-valuenow', String(value));
    };
    xhr.onload = function () {
      button.disabled = false;
      var result = null;
      try { result = JSON.parse(xhr.responseText); } catch (error) { result = null; }
      if (!result || !result.success) {
        var message = result && result.error ? result.error : 'Upload failed (HTTP ' + xhr.status + ').';
        setStatus('swf-upload-status', message);
        return;
      }
      handleUploadResult(result);
    };
    xhr.onerror = function () {
      button.disabled = false;
      setStatus('swf-upload-status', 'Upload request failed.');
    };
    xhr.send(form);
  }

  function loadDemoArchive() {
    var packageName = byId('swf-demo-package').value;
    var mode = byId('swf-mode').value;
    var form = new FormData();
    form.append('package', packageName);
    form.append('execution_mode', mode);
    setStatus('swf-upload-status', 'Loading bundled archive ' + packageName + '...');
    postForm(demoUrl, form).then(function (result) {
      if (!result.success) throw new Error(result.error || 'Demo upload failed.');
      handleUploadResult(result);
    }).catch(function (error) {
      setStatus('swf-upload-status', error.message);
    });
  }

  function handleUploadResult(result) {
    state.reportId = result.report_id || '';
    renderAnalysis(result);
    showStep(1);
    setStatus('swf-upload-status', 'Upload and analysis completed. Report ' + state.reportId + ' is available.');
    if (state.reportId) fetchInspect(state.reportId);
  }

  function renderAnalysis(result) {
    var stages = byId('swf-analysis-stages');
    if (stages) {
      stages.textContent = '';
      (result.stages || []).forEach(function (stage) {
        var li = document.createElement('li');
        li.textContent = stage.name + ': ' + stage.status + (stage.message ? ' — ' + stage.message : '');
        stages.appendChild(li);
      });
      if (!result.stages || !result.stages.length) {
        var empty = document.createElement('li');
        empty.textContent = 'No stage details were returned by the backend.';
        stages.appendChild(empty);
      }
    }
    var summary = result.summary || {};
    var destinations = summary.destinations || {};
    var parts = [
      'Archive: ' + text(summary.file_name, 'Not available'),
      'Files discovered: ' + text(summary.total_files, 'Unknown'),
      'Extracted size: ' + formatBytes(summary.total_uncompressed_bytes),
      'Execution mode: ' + text(summary.execution_mode, 'Unknown'),
      'Local: ' + text(destinations.LOCAL_STORAGE && destinations.LOCAL_STORAGE.count, 'Unknown') + ' files',
      'MEC: ' + text(destinations.MEC_STORAGE && destinations.MEC_STORAGE.count, 'Unknown') + ' files',
      'Cloud: ' + text(destinations.CLOUD_STORAGE && destinations.CLOUD_STORAGE.count, 'Unknown') + ' files'
    ];
    if (result.stages && result.stages.some(function (stage) { return stage.status === 'FAILED'; })) {
      parts.push('Validation or analysis failed; storage allocation was not continued.');
    }
    setStatus('swf-analysis-summary', parts.join(' · '));
  }

  function fetchInspect(reportId) {
    return fetch(inspectUrl + '?report_id=' + encodeURIComponent(reportId), {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' }
    }).then(function (response) { return response.json(); }).then(function (result) {
      if (!result.success) throw new Error(result.error || 'Dataset inspection failed.');
      state.inspect = result;
      state.collapsed = {};
      state.selectedNode = null;
      state.graphScale = 1;
      state.graphOffset = { x: 0, y: 0 };
      renderDataset();
      renderAllocation();
      renderSecurityLayers();
      renderFinalReport();
      populateAttackScenarios();
      return result;
    }).catch(function (error) {
      setStatus('swf-analysis-summary', error.message);
      setStatus('swf-allocation-summary', error.message);
    });
  }

  function treeMatches(node, term) {
    if (!term) return true;
    if ((node.name || '').toLowerCase().indexOf(term) !== -1) return true;
    return (node.children || []).some(function (child) { return treeMatches(child, term); });
  }

  function renderTreeNode(node, term) {
    if (!treeMatches(node, term)) return '';
    var isBranch = node.type === 'folder' || node.type === 'group';
    var collapsed = !!state.collapsed[node.id];
    var label = node.name + (node.size !== undefined && node.size !== null ? ' · ' + formatBytes(node.size) : '');
    var selected = state.selectedNode === node.id ? ' is-selected' : '';
    var html = '<li><button type="button" data-tree-node="' + esc(node.id) + '" class="' + selected + '">'
      + (isBranch ? (collapsed ? '▸ ' : '▾ ') : '• ') + esc(label) + '</button>';
    if (isBranch && !collapsed && node.children && node.children.length) {
      html += '<ul>';
      node.children.forEach(function (child) { html += renderTreeNode(child, term); });
      html += '</ul>';
    }
    return html + '</li>';
  }

  function renderDataset() {
    if (!state.inspect) return;
    var term = (byId('swf-tree-search').value || '').trim().toLowerCase();
    var tree = byId('swf-tree');
    tree.innerHTML = '<ul>' + renderTreeNode(state.inspect.tree, term) + '</ul>';
    renderStats();
    renderGraph();
  }

  function findGraphNode(id) {
    if (!state.inspect) return null;
    for (var i = 0; i < state.inspect.graph_nodes.length; i += 1) {
      if (state.inspect.graph_nodes[i].id === id) return state.inspect.graph_nodes[i];
    }
    return null;
  }

  function graphVisible(node) {
    var parent = node.parent;
    while (parent) {
      if (state.collapsed[parent]) return false;
      var parentNode = findGraphNode(parent);
      parent = parentNode ? parentNode.parent : null;
    }
    return true;
  }

  function renderGraph() {
    if (!state.inspect) return;
    var viewport = byId('swf-graph-viewport');
    if (!viewport) return;
    var nodes = state.inspect.graph_nodes.filter(graphVisible);
    var byParent = {};
    nodes.forEach(function (node) {
      var key = node.parent || 'root-parent';
      byParent[key] = byParent[key] || [];
      byParent[key].push(node);
    });
    var positions = {};
    nodes.forEach(function (node) {
      if (node.id === 'root') {
        positions[node.id] = { x: 380, y: 210 };
        return;
      }
      var parent = node.parent ? positions[node.parent] || { x: 380, y: 210 } : { x: 380, y: 210 };
      var siblings = byParent[node.parent || 'root-parent'] || [];
      var index = siblings.indexOf(node);
      var radius = node.depth <= 1 ? 150 : 70;
      var angle = (index / Math.max(1, siblings.length)) * Math.PI * 2 - Math.PI / 2;
      positions[node.id] = {
        x: Math.max(40, Math.min(720, parent.x + Math.cos(angle) * radius)),
        y: Math.max(35, Math.min(385, parent.y + Math.sin(angle) * radius))
      };
    });
    var search = state.graphSearch.toLowerCase();
    var html = '';
    state.inspect.graph_edges.forEach(function (edge) {
      var a = positions[edge.from];
      var b = positions[edge.to];
      if (!a || !b) return;
      html += '<line x1="' + a.x + '" y1="' + a.y + '" x2="' + b.x + '" y2="' + b.y + '" stroke="#94a3b8" stroke-width="1.2"/>';
    });
    nodes.forEach(function (node) {
      var point = positions[node.id];
      if (!point) return;
      var match = search && (node.name || '').toLowerCase().indexOf(search) !== -1;
      var selected = state.selectedNode === node.id;
      var fill = node.type === 'root' ? '#0c4a6e' : node.type === 'folder' ? '#0369a1' : node.type === 'group' ? '#7c3aed' : '#0f766e';
      html += '<g class="swf-graph-node' + (match ? ' is-match' : '') + '" data-graph-node="' + esc(node.id) + '" transform="translate(' + point.x + ',' + point.y + ')" style="cursor:pointer">'
        + '<circle r="' + (node.type === 'root' ? 20 : 13) + '" fill="' + fill + '" stroke="' + (selected || match ? '#f59e0b' : '#ffffff') + '" stroke-width="' + (selected || match ? 3 : 1.5) + '"/>'
        + '<text y="-' + (node.type === 'root' ? 26 : 19) + '" text-anchor="middle" font-size="10" fill="#0f172a">' + esc(String(node.name).slice(0, 20)) + '</text>'
        + '</g>';
    });
    viewport.setAttribute('transform', 'translate(' + state.graphOffset.x + ',' + state.graphOffset.y + ') scale(' + state.graphScale + ')');
    viewport.innerHTML = html;
  }

  function selectNode(id) {
    state.selectedNode = id;
    var node = findGraphNode(id);
    if (!node) return;
    var details = [
      'Name: ' + node.name,
      'Type: ' + node.type,
      'Path: ' + (node.path || 'root'),
      'Size: ' + formatBytes(node.size)
    ];
    var treeNode = null;
    function searchTree(item) {
      if (item.id === id) treeNode = item;
      (item.children || []).forEach(searchTree);
    }
    if (state.inspect) searchTree(state.inspect.tree);
    if (treeNode) {
      details.push('Policy: ' + text(treeNode.privacy_policy, 'Unknown'));
      details.push('Destination: ' + text(treeNode.selected_destination, 'Unknown'));
    }
    setStatus('swf-selection', details.join(' · '));
    renderDataset();
  }

  function renderStats() {
    if (!state.inspect) return;
    var stats = state.inspect.stats || {};
    var html = '';
    html += '<div class="swf-stat"><span>Total files</span><strong>' + esc(text(stats.total_files, 'Unknown')) + '</strong></div>';
    html += '<div class="swf-stat"><span>Total folders</span><strong>' + esc(text(stats.total_folders, 'Unknown')) + '</strong></div>';
    html += '<div class="swf-stat"><span>Total size</span><strong>' + esc(formatBytes(stats.total_size_bytes)) + '</strong></div>';
    html += '<div class="swf-stat"><span>Metadata files</span><strong>' + esc(text(stats.metadata_files, 'Unknown')) + '</strong></div>';
    html += '<div class="swf-stat"><span>File formats</span><ul>'
      + (stats.formats || []).map(function (item) { return '<li>' + esc(item.name) + ': ' + esc(item.count) + '</li>'; }).join('')
      + '</ul></div>';
    html += '<div class="swf-stat"><span>Recorded categories</span><ul>'
      + (stats.categories || []).map(function (item) { return '<li>' + esc(item.name) + ': ' + esc(item.count) + '</li>'; }).join('')
      + '</ul></div>';
    html += '<div class="swf-stat"><span>Largest files</span><ul>'
      + (stats.largest_files || []).map(function (item) { return '<li>' + esc(item.name) + ': ' + esc(item.size_formatted) + '</li>'; }).join('')
      + '</ul></div>';
    html += '<div class="swf-stat"><span>Classification method</span><strong>' + esc(text(stats.category_method, 'Not available')) + '</strong></div>';
    byId('swf-stats').innerHTML = html;
  }

  function renderAllocation() {
    if (!state.inspect) return;
    var allocation = state.inspect.allocation || {};
    setStatus('swf-allocation-label', allocation.label || 'No allocation plan loaded.');
    var total = (state.inspect.stats || {}).total_size_bytes || 0;
    var proposed = allocation.proposed || {};
    var tiers = allocation.tiers || {};
    var names = {
      LOCAL_STORAGE: 'Local',
      MEC_STORAGE: 'MEC',
      CLOUD_STORAGE: 'Cloud',
      UNASSIGNED: 'Unassigned / Blocked'
    };
    var chartHtml = '';
    Object.keys(names).forEach(function (key) {
      var value = proposed[key] || { bytes: 0, file_count: 0 };
      var percent = total > 0 ? Math.round(value.bytes / total * 100) : 0;
      chartHtml += '<div class="swf-bar-row"><div class="swf-bar-label"><span>' + names[key] + '</span><span>'
        + esc(formatBytes(value.bytes)) + ' · ' + esc(text(value.file_count, 0)) + ' files</span></div>'
        + '<div class="swf-bar"><span style="width:' + Math.min(100, Math.max(0, percent)) + '%"></span></div></div>';
    });
    byId('swf-allocation-chart').innerHTML = chartHtml || 'No allocation plan loaded.';

    byId('swf-partitions').innerHTML = (state.inspect.partitions || []).map(function (partition) {
      return '<div class="swf-partition' + (partition.status === 'BLOCKED' ? ' is-blocked' : '') + '"><strong>'
        + esc(partition.partition_id) + ' — ' + esc(partition.source) + '</strong><br>Files: '
        + esc(partition.file_count) + ' · Size: ' + esc(partition.size_formatted)
        + ' · Destination: ' + esc(partition.proposed_destination)
        + ' · Policy: ' + esc((partition.privacy_policies || []).join(', ') || 'Unknown')
        + ' · Status: ' + esc(partition.status) + '</div>';
    }).join('') || 'No partitions were generated.';

    byId('swf-tier-cards').innerHTML = Object.keys(tiers).map(function (key) {
      var tier = tiers[key];
      var utilization = tier.capacity_bytes && tier.used_bytes !== null
        ? Math.round(tier.used_bytes / tier.capacity_bytes * 100) : null;
      return '<div class="swf-tier"><strong>' + esc(tier.name) + '</strong>ID: ' + esc(tier.destination_id)
        + '<br>Type: ' + esc(tier.type) + (tier.is_emulator ? ' · EMULATOR' : '')
        + '<br>Capacity: ' + esc(formatBytes(tier.capacity_bytes))
        + '<br>Used: ' + esc(formatBytes(tier.used_bytes)) + ' · Free: ' + esc(formatBytes(tier.free_bytes))
        + '<br>Policy: ' + esc(tier.privacy_policy)
        + (tier.connected_devices !== null ? '<br>Connected devices: ' + esc(tier.connected_devices) : '')
        + '<div class="swf-bar"><span style="width:' + (utilization === null ? 0 : Math.min(100, utilization)) + '%"></span></div></div>';
    }).join('') || 'No storage tiers were reported.';
  }

  function confirmAllocation() {
    if (!state.reportId) {
      setStatus('swf-allocation-summary', 'No report is available to confirm.');
      return;
    }
    var form = new FormData();
    form.append('report_id', state.reportId);
    postForm(confirmUrl, form).then(function (result) {
      if (!result.success) throw new Error(result.error || 'Confirmation failed.');
      setStatus('swf-allocation-summary', result.label + ' · ' + result.message
        + ' Verified items: ' + result.verified_count + '. Blocked items: ' + result.blocked_count + '.');
      setStatus('swf-mode-badge', result.simulated ? 'SIMULATED ALLOCATION' : 'LIVE BACKEND', result.simulated);
    }).catch(function (error) {
      setStatus('swf-allocation-summary', error.message);
    });
  }

  function fetchScene() {
    return fetch(sceneUrl, {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' }
    }).then(function (response) { return response.json(); }).then(function (data) {
      if (!data || data.mode !== 'live') throw new Error('Scene data is unavailable.');
      state.scene = data;
      return data;
    });
  }

  function jump3dStage(index) {
    var select = byId('dt3d-workflow-stage');
    if (!select) return;
    select.value = String(index);
    select.dispatchEvent(new Event('change', { bubbles: true }));
    var operationsButton = root.querySelector('[data-swf-screen="network"] #swf-show-network');
    if (operationsButton) operationsButton.click();
    showOperations(true);
  }

  function showScheduling() {
    fetchScene().then(function (data) {
      var decisions = (data.scheduling && data.scheduling.decisions) || [];
      var message = decisions.length
        ? 'Recorded GA decision: ' + decisions[0].selected_resource + ' for task ' + decisions[0].task_id + ' (' + decisions[0].algorithm + ').'
        : 'No recorded GA dispatch decision exists. The scheduler capability is available; this visualization does not fabricate generations or fitness values.';
      setStatus('swf-scheduling-status', message);
      jump3dStage(7);
    }).catch(function (error) {
      setStatus('swf-scheduling-status', error.message);
    });
  }

  function showTransfers() {
    fetchScene().then(function (data) {
      var transfers = data.transfers || [];
      var message = transfers.length
        ? transfers.slice(0, 4).map(function (item) {
          return item.source + ' → ' + item.destination + ': ' + item.state + ' (' + item.label + ')';
        }).join(' · ')
        : 'No persisted transfer records are available. Live transfer percentage, speed, and ETA are not available.';
      setStatus('swf-transfer-status', message + ' No progress percentage is invented.');
      jump3dStage(9);
    }).catch(function (error) {
      setStatus('swf-transfer-status', error.message);
    });
  }

  function renderSecurityLayers() {
    fetchScene().then(function (data) {
      var layers = data.security_layers || [];
      byId('swf-security-layers').innerHTML = layers.map(function (layer) {
        return '<div class="swf-tier"><strong>' + esc(layer.label) + '</strong>' + esc(layer.status)
          + '<br>' + esc(layer.evidence) + '</div>';
      }).join('') || 'No security layer records are available.';
    }).catch(function (error) {
      setStatus('swf-security-layers', error.message);
    });
  }

  function populateAttackScenarios() {
    var select = byId('swf-attack-scenario');
    if (!select || select.options.length) return;
    fetchScene().then(function (data) {
      var scenarios = (data.simulation_catalog || []).map(function (item) {
        return { id: item.id, label: item.label, evidence: item.backend_evidence };
      });
      scenarios.forEach(function (scenario) {
        var option = document.createElement('option');
        option.value = scenario.id;
        option.textContent = scenario.label;
        option.setAttribute('data-evidence', scenario.evidence || '');
        select.appendChild(option);
      });
    }).catch(function () {
      var option = document.createElement('option');
      option.value = 'UNAUTHORIZED_TASK_SUBMISSION';
      option.textContent = 'Unauthorized task submission';
      select.appendChild(option);
    });
  }

  function runAttack() {
    var select = byId('swf-attack-scenario');
    var selected = select && select.selectedOptions[0];
    var scenarioId = select ? select.value : 'UNAUTHORIZED_TASK_SUBMISSION';
    var evidence = selected ? selected.getAttribute('data-evidence') : '';
    var target = byId('swf-attack-target').value;
    setStatus('swf-attack-status', 'SIMULATION — NO REAL ATTACK PERFORMED · ' + scenarioId + ' → ' + target
      + '. ' + text(evidence, 'Bounded local visualization only.') + ' No host was contacted and no resource state was changed by this action.');
    var scenarioSelect = byId('dt3d-attack-scenario');
    if (scenarioSelect) {
      scenarioSelect.value = scenarioId;
      scenarioSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }
    var attackButton = document.querySelector('[data-dt3d-action="attack-sim"]');
    if (attackButton) attackButton.click();
    showOperations(true);
  }

  function targetNodeId(value) {
    if (value === 'LOCAL') return 'LOCAL';
    if (value === 'CLOUD') return 'CLOUD';
    return 'MEC_STORAGE';
  }

  function evaluateFailover() {
    fetchScene().then(function (data) {
      var policy = byId('dt3d-policy').value;
      var info = (data.policies || {})[policy] || {};
      var eligible = (info.eligible_resources || []).slice();
      var affected = targetNodeId(byId('swf-attack-target').value);
      var remaining = eligible.filter(function (id) { return id !== affected; });
      var message = 'Policy ' + policy + ' · affected resource ' + affected + '. ';
      if (!remaining.length) message += 'Task Blocked — No Eligible Resource.';
      else message += 'Remaining eligible resources: ' + remaining.join(', ') + '. ';
      message += 'Local-only tasks were not moved to MEC or Cloud. No task was actually reassigned by this simulation; data recovery and replication are not verified.';
      setStatus('swf-failover-status', message);
      var layersButton = document.querySelector('[data-dt3d-action="show-security"]');
      if (layersButton) layersButton.click();
      showOperations(true);
    }).catch(function (error) {
      setStatus('swf-failover-status', error.message);
    });
  }

  function renderFinalReport() {
    if (!state.inspect) return;
    var stats = state.inspect.stats || {};
    var allocation = state.inspect.allocation || {};
    var parts = [
      'Report: ' + state.reportId,
      'Dataset: ' + state.inspect.file_name,
      'Files: ' + text(stats.total_files, 'Unknown'),
      'Dataset size: ' + formatBytes(stats.total_size_bytes),
      'Allocation: ' + text(allocation.label, 'Unknown'),
      'Security: ' + (state.inspect.security && state.inspect.security.integrity_verified ? 'archive integrity verified' : 'integrity not confirmed')
    ];
    var scene = state.scene;
    if (scene) {
      parts.push('MECs: ' + scene.server.registered_mecs + ' registered / ' + scene.server.connected_mecs + ' connected');
      parts.push('Tasks: ' + scene.tasks.length + ' recorded');
      parts.push('Audit events: ' + scene.security_events.length + ' recorded');
    }
    parts.push('Encrypted transport: NOT VERIFIED');
    setStatus('swf-final-report', parts.join(' · '));
  }

  function resetWorkflow() {
    state.file = null;
    state.reportId = '';
    state.inspect = null;
    state.scene = null;
    state.selectedNode = null;
    state.collapsed = {};
    var fileInput = byId('swf-file');
    if (fileInput) fileInput.value = '';
    var progress = byId('swf-progress');
    var fill = byId('swf-progress-fill');
    if (fill) fill.style.width = '0%';
    if (progress) progress.setAttribute('aria-valuenow', '0');
    updateFileSelection(null);
    setStatus('swf-analysis-summary', 'No analysis result loaded.');
    setStatus('swf-allocation-summary', '');
    setStatus('swf-mode-badge', 'LIVE BACKEND', false);
    byId('swf-analysis-stages').innerHTML = '<li>Waiting for upload.</li>';
    byId('swf-tree').textContent = 'No dataset loaded.';
    byId('swf-stats').textContent = 'No dataset loaded.';
    byId('swf-allocation-chart').textContent = 'No allocation plan loaded.';
    byId('swf-partitions').textContent = 'No partitions loaded.';
    byId('swf-tier-cards').textContent = 'No tiers loaded.';
    showStep(0);
  }

  var fileInput = byId('swf-file');
  var dropzone = byId('swf-dropzone');
  if (fileInput) {
    fileInput.addEventListener('change', function () { updateFileSelection(fileInput.files[0]); });
  }
  if (dropzone) {
    dropzone.addEventListener('click', function () { fileInput.click(); });
    dropzone.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        fileInput.click();
      }
    });
    ['dragenter', 'dragover'].forEach(function (type) {
      dropzone.addEventListener(type, function (event) {
        event.preventDefault();
        dropzone.classList.add('dragover');
      });
    });
    ['dragleave', 'drop'].forEach(function (type) {
      dropzone.addEventListener(type, function (event) {
        event.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });
    dropzone.addEventListener('drop', function (event) {
      var file = event.dataTransfer && event.dataTransfer.files[0];
      if (file) {
        fileInput.files = event.dataTransfer.files;
        updateFileSelection(file);
      }
    });
  }

  byId('swf-upload').addEventListener('click', uploadSelectedFile);
  byId('swf-reset').addEventListener('click', resetWorkflow);
  byId('swf-load-demo').addEventListener('click', loadDemoArchive);
  byId('swf-analysis-retry').addEventListener('click', function () { showStep(0); });
  byId('swf-to-allocation').addEventListener('click', function () { showStep(3); });
  byId('swf-confirm-allocation').addEventListener('click', confirmAllocation);
  byId('swf-to-network').addEventListener('click', function () { showOperations(true); showStep(4); });
  byId('swf-show-network').addEventListener('click', function () { showOperations(true); });
  byId('swf-skip-network').addEventListener('click', function () { showOperations(true); showStep(4); });
  byId('swf-run-scheduling').addEventListener('click', showScheduling);
  byId('swf-show-transfer').addEventListener('click', showTransfers);
  byId('swf-run-attack').addEventListener('click', runAttack);
  byId('swf-evaluate-failover').addEventListener('click', evaluateFailover);
  byId('swf-speed').addEventListener('change', function (event) {
    state.demoSpeed = Number(event.target.value) || 1;
    scheduleDemoTimer();
  });
  byId('swf-step-jump').addEventListener('change', function (event) {
    showDemoStep(Number(event.target.value));
  });
  byId('swf-start-demo').addEventListener('click', function () { startDemo(); scheduleDemoTimer(); });
  byId('swf-play').addEventListener('click', function () { startDemo(); scheduleDemoTimer(); });
  byId('swf-pause').addEventListener('click', pauseDemo);
  byId('swf-prev').addEventListener('click', function () { showDemoStep(state.demoIndex - 1); });
  byId('swf-next').addEventListener('click', function () { showDemoStep(state.demoIndex + 1); });
  byId('swf-restart').addEventListener('click', function () { startDemo(); scheduleDemoTimer(); });
  byId('swf-exit').addEventListener('click', function () {
    pauseDemo();
    showStep(0);
    setStatus('swf-final-report', 'Demonstration exited.');
  });

  Array.prototype.forEach.call(root.querySelectorAll('[data-swf-step]'), function (button) {
    button.addEventListener('click', function () { showStep(SCREENS.indexOf(button.getAttribute('data-swf-step'))); });
  });

  var tree = byId('swf-tree');
  tree.addEventListener('click', function (event) {
    var button = event.target.closest('[data-tree-node]');
    if (!button) return;
    var id = button.getAttribute('data-tree-node');
    var node = findGraphNode(id);
    if (node && (node.type === 'folder' || node.type === 'group')) {
      state.collapsed[id] = !state.collapsed[id];
      renderDataset();
      return;
    }
    selectNode(id);
  });
  byId('swf-tree-search').addEventListener('input', renderDataset);

  var graph = byId('swf-graph');
  graph.addEventListener('click', function (event) {
    var node = event.target.closest('[data-graph-node]');
    if (!node) return;
    var id = node.getAttribute('data-graph-node');
    var definition = findGraphNode(id);
    if (definition && (definition.type === 'folder' || definition.type === 'group')) {
      state.collapsed[id] = !state.collapsed[id];
      renderGraph();
      return;
    }
    selectNode(id);
  });
  graph.addEventListener('pointerdown', function (event) {
    state.graphPan = { x: event.clientX, y: event.clientY, ox: state.graphOffset.x, oy: state.graphOffset.y };
    graph.setPointerCapture(event.pointerId);
  });
  graph.addEventListener('pointermove', function (event) {
    if (!state.graphPan) return;
    state.graphOffset.x = state.graphPan.ox + event.clientX - state.graphPan.x;
    state.graphOffset.y = state.graphPan.oy + event.clientY - state.graphPan.y;
    renderGraph();
  });
  graph.addEventListener('pointerup', function () { state.graphPan = null; });
  byId('swf-zoom-in').addEventListener('click', function () { state.graphScale = Math.min(2.5, state.graphScale * 1.2); renderGraph(); });
  byId('swf-zoom-out').addEventListener('click', function () { state.graphScale = Math.max(0.4, state.graphScale / 1.2); renderGraph(); });
  byId('swf-graph-reset').addEventListener('click', function () {
    state.graphScale = 1;
    state.graphOffset = { x: 0, y: 0 };
    state.collapsed = {};
    renderGraph();
  });
  byId('swf-graph-search').addEventListener('input', function (event) {
    state.graphSearch = event.target.value;
    renderGraph();
  });

  var params = new URLSearchParams(window.location.search);
  var initialReport = params.get('report_id');
  populateStepJump();
  if (initialReport) {
    state.reportId = initialReport;
    fetchInspect(initialReport);
  }
  showStep(0);
})();
