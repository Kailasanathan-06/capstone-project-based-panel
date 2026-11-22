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
    eligible: [],
    simulationActive: false,
    simulationToken: 0,
    attackIndex: 0
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
    { type: 'INVALID_MEC_AUTH', target: 'MEC', label: 'Invalid MEC agent credentials' },
    { type: 'ZIP_VALIDATION_ERROR', target: 'CENTRAL', label: 'Invalid dataset archive' },
    { type: 'PRIVACY_POLICY_VIOLATION', target: 'CLOUD', label: 'Privacy policy violation' }
  ];

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

  function storageDestForNode(nodeId) {
    if (nodeId === 'LOCAL') return 'LOCAL_STORAGE';
    if (nodeId === 'MEC_STORAGE') return 'MEC_STORAGE';
    if (nodeId === 'CLOUD') return 'CLOUD_STORAGE';
    return null;
  }

  function ensureStorageModal() {
    var modal = byId('dt3d-storage-modal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'dt3d-storage-modal';
    modal.className = 'dt3d-modal';
    modal.hidden = true;
    modal.innerHTML = '' +
      '<div class="dt3d-modal-backdrop" data-dt3d-close="1"></div>' +
      '<div class="dt3d-modal-panel" role="dialog" aria-modal="true" aria-labelledby="dt3d-storage-title">' +
        '<div class="dt3d-modal-head">' +
          '<div><div class="dt3d-modal-kicker">STORAGE NODE DETAILS</div><h3 id="dt3d-storage-title">Storage</h3><div class="dt3d-modal-sub" id="dt3d-storage-sub"></div></div>' +
          '<button type="button" class="dt3d-ctrl" data-dt3d-close="1">Close</button>' +
        '</div>' +
        '<div class="dt3d-modal-stats" id="dt3d-storage-stats"></div>' +
        '<div class="dt3d-modal-body" id="dt3d-storage-body"><p class="dt3d-empty-note">Click a storage node to load details.</p></div>' +
      '</div>';
    document.body.appendChild(modal);
    modal.addEventListener('click', function (e) {
      if (e.target && e.target.getAttribute('data-dt3d-close')) closeStorageModal();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden) closeStorageModal();
    });
    return modal;
  }

  function closeStorageModal() {
    var modal = byId('dt3d-storage-modal');
    if (modal) modal.hidden = true;
  }

  function openStorageModal(nodeId) {
    var dest = storageDestForNode(nodeId);
    if (!dest) return;
    var modal = ensureStorageModal();
    var title = byId('dt3d-storage-title');
    var sub = byId('dt3d-storage-sub');
    var stats = byId('dt3d-storage-stats');
    var body = byId('dt3d-storage-body');
    modal.hidden = false;
    if (title) title.textContent = dest.replace('_', ' ');
    if (sub) sub.textContent = 'Loading stored data details...';
    if (stats) stats.innerHTML = '';
    if (body) body.innerHTML = '<p class="dt3d-empty-note">Loading...</p>';

    fetch('/api/digital-twin/storage/detail/?destination=' + encodeURIComponent(dest), { credentials: 'same-origin' })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) throw new Error(res.data.error || 'Failed to load storage details');
        renderStorageDetail(res.data);
      })
      .catch(function (err) {
        if (sub) sub.textContent = 'Unable to load storage details';
        if (body) body.innerHTML = '<p class="dt3d-empty-note" style="color:#f87171;">' + esc(err.message || 'Error') + '</p>';
      });
  }

  function renderStorageDetail(d) {
    var title = byId('dt3d-storage-title');
    var sub = byId('dt3d-storage-sub');
    var stats = byId('dt3d-storage-stats');
    var body = byId('dt3d-storage-body');
    if (title) title.textContent = d.name || d.destination_id;
    if (sub) sub.textContent = d.destination_id + ' | ' + (d.destination_type || '') + (d.is_emulator ? ' | Emulator' : '');
    if (stats) {
      stats.innerHTML = [
        ['Capacity', d.capacity], ['Used', d.used], ['Free', d.free],
        ['Replicas', d.replicas_count], ['Inventory Items', d.inventory_items_count], ['Uploads', d.uploads_count]
      ].map(function (kv) {
        return '<div class="dt3d-modal-stat"><span>' + esc(kv[0]) + '</span><strong>' + esc(String(kv[1] == null ? '-' : kv[1])) + '</strong></div>';
      }).join('');
    }
    var html = '';
    html += '<section class="dt3d-modal-section"><h4>Stored Replicas / Files</h4>';
    if (d.replicas && d.replicas.length) {
      html += '<div class="dt3d-table-wrap"><table class="dt3d-modal-table"><thead><tr><th>File</th><th>Size</th><th>Status</th><th>Stored Date/Time</th><th>Verified</th><th>SHA-256</th></tr></thead><tbody>';
      d.replicas.forEach(function (r) {
        html += '<tr><td title="' + esc(r.relative_key || '') + '">' + esc(r.file_name || r.replica_id) + '<div class="dt3d-muted">' + esc(r.dataset_id || '') + '</div></td>' +
          '<td>' + esc(r.file_size || '') + '</td>' +
          '<td><span class="dt3d-pill">' + esc(r.replication_status || '') + '</span></td>' +
          '<td>' + esc(r.stored_at_display || '-') + '</td>' +
          '<td>' + esc(r.last_verified_display || '-') + '</td>' +
          '<td class="dt3d-mono" title="' + esc(r.sha256_checksum || '') + '">' + esc((r.sha256_checksum || '').slice(0, 16)) + (r.sha256_checksum ? '…' : '-') + '</td></tr>';
      });
      html += '</tbody></table></div>';
    } else {
      html += '<p class="dt3d-empty-note">No stored replicas found for this tier.</p>';
    }
    html += '</section>';

    html += '<section class="dt3d-modal-section"><h4>Dataset Inventory Items</h4>';
    if (d.inventory_items && d.inventory_items.length) {
      html += '<div class="dt3d-table-wrap"><table class="dt3d-modal-table"><thead><tr><th>File</th><th>Format</th><th>Size</th><th>Policy</th><th>Status</th><th>Stored Date/Time</th></tr></thead><tbody>';
      d.inventory_items.forEach(function (i) {
        html += '<tr><td title="' + esc(i.relative_path || '') + '">' + esc(i.file_name || '') + '<div class="dt3d-muted">' + esc(i.upload_id || '') + '</div></td>' +
          '<td>' + esc(i.format || '-') + '</td><td>' + esc(i.file_size || '') + '</td>' +
          '<td>' + esc(i.privacy_policy || '-') + '</td><td><span class="dt3d-pill">' + esc(i.status || '') + '</span></td>' +
          '<td>' + esc(i.stored_at_display || '-') + '</td></tr>';
      });
      html += '</tbody></table></div>';
    } else {
      html += '<p class="dt3d-empty-note">No inventory items assigned to this tier.</p>';
    }
    html += '</section>';

    html += '<section class="dt3d-modal-section"><h4>Recent Uploads to Tier</h4>';
    if (d.uploads && d.uploads.length) {
      html += '<div class="dt3d-table-wrap"><table class="dt3d-modal-table"><thead><tr><th>Upload ID</th><th>File</th><th>Size</th><th>Files</th><th>Status</th><th>Date/Time</th></tr></thead><tbody>';
      d.uploads.forEach(function (u) {
        html += '<tr><td class="dt3d-mono">' + esc(u.upload_id || '') + '</td><td>' + esc(u.file_name || '') + '</td><td>' + esc(u.file_size || '') + '</td><td>' + esc(String(u.file_count == null ? '-' : u.file_count)) + '</td><td><span class="dt3d-pill">' + esc(u.status || '') + '</span></td><td>' + esc(u.uploaded_at_display || '-') + '</td></tr>';
      });
      html += '</tbody></table></div>';
    } else {
      html += '<p class="dt3d-empty-note">No uploads recorded for this tier.</p>';
    }
    html += '</section>';
    if (body) body.innerHTML = html;
  }

  function colorFor(node) {
    if (node.kind === 'attacker') return 0xef4444;
    if (node.status === 'offline') return 0x64748b;
    if (node.status === 'connecting') return 0xf59e0b;
    if (node.status === 'simulated') return 0xf59e0b;
    if (node.kind === 'central') return 0x38bdf8;
    if (node.kind === 'cloud') return 0x60a5fa;
    if (node.kind === 'local') return 0x2dd4bf;
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
      entry.select.visible = nextModel.highlightIds.indexOf(n.id) !== -1;
      entry.ring.material.color.setHex(colorFor(n));
      entry.mesh.material.color.setHex(colorFor(n));
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
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(p.x, p.y, size + 7, 0, Math.PI * 2); ctx.stroke();
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
    if (!modeBadge) return;
    modeBadge.textContent = simulated ? 'SIMULATED EVENT - NOT LIVE' : 'LIVE BACKEND DATA';
    modeBadge.classList.toggle('is-simulated', !!simulated);
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

  function buildModel(data) {
    var nodes = [];
    var links = [];
    var mecs = data.mec_devices || [];
    var tasks = data.tasks || [];
    var tiers = {};
    (data.tiers || []).forEach(function (tier) { tiers[tier.destination_id] = tier; });

    nodes.push({ id: 'CENTRAL', label: 'SecureDT Central Server', kind: 'central', status: 'connected', x: 0, y: 0, z: 0, detail: data.server.label });
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
    updateStats(data.server || {});
    if (emptyNotice) emptyNotice.hidden = (data.mec_devices || []).length > 0;
    if (engineBadge) engineBadge.textContent = backend.engine + (reducedMotion ? ' | REDUCED MOTION' : '');
    backend.sync(model);
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
    var scenario = ATTACK_SCENARIOS[state.attackIndex % ATTACK_SCENARIOS.length];
    state.attackIndex += 1;
    state.simulatedCount += 1;
    var token = ++state.simulationToken;
    setMode(true);
    var target = scenario.target === 'MEC'
      ? (state.data && state.data.server.connected_mecs > 0
        ? (state.data.mec_devices.filter(function (m) { return m.connection_state === 'CONNECTED'; })[0] || {}).device_id || 'CENTRAL'
        : 'CENTRAL')
      : scenario.target;
    if (!findNode(target)) target = 'CENTRAL';
    var linkId = ensureTransferLink('ATTACKER', target, 'attack');
    var recorded = (state.data && state.data.security_events || []).filter(function (e) {
      return e.event_type === scenario.type;
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
        var text = 'SIMULATED ' + scenario.label + ' -> ' + target + '. ' +
          (recorded ? 'Matching backend audit record: ' + scenario.type + ' (' + verdict + ').'
            : 'No matching backend audit record; nothing was blocked or recorded by this simulation.');
        addEvent('sim', text);
        endSimulation(token);
      }
    });
    addEvent('sim', 'SIMULATED attack scenario: ' + scenario.label + ' targeting ' + target + '.');
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

  function updateLabels() {
    if (!state.showLabels || !labelLayer) return;
    var current = {};
    model.nodes.forEach(function (node) {
      if (node.kind === 'task' && !state.showLinks) return;
      current[node.id] = true;
      var el = labelElements[node.id];
      if (!el) {
        el = document.createElement('div');
        el.className = 'dt3d-label';
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
        + (state.eligible.indexOf(node.id) !== -1 && node.kind === 'mec' ? ' is-selected' : '');
      el.style.left = projected.x + 'px';
      el.style.top = projected.y + 'px';
      el.style.display = projected.visible ? '' : 'none';
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
      var point = {
        x: a.x + (b.x - a.x) * t,
        y: a.y + (b.y - a.y) * t + Math.sin(Math.PI * t) * 0.55,
        z: a.z + (b.z - a.z) * t
      };
      var projected = backend.project(point);
      el.textContent = packet.label + (packet.simulated ? ' [SIMULATED]' : ' [BACKEND]');
      el.className = 'dt3d-label' + (packet.kind === 'attack' ? ' is-threat' : '');
      el.style.left = projected.x + 'px';
      el.style.top = (projected.y - 18) + 'px';
      el.style.display = projected.visible && state.showTransfers ? '' : 'none';
    });
    Object.keys(labelElements).forEach(function (id) {
      if (!current[id]) {
        labelLayer.removeChild(labelElements[id]);
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
      backend.sync(model);
      if (hasMotion) active = true;
    }
    if (dirty || active) {
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
      if (!dragging) return;
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
        if (nodeId && storageDestForNode(nodeId)) openStorageModal(nodeId);
      }
    });
    on(canvas, 'pointercancel', function () { dragging = false; });
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
      else handled = false;
      if (handled) {
        event.preventDefault();
        dirty = true;
      }
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
