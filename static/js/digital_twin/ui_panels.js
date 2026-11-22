import { display, escapeHtml, formatBytes } from './api_client.js';

const STAGE_TITLES = {
  upload: 'Upload',
  extraction: 'Extraction',
  'dataset-tree': 'Dataset Tree',
  analysis: 'Analysis',
  allocation: 'Storage Allocation',
  ga: 'GA Scheduling',
  transfer: 'File Transfer',
  storage: 'Storage',
  protection: 'Protection',
  attacker: 'Attacker Simulation',
  results: 'Final Report'
};

const PANEL_FOR_STAGE = {
  upload: 'upload',
  extraction: 'upload',
  'dataset-tree': 'analyze',
  analysis: 'analyze',
  allocation: 'allocate',
  ga: 'schedule',
  transfer: 'transfer',
  storage: 'transfer',
  protection: 'security',
  attacker: 'security',
  results: 'results'
};

export function setStage(root, stage, stages) {
  if (!root) return;
  root.dataset.stage = stage;
  var index = Math.max(0, stages.indexOf(stage));
  var kicker = document.getElementById('dtw-context-kicker');
  var title = document.getElementById('dtw-context-title');
  if (kicker) kicker.textContent = 'STAGE ' + String(index + 1).padStart(2, '0') + ' / ' + String(stages.length).padStart(2, '0');
  if (title) title.textContent = STAGE_TITLES[stage] || stage;
  var steps = document.querySelectorAll('#dtw-steps button');
  Array.prototype.forEach.call(steps, function (button) {
    if (button.dataset.stage === stage) button.setAttribute('aria-current', 'step');
    else button.removeAttribute('aria-current');
  });
  var panelStage = PANEL_FOR_STAGE[stage] || stage;
  var panels = document.querySelectorAll('#dtw-context-body [data-panel]');
  Array.prototype.forEach.call(panels, function (panel) { panel.hidden = panel.dataset.panel !== panelStage; });
  var jump = document.getElementById('dtw-jump');
  if (jump && jump.value !== stage) jump.value = stage;
  var hint = document.getElementById('dtw-viewport-hint');
  if (hint) hint.textContent = hintForStage(stage);
}

function hintForStage(stage) {
  if (stage === 'extraction') return 'Dataset inventory is read from persisted extraction records';
  if (stage === 'dataset-tree' || stage === 'analysis') return 'Light analysis view · click a tree row or graph node to inspect dataset structure';
  if (stage === 'allocation') return 'Proposed placement only · blocked partitions are shown explicitly';
  if (stage === 'ga') return 'Recorded eligible and blocked candidates · simulated benchmark metrics are labeled separately';
  if (stage === 'transfer') return 'Persisted replica states only · no transfer percentage, speed, or ETA is invented';
  if (stage === 'storage') return 'Storage nodes show recorded placement, not live capacity guarantees';
  if (stage === 'protection' || stage === 'attacker') return 'Shields show policy enforcement · encryption is NOT VERIFIED';
  if (stage === 'results') return 'Final report reflects recorded backend state and labeled simulations';
  return 'Drag to orbit · Shift+drag to pan · Scroll to zoom · Click a node for details';
}

export function showDetails(node) {
  var panel = document.getElementById('dtw-details');
  if (!panel) return;
  var title = document.getElementById('dtw-details-title');
  var id = document.getElementById('dtw-details-id');
  var kicker = document.getElementById('dtw-details-kicker');
  var body = document.getElementById('dtw-details-body');
  if (title) title.textContent = display(node.label, 'Resource');
  if (id) id.textContent = 'ID: ' + display(node.id, '—');
  if (kicker) kicker.textContent = display(node.meta && node.meta.kicker, 'NODE DETAILS');
  if (body) {
    body.textContent = '';
    var sections = (node.meta && node.meta.sections) || [{ title: 'Details', rows: [] }];
    sections.forEach(function (section) {
      var group = document.createElement('div');
      group.className = 'dtw-detail-group';
      var heading = document.createElement('h3');
      heading.textContent = section.title;
      group.appendChild(heading);
      (section.rows || []).forEach(function (row) {
        var line = document.createElement('div');
        line.className = 'dtw-detail-row';
        var label = document.createElement('span');
        label.textContent = row[0];
        var value = document.createElement('strong');
        value.textContent = display(row[1], 'Unknown');
        line.appendChild(label);
        line.appendChild(value);
        group.appendChild(line);
      });
      body.appendChild(group);
    });
  }
  panel.hidden = false;
}

export function hideDetails() {
  var panel = document.getElementById('dtw-details');
  if (panel) panel.hidden = true;
}

export function updateViewportHead(sceneMode, nodeCount, reducedMotion) {
  var mode = document.getElementById('dtw-view-mode');
  var count = document.getElementById('dtw-node-count');
  var motion = document.getElementById('dtw-motion-note');
  if (mode) mode.textContent = sceneMode === 'webgl' ? 'THREE.JS VIEW' : '2D FALLBACK VIEW';
  if (count) count.textContent = nodeCount + ' NODES';
  if (motion) motion.textContent = reducedMotion ? 'MOTION REDUCED' : 'MOTION ENABLED';
  var fallback = document.getElementById('dtw-fallback-note');
  if (fallback) fallback.hidden = sceneMode === 'webgl';
}

