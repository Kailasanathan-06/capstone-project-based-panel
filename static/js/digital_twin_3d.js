(function () {
  'use strict';

  function byId(id) { return document.getElementById(id); }

  var stage = byId('dt3d-stage');
  if (!stage) return;

  var canvas = byId('dt3d-canvas');
  var labelLayer = byId('dt3d-labels');
  var emptyNotice = byId('dt3d-empty');
  var modeBadge = byId('dt3d-mode');
  var engineBadge = byId('dt3d-engine');
  var eventList = byId('dt3d-event-list');
  var policySelect = byId('dt3d-policy');
  var detailNode = byId('dt3d-detail');
  var protectionNote = byId('dt3d-protection-note');
  var detailsPanel = byId('dt3d-details');
  var runModeSelect = byId('dt3d-run-mode');
  var runModeBadge = byId('dt3d-run-mode-badge');
  var workflowKicker = byId('dt3d-workflow-kicker');
  var workflowStatus = byId('dt3d-workflow-status');
  var workflowDetail = byId('dt3d-workflow-detail');
  var workflowProgress = byId('dt3d-workflow-progress');
  var workflowProgressFill = byId('dt3d-workflow-progress-fill');
  var workflowTime = byId('dt3d-workflow-time');
  var workflowSteps = byId('dt3d-workflow-steps');
  var workflowStageSelect = byId('dt3d-workflow-stage');
  var workflowSpeedSelect = byId('dt3d-workflow-speed');
  var currentDataSource = byId('dt3d-current-data-source');
  var currentSource = byId('dt3d-current-source');
  var currentDestination = byId('dt3d-current-destination');
  var currentTask = byId('dt3d-current-task');
  var currentArtifact = byId('dt3d-current-artifact');
  var currentDetail = byId('dt3d-current-detail');
  var securityPanel = byId('dt3d-security-panel');
  var securityLayers = byId('dt3d-security-layers');
  var securitySummary = byId('dt3d-security-summary');
  var attackSelect = byId('dt3d-attack-scenario');
  var stageChips = {
    policy: byId('dt3d-chip-policy'),
    destination: byId('dt3d-chip-destination'),
    authorized: byId('dt3d-chip-authorized'),
    transfer: byId('dt3d-chip-transfer'),
    result: byId('dt3d-chip-result')
  };

  var API_URL = stage.getAttribute('data-scene-url') || '/api/digital-twin/scene/';
  var motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var reducedMotion = !!(motionQuery && motionQuery.matches);
  var POLL_MS = 15000;

  var state = {
    data: null,
    paused: false,
    showLabels: true,
    showLinks: true,
    showTransfers: true,
    showSecurity: true,
    policy: 'TRUSTED_EDGE',
    simulatedCount: 0,
    events: [],
    seenTransfers: {},
    seenTasks: {},
    selectedResource: null,
    selectedDeviceId: null,
    hoverId: null,
    returnFocus: null,
    detailsTimer: 0,
    eligible: [],
    simulationActive: false,
    simulationToken: 0,
    attackIndex: 0,
    forceSim: false,
    workflow: {
      active: false,
      playing: false,
      completed: false,
      index: 0,
      elapsed: 0,
      speed: 1,
      mode: 'live',
      token: 0,
      lastPaint: 0
    }
  };

  var model = { nodes: [], links: [], packets: [] };
  var backend = null;
  var rafId = 0;
  var lastFrame = 0;
  var dirty = true;
  var pollTimer = 0;
  var labelElements = {};
  var dead = false;
  var listeners = [];

  var ATTACK_SCENARIOS = [
    { type: 'UNAUTHORIZED_TASK_SUBMISSION', target: 'CENTRAL', label: 'Unauthorized task submission' },
    { type: 'INVALID_MEC_AUTH', target: 'MEC', label: 'Invalid MEC credentials' },
    { type: 'ZIP_VALIDATION_ERROR', target: 'CENTRAL', label: 'Invalid ZIP archive' },
    { type: 'PRIVACY_POLICY_VIOLATION', target: 'CLOUD', label: 'Privacy policy violation' },
    { type: 'OFFLINE_MEC_RESOURCE', target: 'MEC', label: 'Offline MEC resource' },
    { type: 'TASK_QUEUE_ACCESS', target: 'CENTRAL', label: 'Unauthorized queue access' },
    { type: 'REPEATED_SUSPICIOUS_REQUESTS', target: 'CENTRAL', label: 'Repeated suspicious requests' },
    { type: 'TRANSFER_INTERRUPTION', target: 'MEC_STORAGE', label: 'Transfer interruption' }
  ];

  var WORKFLOW_STAGES = [
    { id: 'infrastructure', title: 'Infrastructure Overview', description: 'Confirm the live control plane, configured storage tiers, and registered MEC agents.', source: 'CENTRAL', destination: 'CENTRAL', duration: 3000, visual: 'overview' },
    { id: 'dataset_source', title: 'Dataset Source Selection', description: 'Select the dataset submission client and identify the upload record without exposing filenames.', source: 'CLIENT', destination: 'CENTRAL', duration: 4000, visual: 'client' },
    { id: 'zip_upload', title: 'ZIP Upload', description: 'Review the recorded archive upload state and execution mode.', source: 'CLIENT', destination: 'CENTRAL', duration: 5500, visual: 'upload' },
    { id: 'zip_validation', title: 'Archive Validation', description: 'Show recorded readability, corruption, traversal, and extension checks without opening data.', source: 'CENTRAL', destination: 'CENTRAL', duration: 5000, visual: 'validation' },
    { id: 'dataset_analysis', title: 'Dataset Analysis', description: 'Summarize the persisted analysis report; no file contents are displayed.', source: 'CENTRAL', destination: 'CENTRAL', duration: 5500, visual: 'analysis' },
    { id: 'privacy_policy', title: 'Privacy Policy Check', description: 'Apply the selected backend policy and show eligible destinations only.', source: 'CENTRAL', destination: 'CENTRAL', duration: 4500, visual: 'policy' },
    { id: 'resource_monitoring', title: 'Digital Twin Resource State', description: 'Read CPU, memory, latency, trust, and heartbeat telemetry from the resource registry.', source: 'CENTRAL', destination: 'LOCAL', duration: 5000, visual: 'monitor' },
    { id: 'ga_scheduling', title: 'Genetic Algorithm Scheduling', description: 'Show GA cost metrics only when a recorded decision exists; otherwise mark the stage as a backend capability.', source: 'CENTRAL', destination: 'LOCAL', duration: 6000, visual: 'ga' },
    { id: 'resource_selection', title: 'Resource Selection', description: 'Highlight the selected storage or MEC resource from the recorded schedule.', source: 'CENTRAL', destination: 'LOCAL', duration: 4500, visual: 'selection' },
    { id: 'file_transfer', title: 'Data Transfer', description: 'Display recorded replication states; live percentages and ETA are not available.', source: 'LOCAL', destination: 'MEC_STORAGE', duration: 6500, visual: 'transfer' },
    { id: 'task_processing', title: 'Task Processing', description: 'Show task dispatch and local execution state from persisted task records.', source: 'CENTRAL', destination: 'LOCAL', duration: 6500, visual: 'task' },
    { id: 'result_delivery', title: 'Result Delivery', description: 'Show completed task records being acknowledged by the control plane.', source: 'LOCAL', destination: 'CENTRAL', duration: 5000, visual: 'result' },
    { id: 'storage_allocation', title: 'Storage Allocation', description: 'Map used and free capacity for configured storage tiers without exposing dataset paths.', source: 'CENTRAL', destination: 'MEC_STORAGE', duration: 5000, visual: 'storage' },
    { id: 'task_completion', title: 'Task Completion', description: 'Summarize confirmed completion records only.', source: 'CENTRAL', destination: 'LOCAL', duration: 5000, visual: 'completion' },
    { id: 'security_audit', title: 'Security Audit Summary', description: 'Close with recorded audit events and clearly separated simulated attacker behavior.', source: 'ATTACKER', destination: 'CENTRAL', duration: 4500, visual: 'audit' }
  ];

  var WORKFLOW_TOTAL_MS = WORKFLOW_STAGES.reduce(function (sum, item) { return sum + item.duration; }, 0);

  function on(target, type, handler, options) {
    target.addEventListener(type, handler, options);
    listeners.push([target, type, handler, options]);
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function shortId(value) {
    var text = String(value || '');
    return text.length > 18 ? text.slice(0, 15) + '...' : text;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function safeText(value) {
    if (value === null || value === undefined || value === '') return 'Not available';
    return String(value);
  }

  function formatBytes(value) {
    if (value === null || value === undefined || value === '') return 'Not available';
    var number = Number(value);
    if (!isFinite(number) || number < 0) return 'Not available';
    var units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var index = 0;
    while (number >= 1024 && index < units.length - 1) {
      number /= 1024;
      index += 1;
    }
    var digits = index === 0 ? 0 : number >= 100 ? 0 : number >= 10 ? 1 : 2;
    return number.toFixed(digits) + ' ' + units[index];
  }

  function formatPercent(value) {
    if (value === null || value === undefined || value === '') return 'Not available';
    var number = Number(value);
    if (!isFinite(number) || number < 0) return 'Not available';
    return clamp(number, 0, 100).toFixed(1) + '%';
  }

  function formatInteger(value) {
    if (value === null || value === undefined || value === '') return 'Not available';
    var number = Number(value);
    if (!isFinite(number) || number < 0) return 'Not available';
    return String(Math.round(number));
  }

  function formatAge(value) {
    if (value === null || value === undefined || value === '') return 'Not available';
    var number = Number(value);
    if (!isFinite(number) || number < 0) return 'Not available';
    if (number < 2) return 'just now';
    if (number < 60) return Math.round(number) + 's ago';
    return Math.round(number / 60) + 'm ago';
  }

  function isClickableNode(node) {
    if (!node) return false;
    return node.kind === 'central' || node.kind === 'local' || node.kind === 'cloud'
      || node.kind === 'edge-store' || node.kind === 'mec' || node.kind === 'client'
      || node.kind === 'attacker';
  }

  function statRow(label, value, tone) {
    return '<div class="dt3d-details-stat"><span>' + esc(label) + '</span><strong'
      + (tone ? ' class="' + tone + '"' : '') + '>' + esc(safeText(value)) + '</strong></div>';
  }

  function renderDeviceDetails(nodeId) {
    if (!detailsPanel) return;
    var node = findNode(nodeId);
    var details = state.data && state.data.device_details ? state.data.device_details[nodeId] : null;
    if (!details && nodeId === 'CLIENT' && state.data && state.data.client_devices && state.data.client_devices.length) {
      var client = state.data.client_devices[0];
      details = {
        device_id: client.client_id,
        label: client.label,
        device_type: 'WEB_UPLOAD_CLIENT',
        status: 'CONNECTED',
        telemetry_mode: client.client_type,
        details_note: client.note,
        is_simulated: !!client.is_simulated
      };
    }
    if (!node && !details) return;
    details = details || {
      device_id: nodeId,
      label: node.label,
      device_type: 'DEVICE',
      node_kind: node.kind,
      status: node.status
    };

    var title = byId('dt3d-details-title');
    var kicker = byId('dt3d-details-kicker');
    var idNode = byId('dt3d-details-id');
    var statusNode = byId('dt3d-details-status');
    var body = byId('dt3d-details-body');
    var kindNames = {
      STORAGE_TIER: 'STORAGE TIER DETAILS',
      EDGE_AGENT: 'MEC AGENT DETAILS',
      CONTROL_PLANE: 'CONTROL PLANE DETAILS',
      WEB_UPLOAD_CLIENT: 'WEB UPLOAD CLIENT DETAILS',
      SIMULATION: 'SIMULATED SCENARIO'
    };
    var status = safeText(details.status || (node && node.status) || 'UNKNOWN');
    var statusTone = /ONLINE|CONNECTED|SAFE/.test(status) ? 'is-online'
      : /SIMULATED/.test(status) ? 'is-simulated'
        : /CONNECTING|PENDING/.test(status) ? 'is-connecting' : 'is-offline';
    if (kicker) kicker.textContent = kindNames[details.device_type] || 'DEVICE DETAILS';
    if (title) title.textContent = safeText(details.label || (node && node.label) || nodeId);
    if (idNode) idNode.textContent = 'ID: ' + safeText(details.device_id || nodeId);
    if (statusNode) {
      statusNode.textContent = status;
      statusNode.className = 'dt3d-details-status ' + statusTone;
    }

    var html = '';
    if (details.is_simulated) {
      html += '<div class="dt3d-details-badge">'
        + (details.device_type === 'STORAGE_TIER' ? 'SIMULATED STORAGE DATA' : 'SIMULATED / NOT LIVE')
        + '</div>';
    }
    html += '<div class="dt3d-details-stats">';
    if (details.device_type === 'STORAGE_TIER') {
      var free = details.free_bytes === null || details.free_bytes === undefined
        ? null : Math.max(0, Number(details.free_bytes));
      html += statRow('Total Capacity', formatBytes(details.capacity_bytes));
      html += statRow('Used Storage', formatBytes(details.used_bytes));
      html += statRow('Free Capacity', formatBytes(free));
      var utilization = details.utilization_percent === null || details.utilization_percent === undefined
        || details.utilization_percent === '' ? NaN : Number(details.utilization_percent);
      html += statRow('Utilization', formatPercent(details.utilization_percent));
      if (isFinite(utilization)) {
        html += '<div class="dt3d-util-bar" role="img" aria-label="Storage utilization '
          + esc(clamp(utilization, 0, 100).toFixed(1)) + ' percent"><span style="width:'
          + esc(clamp(utilization, 0, 100).toFixed(1)) + '%"></span></div>';
      }
      html += statRow('Replicas', formatInteger(details.replica_count));
      html += statRow('Inventory Items', formatInteger(details.inventory_item_count));
    } else if (details.device_type === 'EDGE_AGENT') {
      html += statRow('Heartbeat Age', formatAge(details.freshness_seconds));
      html += statRow('CPU Load', formatPercent(details.cpu_utilization === null ? null : Number(details.cpu_utilization) * 100));
      html += statRow('Memory', formatPercent(details.memory_utilization === null ? null : Number(details.memory_utilization) * 100));
      html += statRow('Network Latency', safeText(details.network_latency_ms) === 'Not available' ? 'Not available' : formatInteger(details.network_latency_ms) + ' ms');
      html += statRow('Active Tasks', formatInteger(details.active_tasks));
      html += statRow('Storage Source', safeText(details.shared_storage_tier_id || 'Not available'));
    } else if (details.device_type === 'CONTROL_PLANE') {
      html += statRow('Registered MECs', formatInteger(details.registered_mecs));
      html += statRow('Connected MECs', formatInteger(details.connected_mecs));
      html += statRow('Active Tasks', formatInteger(details.active_tasks));
      html += statRow('Active Transfers', formatInteger(details.active_transfers));
      html += statRow('Policy Enforcement', details.policy_enforcement ? 'ENABLED' : 'NOT REPORTED');
      html += statRow('Transport Encryption', details.encryption_confirmed ? 'CONFIRMED' : 'NOT CONFIRMED');
    } else {
      html += statRow('Node Type', safeText(details.device_type));
      html += statRow('Telemetry', safeText(details.telemetry_mode));
    }
    html += '</div>';

    html += '<div class="dt3d-details-section"><h4>Backend Fields</h4><div class="dt3d-details-fields">';
    html += statRow('Device ID', details.device_id);
    html += statRow('Telemetry Mode', details.telemetry_mode);
    if (details.device_type === 'STORAGE_TIER') {
      html += statRow('Assigned Tasks', formatInteger(details.assigned_task_count));
      html += statRow('Allowed Policy', details.privacy_tier_allowed);
    }
    if (details.device_type === 'EDGE_AGENT') {
      html += statRow('Connection State', details.status);
      html += statRow('Telemetry Freshness', formatAge(details.freshness_seconds));
    }
    if (details.device_type === 'SIMULATION') {
      html += statRow('Real Host Impact', 'NONE');
    }
    html += '</div></div>';

    html += '<div class="dt3d-details-note">' + esc(safeText(details.details_note)) + '</div>';
    html += '<div class="dt3d-details-source">'
      + (details.device_type === 'SIMULATION' ? 'LOCAL SIMULATION' : 'LIVE BACKEND SNAPSHOT')
      + '</div>';
    if (body) {
      body.innerHTML = html;
      body.scrollTop = 0;
    }
  }

  function openDeviceDetails(nodeId) {
    if (!detailsPanel || !isClickableNode(findNode(nodeId))) return;
    var wasHidden = detailsPanel.hidden;
    if (wasHidden) state.returnFocus = document.activeElement;
    state.selectedDeviceId = nodeId;
    model.selectedDeviceId = nodeId;
    renderDeviceDetails(nodeId);
    window.clearTimeout(state.detailsTimer);
    detailsPanel.hidden = false;
    detailsPanel.classList.remove('is-open');
    window.requestAnimationFrame(function () {
      if (!detailsPanel.hidden) detailsPanel.classList.add('is-open');
    });
    if (stage) stage.classList.add('has-details');
    dirty = true;
    if (wasHidden) detailsPanel.focus();
  }

  function closeDeviceDetails() {
    if (!detailsPanel || detailsPanel.hidden) return;
    detailsPanel.classList.remove('is-open');
    if (stage) stage.classList.remove('has-details');
    state.selectedDeviceId = null;
    model.selectedDeviceId = null;
    dirty = true;
    var panel = detailsPanel;
    state.detailsTimer = window.setTimeout(function () {
      if (!panel.classList.contains('is-open')) panel.hidden = true;
    }, 160);
    var target = state.returnFocus;
    state.returnFocus = null;
    if (target && document.contains(target) && target.focus) target.focus();
    else if (canvas && canvas.focus) canvas.focus();
  }

  function setHoverNode(nodeId) {
    if (state.hoverId === nodeId) return;
    state.hoverId = nodeId;
    model.hoverId = nodeId;
    if (canvas) {
      canvas.style.cursor = nodeId ? 'pointer' : '';
      canvas.title = nodeId ? 'Click to view device details' : '';
    }
    dirty = true;
  }

  function cycleDeviceSelection(step) {
    var devices = model.nodes.filter(isClickableNode);
    if (!devices.length) return;
    var index = -1;
    for (var i = 0; i < devices.length; i += 1) {
      if (devices[i].id === state.selectedDeviceId) index = i;
    }
    var next = devices[(index + step + devices.length) % devices.length];
    openDeviceDetails(next.id);
  }

  function colorFor(node) {
    if (node.kind === 'attacker') return 0xef4444;
    if (node.status === 'offline') return 0x64748b;
    if (node.status === 'connecting') return 0xf59e0b;
    if (node.status === 'simulated') return 0xf59e0b;
    if (node.kind === 'central') return 0x38bdf8;
    if (node.kind === 'cloud') return 0x60a5fa;
    if (node.kind === 'local') return 0x2dd4bf;
    if (node.kind === 'client') return 0xa78bfa;
    if (node.kind === 'task') return 0xfbbf24;
    return 0x10b981;
  }

  function colorHex(node) {
    return '#' + colorFor(node).toString(16).padStart(6, '0');
  }

  function ThreeBackend(el) {
    this.el = el;
    this.renderer = new THREE.WebGLRenderer({ canvas: el, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setClearColor(0x071120, 0);
    this.scene = new THREE.Scene();
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 400);
    this.yaw = 0.55;
    this.pitch = 0.48;
    this.distance = 31;
    this.width = 1;
    this.height = 1;
    this.nodes = {};
    this.links = {};
    this.packets = {};
    this.linksVisible = true;

    this.scene.add(new THREE.AmbientLight(0xb9d7ff, 0.85));
    var key = new THREE.DirectionalLight(0xffffff, 0.7);
    key.position.set(8, 16, 12);
    this.scene.add(key);

    var grid = new THREE.GridHelper(40, 16, 0x1c4b78, 0x143154);
    grid.position.y = -1.35;
    grid.material.transparent = true;
    grid.material.opacity = 0.34;
    this.scene.add(grid);

    var shieldGeo = new THREE.SphereGeometry(3.1, 18, 12);
    var shieldMat = new THREE.MeshBasicMaterial({
      color: 0x2dd4bf, wireframe: true, transparent: true, opacity: 0.16
    });
    this.shield = new THREE.Mesh(shieldGeo, shieldMat);
    this.scene.add(this.shield);
    this.updateCamera();
  }

  ThreeBackend.prototype.updateCamera = function () {
    var cp = Math.cos(this.pitch);
    this.camera.position.set(
      this.distance * Math.sin(this.yaw) * cp,
      this.distance * Math.sin(this.pitch),
      this.distance * Math.cos(this.yaw) * cp
    );
    this.camera.lookAt(0, 0, 0);
  };

  ThreeBackend.prototype.resize = function (w, h) {
    this.width = w;
    this.height = h;
    this.camera.aspect = w / Math.max(1, h);
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  };

  ThreeBackend.prototype.rotate = function (dx, dy) {
    this.yaw += dx * 0.005;
    this.pitch = Math.max(0.1, Math.min(1.32, this.pitch + dy * 0.004));
    this.updateCamera();
  };

  ThreeBackend.prototype.zoom = function (factor) {
    this.distance = Math.max(15, Math.min(60, this.distance * factor));
    this.updateCamera();
  };

  ThreeBackend.prototype.resetView = function () {
    this.yaw = 0.55;
    this.pitch = 0.48;
    this.distance = 31;
    this.updateCamera();
  };

  ThreeBackend.prototype.buildNode = function (node) {
    var group = new THREE.Group();
    var size = node.kind === 'central' ? 1.5 : node.kind === 'mec' ? 0.92 : 0.72;
    var geo;
    if (node.kind === 'cloud') geo = new THREE.SphereGeometry(size, 14, 10);
    else if (node.kind === 'attacker') geo = new THREE.OctahedronGeometry(size, 0);
    else if (node.kind === 'task') geo = new THREE.BoxGeometry(0.52, 0.52, 0.52);
    else geo = new THREE.BoxGeometry(size, size * 1.35, size * 0.8);

    var color = colorFor(node);
    var mesh = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({
      color: color, transparent: true, opacity: 0.94
    }));
    group.add(mesh);

    var edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(geo),
      new THREE.LineBasicMaterial({ color: 0xa6d8ff, transparent: true, opacity: 0.42 })
    );
    group.add(edges);

    var ringGeo = new THREE.RingGeometry(size * 1.25, size * 1.44, 28);
    var ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({
      color: color, side: THREE.DoubleSide, transparent: true, opacity: 0.8
    }));
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = -size * 0.9 - 0.12;
    group.add(ring);

    var selectGeo = new THREE.RingGeometry(size * 1.6, size * 1.82, 28);
    var select = new THREE.Mesh(selectGeo, new THREE.MeshBasicMaterial({
      color: 0xfbbf24, side: THREE.DoubleSide, transparent: true, opacity: 0.85
    }));
    select.rotation.x = -Math.PI / 2;
    select.position.y = -size * 0.9 - 0.16;
    select.visible = false;
    group.add(select);

    group.position.set(node.x, node.y, node.z);
    this.root.add(group);
    return { group: group, mesh: mesh, ring: ring, select: select };
  };

  ThreeBackend.prototype.buildLink = function (link, positions) {
    var a = positions[link.from];
    var b = positions[link.to];
    if (!a || !b) return null;
    var geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(a.x, a.y, a.z),
      new THREE.Vector3(b.x, b.y, b.z)
    ]);
    var dashed = link.state === 'offline' || link.state === 'connecting' || link.kind === 'attack';
    var color = link.kind === 'attack' ? 0xef4444
      : link.kind === 'task' ? 0xfbbf24
        : link.state === 'offline' ? 0x475569
          : link.state === 'connecting' ? 0xf59e0b : 0x38bdf8;
    var material = dashed
      ? new THREE.LineDashedMaterial({ color: color, dashSize: 0.34, gapSize: 0.24, transparent: true, opacity: 0.8 })
      : new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: link.kind === 'connection' ? 0.58 : 0.82 });
    var line = new THREE.Line(geometry, material);
    if (dashed) line.computeLineDistances();
    line.visible = this.linksVisible;
    this.root.add(line);
    return { line: line, a: { x: a.x, y: a.y, z: a.z }, b: { x: b.x, y: b.y, z: b.z } };
  };

  ThreeBackend.prototype.buildPacket = function (packet, positions) {
    var link = this.links[packet.linkId];
    if (!link) return null;
    var group = new THREE.Group();
    var color = packet.kind === 'attack' ? 0xef4444 : packet.kind === 'task' ? 0xfbbf24 : 0x60a5fa;
    var body = new THREE.Mesh(
      new THREE.BoxGeometry(0.48, 0.6, 0.09),
      new THREE.MeshLambertMaterial({ color: color, emissive: color, emissiveIntensity: 0.35 })
    );
    group.add(body);
    var fold = new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.18, 0.11),
      new THREE.MeshBasicMaterial({ color: 0xe0f2fe })
    );
    fold.position.set(0.14, 0.21, 0);
    group.add(fold);
    this.root.add(group);
    return { group: group, link: link };
  };

  ThreeBackend.prototype.sync = function (nextModel) {
    var self = this;
    var positions = {};
    var nodeIds = {};
    nextModel.nodes.forEach(function (n) { nodeIds[n.id] = true; positions[n.id] = n; });
    Object.keys(this.nodes).forEach(function (id) {
      if (!nodeIds[id]) {
        self.root.remove(self.nodes[id].group);
        self.nodes[id].group.traverse(function (obj) {
          if (obj.geometry) obj.geometry.dispose();
          if (obj.material) obj.material.dispose();
        });
        delete self.nodes[id];
      }
    });
    nextModel.nodes.forEach(function (n) {
      if (!self.nodes[n.id]) self.nodes[n.id] = self.buildNode(n);
      var entry = self.nodes[n.id];
      var selected = nextModel.selectedDeviceId === n.id;
      var hovered = nextModel.hoverId === n.id;
      entry.select.visible = selected || nextModel.highlightIds.indexOf(n.id) !== -1;
      entry.select.material.color.setHex(selected ? 0xfbbf24 : 0x2dd4bf);
      entry.mesh.scale.setScalar(hovered ? 1.12 : 1);
      entry.mesh.material.color.setHex(colorFor(n));
      entry.mesh.material.emissive.setHex(hovered || selected ? 0x1e3a5f : 0x000000);
      entry.mesh.material.emissiveIntensity = hovered ? 0.45 : selected ? 0.25 : 0;
      entry.ring.material.color.setHex(colorFor(n));
      entry.ring.material.opacity = hovered ? 1 : 0.8;
    });

    var linkIds = {};
    nextModel.links.forEach(function (l) { linkIds[l.id] = true; });
    Object.keys(this.links).forEach(function (id) {
      if (!linkIds[id]) {
        self.root.remove(self.links[id].line);
        self.links[id].line.geometry.dispose();
        self.links[id].line.material.dispose();
        delete self.links[id];
      }
    });
    nextModel.links.forEach(function (l) {
      if (!self.links[l.id]) self.links[l.id] = self.buildLink(l, positions);
    });

    var packetIds = {};
    nextModel.packets.forEach(function (p) { packetIds[p.id] = true; });
    Object.keys(this.packets).forEach(function (id) {
      if (!packetIds[id]) {
        var entry = self.packets[id];
        self.root.remove(entry.group);
        entry.group.traverse(function (obj) {
          if (obj.geometry) obj.geometry.dispose();
          if (obj.material) obj.material.dispose();
        });
        delete self.packets[id];
      }
    });
    nextModel.packets.forEach(function (p) {
      if (!self.packets[p.id]) self.packets[p.id] = self.buildPacket(p, positions);
    });
  };

  ThreeBackend.prototype.draw = function (nextModel, showSecurity) {
    this.shield.visible = !!showSecurity;
    var self = this;
    nextModel.packets.forEach(function (p) {
      var entry = self.packets[p.id];
      if (!entry || !entry.link) return;
      var t = p.direction === 'reverse' ? 1 - p.t : p.t;
      var a = entry.link.a;
      var b = entry.link.b;
      entry.group.position.set(
        a.x + (b.x - a.x) * t,
        a.y + (b.y - a.y) * t + Math.sin(Math.PI * t) * 0.55,
        a.z + (b.z - a.z) * t
      );
      entry.group.rotation.y += 0.02;
    });
    this.renderer.render(this.scene, this.camera);
  };

  ThreeBackend.prototype.project = function (point) {
    var v = new THREE.Vector3(point.x, point.y, point.z).project(this.camera);
    return {
      x: (v.x * 0.5 + 0.5) * this.width,
      y: (-v.y * 0.5 + 0.5) * this.height,
      visible: v.z < 1
    };
  };

  ThreeBackend.prototype.pick = function (clientX, clientY, rect, nodes) {
    var raycaster = new THREE.Raycaster();
    var mouse = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1
    );
    raycaster.setFromCamera(mouse, this.camera);
    var objects = [];
    var self = this;
    Object.keys(this.nodes).forEach(function (id) {
      var entry = self.nodes[id];
      entry.group.traverse(function (obj) { if (obj.isMesh) { obj.userData.nodeId = id; objects.push(obj); } });
    });
    var hits = raycaster.intersectObjects(objects, false);
    if (!hits.length) return null;
    return hits[0].object.userData.nodeId || null;
  };

  ThreeBackend.prototype.dispose = function () {
    this.root.traverse(function (obj) {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    });
    this.shield.geometry.dispose();
    this.shield.material.dispose();
    this.renderer.dispose();
  };

  function CanvasBackend(el) {
    this.el = el;
    this.ctx = el.getContext('2d');
    this.yaw = 0.55;
    this.pitch = 0.48;
    this.distance = 31;
    this.width = 1;
    this.height = 1;
    this.linksVisible = true;
  }

  CanvasBackend.prototype.resize = function (w, h) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.width = w;
    this.height = h;
    this.el.width = Math.max(1, Math.floor(w * dpr));
    this.el.height = Math.max(1, Math.floor(h * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  CanvasBackend.prototype.rotate = function (dx, dy) {
    this.yaw += dx * 0.005;
    this.pitch = Math.max(0.1, Math.min(1.32, this.pitch + dy * 0.004));
  };

  CanvasBackend.prototype.zoom = function (factor) {
    this.distance = Math.max(15, Math.min(60, this.distance * factor));
  };

  CanvasBackend.prototype.resetView = function () {
    this.yaw = 0.55;
    this.pitch = 0.48;
    this.distance = 31;
  };

  CanvasBackend.prototype.sync = function () {};

  CanvasBackend.prototype.project = function (p) {
    var cy = Math.cos(this.yaw), sy = Math.sin(this.yaw);
    var x1 = p.x * cy - p.z * sy;
    var z1 = p.x * sy + p.z * cy;
    var cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    var y2 = p.y * cp - z1 * sp;
    var z2 = p.y * sp + z1 * cp;
    var focal = Math.min(this.width, this.height) * 1.3;
    var scale = focal / Math.max(5, this.distance + z2);
    return {
      x: this.width / 2 + x1 * scale,
      y: this.height / 2 - y2 * scale + 18,
      visible: true,
      scale: scale
    };
  };

  CanvasBackend.prototype.pick = function (clientX, clientY, rect, nodes) {
    var x = clientX - rect.left;
    var y = clientY - rect.top;
    var best = null;
    var bestDist = 22;
    var self = this;
    (nodes || []).forEach(function (node) {
      var p = self.project(node);
      var dx = p.x - x, dy = p.y - y;
      var d = Math.sqrt(dx*dx + dy*dy);
      if (d < bestDist) { bestDist = d; best = node.id; }
    });
    return best;
  };

  CanvasBackend.prototype.draw = function (nextModel, showSecurity) {
    var ctx = this.ctx;
    var self = this;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.strokeStyle = 'rgba(44, 91, 139, 0.28)';
    ctx.lineWidth = 1;
    for (var g = -20; g <= 20; g += 5) {
      var g1 = this.project({ x: g, y: -1.35, z: -20 });
      var g2 = this.project({ x: g, y: -1.35, z: 20 });
      var g3 = this.project({ x: -20, y: -1.35, z: g });
      var g4 = this.project({ x: 20, y: -1.35, z: g });
      ctx.beginPath(); ctx.moveTo(g1.x, g1.y); ctx.lineTo(g2.x, g2.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(g3.x, g3.y); ctx.lineTo(g4.x, g4.y); ctx.stroke();
    }

    if (showSecurity) {
      var c = this.project({ x: 0, y: 0, z: 0 });
      ctx.strokeStyle = 'rgba(45, 212, 191, 0.35)';
      ctx.setLineDash([4, 5]);
      ctx.beginPath();
      ctx.ellipse(c.x, c.y, 78, 54, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    if (this.linksVisible) {
      nextModel.links.forEach(function (link) {
        var a = self.project(link.a);
        var b = self.project(link.b);
        ctx.strokeStyle = link.kind === 'attack' ? '#ef4444'
          : link.kind === 'task' ? '#fbbf24'
            : link.state === 'offline' ? '#475569'
              : link.state === 'connecting' ? '#f59e0b' : '#38bdf8';
        ctx.lineWidth = link.kind === 'connection' ? 1.4 : 2;
        ctx.globalAlpha = link.state === 'offline' ? 0.45 : 0.85;
        ctx.setLineDash(link.state === 'offline' || link.state === 'connecting' || link.kind === 'attack' ? [6, 5] : []);
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;
      });
    }

    nextModel.nodes.forEach(function (node) {
      var p = self.project(node);
      var size = node.kind === 'central' ? 22 : node.kind === 'task' ? 8 : 13;
      ctx.fillStyle = colorHex(node);
      ctx.globalAlpha = 0.92;
      ctx.fillRect(p.x - size / 2, p.y - size / 2, size, size);
      ctx.strokeStyle = 'rgba(190, 226, 255, 0.65)';
      ctx.lineWidth = 1;
      ctx.strokeRect(p.x - size / 2, p.y - size / 2, size, size);
      ctx.globalAlpha = 1;
      if (nextModel.highlightIds.indexOf(node.id) !== -1) {
        ctx.strokeStyle = '#2dd4bf';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(p.x, p.y, size + 7, 0, Math.PI * 2); ctx.stroke();
      }
      if (nextModel.selectedDeviceId === node.id || nextModel.hoverId === node.id) {
        ctx.strokeStyle = nextModel.selectedDeviceId === node.id ? '#fbbf24' : '#7dd3fc';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(p.x, p.y, size + 11, 0, Math.PI * 2); ctx.stroke();
      }
    });

    nextModel.packets.forEach(function (packet) {
      var link = packet.link;
      if (!link) return;
      var t = packet.direction === 'reverse' ? 1 - packet.t : packet.t;
      var a = self.project(link.a);
      var b = self.project(link.b);
      var x = a.x + (b.x - a.x) * t;
      var y = a.y + (b.y - a.y) * t - Math.sin(Math.PI * t) * 12;
      ctx.fillStyle = packet.kind === 'attack' ? '#ef4444' : packet.kind === 'task' ? '#fbbf24' : '#60a5fa';
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 10;
      ctx.fillRect(x - 4, y - 5, 8, 10);
      ctx.shadowBlur = 0;
    });
  };

  CanvasBackend.prototype.dispose = function () {
    this.ctx.clearRect(0, 0, this.width, this.height);
  };

  function createBackend() {
    if (window.THREE) {
      try {
        var webgl = document.createElement('canvas');
        if (webgl.getContext('webgl2') || webgl.getContext('webgl')) {
          return { backend: new ThreeBackend(canvas), engine: 'THREE.JS / WEBGL' };
        }
      } catch (error) {
        console.warn('WebGL unavailable, using Canvas2D fallback', error);
      }
    }
    return { backend: new CanvasBackend(canvas), engine: 'CANVAS2D FALLBACK' };
  }

  function findNode(id) {
    for (var i = 0; i < model.nodes.length; i += 1) {
      if (model.nodes[i].id === id) return model.nodes[i];
    }
    return null;
  }

  function findLink(id) {
    for (var i = 0; i < model.links.length; i += 1) {
      if (model.links[i].id === id) return model.links[i];
    }
    return null;
  }

  function addEvent(kind, text) {
    state.events.unshift({ kind: kind, text: text, at: Date.now() });
    if (state.events.length > 8) state.events.length = 8;
    renderEvents();
  }

  function renderEvents() {
    if (!eventList) return;
    eventList.textContent = '';
    state.events.forEach(function (event) {
      var li = document.createElement('li');
      var badge = document.createElement('span');
      badge.className = 'dt3d-event-kind ' + (event.kind === 'sim' ? 'sim' : event.kind === 'blocked' ? 'blocked' : '');
      badge.textContent = event.kind.toUpperCase();
      li.appendChild(badge);
      li.appendChild(document.createTextNode(event.text));
      eventList.appendChild(li);
    });
  }

  function setMode(simulated) {
    state.forceSim = !!simulated;
    updateModeBadge();
  }

  function updateModeBadge() {
    if (!modeBadge) return;
    var demo = state.workflow.mode === 'demo';
    var simulated = state.forceSim || state.simulatedCount > 0;
    modeBadge.textContent = demo ? 'DEMONSTRATION MODE — SIMULATED DATA'
      : simulated ? 'SIMULATED EVENT - NOT LIVE' : 'LIVE BACKEND DATA';
    modeBadge.classList.toggle('is-simulated', demo || simulated);
    if (runModeBadge) {
      runModeBadge.textContent = demo ? 'DEMONSTRATION MODE' : 'LIVE BACKEND';
      runModeBadge.classList.toggle('is-demo', demo);
    }
  }

  function setChip(name, text, mode) {
    var chip = stageChips[name];
    if (!chip) return;
    chip.textContent = text;
    chip.classList.toggle('is-active', mode === 'active');
    chip.classList.toggle('is-blocked', mode === 'blocked');
  }

  function setDetail(text) {
    if (detailNode) detailNode.textContent = text;
  }

  function updateStats(server) {
    var values = {
      'dt3d-stat-connected': server.connected_mecs,
      'dt3d-stat-registered': server.registered_mecs,
      'dt3d-stat-tasks': server.active_tasks,
      'dt3d-stat-transfers': server.active_transfers,
      'dt3d-stat-events': (state.data && state.data.security_events ? state.data.security_events.length : 0)
    };
    Object.keys(values).forEach(function (id) {
      var el = byId(id);
      if (el) el.textContent = String(values[id]);
    });
  }

  function workflowBackendStage(index) {
    var stages = state.data && state.data.workflow && state.data.workflow.stages
      ? state.data.workflow.stages : [];
    return stages[index] || null;
  }

  function formatWorkflowTime(ms) {
    var seconds = Math.max(0, Math.floor(ms / 1000));
    return String(Math.floor(seconds / 60)).padStart(2, '0') + ':'
      + String(seconds % 60).padStart(2, '0');
  }

  function workflowTarget() {
    if (state.policy === 'CLOUD_ALLOWED') return 'CLOUD';
    if (state.policy === 'TRUSTED_EDGE') {
      var mec = state.eligible.filter(function (id) { return id.indexOf('MEC-') === 0; })[0];
      if (mec && findNode(mec)) return mec;
      var connected = (state.data && state.data.mec_devices || []).filter(function (item) {
        return item.connection_state === 'CONNECTED';
      })[0];
      if (connected && findNode(connected.device_id)) return connected.device_id;
    }
    return 'LOCAL';
  }

  function workflowRecordId() {
    var latest = state.data && state.data.workflow ? state.data.workflow.latest_upload : null;
    return latest && latest.upload_id ? latest.upload_id : 'Not available';
  }

  function populateWorkflowUI() {
    if (workflowStageSelect && workflowStageSelect.options.length !== WORKFLOW_STAGES.length) {
      workflowStageSelect.textContent = '';
      WORKFLOW_STAGES.forEach(function (definition, index) {
        var option = document.createElement('option');
        option.value = String(index);
        option.textContent = (index + 1) + '. ' + definition.title;
        workflowStageSelect.appendChild(option);
      });
    }
    if (workflowSteps && !workflowSteps.children.length) {
      WORKFLOW_STAGES.forEach(function (definition, index) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'dt3d-workflow-step';
        button.setAttribute('data-workflow-step', String(index));
        button.title = definition.title;
        on(button, 'click', function () { jumpToWorkflowStage(index); });
        workflowSteps.appendChild(button);
      });
    }
    renderWorkflowSteps();
  }

  function renderWorkflowSteps() {
    if (!workflowSteps) return;
    var index = state.workflow.index;
    Array.prototype.forEach.call(workflowSteps.querySelectorAll('[data-workflow-step]'), function (button) {
      var step = Number(button.getAttribute('data-workflow-step'));
      var backendStage = workflowBackendStage(step);
      var status = backendStage ? backendStage.status : 'PENDING';
      button.className = 'dt3d-workflow-step'
        + (step < index || state.workflow.completed ? ' is-complete' : '')
        + (step === index && !state.workflow.completed ? ' is-active' : '');
      button.textContent = (step + 1) + '. ' + WORKFLOW_STAGES[step].title + ' — ' + status;
    });
  }

  function renderWorkflowUI() {
    var index = state.workflow.index;
    var definition = WORKFLOW_STAGES[index];
    var backendStage = workflowBackendStage(index);
    var demo = state.workflow.mode === 'demo';
    var speed = state.workflow.speed || 1;
    var prior = 0;
    for (var i = 0; i < index; i += 1) prior += WORKFLOW_STAGES[i].duration / speed;
    var elapsed = prior + state.workflow.elapsed;
    var total = WORKFLOW_TOTAL_MS / speed;
    var percent = state.workflow.completed ? 100 : clamp((elapsed / total) * 100, 0, 99);
    if (workflowKicker) {
      workflowKicker.textContent = 'STAGE ' + (index + 1) + ' / ' + WORKFLOW_STAGES.length
        + (demo ? ' · SIMULATED' : '');
    }
    if (workflowStatus) {
      workflowStatus.textContent = state.workflow.completed ? 'Workflow Complete' : definition.title;
    }
    if (workflowDetail) {
      workflowDetail.textContent = demo ? definition.description + ' DEMONSTRATION MODE — SIMULATED DATA.'
        : backendStage && backendStage.detail ? backendStage.detail : definition.description;
    }
    if (workflowProgressFill) workflowProgressFill.style.width = percent.toFixed(1) + '%';
    if (workflowProgress) workflowProgress.setAttribute('aria-valuenow', String(Math.round(percent)));
    if (workflowTime) {
      workflowTime.textContent = 'Step ' + (index + 1) + ' / ' + WORKFLOW_STAGES.length
        + ' · ' + formatWorkflowTime(elapsed) + ' / ' + formatWorkflowTime(total);
    }
    if (workflowStageSelect) workflowStageSelect.value = String(index);
    renderWorkflowSteps();
  }

  function updateWorkflowStatusPanel() {
    var index = state.workflow.index;
    var definition = WORKFLOW_STAGES[index];
    var backendStage = workflowBackendStage(index);
    var demo = state.workflow.mode === 'demo';
    if (currentDataSource) {
      currentDataSource.textContent = demo ? 'SIMULATED DATA'
        : backendStage && backendStage.data_source === 'BACKEND_CAPABILITY' ? 'BACKEND CAPABILITY'
          : 'BACKEND RECORD';
      currentDataSource.classList.toggle('is-demo', demo);
    }
    if (currentSource) currentSource.textContent = definition.source;
    if (currentDestination) currentDestination.textContent = definition.destination;
    if (currentTask) currentTask.textContent = demo
      ? 'DEMO-TASK-' + String(index + 1).padStart(3, '0') : workflowRecordId();
    if (currentArtifact) currentArtifact.textContent = demo
      ? 'SIMULATED STAGE ARTIFACT' : backendStage ? backendStage.status : 'BACKEND RECORD';
    if (currentDetail) {
      currentDetail.textContent = demo ? definition.description + ' No backend record was created.'
        : backendStage && backendStage.detail ? backendStage.detail : definition.description;
    }
  }

  function applyWorkflowVisuals(index, quiet) {
    var definition = WORKFLOW_STAGES[index];
    var demo = state.workflow.mode === 'demo';
    var target = workflowTarget();
    var destination = definition.destination;
    if (definition.visual === 'selection' || definition.visual === 'transfer'
      || definition.visual === 'task' || definition.visual === 'result' || definition.visual === 'completion') {
      destination = target;
    }
    if (!findNode(destination)) destination = 'CENTRAL';
    model.highlightIds = definition.visual === 'policy' ? state.eligible.slice()
      : definition.visual === 'audit' ? ['ATTACKER', 'CENTRAL']
        : [definition.source, destination];

    var packetVisuals = ['client', 'upload', 'transfer', 'task', 'result', 'audit'];
    if (packetVisuals.indexOf(definition.visual) === -1 || quiet || !state.showTransfers) {
      dirty = true;
      return;
    }
    var linkId = ensureTransferLink(definition.source, destination, 'workflow');
    var speed = state.workflow.speed || 1;
    addPacket({
      id: 'workflow-' + definition.id + '-' + state.workflow.token + '-' + index,
      linkId: linkId,
      label: (demo ? 'SIM-' : 'LIVE-') + definition.id.toUpperCase(),
      kind: definition.visual === 'audit' ? 'attack' : definition.visual === 'task' ? 'task' : 'transfer',
      simulated: demo,
      duration: reducedMotion ? 900 : Math.min(3000, definition.duration / speed * 0.7),
      onDone: quiet ? null : function () {
        addEvent(demo ? 'sim' : 'workflow', (demo ? 'SIMULATED ' : 'BACKEND ') + definition.title
          + ': ' + definition.source + ' -> ' + destination + '.');
      }
    });
  }

  function syncWorkflowPlayButton() {
    var button = document.querySelector('[data-dt3d-action="workflow-play"]');
    if (!button) return;
    if (!state.workflow.active || state.workflow.completed) button.textContent = 'Run Guided Workflow';
    else if (state.workflow.playing) button.textContent = 'Pause Workflow';
    else button.textContent = 'Resume Workflow';
  }

  function setAnimationPaused(paused) {
    state.paused = !!paused;
    Array.prototype.forEach.call(document.querySelectorAll('[data-dt3d-action="pause"]'), function (button) {
      button.setAttribute('aria-pressed', state.paused ? 'true' : 'false');
      button.textContent = state.paused ? 'Resume Animation' : 'Pause Animation';
    });
    dirty = true;
  }

  function beginWorkflowStage(index, quiet) {
    state.workflow.index = clamp(index, 0, WORKFLOW_STAGES.length - 1);
    state.workflow.elapsed = 0;
    renderWorkflowUI();
    updateWorkflowStatusPanel();
    applyWorkflowVisuals(state.workflow.index, !!quiet);
    syncWorkflowPlayButton();
  }

  function startWorkflow() {
    state.workflow.token += 1;
    state.workflow.active = true;
    state.workflow.playing = true;
    state.workflow.completed = false;
    state.workflow.index = 0;
    state.workflow.elapsed = 0;
    setAnimationPaused(false);
    updateModeBadge();
    beginWorkflowStage(0, false);
    addEvent(state.workflow.mode === 'demo' ? 'sim' : 'workflow',
      (state.workflow.mode === 'demo' ? 'SIMULATED ' : 'BACKEND ')
      + 'guided workflow started: ' + WORKFLOW_STAGES.length + ' stages.');
    syncWorkflowPlayButton();
  }

  function toggleWorkflowPlay() {
    if (!state.workflow.active || state.workflow.completed) {
      startWorkflow();
      return;
    }
    state.workflow.playing = !state.workflow.playing;
    if (state.workflow.playing) setAnimationPaused(false);
    syncWorkflowPlayButton();
  }

  function advanceWorkflow(direction) {
    if (!state.workflow.active || state.workflow.completed) startWorkflow();
    beginWorkflowStage(state.workflow.index + direction, false);
  }

  function jumpToWorkflowStage(index) {
    if (!state.workflow.active || state.workflow.completed) startWorkflow();
    beginWorkflowStage(index, false);
  }

  function restartWorkflow() {
    startWorkflow();
  }

  function finishWorkflow() {
    state.workflow.playing = false;
    state.workflow.completed = true;
    state.workflow.elapsed = 0;
    renderWorkflowUI();
    syncWorkflowPlayButton();
    addEvent(state.workflow.mode === 'demo' ? 'sim' : 'workflow',
      state.workflow.mode === 'demo'
        ? 'SIMULATED guided workflow complete. No backend records were created.'
        : 'Guided walkthrough complete using recorded backend data.');
  }

  function updateWorkflow(ms, now) {
    var workflow = state.workflow;
    if (!workflow.active || !workflow.playing || document.hidden) return;
    var definition = WORKFLOW_STAGES[workflow.index];
    var duration = definition.duration / (workflow.speed || 1);
    workflow.elapsed += ms;
    if (workflow.elapsed >= duration) {
      if (workflow.index >= WORKFLOW_STAGES.length - 1) finishWorkflow();
      else beginWorkflowStage(workflow.index + 1, false);
      return;
    }
    if (now - workflow.lastPaint > 120) {
      workflow.lastPaint = now;
      renderWorkflowUI();
    }
  }

  function setWorkflowMode(mode) {
    state.workflow.mode = mode === 'demo' ? 'demo' : 'live';
    if (runModeSelect) runModeSelect.value = state.workflow.mode;
    updateModeBadge();
    renderWorkflowUI();
    updateWorkflowStatusPanel();
    if (state.workflow.active) beginWorkflowStage(state.workflow.index, true);
    addEvent(state.workflow.mode === 'demo' ? 'sim' : 'workflow', state.workflow.mode === 'demo'
      ? 'Demonstration mode enabled. All walkthrough data is simulated.'
      : 'Live backend mode enabled. Recorded data only.');
  }

  function populateAttackScenarios() {
    if (!attackSelect || attackSelect.options.length) return;
    var catalog = state.data && state.data.simulation_catalog && state.data.simulation_catalog.length
      ? state.data.simulation_catalog : ATTACK_SCENARIOS;
    catalog.forEach(function (scenario) {
      var option = document.createElement('option');
      option.value = scenario.id || scenario.type;
      option.textContent = scenario.label;
      attackSelect.appendChild(option);
    });
  }

  function selectedAttackScenario() {
    var selectedId = attackSelect && attackSelect.value;
    var catalog = state.data && state.data.simulation_catalog && state.data.simulation_catalog.length
      ? state.data.simulation_catalog : ATTACK_SCENARIOS;
    for (var i = 0; i < catalog.length; i += 1) {
      if ((catalog[i].id || catalog[i].type) === selectedId) return catalog[i];
    }
    return catalog[0] || ATTACK_SCENARIOS[0];
  }

  function renderSecurityLayers() {
    if (!securityLayers) return;
    var layers = state.data && state.data.security_layers ? state.data.security_layers : [];
    if (!layers.length) {
      securityLayers.innerHTML = '<span class="dt3d-security-placeholder">No security layer records available.</span>';
      return;
    }
    securityLayers.textContent = '';
    layers.forEach(function (layer) {
      var item = document.createElement('div');
      item.className = 'dt3d-security-layer';
      var head = document.createElement('div');
      head.className = 'dt3d-security-layer-head';
      var label = document.createElement('strong');
      label.textContent = layer.label;
      var status = document.createElement('span');
      var statusClass = layer.status === 'ENFORCED' ? 'is-enforced'
        : layer.status === 'PARTIAL' ? 'is-partial'
          : layer.status === 'POLICY_ONLY' ? 'is-policy-only' : '';
      status.className = 'dt3d-security-status ' + statusClass;
      status.textContent = layer.status.replace('_', ' ');
      var focus = document.createElement('button');
      focus.type = 'button';
      focus.textContent = 'Focus';
      focus.title = 'Highlight the nodes related to ' + layer.label;
      on(focus, 'click', function () { focusSecurityLayer(layer); });
      head.appendChild(label);
      head.appendChild(status);
      head.appendChild(focus);
      var evidence = document.createElement('p');
      evidence.textContent = layer.evidence;
      item.appendChild(head);
      item.appendChild(evidence);
      securityLayers.appendChild(item);
    });
    var enforced = layers.filter(function (layer) { return layer.status === 'ENFORCED'; }).length;
    if (securitySummary) securitySummary.textContent = enforced + ' / ' + layers.length + ' ENFORCED';
  }

  function focusSecurityLayer(layer) {
    var targets = {
      upload_validation: ['CLIENT', 'CENTRAL'],
      authentication_authorization: ['CENTRAL', 'MEC'],
      privacy_aware_scheduling: ['CENTRAL', 'CLOUD'],
      resource_trust_availability: ['CENTRAL', 'LOCAL'],
      security_audit: ['ATTACKER', 'CENTRAL'],
      data_protection: ['CENTRAL', 'LOCAL']
    };
    model.highlightIds = (targets[layer.id] || ['CENTRAL']).filter(function (id) { return !!findNode(id); });
    if (!model.highlightIds.length) model.highlightIds = ['CENTRAL'];
    dirty = true;
    addEvent('security', 'Security layer focused: ' + layer.label + ' (' + layer.status + ').');
  }

  function showDeviceDetails() {
    var target = state.selectedDeviceId;
    if (!target) {
      var devices = model.nodes.filter(isClickableNode);
      target = devices.length ? devices[0].id : null;
    }
    if (target) openDeviceDetails(target);
  }

  function showSecurityLayers() {
    if (!securityPanel) return;
    securityPanel.hidden = false;
    if (securityPanel.scrollIntoView) securityPanel.scrollIntoView({ block: 'nearest' });
    var first = securityPanel.querySelector('button');
    if (first && first.focus) first.focus();
  }

  function buildModel(data) {
    var nodes = [];
    var links = [];
    var mecs = data.mec_devices || [];
    var tasks = data.tasks || [];
    var tiers = {};
    (data.tiers || []).forEach(function (tier) { tiers[tier.destination_id] = tier; });

    nodes.push({ id: 'CENTRAL', label: 'SecureDT Central Server', kind: 'central', status: 'connected', x: 0, y: 0, z: 0, detail: data.server.label });
    nodes.push({ id: 'CLIENT', label: 'Dataset Submission Client', kind: 'client', status: 'connected', x: -14, y: 1.2, z: 5.5, detail: 'WEB_UPLOAD_CLIENT' });
    nodes.push({ id: 'LOCAL', label: 'LOCAL WORKSTATION', kind: 'local', status: 'connected', x: -11, y: 0.2, z: 2.5 });
    nodes.push({ id: 'CLOUD', label: tiers.CLOUD_STORAGE && tiers.CLOUD_STORAGE.is_emulator ? 'CLOUD EMULATOR' : 'CLOUD TIER', kind: 'cloud', status: 'connected', x: 11, y: 1.4, z: -1.5 });
    nodes.push({ id: 'MEC_STORAGE', label: 'MEC STORAGE TIER', kind: 'edge-store', status: 'connected', x: 0.5, y: 0.4, z: -9 });

    var radius = 8.6;
    mecs.forEach(function (mec, index) {
      var angle = (index / Math.max(1, mecs.length)) * Math.PI * 2 - Math.PI / 2;
      var r = radius + (index % 2) * 0.9;
      nodes.push({
        id: mec.device_id,
        label: mec.device_id,
        kind: 'mec',
        status: mec.connection_state === 'CONNECTED' ? 'connected'
          : mec.connection_state === 'CONNECTING' ? 'connecting' : 'offline',
        x: Math.cos(angle) * r,
        y: 0.1,
        z: Math.sin(angle) * r,
        detail: mec.telemetry_mode + ' | tasks ' + mec.active_tasks
      });
      links.push({
        id: 'central-' + mec.device_id,
        from: 'CENTRAL',
        to: mec.device_id,
        kind: 'connection',
        state: mec.connection_state === 'CONNECTED' ? 'connected'
          : mec.connection_state === 'CONNECTING' ? 'connecting' : 'offline'
      });
    });

    var taskCount = 0;
    tasks.forEach(function (task) {
      if (taskCount >= 6) return;
      if (task.status !== 'ASSIGNED' && task.status !== 'RUNNING') return;
      var parent = findNodeById(nodes, task.assigned_node);
      if (!parent || parent.kind !== 'mec') return;
      var factor = 1.32;
      var taskId = 'TASK-' + shortId(task.task_id).replace(/[^A-Za-z0-9_-]/g, '');
      nodes.push({
        id: taskId,
        label: shortId(task.task_id),
        kind: 'task',
        status: 'connected',
        x: parent.x * factor,
        y: parent.y + 0.8,
        z: parent.z * factor,
        detail: task.privacy_policy + ' | ' + task.status
      });
      links.push({ id: 'tasklink-' + taskId, from: parent.id, to: taskId, kind: 'task', state: 'connected' });
      taskCount += 1;
    });

    links.push({ id: 'client-CENTRAL', from: 'CLIENT', to: 'CENTRAL', kind: 'connection', state: 'connected' });
    links.push({ id: 'central-LOCAL', from: 'CENTRAL', to: 'LOCAL', kind: 'connection', state: 'connected' });
    links.push({ id: 'central-CLOUD', from: 'CENTRAL', to: 'CLOUD', kind: 'connection', state: 'connected' });
    links.push({ id: 'central-MEC_STORAGE', from: 'CENTRAL', to: 'MEC_STORAGE', kind: 'connection', state: 'connected' });
    nodes.push({ id: 'ATTACKER', label: 'Simulated Attacker', kind: 'attacker', status: 'simulated', x: 0, y: 2.8, z: -15 });

    links.forEach(function (link) {
      link.a = findNodeById(nodes, link.from);
      link.b = findNodeById(nodes, link.to);
    });

    model.nodes = nodes;
    model.links = links;
    model.packets = [];
    model.highlightIds = [];
    return { tiers: tiers, tasks: tasks };
  }

  function findNodeById(nodes, id) {
    for (var i = 0; i < nodes.length; i += 1) {
      if (nodes[i].id === id) return nodes[i];
    }
    return null;
  }

  function destinationNodeId(destination) {
    if (destination === 'LOCAL_STORAGE') return 'LOCAL';
    if (destination === 'MEC_STORAGE') return 'MEC_STORAGE';
    if (destination === 'CLOUD_STORAGE') return 'CLOUD';
    return 'CENTRAL';
  }

  function ensureTransferLink(sourceId, destId, kind) {
    var linkId = kind + '-' + sourceId + '-' + destId;
    if (!findLink(linkId)) {
      var link = { id: linkId, from: sourceId, to: destId, kind: kind, state: 'connected' };
      link.a = findNode(sourceId);
      link.b = findNode(destId);
      model.links.push(link);
    }
    return linkId;
  }

  function addPacket(options) {
    if (!state.showTransfers && options.kind !== 'attack' && options.kind !== 'task') return;
    var link = findLink(options.linkId);
    if (!link) return;
    var packet = {
      id: options.id,
      linkId: options.linkId,
      link: link,
      label: options.label,
      kind: options.kind,
      direction: options.direction || 'forward',
      t: 0,
      elapsed: 0,
      duration: options.duration || 2600,
      simulated: !!options.simulated,
      onDone: options.onDone || null,
      staticOnly: !!options.staticOnly
    };
    if (reducedMotion && !packet.staticOnly) {
      packet.staticOnly = true;
      packet.t = 0.5;
      packet.expiresAt = (window.performance && performance.now ? performance.now() : Date.now()) + 1600;
    }
    model.packets.push(packet);
    dirty = true;
  }

  function policyAllowed(policy, destinationId) {
    var info = state.data && state.data.policies ? state.data.policies[policy] : null;
    if (!info) return false;
    return (info.eligible_resources || []).indexOf(destinationId) !== -1;
  }

  function applyRecordedActivity(data) {
    (data.transfers || []).forEach(function (transfer) {
      var key = transfer.transfer_id + ':' + transfer.state;
      if (state.seenTransfers[key]) return;
      state.seenTransfers[key] = true;
      var dest = destinationNodeId(transfer.destination);
      var source = transfer.source_known && findNode(transfer.source) ? transfer.source : 'CENTRAL';
      if (transfer.state === 'TRANSFERRING') {
        var linkId = ensureTransferLink(source, dest, 'transfer');
        addPacket({
          id: 'real-transfer-' + transfer.transfer_id,
          linkId: linkId,
          label: transfer.label,
          kind: 'transfer',
          duration: 3200,
          onDone: function () {
            addEvent('transfer', 'Backend transfer in progress: ' + transfer.label + ' -> ' + transfer.destination);
          }
        });
      } else {
        addEvent(transfer.state === 'BLOCKED' || transfer.state === 'FAILED' ? 'blocked' : 'transfer',
          'Backend record: ' + transfer.label + ' ' + transfer.state + ' -> ' + transfer.destination);
      }
    });

    (data.tasks || []).forEach(function (task) {
      var key = task.task_id + ':' + task.status + ':' + task.assigned_node;
      if (state.seenTasks[key]) return;
      state.seenTasks[key] = true;
      if (task.status !== 'ASSIGNED' && task.status !== 'RUNNING') return;
      if (!findNode(task.assigned_node)) return;
      var linkId = ensureTransferLink('CENTRAL', task.assigned_node, 'dispatch');
      addPacket({
        id: 'real-task-' + task.task_id + '-' + key.length,
        linkId: linkId,
        label: shortId(task.task_id),
        kind: 'task',
        duration: 2800,
        onDone: function () {
          addEvent('dispatch', 'GA assignment: ' + shortId(task.task_id) + ' -> ' + task.assigned_node);
        }
      });
    });

    (data.security_events || []).slice(0, 4).forEach(function (event) {
      addEvent(event.blocked ? 'blocked' : 'recorded',
        'Backend audit: ' + event.event_type + ' (' + event.verdict + ')');
    });

    var decisions = data.scheduling && data.scheduling.decisions ? data.scheduling.decisions : [];
    if (decisions.length) {
      state.selectedResource = decisions[0].selected_resource;
      setDetail('Recorded GA decision: ' + shortId(decisions[0].task_id) + ' -> ' +
        decisions[0].selected_resource + ' (' + decisions[0].algorithm + ')');
    } else {
      setDetail('No recorded GA decisions yet. Eligible candidates are computed by the live Policy Engine.');
    }
  }

  function applyPolicyFocus() {
    var info = state.data && state.data.policies ? state.data.policies[state.policy] : null;
    state.eligible = info ? info.eligible_resources || [] : [];
    var tiers = info ? info.allowed_tiers || [] : [];
    setChip('policy', 'POLICY CHECK: ' + state.policy, 'active');
    setChip('destination', 'DESTINATION VALIDATED: ' + (tiers.join(' / ') || 'NONE'), tiers.length ? 'active' : 'blocked');
    setChip('authorized', 'TASK AUTHORIZED: ' + state.eligible.length + ' ELIGIBLE', state.eligible.length ? 'active' : 'blocked');
    model.highlightIds = state.eligible.slice();
    if (protectionNote) {
      protectionNote.textContent = 'Protection policy visualization only. The backend enforces placement rules; ' +
        'no transport encryption is confirmed by the application, so this shield does not indicate encryption.';
    }
    dirty = true;
  }

  function applyData(data) {
    state.data = data;
    var meta = buildModel(data);
    applyRecordedActivity(data);
    applyPolicyFocus();
    populateWorkflowUI();
    populateAttackScenarios();
    renderSecurityLayers();
    updateStats(data.server || {});
    if (state.workflow.active) beginWorkflowStage(state.workflow.index, true);
    else {
      renderWorkflowUI();
      updateWorkflowStatusPanel();
    }
    updateModeBadge();
    if (emptyNotice) emptyNotice.hidden = (data.mec_devices || []).length > 0;
    if (engineBadge) engineBadge.textContent = backend.engine + (reducedMotion ? ' | REDUCED MOTION' : '');
    model.hoverId = state.hoverId;
    model.selectedDeviceId = state.selectedDeviceId;
    backend.sync(model);
    if (detailsPanel && !detailsPanel.hidden && state.selectedDeviceId) renderDeviceDetails(state.selectedDeviceId);
    dirty = true;
  }

  function refresh() {
    fetch(API_URL, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (data) {
        if (dead) return;
        if (!data || data.mode !== 'live') throw new Error('Unexpected scene payload');
        applyData(data);
        if (!state.simulatedCount) setMode(false);
      })
      .catch(function (error) {
        console.error('Digital Twin scene refresh failed', error);
        if (engineBadge) engineBadge.textContent = 'BACKEND UNREACHABLE - LAST SNAPSHOT RETAINED';
      });
  }

  function runTransferSimulation() {
    var policy = state.policy;
    var eligible = state.eligible || [];
    state.simulatedCount += 1;
    var token = ++state.simulationToken;
    setMode(true);
    setChip('policy', 'POLICY CHECK: ' + policy + ' (SIMULATED)', 'active');
    var source = 'LOCAL';
    var dest = policy === 'CLOUD_ALLOWED' ? 'CLOUD'
      : policy === 'TRUSTED_EDGE' ? eligible.filter(function (id) { return id.indexOf('MEC-') === 0; })[0] || 'LOCAL'
        : 'LOCAL';

    if (!policyAllowed(policy, dest)) {
      setChip('destination', 'DESTINATION BLOCKED BY POLICY', 'blocked');
      setChip('result', 'TRANSFER BLOCKED (SIMULATED)', 'blocked');
      addEvent('sim', 'SIMULATED transfer blocked: ' + policy + ' forbids ' + dest + '. No file created.');
      setTimeout(function () { endSimulation(token); }, 1200);
      return;
    }

    setChip('destination', 'DESTINATION VALIDATED: ' + dest, 'active');
    setChip('authorized', 'TASK AUTHORIZED (SIMULATED)', 'active');
    setChip('transfer', 'TRANSFER ACTIVE (SIMULATED)', 'active');
    setChip('result', 'AWAITING RESULT', 'active');
    var label = 'SIM-DATA-' + String(state.simulatedCount).padStart(3, '0');
    var linkId = ensureTransferLink(source, dest, 'sim-transfer');
    addPacket({
      id: label,
      linkId: linkId,
      label: label,
      kind: 'transfer',
      simulated: true,
      duration: reducedMotion ? 900 : 2800,
      onDone: function () {
        setChip('transfer', 'TRANSFER ACTIVITY: NONE', 'active');
        setChip('result', 'COMPLETED (SIMULATED)', 'active');
        addEvent('sim', 'SIMULATED transfer ' + label + ' ' + source + ' -> ' + dest + '. No real file was transferred.');
        endSimulation(token);
      }
    });
    addEvent('sim', 'SIMULATED transfer started: ' + source + ' -> ' + dest + ' (' + policy + ').');
  }

  function runAttackSimulation() {
    var scenario = selectedAttackScenario();
    var scenarioId = scenario.id || scenario.type;
    state.simulatedCount += 1;
    var token = ++state.simulationToken;
    setMode(true);
    var target = scenario.target;
    if (target === 'MEC') {
      var connected = (state.data && state.data.mec_devices || []).filter(function (mec) {
        return mec.connection_state === 'CONNECTED';
      })[0];
      target = connected && findNode(connected.device_id) ? connected.device_id : 'CENTRAL';
    }
    if (!findNode(target)) target = 'CENTRAL';
    var linkId = ensureTransferLink('ATTACKER', target, 'attack');
    var recorded = (state.data && state.data.security_events || []).filter(function (event) {
      return event.event_type === scenarioId;
    })[0];
    setChip('policy', 'SECURITY CHECK (SIMULATED)', 'active');
    setChip('destination', 'TARGET: ' + target, 'active');
    setChip('authorized', 'NO REAL SYSTEM CONTACTED', 'blocked');
    setChip('transfer', 'SIMULATED ATTACK IN FLIGHT', 'blocked');
    setChip('result', 'PENDING', 'blocked');
    addPacket({
      id: 'sim-attack-' + token,
      linkId: linkId,
      label: 'SIM ATTACK',
      kind: 'attack',
      simulated: true,
      duration: reducedMotion ? 900 : 2200,
      onDone: function () {
        var verdict = recorded ? recorded.verdict + ' (BACKEND AUDIT)' : 'NO BACKEND EVENT';
        setChip('result', verdict, 'blocked');
        setChip('transfer', 'SIMULATION COMPLETE', 'blocked');
        addEvent('sim', 'SIMULATED ' + scenario.label + ' -> ' + target + '. ' + verdict + '. '
          + (scenario.backend_evidence || 'Bounded local visualization only.') + ' No real system was contacted.');
        endSimulation(token);
      }
    });
    addEvent('sim', 'SIMULATED attack scenario: ' + scenario.label + ' -> ' + target + '. '
      + (scenario.backend_evidence || 'Bounded local visualization only.') + ' No real attack was performed.');
  }

  function endSimulation(token) {
    if (token !== state.simulationToken) return;
    state.simulatedCount = Math.max(0, state.simulatedCount - 1);
    if (!state.simulatedCount) {
      setMode(false);
      applyPolicyFocus();
      setChip('transfer', 'TRANSFER ACTIVITY: ' + (state.data ? state.data.server.active_transfers : 0), 'active');
      setChip('result', state.data && state.data.server ? 'LIVE SNAPSHOT READY' : 'NO DATA', 'active');
    }
  }

  function labelBounds() {
    var width = stage ? stage.clientWidth : 0;
    var height = stage ? stage.clientHeight : 0;
    var bounds = {
      left: 8,
      top: 8,
      right: Math.max(9, width - 8),
      bottom: Math.max(9, height - 28)
    };
    if (detailsPanel && !detailsPanel.hidden) {
      if (window.innerWidth > 720) {
        bounds.right = Math.max(bounds.left + 120, width - detailsPanel.offsetWidth - 18);
      } else {
        bounds.bottom = Math.max(bounds.top + 80, height - detailsPanel.offsetHeight - 12);
      }
    }
    return bounds;
  }

  function placeLabel(x, y, width, height, placed, bounds) {
    var px = clamp(x, bounds.left + width / 2, Math.max(bounds.left + width / 2, bounds.right - width / 2));
    var py = clamp(y, bounds.top + height / 2, Math.max(bounds.top + height / 2, bounds.bottom - height / 2));
    for (var attempt = 0; attempt < 6; attempt += 1) {
      var collision = null;
      for (var i = 0; i < placed.length; i += 1) {
        var other = placed[i];
        if (Math.abs(px - other.x) < (width + other.w) / 2 + 6
          && Math.abs(py - other.y) < (height + other.h) / 2 + 4) {
          collision = other;
          break;
        }
      }
      if (!collision) break;
      py = collision.y + (collision.h + height) / 2 + 5;
      if (py > bounds.bottom - height / 2) py = bounds.top + height / 2;
    }
    placed.push({ x: px, y: py, w: width, h: height });
    return { x: px, y: py };
  }

  function updateLabels() {
    if (!state.showLabels || !labelLayer) return;
    var current = {};
    var placed = [];
    var bounds = labelBounds();
    model.nodes.forEach(function (node) {
      if (node.kind === 'task' && !state.showLinks) return;
      current[node.id] = true;
      var clickable = isClickableNode(node);
      var el = labelElements[node.id];
      if (!el) {
        el = document.createElement(clickable ? 'button' : 'div');
        if (clickable) {
          el.type = 'button';
          el.setAttribute('data-node-id', node.id);
          on(el, 'click', function (event) {
            event.stopPropagation();
            openDeviceDetails(node.id);
          });
          on(el, 'mouseenter', function () { setHoverNode(node.id); });
          on(el, 'mouseleave', function () { setHoverNode(null); });
          on(el, 'focus', function () { setHoverNode(node.id); });
          on(el, 'blur', function () { setHoverNode(null); });
        }
        labelLayer.appendChild(el);
        labelElements[node.id] = el;
      }
      var projected = backend.project(node);
      el.textContent = node.label + (node.kind === 'mec'
        ? node.status === 'connected' ? ' | CONNECTED' : node.status === 'connecting' ? ' | CONNECTING' : ' | OFFLINE'
        : '');
      el.className = 'dt3d-label'
        + (node.kind === 'central' ? ' is-central' : '')
        + (node.status === 'offline' ? ' is-offline' : '')
        + (node.status === 'connecting' ? ' is-connecting' : '')
        + (node.status === 'simulated' ? ' is-threat' : '')
        + (state.eligible.indexOf(node.id) !== -1 && node.kind === 'mec' ? ' is-selected' : '')
        + (clickable ? ' is-clickable' : '')
        + (state.selectedDeviceId === node.id ? ' is-detail-selected' : '');
      if (clickable) {
        el.setAttribute('aria-label', node.label + ', view device details');
        el.title = 'Click to view device details';
      }
      el.style.display = projected.visible ? '' : 'none';
      if (!projected.visible) return;
      var point = placeLabel(
        projected.x,
        projected.y - (node.kind === 'mec' ? 14 : 0),
        el.offsetWidth || 80,
        el.offsetHeight || 22,
        placed,
        bounds
      );
      el.style.left = point.x + 'px';
      el.style.top = point.y + 'px';
    });
    model.packets.forEach(function (packet) {
      var id = 'packet-' + packet.id;
      current[id] = true;
      var el = labelElements[id];
      if (!el) {
        el = document.createElement('div');
        el.className = 'dt3d-label';
        labelLayer.appendChild(el);
        labelElements[id] = el;
      }
      var link = findLink(packet.linkId);
      if (!link) return;
      var t = packet.direction === 'reverse' ? 1 - packet.t : packet.t;
      var a = link.a || findNode(link.from);
      var b = link.b || findNode(link.to);
      if (!a || !b) return;
      var point3d = {
        x: a.x + (b.x - a.x) * t,
        y: a.y + (b.y - a.y) * t + Math.sin(Math.PI * t) * 0.55,
        z: a.z + (b.z - a.z) * t
      };
      var projected = backend.project(point3d);
      el.textContent = packet.label + (packet.simulated ? ' [SIMULATED]' : ' [BACKEND]');
      el.className = 'dt3d-label' + (packet.kind === 'attack' ? ' is-threat' : '');
      el.style.display = projected.visible && state.showTransfers ? '' : 'none';
      if (!projected.visible || !state.showTransfers) return;
      var point = placeLabel(
        projected.x,
        projected.y - 18,
        el.offsetWidth || 80,
        el.offsetHeight || 18,
        placed,
        bounds
      );
      el.style.left = point.x + 'px';
      el.style.top = point.y + 'px';
    });
    Object.keys(labelElements).forEach(function (id) {
      if (!current[id]) {
        var stale = labelElements[id];
        if (stale.parentNode === labelLayer) labelLayer.removeChild(stale);
        delete labelElements[id];
      }
    });
  }

  function animate(now) {
    if (dead) return;
    var dt = Math.min(0.05, (now - lastFrame) / 1000 || 0);
    lastFrame = now;
    var active = false;
    if (!state.paused && !document.hidden) {
      var remaining = [];
      var hasMotion = false;
      model.packets.forEach(function (packet) {
        if (packet.staticOnly) {
          if (packet.expiresAt && now >= packet.expiresAt) {
            if (packet.onDone) packet.onDone();
            active = true;
          } else {
            remaining.push(packet);
          }
          return;
        }
        packet.elapsed += dt;
        packet.t = Math.min(1, packet.elapsed / (packet.duration / 1000));
        if (packet.t >= 1 && packet.onDone) packet.onDone();
        if (packet.t < 1) {
          remaining.push(packet);
          hasMotion = true;
        } else {
          active = true;
        }
      });
      model.packets = remaining;
      if (hasMotion) active = true;
    }
    if (dirty || active) {
      model.hoverId = state.hoverId;
      model.selectedDeviceId = state.selectedDeviceId;
      backend.sync(model);
      backend.draw(model, state.showSecurity);
      updateLabels();
      dirty = false;
    }
    rafId = window.requestAnimationFrame(animate);
  }

  function resize() {
    var rect = stage.getBoundingClientRect();
    backend.resize(Math.max(1, rect.width), Math.max(1, rect.height));
    dirty = true;
  }

  function setToggle(button, key) {
    state[key] = !state[key];
    button.setAttribute('aria-pressed', state[key] ? 'true' : 'false');
    var labels = {
      showLabels: 'Device Labels',
      showLinks: 'Connection Lines',
      showTransfers: 'Transfer Animation',
      showSecurity: 'Security Layer'
    };
    if (labels[key]) button.textContent = labels[key] + ': ' + (state[key] ? 'On' : 'Off');
    if (key === 'showLinks') backend.linksVisible = state.showLinks;
    if (key === 'showLabels' && labelLayer) labelLayer.style.display = state.showLabels ? '' : 'none';
    dirty = true;
  }

  function bindControls() {
    var controls = document.querySelectorAll('[data-dt3d-action]');
    Array.prototype.forEach.call(controls, function (button) {
      var action = button.getAttribute('data-dt3d-action');
      var handler;
      if (action === 'reset') handler = function () { backend.resetView(); dirty = true; };
      else if (action === 'zoom-in') handler = function () { backend.zoom(0.85); dirty = true; };
      else if (action === 'zoom-out') handler = function () { backend.zoom(1.18); dirty = true; };
      else if (action === 'pause') handler = function () {
        state.paused = !state.paused;
        button.setAttribute('aria-pressed', state.paused ? 'true' : 'false');
        button.textContent = state.paused ? 'Resume Animation' : 'Pause Animation';
        dirty = true;
      };
      else if (action === 'labels') handler = function () { setToggle(button, 'showLabels'); };
      else if (action === 'links') handler = function () { setToggle(button, 'showLinks'); };
      else if (action === 'transfers') handler = function () { setToggle(button, 'showTransfers'); };
      else if (action === 'security') handler = function () { setToggle(button, 'showSecurity'); };
      else if (action === 'transfer-sim') handler = runTransferSimulation;
      else if (action === 'attack-sim') handler = runAttackSimulation;
      else if (action === 'close-details') handler = closeDeviceDetails;
      if (handler) on(button, 'click', handler);
    });

    if (policySelect) {
      on(policySelect, 'change', function () {
        state.policy = policySelect.value;
        applyPolicyFocus();
      });
    }

    var dragging = false;
    var moved = false;
    var downX = 0, downY = 0;
    var lastX = 0;
    var lastY = 0;
    on(canvas, 'pointerdown', function (event) {
      dragging = true; moved = false;
      downX = event.clientX; downY = event.clientY;
      lastX = event.clientX;
      lastY = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    });
    on(canvas, 'pointermove', function (event) {
      if (!dragging) {
        var rect = canvas.getBoundingClientRect();
        var hovered = backend.pick ? backend.pick(event.clientX, event.clientY, rect, model.nodes) : null;
        setHoverNode(hovered && isClickableNode(findNode(hovered)) ? hovered : null);
        return;
      }
      var dx = event.clientX - downX, dy = event.clientY - downY;
      if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
      backend.rotate(event.clientX - lastX, event.clientY - lastY);
      lastX = event.clientX;
      lastY = event.clientY;
      dirty = true;
    });
    on(canvas, 'pointerup', function (event) {
      var wasDragging = dragging;
      dragging = false;
      if (wasDragging && !moved) {
        var rect = canvas.getBoundingClientRect();
        var nodeId = backend.pick ? backend.pick(event.clientX, event.clientY, rect, model.nodes) : null;
        if (nodeId && isClickableNode(findNode(nodeId))) openDeviceDetails(nodeId);
        else if (!nodeId) closeDeviceDetails();
      }
    });
    on(canvas, 'pointercancel', function () { dragging = false; });
    on(canvas, 'pointerleave', function () { setHoverNode(null); });
    on(canvas, 'wheel', function (event) {
      event.preventDefault();
      backend.zoom(event.deltaY > 0 ? 1.08 : 0.92);
      dirty = true;
    }, { passive: false });
    on(canvas, 'keydown', function (event) {
      var handled = true;
      if (event.key === 'ArrowLeft') backend.rotate(-18, 0);
      else if (event.key === 'ArrowRight') backend.rotate(18, 0);
      else if (event.key === 'ArrowUp') backend.rotate(0, -14);
      else if (event.key === 'ArrowDown') backend.rotate(0, 14);
      else if (event.key === '+' || event.key === '=') backend.zoom(0.86);
      else if (event.key === '-') backend.zoom(1.16);
      else if (event.key === '[') cycleDeviceSelection(-1);
      else if (event.key === ']') cycleDeviceSelection(1);
      else if (event.key === 'Enter' || event.key === ' ') {
        var targetId = state.hoverId || state.selectedDeviceId;
        if (!targetId && model.nodes.length) targetId = model.nodes[0].id;
        if (targetId && isClickableNode(findNode(targetId))) openDeviceDetails(targetId);
      } else handled = false;
      if (handled) {
        event.preventDefault();
        dirty = true;
      }
    });

    on(document, 'keydown', function (event) {
      if (event.key === 'Escape' && detailsPanel && !detailsPanel.hidden) {
        event.preventDefault();
        closeDeviceDetails();
      }
    });
    on(document, 'click', function (event) {
      if (!detailsPanel || detailsPanel.hidden) return;
      if (detailsPanel.contains(event.target)) return;
      if (event.target === canvas) return;
      if (event.target && event.target.getAttribute && event.target.getAttribute('data-node-id')) return;
      closeDeviceDetails();
    });

    on(document, 'visibilitychange', function () {
      if (!document.hidden && !state.simulatedCount) refresh();
    });
    on(window, 'resize', resize);
    on(window, 'pagehide', dispose);
  }

  function dispose() {
    if (dead) return;
    dead = true;
    window.clearInterval(pollTimer);
    window.clearTimeout(state.detailsTimer);
    window.cancelAnimationFrame(rafId);
    listeners.forEach(function (entry) {
      entry[0].removeEventListener(entry[1], entry[2], entry[3]);
    });
    backend.dispose();
  }

  var created = createBackend();
  backend = created.backend;
  if (engineBadge) engineBadge.textContent = created.engine;
  bindControls();
  resize();
  refresh();
  pollTimer = window.setInterval(function () {
    if (!document.hidden && !state.simulatedCount) refresh();
  }, POLL_MS);
  rafId = window.requestAnimationFrame(animate);
})();
