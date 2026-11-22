const SHAPE_GEOMETRY = {
  server: 'box',
  storage: 'cylinder',
  device: 'sphere',
  attacker: 'cone',
  folder: 'octahedron',
  file: 'box',
  checkpoint: 'torus',
  cloud: 'sphere',
  partition: 'octahedron',
  task: 'box',
  packet: 'sphere'
};

export class TwinScene {
  constructor(options) {
    this.root = options.root;
    this.canvas = options.canvas;
    this.viewport = options.viewport;
    this.labelLayer = options.labelLayer;
    this.onSelect = options.onSelect || function () {};
    this.nodes = new Map();
    this.links = [];
    this.packets = [];
    this.selectedId = null;
    this.labelsVisible = true;
    this.linksVisible = true;
    this.reducedMotion = false;
    this.paused = false;
    this.theme = 'dark';
    this.cameraState = { theta: 0.68, phi: 1.15, radius: 34, target: { x: 0, y: 0, z: 0 } };
    this.pointer = null;
    this.geometryCache = new Map();
    this.materialCache = new Map();
    this.frame = 0;
    this.needsRender = true;
    this.mode = '2d';

    this.initializeBackend();
    this.bindEvents();
    this.resize();
    this.loop();
  }

  initializeBackend() {
    var THREE = window.THREE;
    var supportsWebGL = false;
    try {
      var probe = document.createElement('canvas');
      supportsWebGL = !!(probe.getContext('webgl') || probe.getContext('experimental-webgl'));
    } catch (error) {
      supportsWebGL = false;
    }
    if (THREE && supportsWebGL) {
      try {
        this.THREE = THREE;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(48, 1, 0.1, 500);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
        this.world = new THREE.Group();
        this.scene.add(this.world);
        this.scene.add(new THREE.AmbientLight(0x9fb6d4, 0.85));
        var key = new THREE.DirectionalLight(0xffffff, 1.05);
        key.position.set(8, 14, 10);
        this.scene.add(key);
        var rim = new THREE.DirectionalLight(0x38bdf8, 0.55);
        rim.position.set(-12, 6, -10);
        this.scene.add(rim);
        this.grid = new THREE.GridHelper(46, 23, 0x1d3c60, 0x10213a);
        this.grid.material.transparent = true;
        this.grid.material.opacity = 0.45;
        this.scene.add(this.grid);
        this.raycaster = new THREE.Raycaster();
        this.selectionRing = new THREE.Mesh(
          this.geometry('torus', 1.35),
          new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.9 })
        );
        this.selectionRing.rotation.x = Math.PI / 2;
        this.selectionRing.visible = false;
        this.scene.add(this.selectionRing);
        this.mode = 'webgl';
        this.updateCamera();
        return;
      } catch (error) {
        this.mode = '2d';
      }
    }
    this.context = this.canvas.getContext('2d');
    this.mode = '2d';
  }

  geometry(shape, size) {
    var THREE = this.THREE;
    var multiplier = size || 1;
    var key = String(shape) + ':' + multiplier.toFixed(2);
    if (this.geometryCache.has(key)) return this.geometryCache.get(key);
    var geometry;
    switch (shape) {
      case 'cylinder': geometry = new THREE.CylinderGeometry(0.9 * multiplier, 0.9 * multiplier, 1.3 * multiplier, 6); break;
      case 'sphere': geometry = new THREE.SphereGeometry(0.75 * multiplier, 14, 10); break;
      case 'cone': geometry = new THREE.ConeGeometry(0.95 * multiplier, 1.8 * multiplier, 4); break;
      case 'octahedron': geometry = new THREE.OctahedronGeometry(0.9 * multiplier); break;
      case 'torus': geometry = new THREE.TorusGeometry(0.85 * multiplier, 0.09 * multiplier, 8, 24); break;
      default: geometry = new THREE.BoxGeometry(1.5 * multiplier, 1.5 * multiplier, 1.2 * multiplier);
    }
    this.geometryCache.set(key, geometry);
    return geometry;
  }

  material(color, opacity) {
    var value = Number(color) || 0x38bdf8;
    var alpha = opacity === undefined ? 1 : opacity;
    var key = value + ':' + alpha.toFixed(2);
    if (this.materialCache.has(key)) return this.materialCache.get(key);
    var material = new this.THREE.MeshStandardMaterial({
      color: value,
      emissive: value,
      emissiveIntensity: 0.16,
      roughness: 0.55,
      metalness: 0.18,
      transparent: alpha < 1,
      opacity: alpha
    });
    this.materialCache.set(key, material);
    return material;
  }

  bindEvents() {
    var self = this;
    this.handleResize = function () { self.resize(); };
    window.addEventListener('resize', this.handleResize);
    if (window.ResizeObserver) {
      this.resizeObserver = new ResizeObserver(function () { self.resize(); });
      this.resizeObserver.observe(this.viewport);
    }

    this.canvas.addEventListener('pointerdown', function (event) {
      self.canvas.setPointerCapture(event.pointerId);
      self.pointer = {
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        startX: event.clientX,
        startY: event.clientY,
        pan: event.shiftKey || event.button === 1 || event.button === 2,
        moved: false
      };
    });
    this.canvas.addEventListener('pointermove', function (event) {
      if (!self.pointer || self.pointer.id !== event.pointerId) return;
      var dx = event.clientX - self.pointer.x;
      var dy = event.clientY - self.pointer.y;
      if (Math.abs(event.clientX - self.pointer.startX) + Math.abs(event.clientY - self.pointer.startY) > 4) self.pointer.moved = true;
      self.pointer.x = event.clientX;
      self.pointer.y = event.clientY;
      if (self.mode === 'webgl') {
        if (self.pointer.pan) {
          var scale = self.cameraState.radius * 0.0016;
          self.cameraState.target.x -= dx * scale;
          self.cameraState.target.y += dy * scale;
        } else {
          self.cameraState.theta -= dx * 0.006;
          self.cameraState.phi = Math.max(0.22, Math.min(2.85, self.cameraState.phi - dy * 0.006));
        }
        self.updateCamera();
      } else {
        self.pan2d(dx, dy);
      }
      self.needsRender = true;
    });
    this.canvas.addEventListener('pointerup', function (event) {
      if (!self.pointer || self.pointer.id !== event.pointerId) return;
      if (!self.pointer.moved) {
        var node = self.pick(event.clientX, event.clientY);
        if (node) self.select(node.id);
      }
      self.pointer = null;
    });
    this.canvas.addEventListener('contextmenu', function (event) { event.preventDefault(); });
    this.canvas.addEventListener('wheel', function (event) {
      event.preventDefault();
      self.zoom(event.deltaY > 0 ? 0.9 : 1.1);
    }, { passive: false });

    this.viewport.addEventListener('keydown', function (event) {
      var handled = true;
      if (event.key === 'ArrowLeft') { if (event.shiftKey) self.panTarget(-1, 0); else self.cameraState.theta += 0.1; }
      else if (event.key === 'ArrowRight') { if (event.shiftKey) self.panTarget(1, 0); else self.cameraState.theta -= 0.1; }
      else if (event.key === 'ArrowUp') { if (event.shiftKey) self.panTarget(0, 1); else self.cameraState.phi -= 0.1; }
      else if (event.key === 'ArrowDown') { if (event.shiftKey) self.panTarget(0, -1); else self.cameraState.phi += 0.1; }
      else if (event.key === '+' || event.key === '=') self.zoom(1.12);
      else if (event.key === '-' || event.key === '_') self.zoom(0.9);
      else if (event.key === 'Home') self.resetCamera();
      else handled = false;
      if (handled) {
        event.preventDefault();
        self.updateCamera();
        self.needsRender = true;
      }
    });
  }

  panTarget(directionX, directionY) {
    var amount = this.cameraState.radius * 0.05;
    this.cameraState.target.x += directionX * amount;
    this.cameraState.target.y += directionY * amount;
  }

  pan2d(dx, dy) {
    this.cameraState.target.x -= dx * 0.03;
    this.cameraState.target.y -= dy * 0.03;
    this.needsRender = true;
  }

  updateCamera() {
    if (this.mode !== 'webgl' || !this.camera) return;
    var state = this.cameraState;
    state.phi = Math.max(0.22, Math.min(2.85, state.phi));
    state.radius = Math.max(6, Math.min(140, state.radius));
    this.camera.position.set(
      state.target.x + state.radius * Math.sin(state.phi) * Math.sin(state.theta),
      state.target.y + state.radius * Math.cos(state.phi),
      state.target.z + state.radius * Math.sin(state.phi) * Math.cos(state.theta)
    );
    this.camera.lookAt(state.target.x, state.target.y, state.target.z);
    this.needsRender = true;
  }

  resize() {
    var rect = this.viewport.getBoundingClientRect();
    var width = Math.max(1, Math.floor(rect.width));
    var height = Math.max(1, Math.floor(rect.height));
    if (this.mode === 'webgl') {
      this.renderer.setSize(width, height, false);
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
    } else if (this.context) {
      var ratio = Math.min(window.devicePixelRatio || 1, 1.75);
      this.canvas.width = Math.floor(width * ratio);
      this.canvas.height = Math.floor(height * ratio);
      this.canvas.style.width = width + 'px';
      this.canvas.style.height = height + 'px';
      this.context.setTransform(ratio, 0, 0, ratio, 0, 0);
    }
    this.width = width;
    this.height = height;
    this.needsRender = true;
  }

  setTheme(theme) {
    this.theme = theme;
    if (this.grid) this.grid.visible = theme !== 'light';
    this.needsRender = true;
  }

  clear() {
    if (this.mode === 'webgl') {
      while (this.world.children.length) this.world.remove(this.world.children[0]);
      this.links.forEach(function (link) { if (link.object && link.object.geometry) link.object.geometry.dispose(); });
    }
    this.labelLayer.textContent = '';
    this.nodes.clear();
    this.links = [];
    this.packets = [];
    this.selectedId = null;
    if (this.selectionRing) this.selectionRing.visible = false;
    this.needsRender = true;
  }

  setView(nodes, links, options) {
    this.clear();
    var self = this;
    nodes.forEach(function (node) { self.addNode(node); });
    links.forEach(function (link) { self.addLink(link); });
    this.setTheme((options && options.theme) || 'dark');
    if (options && options.fit !== false) this.fit(nodes);
    this.needsRender = true;
  }

  addNode(node) {
    var position = node.position || { x: 0, y: 0, z: 0 };
    var color = typeof node.color === 'number' ? node.color : 0x38bdf8;
    var size = node.size || 1;
    var record = { data: node, position: position, label: null, object: null, screen: null };

    if (this.mode === 'webgl') {
      var shape = SHAPE_GEOMETRY[node.shape] || 'box';
      var mesh = new this.THREE.Mesh(this.geometry(shape, size), this.material(color, node.opacity));
      mesh.position.set(position.x, position.y, position.z);
      if (node.shape === 'checkpoint') mesh.rotation.x = Math.PI / 2;
      mesh.userData.nodeId = node.id;
      this.world.add(mesh);
      record.object = mesh;
    }

    var label = document.createElement('div');
    label.className = 'dtw-label';
    label.textContent = node.label || node.id;
    if (node.status === 'offline' || node.status === 'ISOLATED') label.classList.add('is-offline');
    if (node.type === 'attacker') label.classList.add('is-attacker');
    label.style.display = 'none';
    this.labelLayer.appendChild(label);
    record.label = label;
    this.nodes.set(node.id, record);
    return record;
  }

  addLink(link) {
    var record = { data: link, object: null };
    if (this.mode === 'webgl') {
      var from = this.nodes.get(link.from);
      var to = this.nodes.get(link.to);
      if (!from || !to) return;
      var geometry = new this.THREE.BufferGeometry().setFromPoints([
        new this.THREE.Vector3(from.position.x, from.position.y, from.position.z),
        new this.THREE.Vector3(to.position.x, to.position.y, to.position.z)
      ]);
      var color = typeof link.color === 'number' ? link.color : 0x426996;
      var material = new this.THREE.LineBasicMaterial({ color: color, transparent: true, opacity: link.opacity || 0.65 });
      var line = new this.THREE.Line(geometry, material);
      this.world.add(line);
      record.object = line;
    }
    this.links.push(record);
  }

  setLinksVisible(visible) {
    this.linksVisible = visible;
    this.links.forEach(function (link) { if (link.object) link.object.visible = visible; });
    this.needsRender = true;
  }

  setLabelsVisible(visible) {
    this.labelsVisible = visible;
    this.labelLayer.style.display = visible ? '' : 'none';
    this.needsRender = true;
  }

  setReducedMotion(reduced) {
    this.reducedMotion = reduced;
    this.needsRender = true;
  }

  setPaused(paused) {
    this.paused = paused;
    this.needsRender = true;
  }

  select(id) {
    var record = this.nodes.get(id);
    this.selectedId = record ? id : null;
    this.nodes.forEach(function (item) {
      if (item.label) item.label.classList.toggle('is-selected', item.data.id === id);
    });
    if (this.selectionRing) {
      this.selectionRing.visible = !!record;
      if (record) this.selectionRing.position.set(record.position.x, record.position.y, record.position.z);
    }
    this.needsRender = true;
    if (record) this.onSelect(record.data);
  }

  focus(id) {
    var record = this.nodes.get(id);
    if (!record) return;
    this.cameraState.target = { x: record.position.x, y: record.position.y, z: record.position.z };
    this.cameraState.radius = Math.min(this.cameraState.radius, 24);
    this.updateCamera();
  }

  fit(nodes) {
    if (!nodes || !nodes.length) return;
    var min = { x: Infinity, y: Infinity, z: Infinity };
    var max = { x: -Infinity, y: -Infinity, z: -Infinity };
    nodes.forEach(function (node) {
      var position = node.position || { x: 0, y: 0, z: 0 };
      min.x = Math.min(min.x, position.x); min.y = Math.min(min.y, position.y); min.z = Math.min(min.z, position.z);
      max.x = Math.max(max.x, position.x); max.y = Math.max(max.y, position.y); max.z = Math.max(max.z, position.z);
    });
    this.cameraState.target = {
      x: (min.x + max.x) / 2,
      y: (min.y + max.y) / 2,
      z: (min.z + max.z) / 2
    };
    var span = Math.max(max.x - min.x, max.y - min.y, max.z - min.z, 8);
    this.cameraState.radius = Math.max(18, Math.min(95, span * 1.65));
    this.updateCamera();
  }

  resetCamera() {
    this.cameraState = { theta: 0.68, phi: 1.15, radius: 34, target: { x: 0, y: 0, z: 0 } };
    this.updateCamera();
  }

  zoom(factor) {
    this.cameraState.radius = Math.max(6, Math.min(140, this.cameraState.radius / factor));
    this.updateCamera();
  }

  addPacket(fromId, toId, options) {
    var from = this.nodes.get(fromId);
    var to = this.nodes.get(toId);
    if (!from || !to) return;
    var self = this;
    var packet = {
      from: from.position,
      to: to.position,
      progress: 0,
      state: (options && options.state) || 'QUEUED',
      color: (options && options.color) || 0xf59e0b,
      label: options && options.label,
      object: null,
      onComplete: options && options.onComplete
    };
    if (this.mode === 'webgl') {
      packet.object = new this.THREE.Mesh(
        this.geometry('sphere', 0.36),
        this.material(packet.color, 1)
      );
      this.world.add(packet.object);
    }
    if (this.reducedMotion) {
      packet.progress = 0.5;
      this.positionPacket(packet);
      if (packet.onComplete) window.setTimeout(function () { packet.onComplete(); }, 0);
    }
    this.packets.push(packet);
    self.needsRender = true;
  }

  setPackets(packets) {
    this.packets.forEach(function (packet) {
      if (packet.object && packet.object.parent) packet.object.parent.remove(packet.object);
    });
    this.packets = [];
    var self = this;
    (packets || []).forEach(function (packet) {
      self.addPacket(packet.from, packet.to, packet);
    });
  }

  positionPacket(packet) {
    var x = packet.from.x + (packet.to.x - packet.from.x) * packet.progress;
    var y = packet.from.y + (packet.to.y - packet.from.y) * packet.progress;
    var z = packet.from.z + (packet.to.z - packet.from.z) * packet.progress;
    if (this.mode === 'webgl' && packet.object) packet.object.position.set(x, y, z);
    packet.screen = { x: x, y: y, z: z };
  }

  updatePackets() {
    if (this.paused || this.reducedMotion) return;
    var remaining = [];
    var self = this;
    this.packets.forEach(function (packet) {
      packet.progress += packet.state === 'TRANSFERRING' ? 0.014 : 0.009;
      self.positionPacket(packet);
      if (packet.progress < 1) {
        remaining.push(packet);
        return;
      }
      if (packet.object && packet.object.parent) packet.object.parent.remove(packet.object);
      if (packet.onComplete) packet.onComplete();
    });
    this.packets = remaining;
    if (this.packets.length) this.needsRender = true;
  }

  pick(clientX, clientY) {
    var rect = this.canvas.getBoundingClientRect();
    if (this.mode === 'webgl') {
      var pointer = new this.THREE.Vector2(
        ((clientX - rect.left) / rect.width) * 2 - 1,
        -((clientY - rect.top) / rect.height) * 2 + 1
      );
      this.raycaster.setFromCamera(pointer, this.camera);
      var meshes = [];
      this.nodes.forEach(function (node) { if (node.object) meshes.push(node.object); });
      var hits = this.raycaster.intersectObjects(meshes, false);
      if (!hits.length) return null;
      return hits[0].object.userData.nodeId ? this.nodes.get(hits[0].object.userData.nodeId).data : null;
    }
    var closest = null;
    var distance = 26;
    this.nodes.forEach(function (node) {
      if (!node.screen) return;
      var delta = Math.hypot(clientX - rect.left - node.screen.x, clientY - rect.top - node.screen.y);
      if (delta < distance) { distance = delta; closest = node.data; }
    });
    return closest;
  }

  project(position) {
    var point = this.THREE.Vector3 ? new this.THREE.Vector3(position.x, position.y, position.z) : null;
    point.project(this.camera);
    if (point.z > 1) return null;
    return {
      x: (point.x * 0.5 + 0.5) * this.width,
      y: (-point.y * 0.5 + 0.5) * this.height
    };
  }

  project2d(position) {
    var scale = Math.min(this.width, this.height) / 28;
    return {
      x: this.width / 2 + (position.x - this.cameraState.target.x) * scale,
      y: this.height / 2 + (position.y - this.cameraState.target.y + position.z * 0.35) * scale
    };
  }

  renderLabels() {
    if (!this.labelsVisible) return;
    var self = this;
    var placed = [];
    this.nodes.forEach(function (node) {
      var point = self.mode === 'webgl' ? self.project(node.position) : self.project2d(node.position);
      if (!point) { node.label.style.display = 'none'; return; }
      node.screen = { x: point.x, y: point.y };
      var y = point.y;
      placed.sort(function (a, b) { return a.y - b.y; });
      for (var index = 0; index < placed.length; index += 1) {
        if (Math.abs(placed[index].x - point.x) < 150 && Math.abs(placed[index].y - y) < 24) y += 25;
      }
      placed.push({ x: point.x, y: y });
      node.label.style.display = 'block';
      node.label.style.left = point.x + 'px';
      node.label.style.top = y + 'px';
    });
  }

  render2d() {
    var context = this.context;
    if (!context) return;
    context.clearRect(0, 0, this.width, this.height);
    var self = this;
    if (this.linksVisible) {
      this.links.forEach(function (link) {
        var from = self.nodes.get(link.from);
        var to = self.nodes.get(link.to);
        if (!from || !to || !from.screen || !to.screen) return;
        context.beginPath();
        context.strokeStyle = link.color === 0xfb7185 ? '#fb7185' : '#426996';
        context.globalAlpha = link.opacity || 0.65;
        context.moveTo(from.screen.x, from.screen.y);
        context.lineTo(to.screen.x, to.screen.y);
        context.stroke();
      });
    }
    context.globalAlpha = 1;
    this.nodes.forEach(function (node) {
      if (!node.screen) return;
      context.beginPath();
      context.fillStyle = '#' + String(node.data.color || 0x38bdf8).padStart(6, '0');
      context.arc(node.screen.x, node.screen.y, 10 * (node.data.size || 1), 0, Math.PI * 2);
      context.fill();
      if (node.data.id === self.selectedId) {
        context.beginPath();
        context.strokeStyle = '#f59e0b';
        context.lineWidth = 3;
        context.arc(node.screen.x, node.screen.y, 15 * (node.data.size || 1), 0, Math.PI * 2);
        context.stroke();
        context.lineWidth = 1;
      }
    });
    this.packets.forEach(function (packet) {
      if (!packet.screen) return;
      var point = self.project2d(packet.screen);
      context.beginPath();
      context.fillStyle = '#f59e0b';
      context.arc(point.x, point.y, 5, 0, Math.PI * 2);
      context.fill();
    });
  }

  loop() {
    var self = this;
    this.frame = window.requestAnimationFrame(function () {
      self.updatePackets();
      if (self.needsRender || self.packets.length) {
        if (self.mode === 'webgl') self.renderer.render(self.scene, self.camera);
        else self.render2d();
        self.renderLabels();
        self.needsRender = false;
      }
      self.loop();
    });
  }

  destroy() {
    window.cancelAnimationFrame(this.frame);
    window.removeEventListener('resize', this.handleResize);
    if (this.resizeObserver) this.resizeObserver.disconnect();
    this.geometryCache.forEach(function (geometry) { geometry.dispose(); });
    this.materialCache.forEach(function (material) { material.dispose(); });
    if (this.renderer) this.renderer.dispose();
  }
}