export function buildTransferGraph(data) {
  var transfers = (data && data.transfers) || [];
  var nodes = [];
  var links = [];
  var sources = Array.from(new Set(transfers.map(function (transfer) { return display(transfer.source, 'SOURCE NOT RECORDED'); })));
  var destinations = Array.from(new Set(transfers.map(function (transfer) { return display(transfer.destination, 'UNKNOWN'); })));

  sources.slice(0, 6).forEach(function (source, index) {
    nodes.push({
      id: 'SOURCE:' + source,
      label: source,
      type: 'source',
      shape: 'folder',
      status: 'online',
      color: 0xa78bfa,
      size: 0.8,
      position: { x: -10, y: 3 - index * 1.1, z: 0 },
      meta: { kicker: 'TRANSFER SOURCE', sections: [{ title: 'Source', rows: [['Source', source]] }] }
    });
  });

  destinations.slice(0, 6).forEach(function (destination, index) {
    nodes.push({
      id: 'DEST:' + destination,
      label: destination,
      type: 'destination',
      shape: 'storage',
      status: 'online',
      color: 0x22d3ee,
      size: 0.8,
      position: { x: 10, y: 3 - index * 1.1, z: 0 },
      meta: { kicker: 'TRANSFER DESTINATION', sections: [{ title: 'Destination', rows: [['Destination', destination]] }] }
    });
  });

  transfers.slice(0, 12).forEach(function (transfer, index) {
    var state = display(transfer.state, 'WAITING');
    var blocked = state === 'BLOCKED';
    var failed = state === 'FAILED';
    var color = blocked || failed ? 0xfb7185 : state === 'COMPLETED' ? 0x34d399 : state === 'TRANSFERRING' ? 0xf59e0b : 0x64748b;
    var id = 'TRANSFER:' + (transfer.transfer_id || index);
    nodes.push({
      id: id,
      label: transfer.label || transfer.transfer_id,
      type: 'transfer',
      shape: state === 'COMPLETED' ? 'octahedron' : 'file',
      status: blocked || failed ? 'blocked' : 'online',
      color: color,
      size: 0.6,
      position: { x: 0, y: 4 - index * 0.8, z: 0 },
      meta: {
        kicker: 'PERSISTED TRANSFER',
        sections: [{
          title: 'Transfer Information',
          rows: [
            ['Transfer ID', display(transfer.transfer_id, 'Unknown')],
            ['Source', display(transfer.source, 'SOURCE NOT RECORDED')],
            ['Destination', display(transfer.destination, 'UNKNOWN')],
            ['State', state],
            ['Privacy policy', display(transfer.privacy_policy, 'UNKNOWN')],
            ['Recorded at', display(transfer.recorded_at, 'Unknown')],
            ['Live progress', 'NOT AVAILABLE'],
            ['Encryption', 'NOT VERIFIED']
          ]
        }]
      }
    });
    var sourceId = 'SOURCE:' + display(transfer.source, 'SOURCE NOT RECORDED');
    var destinationId = 'DEST:' + display(transfer.destination, 'UNKNOWN');
    if (nodes.some(function (node) { return node.id === sourceId; })) links.push({ from: sourceId, to: id, color: color, opacity: 0.5 });
    if (nodes.some(function (node) { return node.id === destinationId; })) links.push({ from: id, to: destinationId, color: color, opacity: 0.5 });
  });

  return { nodes: nodes, links: links };
}

export function renderTransferStatus(container, data) {
  if (!container) return;
  var transfers = (data && data.transfers) || [];
  if (!transfers.length) { container.textContent = 'No persisted transfer records are available.'; return; }
  var counts = {};
  transfers.forEach(function (transfer) {
    var state = display(transfer.state, 'WAITING');
    counts[state] = (counts[state] || 0) + 1;
  });
  var lines = [transfers.length + ' persisted transfer record(s)'];
  Object.keys(counts).sort().forEach(function (state) { lines.push(state + ': ' + counts[state]); });
  lines.push('Live percentage, speed, and ETA are not available.');
  container.innerHTML = lines.map(escapeHtml).join('<br>');
}

export function renderUploadState(name, size) {
  var nameNode = document.getElementById('dtw-file-name');
  var sizeNode = document.getElementById('dtw-file-size');
  if (nameNode) nameNode.textContent = name || 'None';
  if (sizeNode) sizeNode.textContent = size ? formatBytes(size) : 'Unknown';
}

export function setUploadProgress(value) {
  var bar = document.getElementById('dtw-progress');
  var fill = document.getElementById('dtw-progress-fill');
  var bounded = Math.max(0, Math.min(100, Math.round(value)));
  if (fill) fill.style.width = bounded + '%';
  if (bar) bar.setAttribute('aria-valuenow', String(bounded));
}

export function setUploadStatus(message) {
  var status = document.getElementById('dtw-upload-status');
  if (status) status.textContent = message;
}

export function openUpload(open) {
  var overlay = document.getElementById('dtw-upload-overlay');
  if (overlay) overlay.hidden = !open;
}

export function renderFinalReport(container, data, inspection, comparison) {
  if (!container) return;
  var workflow = (data && data.workflow) || {};
  var final = (inspection && inspection.final) || {};
  var stages = workflow.stages || [];
  var blocked = stages.filter(function (stage) { return stage.status === 'BLOCKED'; });
  var pending = stages.filter(function (stage) { return stage.status === 'PENDING'; });
  var lines = [
    '<strong>' + escapeHtml(display(final.status, 'WORKFLOW STATUS RECORDED')) + '</strong>',
    'Selected dataset: ' + escapeHtml(display(inspection && inspection.dataset && inspection.dataset.dataset_name, 'Not loaded')),
    'Backend stages: ' + stages.length,
    'Blocked stages: ' + blocked.length,
    'Pending stages: ' + pending.length,
    'Latest report: ' + escapeHtml(display(inspection && inspection.report_id, 'Not loaded')),
    'Transfer progress: NOT AVAILABLE',
    'Encryption: NOT VERIFIED'
  ];
  if (comparison) lines.push('Simulated GA comparison: AVAILABLE');
  if (blocked.length) lines.push('<strong>TASK BLOCKED — NO ELIGIBLE RESOURCE</strong>');
  container.innerHTML = lines.join('<br>');
}

export function setStatusStrip(part, value) {
  var ids = {
    selected: 'dtw-selected',
    transfer: 'dtw-status-transfer',
    ga: 'dtw-status-ga',
    security: 'dtw-status-security'
  };
  var element = document.getElementById(ids[part]);
  if (element) element.textContent = value;
}

export function renderDatasetSelector(select, datasets, currentId, onChange, placeholder) {
  if (!select) return;
  var previous = currentId || select.value;
  select.textContent = '';
  if (placeholder) {
    var prompt = document.createElement('option');
    prompt.value = '';
    prompt.textContent = placeholder;
    select.appendChild(prompt);
  }
  if (!datasets.length) {
    if (!placeholder) {
      var empty = document.createElement('option');
      empty.value = '';
      empty.textContent = 'No uploaded datasets';
      select.appendChild(empty);
    }
    return;
  }
  datasets.forEach(function (dataset) {
    var option = document.createElement('option');
    option.value = dataset.upload_id;
    option.textContent = dataset.dataset_name + ' · ' + dataset.upload_id;
    select.appendChild(option);
  });
  if (previous && datasets.some(function (dataset) { return dataset.upload_id === previous; })) select.value = previous;
  select.onchange = function () { onChange(this.value); };
}

export function renderDatasetInfo(container, dataset) {
  if (!container) return;
  if (!dataset) { container.textContent = 'Select an uploaded dataset to drive the workflow.'; return; }
  var rows = [
    ['Dataset', dataset.dataset_name],
    ['Upload ID', dataset.upload_id],
    ['Filename', dataset.file_name],
    ['File count', display(dataset.file_count, 0)],
    ['Total size', display(dataset.total_size_formatted, formatBytes(dataset.total_size_bytes))],
    ['Upload status', display(dataset.upload_status, 'Unknown')],
    ['Analysis status', display(dataset.analysis_status, 'Unknown')],
    ['Allocation status', dataset.allocation_status ? display(dataset.allocation_status.execution_mode, 'Unknown') : 'Unknown']
  ];
  container.innerHTML = '<strong>' + escapeHtml(dataset.dataset_name) + '</strong><br>' + rows.map(function (row) {
    return escapeHtml(row[0]) + ': ' + escapeHtml(row[1]);
  }).join('<br>');
}

export function renderEventLog(container, entries) {
  if (!container) return;
  if (!entries || !entries.length) { container.textContent = 'No events recorded yet.'; return; }
  container.textContent = '';
  entries.slice(-40).forEach(function (entry) {
    var line = document.createElement('div');
    line.textContent = '[' + entry.time + '] ' + entry.label;
    container.appendChild(line);
  });
}

export function updatePlayback(index, total, stage, elapsedMilliseconds, playing) {
  var timeline = document.getElementById('dtw-timeline');
  var label = document.getElementById('dtw-stage-label');
  var elapsed = document.getElementById('dtw-elapsed');
  if (timeline) {
    timeline.max = String(Math.max(0, total - 1));
    timeline.value = String(index);
    timeline.setAttribute('aria-valuetext', String(index + 1) + ' of ' + total + ': ' + stage);
  }
  if (label) label.textContent = String(index + 1).padStart(2, '0') + ' / ' + String(total).padStart(2, '0') + ' · ' + stage;
  if (elapsed) elapsed.textContent = formatElapsed(elapsedMilliseconds);
  var pause = document.getElementById('dtw-pause');
  if (pause) pause.textContent = playing ? 'Pause' : 'Resume';
}

function formatElapsed(milliseconds) {
  var seconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
  return String(Math.floor(seconds / 60)).padStart(2, '0') + ':' + String(seconds % 60).padStart(2, '0');
}
