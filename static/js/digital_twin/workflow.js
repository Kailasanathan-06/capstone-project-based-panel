import { getJSON, postForm, uploadFile, display, formatBytes } from './api_client.js';
import { TwinScene } from './scene.js';
import { buildNetwork } from './network_topology.js';
import { buildDatasetGraph, renderTree, renderStats, renderSelection, renderPartitions } from './dataset_graph.js';
import { buildAllocationGraph } from './allocation.js';
import { buildSchedulingGraph, buildDatasetSchedulingGraph, buildComparisonGraph, renderGaStatus, renderGaHistory } from './ga_visualization.js';
import { buildSecurityGraph, renderSecurityControls, renderCapabilities, scenarioOptions, targetOptions, attackUrl } from './security.js';
import { buildAttackGraph, renderAttackStatus } from './attacker.js';
import { setStage, showDetails, hideDetails, updateViewportHead, buildTransferGraph, renderTransferStatus, renderUploadState, setUploadProgress, setUploadStatus, openUpload, renderFinalReport, setStatusStrip, renderDatasetSelector, renderDatasetInfo, renderEventLog, updatePlayback } from './ui_panels.js';

export const STAGES = ['upload', 'analyze', 'allocate', 'schedule', 'transfer', 'security', 'results'];

const DEMO_STEPS = [
  { stage: 'upload', action: 'selected-dataset', label: 'Selected dataset locked' },
  { stage: 'upload', action: 'dataset-info', label: 'Dataset overview displayed' },
  { stage: 'analyze', action: 'analyze', label: 'Dataset inventory inspected' },
  { stage: 'analyze', action: 'focus-dataset', label: 'Dataset graph focused' },
  { stage: 'allocate', action: 'allocate', label: 'Proposed allocation rendered' },
  { stage: 'allocate', action: 'confirm', label: 'Allocation confirmation recorded' },
  { stage: 'schedule', action: 'schedule', label: 'Dataset decisions rendered' },
  { stage: 'schedule', action: 'focus-decision', label: 'Allocation decision focused' },
  { stage: 'transfer', action: 'transfer', label: 'Dataset transfers replayed' },
  { stage: 'transfer', action: 'focus-transfer', label: 'Transfer record focused' },
  { stage: 'security', action: 'security', label: 'Security controls rendered' },
  { stage: 'security', action: 'focus-protection', label: 'Protection policy focused' },
  { stage: 'security', action: 'simulate-attack', label: 'Simulated threat executed' },
  { stage: 'security', action: 'dataset-events', label: 'Dataset security events shown' },
  { stage: 'results', action: 'results', label: 'Final report assembled' },
  { stage: 'results', action: 'capabilities', label: 'Capability snapshot rendered' },
  { stage: 'results', action: 'summary', label: 'Backend status summarized' },
  { stage: 'results', action: 'complete', label: 'Workflow complete — selected dataset' }
];

function delay(milliseconds) {
  return new Promise(function (resolve) { window.setTimeout(resolve, milliseconds); });
}

export class WorkflowController {
  constructor(root) {
    this.root = root;
    this.state = {
      scene: null,
      inspection: null,
      comparison: null,
      upload: null,
      attack: null,
      graph: null,
      stage: 'upload',
      file: null,
      demo: false,
      demoIndex: 0,
      demoToken: 0,
      demoElapsed: 0,
      paused: false,
      speed: 1,
      datasets: [],
      selectedDataset: null,
      uploadId: null,
      reportId: null,
      collapsed: new Set(),
      log: [],
      showComparison: false
    };
    this.scene = new TwinScene({
      root: root,
      canvas: document.getElementById('dtw-canvas'),
      viewport: document.getElementById('dtw-viewport'),
      labelLayer: document.getElementById('dtw-labels'),
      onSelect: this.handleNodeSelect.bind(this)
    });
    this.reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.scene.setReducedMotion(this.reducedMotion);
    var reduceButton = document.getElementById('dtw-toggle-motion');
    if (reduceButton && this.reducedMotion) {
      reduceButton.setAttribute('aria-pressed', 'true');
      reduceButton.textContent = 'Motion Reduced';
    }
  }

  async boot() {
    this.populateJump();
    this.bindEvents();
    try {
      await this.loadScene();
      await this.loadDatasets();
      var selected = this.state.datasets.find(function (dataset) { return dataset.report_available; });
      if (selected) await this.selectDataset(selected.upload_id, false);
      else {
        renderDatasetInfo(document.getElementById('dtw-dataset-info'), null);
        setUploadStatus('No analyzed dataset is available. Upload a ZIP or load a bundled archive.');
      }
      this.syncPlayback('upload');
    } catch (error) {
      this.showBootError(error);
    }
  }

  showBootError(error) {
    setUploadStatus('Backend snapshot unavailable: ' + display(error && error.message, 'Unknown error'));
    setStatusStrip('security', 'ENCRYPTION NOT VERIFIED · BACKEND SNAPSHOT UNAVAILABLE');
    updateViewportHead(this.scene.mode, this.scene.nodes.size, this.reducedMotion);
  }

  populateJump() {
    var jump = document.getElementById('dtw-jump');
    if (!jump) return;
    STAGES.forEach(function (stage, index) {
      var option = document.createElement('option');
      option.value = stage;
      option.textContent = String(index + 1).padStart(2, '0') + ' · ' + stage;
      jump.appendChild(option);
    });
  }

  bindEvents() {
    var self = this;
    this.on('dtw-open-upload', 'click', function () { openUpload(true); });
    this.on('dtw-panel-upload', 'click', function () { openUpload(true); });
    this.on('dtw-close-upload', 'click', function () { openUpload(false); });
    this.on('dtw-dropzone', 'click', function () { self.clickFileInput(); });
    this.on('dtw-dropzone', 'keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); self.clickFileInput(); }
    });
    this.on('dtw-dropzone', 'dragover', function (event) {
      event.preventDefault();
      this.classList.add('dragover');
    });
    this.on('dtw-dropzone', 'dragleave', function () { this.classList.remove('dragover'); });
    this.on('dtw-dropzone', 'drop', function (event) {
      event.preventDefault();
      this.classList.remove('dragover');
      if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]) {
        self.selectFile(event.dataTransfer.files[0]);
      }
    });
    this.on('dtw-file', 'change', function () { if (this.files && this.files[0]) self.selectFile(this.files[0]); });
    this.on('dtw-upload-btn', 'click', function () { self.uploadSelected(); });
    this.on('dtw-reset-upload', 'click', function () { self.resetUpload(); });
    this.on('dtw-load-demo', 'click', function () {
      var select = document.getElementById('dtw-demo-package');
      self.loadDemoPackage(select ? select.value : 'success_01');
    });

    this.on('dtw-context-collapse', 'click', function () {
      var context = document.getElementById('dtw-context');
      var collapsed = context.classList.toggle('collapsed');
      this.textContent = collapsed ? '‹' : '›';
      this.setAttribute('aria-label', collapsed ? 'Expand contextual panel' : 'Collapse contextual panel');
    });
    this.on('dtw-details-close', 'click', function () { hideDetails(); self.scene.select(null); });

    this.on('dtw-search', 'input', function () { self.rerenderTree(); });
    this.on('dtw-tree-expand', 'click', function () {
      self.state.collapsed.clear();
      self.rerenderTree();
      if (self.state.stage === 'analyze') self.renderView('analyze');
    });
    this.on('dtw-tree-collapse', 'click', function () {
      self.state.collapsed.clear();
      if (self.state.inspection && self.state.inspection.tree) {
        self.folderIds(self.state.inspection.tree).forEach(function (id) { self.state.collapsed.add(id); });
      }
      self.rerenderTree();
      if (self.state.stage === 'analyze') self.renderView('analyze');
    });

    this.on('dtw-confirm-allocation', 'click', function () { self.confirmAllocation(); });
    this.on('dtw-run-schedule', 'click', function () { self.runComparison(true); });
    this.on('dtw-run-transfer', 'click', function () { self.runTransfer(); });
    this.on('dtw-run-attack', 'click', function () { self.runAttack(); });
    this.on('dtw-policy', 'change', function () {
      setUploadStatus('Policy ' + this.value + ' selected. Policy enforcement remains a backend control; encryption is NOT VERIFIED.');
    });

    var steps = document.querySelectorAll('#dtw-steps button');
    Array.prototype.forEach.call(steps, function (button) {
      button.addEventListener('click', function () { self.stopDemo(false); self.setStage(button.dataset.stage); });
    });

    this.on('dtw-reset-camera', 'click', function () { self.scene.resetCamera(); });
    this.on('dtw-zoom-in', 'click', function () { self.scene.zoom(1.2); });
    this.on('dtw-zoom-out', 'click', function () { self.scene.zoom(0.84); });
    this.on('dtw-toggle-labels', 'click', function () {
      var pressed = this.getAttribute('aria-pressed') !== 'true';
      this.setAttribute('aria-pressed', String(pressed));
      this.textContent = pressed ? 'Labels: On' : 'Labels: Off';
      self.scene.setLabelsVisible(pressed);
    });
    this.on('dtw-toggle-links', 'click', function () {
      var pressed = this.getAttribute('aria-pressed') !== 'true';
      this.setAttribute('aria-pressed', String(pressed));
      this.textContent = pressed ? 'Links: On' : 'Links: Off';
      self.scene.setLinksVisible(pressed);
    });
    this.on('dtw-toggle-motion', 'click', function () {
      self.reducedMotion = !self.reducedMotion;
      this.setAttribute('aria-pressed', String(self.reducedMotion));
      this.textContent = self.reducedMotion ? 'Motion Reduced' : 'Reduce Motion';
      self.scene.setReducedMotion(self.reducedMotion);
      updateViewportHead(self.scene.mode, self.scene.nodes.size, self.reducedMotion);
    });
    this.on('dtw-prev', 'click', function () { self.manualDemoStep(-1); });
    this.on('dtw-next', 'click', function () { self.manualDemoStep(1); });
    this.on('dtw-timeline', 'change', function () { self.goToDemoStep(Number(this.value)); });
    this.on('dtw-jump', 'change', function () { self.stopDemo(false); self.setStage(this.value); });
    this.on('dtw-speed', 'change', function () { self.state.speed = Math.max(0.25, Number(this.value) || 1); });
    this.on('dtw-pause', 'click', function () { self.togglePause(); });
    this.on('dtw-restart', 'click', function () { self.startDemo(); });
    this.on('dtw-exit', 'click', function () { self.stopDemo(); });
    this.on('dtw-start-demo', 'click', function () { self.startDemo(); });
  }

  on(id, eventName, handler) {
    var element = document.getElementById(id);
    if (element) element.addEventListener(eventName, handler);
  }

  logEvent(label) {
    var entry = { time: new Date().toLocaleTimeString(), label: label };
    this.state.log.push(entry);
    if (this.state.log.length > 80) this.state.log.shift();
    renderEventLog(document.getElementById('dtw-log-entries'), this.state.log);
  }

  syncPlayback(label) {
    updatePlayback(
      this.state.demoIndex,
      DEMO_STEPS.length,
      display(label, DEMO_STEPS[this.state.demoIndex].label),
      this.state.demoElapsed,
      this.state.demo && !this.state.paused
    );
  }

  async loadScene() {
    var data = await getJSON(this.root.dataset.sceneUrl);
    this.state.scene = data;
    scenarioOptions(document.getElementById('dtw-attack-scenario'), data);
    targetOptions(document.getElementById('dtw-attack-target'), data);
    setStatusStrip('security', 'ENCRYPTION NOT VERIFIED');
    var mode = document.getElementById('dtw-mode-badge');
    if (mode && data.mode) {
      mode.textContent = String(data.mode).toUpperCase() + ' BACKEND';
      if (String(data.mode).toLowerCase().indexOf('sim') !== -1) mode.classList.add('is-simulated');
    }
    this.renderView('upload');
    updateViewportHead(this.scene.mode, this.scene.nodes.size, this.reducedMotion);
    this.logEvent('Backend scene snapshot loaded');
    return data;
  }

  async loadDatasets() {
    var select = document.getElementById('dtw-dataset-select');
    var self = this;
    try {
      var data = await getJSON(this.root.dataset.datasetsUrl);
      this.state.datasets = (data && data.datasets) || [];
      renderDatasetSelector(select, this.state.datasets, this.state.uploadId, function (uploadId) {
        self.selectDataset(uploadId, true);
      });
      if (!this.state.datasets.length) setUploadStatus('No uploaded datasets are available to select.');
      this.logEvent(this.state.datasets.length + ' dataset record(s) loaded');
    } catch (error) {
      this.state.datasets = [];
      renderDatasetSelector(select, [], '', function () {});
      if (select && select.options.length) select.options[0].textContent = 'Dataset list unavailable';
      setUploadStatus('Dataset list unavailable: ' + display(error && error.message, 'Sign in to load uploaded datasets.'));
    }
  }

  async selectDataset(uploadId, announce) {
    if (!uploadId) return;
    var dataset = this.state.datasets.find(function (item) { return item.upload_id === uploadId; });
    if (!dataset) { setUploadStatus('Selected dataset was not found.'); return; }
    this.state.selectedDataset = dataset;
    this.state.uploadId = uploadId;
    this.state.reportId = dataset.report_id;
    this.root.dataset.uploadId = uploadId;
    this.root.dataset.reportId = dataset.report_id || '';
    renderDatasetInfo(document.getElementById('dtw-dataset-info'), dataset);
    setStatusStrip('selected', 'DATASET: ' + display(dataset.dataset_name, uploadId));
    var startButton = document.getElementById('dtw-start-demo');
    if (startButton) startButton.disabled = !dataset.report_available;
    if (!dataset.report_available) {
      setUploadStatus(display(dataset.dataset_name, 'Dataset') + ' has no completed analysis report.');
      return;
    }
    try {
      await this.loadInspection(dataset.report_id, null, false);
      if (announce !== false) setUploadStatus(display(dataset.dataset_name, 'Dataset') + ' selected. All workflow views now use this report.');
      this.logEvent('Selected dataset ' + display(dataset.dataset_name, uploadId));
    } catch (error) {
      setUploadStatus('Dataset inspection failed: ' + display(error && error.message, 'Unknown error'));
    }
  }

  async loadInspection(reportId, nextStage, announce) {
    if (!reportId) { setUploadStatus('No report ID is available to inspect.'); return null; }
    var data = await getJSON(this.root.dataset.inspectUrl + '?report_id=' + encodeURIComponent(reportId));
    if (!data.success) throw new Error(display(data.error, 'Inspection failed.'));
    this.state.inspection = data;
    this.state.reportId = data.report_id || this.state.reportId;
    if (data.dataset) {
      this.state.selectedDataset = data.dataset;
      this.state.uploadId = data.upload_id || this.state.uploadId;
      this.root.dataset.uploadId = this.state.uploadId || '';
    }
    this.root.dataset.reportId = data.report_id || '';
    this.rerenderTree();
    renderStats(document.getElementById('dtw-stats'), data);
    renderPartitions(document.getElementById('dtw-partitions'), data);
    renderSelection(document.getElementById('dtw-selection'), data.tree, data);
    var label = document.getElementById('dtw-allocation-label');
    if (label) label.textContent = display(data.allocation && data.allocation.label, 'No allocation plan loaded.');
    var selectionNode = document.getElementById('dtw-selected');
    if (selectionNode) selectionNode.textContent = 'Dataset: ' + display(data.file_name, reportId);
    if (announce !== false) setUploadStatus(display(data.file_name, 'Dataset') + ' inspected. Report ' + data.report_id + '.');
    this.logEvent('Inspected report ' + display(data.report_id, reportId));
    var startButton = document.getElementById('dtw-start-demo');
    if (startButton) startButton.disabled = false;
    if (nextStage) this.setStage(nextStage);
    else this.renderView(this.state.stage);
    return data;
  }

  rerenderTree() {
    if (!this.state.inspection) return;
    var search = document.getElementById('dtw-search');
    var self = this;
    renderTree(
      document.getElementById('dtw-tree'),
      this.state.inspection.tree,
      this.handleTreeSelect.bind(this),
      search ? search.value : '',
      this.state.collapsed,
      function (id) { self.handleTreeToggle(id); }
    );
  }

  handleTreeToggle(id) {
    if (this.state.collapsed.has(id)) this.state.collapsed.delete(id);
    else this.state.collapsed.add(id);
    this.rerenderTree();
    if (this.state.stage === 'analyze') this.renderView('analyze');
  }

  folderIds(node) {
    var ids = [];
    function walk(current) {
      if (!current) return;
      if (current.type === 'folder' || current.type === 'root' || current.type === 'group') ids.push(current.id);
      (current.children || []).forEach(walk);
    }
    walk(node);
    return ids;
  }

  handleTreeSelect(node) {
    renderSelection(document.getElementById('dtw-selection'), node, this.state.inspection);
    var graphNode = this.state.graph && this.state.graph.nodes.find(function (item) { return item.id === node.id; });
    if (graphNode) {
      this.scene.select(graphNode.id);
      this.scene.focus(graphNode.id);
    }
  }

  handleNodeSelect(node) {
    showDetails(node);
    setStatusStrip('selected', display(node.label, node.id));
    if (node.id && node.id.indexOf('data:') === 0 && this.state.inspection) {
      var treeNode = this.findTreeNode(this.state.inspection.tree, node.id);
      if (treeNode) renderSelection(document.getElementById('dtw-selection'), treeNode, this.state.inspection);
    }
  }

  findTreeNode(node, id) {
    if (!node) return null;
    if (node.id === id) return node;
    var children = node.children || [];
    for (var index = 0; index < children.length; index += 1) {
      var found = this.findTreeNode(children[index], id);
      if (found) return found;
    }
    return null;
  }

  setStage(stage) {
    if (STAGES.indexOf(stage) === -1) return;
    this.state.stage = stage;
    setStage(this.root, stage, STAGES);
    this.renderView(stage);
    this.syncPlayback(stage);
  }

  renderView(stage) {
    var view = null;
    if (stage === 'analyze' && this.state.inspection) view = buildDatasetGraph(this.state.inspection, this.state.collapsed);
    else if (stage === 'allocate' && this.state.inspection) view = buildAllocationGraph(this.state.inspection);
    else if (stage === 'schedule' && this.state.inspection && !this.state.showComparison) view = buildDatasetSchedulingGraph(this.state.inspection);
    else if (stage === 'schedule' && this.state.comparison) view = buildComparisonGraph(this.state.comparison);
    else if (stage === 'schedule') view = buildSchedulingGraph(this.state.scene);
    else if (stage === 'transfer') view = buildTransferGraph({ transfers: (this.state.inspection && this.state.inspection.dataset_transfers) || [] });
    else if (stage === 'security' || stage === 'results') view = buildSecurityGraph(this.state.scene, this.state.inspection);
    else view = buildNetwork(this.state.scene || {});

    if (!view) return;
    this.state.graph = view;
    this.scene.setView(view.nodes, view.links, { theme: stage === 'analyze' ? 'light' : 'dark' });
    this.scene.setLinksVisible(true);
    this.scene.setLabelsVisible(true);
    updateViewportHead(this.scene.mode, view.nodes.length, this.reducedMotion);
    if (view.nodes.length) this.scene.select(view.nodes[0].id);
    this.refreshPanels(stage);
  }

  refreshPanels(stage) {
    if (stage === 'schedule') {
      renderGaStatus(document.getElementById('dtw-ga-status'), this.state.scene, this.state.comparison, this.state.inspection);
      renderGaHistory(document.getElementById('dtw-ga-history'), this.state.scene, this.state.comparison, this.state.inspection);
    }
    if (stage === 'transfer') {
      renderTransferStatus(document.getElementById('dtw-transfer-status'), { transfers: (this.state.inspection && this.state.inspection.dataset_transfers) || [] });
    }
    if (stage === 'security') renderSecurityControls(document.getElementById('dtw-security-list'), this.state.scene, this.state.inspection);
    if (stage === 'results') {
      renderFinalReport(document.getElementById('dtw-final-report'), this.state.scene, this.state.inspection, this.state.comparison);
      renderCapabilities(document.getElementById('dtw-capabilities'), this.state.scene, this.state.inspection, this.state.comparison);
    }
  }

  clickFileInput() {
    var input = document.getElementById('dtw-file');
    if (input) input.click();
  }

  selectFile(file) {
    if (!file) { this.resetUpload(); return; }
    this.state.file = file;
    renderUploadState(file.name, file.size);
    setUploadStatus('Ready: ' + file.name + ' (' + formatBytes(file.size) + '). Files are validated and never executed.');
  }

  resetUpload() {
    this.state.file = null;
    var input = document.getElementById('dtw-file');
    if (input) input.value = '';
    renderUploadState('', 0);
    setUploadProgress(0);
    setUploadStatus('Waiting for a ZIP archive.');
  }

  async uploadSelected() {
    if (!this.state.file) { setUploadStatus('Select a ZIP archive first.'); return; }
    var modeNode = document.getElementById('dtw-mode');
    var mode = modeNode ? modeNode.value : 'SIMULATION';
    var button = document.getElementById('dtw-upload-btn');
    if (button) button.disabled = true;
    setUploadProgress(0);
    setUploadStatus('Uploading ' + this.state.file.name + ' in ' + mode + ' mode…');
    try {
      var result = await uploadFile(this.root.dataset.uploadUrl, this.state.file, mode, setUploadProgress);
      this.state.upload = result;
      setUploadProgress(100);
      setUploadStatus('Upload complete. Report ' + display(result.report_id, 'unknown') + ' saved.');
      openUpload(false);
      await this.loadDatasets();
      await this.selectDataset(result.upload_id, false);
      this.setStage('analyze');
    } catch (error) {
      setUploadStatus(display(error && error.message, 'Upload failed.'));
    } finally {
      if (button) button.disabled = false;
    }
  }

  async loadDemoPackage(packageKey) {
    var button = document.getElementById('dtw-load-demo');
    if (button) button.disabled = true;
    setUploadStatus('Loading bundled archive ' + packageKey + ' in SIMULATION mode…');
    try {
      var result = await postForm(this.root.dataset.demoUrl, { package: packageKey, execution_mode: 'SIMULATION' });
      if (!result.success) throw new Error(display(result.error, 'Demo archive failed validation.'));
      this.state.upload = result;
      setUploadProgress(100);
      setUploadStatus('Bundled archive loaded. Report ' + display(result.report_id, 'unknown') + '.');
      openUpload(false);
      await this.loadDatasets();
      await this.selectDataset(result.upload_id, false);
      this.setStage('analyze');
    } catch (error) {
      setUploadStatus(display(error && error.message, 'Demo archive failed validation.'));
    } finally {
      if (button) button.disabled = false;
    }
  }

  async confirmAllocation() {
    var status = document.getElementById('dtw-allocation-status');
    if (!this.state.inspection || !this.state.inspection.report_id) {
      if (status) status.textContent = 'Select an analyzed dataset before confirming allocation.';
      return;
    }
    var button = document.getElementById('dtw-confirm-allocation');
    if (button) button.disabled = true;
    try {
      var result = await postForm(this.root.dataset.confirmUrl, { report_id: this.state.inspection.report_id });
      if (status) status.textContent = result.label + ' — ' + result.message;
      setStatusStrip('ga', display(result.label, 'Allocation confirmation recorded'));
      this.logEvent('Allocation confirmation recorded for ' + display(this.state.inspection.report_id, 'report'));
    } catch (error) {
      if (status) status.textContent = display(error && error.message, 'Allocation confirmation failed.');
    } finally {
      if (button) button.disabled = false;
    }
  }

  async runComparison(useQueued) {
    var button = document.getElementById('dtw-run-schedule');
    if (button) button.disabled = true;
    var status = document.getElementById('dtw-ga-status');
    if (status) status.textContent = 'Running a simulated benchmark comparison; this is not live dispatch.';
    try {
      var url = this.root.dataset.compareUrl + '?tasks_count=6&population=12&generations=6&seed=42&use_queued=' + (useQueued ? 'true' : 'false');
      var data = await getJSON(url);
      this.state.comparison = data;
      this.state.showComparison = true;
      renderGaStatus(status, this.state.scene, data, this.state.inspection);
      renderGaHistory(document.getElementById('dtw-ga-history'), this.state.scene, data, this.state.inspection);
      setStatusStrip('ga', 'SIMULATED COMPARISON AVAILABLE — NOT LIVE DISPATCH');
      this.setStage('schedule');
      this.logEvent('Simulated GA comparison rendered');
    } catch (error) {
      if (status) status.textContent = display(error && error.message, 'Scheduler comparison failed.');
    } finally {
      if (button) button.disabled = false;
    }
  }

  runTransfer() {
    var transfers = (this.state.inspection && this.state.inspection.dataset_transfers) || [];
    if (!transfers.length) {
      renderTransferStatus(document.getElementById('dtw-transfer-status'), { transfers: [] });
      setStatusStrip('transfer', 'SELECT AN ANALYZED DATASET TO REPLAY ITS TRANSFERS');
      return;
    }
    renderTransferStatus(document.getElementById('dtw-transfer-status'), { transfers: transfers });
    this.setStage('transfer');
    transfers.slice(0, 8).forEach(function (transfer, index) {
      var color = transfer.state === 'COMPLETED' ? 0x34d399 : transfer.state === 'BLOCKED' || transfer.state === 'FAILED' ? 0xfb7185 : 0xf59e0b;
      this.scene.addPacket('SOURCE:' + display(transfer.source, 'SOURCE NOT RECORDED'), 'DEST:' + display(transfer.destination, 'UNKNOWN'), {
        state: display(transfer.state, 'WAITING'),
        color: color,
        label: display(transfer.label, transfer.transfer_id),
        onComplete: index === 0 ? function () {
          setStatusStrip('transfer', 'DATASET TRANSFER STATES REPLAYED — NO LIVE PROGRESS');
        } : null
      });
    }, this);
    setStatusStrip('transfer', transfers.length + ' DATASET TRANSFER RECORD(S)');
    this.logEvent('Replayed ' + transfers.length + ' dataset transfer record(s)');
  }

  async runAttack(forcedScenario, forcedTarget) {
    if (!this.state.inspection) {
      var status = document.getElementById('dtw-attack-status');
      if (status) status.textContent = 'SELECT AN ANALYZED DATASET BEFORE RUNNING A SECURITY DEMONSTRATION';
      return;
    }
    var scenarioSelect = document.getElementById('dtw-attack-scenario');
    var targetSelect = document.getElementById('dtw-attack-target');
    var scenarioId = forcedScenario || (scenarioSelect ? scenarioSelect.value : 'UNAUTHORIZED_TASK_SUBMISSION');
    var targetId = forcedTarget || (targetSelect ? targetSelect.value : 'CENTRAL');
    var scenario = ((this.state.scene && this.state.scene.simulation_catalog) || []).find(function (item) { return item.id === scenarioId; });
    var button = document.getElementById('dtw-run-attack');
    if (button) button.disabled = true;
    var attackStatus = document.getElementById('dtw-attack-status');
    if (attackStatus) attackStatus.textContent = 'SIMULATED ATTACKER — running local simulation only';
    try {
      var result = await postForm(attackUrl(this.root), {
        resource_id: targetId,
        attack_type: scenarioId,
        severity: '0.5'
      });
      this.state.attack = result;
      renderAttackStatus(attackStatus, result, scenario, this.state.inspection);
      setStatusStrip('security', 'SIMULATED ATTACK — ENCRYPTION NOT VERIFIED');
      this.setStage('security');
      var attackGraph = buildAttackGraph(this.state.scene, result, scenario, this.state.inspection);
      this.scene.setView(attackGraph.nodes, attackGraph.links, { theme: 'dark' });
      this.scene.addPacket('SIMULATED_ATTACKER', 'ATTACK_TARGET', { state: 'SIMULATED', color: 0xfb7185 });
      this.logEvent('Simulated threat executed for ' + display(this.state.inspection.report_id, 'selected dataset'));
    } catch (error) {
      if (attackStatus) attackStatus.textContent = 'SIMULATED ATTACKER — ' + display(error && error.message, 'Simulation failed.') + ' · ENCRYPTION NOT VERIFIED';
    } finally {
      if (button) button.disabled = false;
    }
  }

  async startDemo() {
    if (!this.state.selectedDataset || !this.state.inspection) {
      var available = this.state.datasets.find(function (dataset) { return dataset.report_available; });
      if (!available) { setUploadStatus('Upload or select an analyzed dataset before starting the workflow.'); return; }
      await this.selectDataset(available.upload_id, false);
    }
    this.state.demo = true;
    this.state.paused = false;
    this.state.speed = Math.max(0.25, Number((document.getElementById('dtw-speed') || {}).value) || 1);
    this.state.demoIndex = 0;
    this.state.demoElapsed = 0;
    this.state.showComparison = false;
    this.state.demoToken += 1;
    this.scene.setPaused(false);
    var token = this.state.demoToken;
    setUploadStatus(String(this.state.selectedDataset.execution_mode || '').toUpperCase() === 'SIMULATION'
      ? 'DEMONSTRATION MODE — SIMULATED DATA'
      : 'WORKFLOW PLAYBACK — RECORDED DATASET STATE');
    this.logEvent('PLAY DATASET WORKFLOW started');
    while (this.state.demo && token === this.state.demoToken && this.state.demoIndex < DEMO_STEPS.length) {
      var step = DEMO_STEPS[this.state.demoIndex];
      await this.executeDemoStep(step, this.state.demoIndex, token);
      if (!this.state.demo || token !== this.state.demoToken) return;
      if (await this.pauseAwareWait(950, token, step.label)) this.state.demoIndex += 1;
    }
    if (this.state.demo && token === this.state.demoToken) {
      this.state.demoIndex = DEMO_STEPS.length - 1;
      this.syncPlayback('Workflow complete');
    }
  }

  async executeDemoStep(step, index, token) {
    setStatusStrip('selected', 'STEP ' + String(index + 1).padStart(2, '0') + ' · ' + step.label);
    this.logEvent(step.label);
    this.syncPlayback(step.label);
    switch (step.action) {
      case 'selected-dataset':
        this.setStage('upload');
        openUpload(false);
        break;
      case 'dataset-info':
        renderDatasetInfo(document.getElementById('dtw-dataset-info'), this.state.selectedDataset);
        break;
      case 'analyze':
        this.setStage('analyze');
        break;
      case 'focus-dataset':
        this.focusFirst('root', 'folder:', 'file:');
        break;
      case 'allocate':
        this.setStage('allocate');
        break;
      case 'confirm':
        await this.confirmAllocation();
        break;
      case 'schedule':
        this.state.showComparison = false;
        this.setStage('schedule');
        break;
      case 'focus-decision':
        this.focusFirst('DATASET_DECISION:', 'DESTINATION:');
        break;
      case 'transfer':
        this.runTransfer();
        break;
      case 'focus-transfer':
        this.focusFirst('TRANSFER:', 'DEST:');
        break;
      case 'security':
        this.setStage('security');
        break;
      case 'focus-protection':
        this.focusFirst('PROTECTION_POLICY', 'SECURITY_CORE');
        break;
      case 'simulate-attack':
        var scenarioNode = document.getElementById('dtw-attack-scenario');
        var targetNode = document.getElementById('dtw-attack-target');
        await this.runAttack(scenarioNode ? scenarioNode.value : 'UNAUTHORIZED_TASK_SUBMISSION', targetNode ? targetNode.value : 'CENTRAL');
        break;
      case 'dataset-events':
        this.setStage('security');
        this.focusFirst('DATASET_EVENT:');
        break;
      case 'results':
        this.setStage('results');
        break;
      case 'capabilities':
        renderCapabilities(document.getElementById('dtw-capabilities'), this.state.scene, this.state.inspection, this.state.comparison);
        break;
      case 'summary':
        renderFinalReport(document.getElementById('dtw-final-report'), this.state.scene, this.state.inspection, this.state.comparison);
        break;
      case 'complete':
        setStatusStrip('selected', 'WORKFLOW COMPLETE — SELECTED DATASET');
        setUploadStatus('WORKFLOW COMPLETE — ' + display(this.state.selectedDataset && this.state.selectedDataset.dataset_name, 'DATASET'));
        break;
      default:
        break;
    }
    if (token !== this.state.demoToken || !this.state.demo) return;
    updateViewportHead(this.scene.mode, this.scene.nodes.size, this.reducedMotion);
  }

  async pauseAwareWait(milliseconds, token, label) {
    var remaining = milliseconds / this.state.speed;
    while (remaining > 0) {
      if (!this.state.demo || token !== this.state.demoToken) return false;
      if (this.state.paused) { await delay(100); continue; }
      var slice = Math.min(remaining, 100);
      await delay(slice);
      this.state.demoElapsed += slice;
      this.syncPlayback(label);
      remaining -= slice;
    }
    return this.state.demo && token === this.state.demoToken;
  }

  focusFirst() {
    var candidates = Array.prototype.slice.call(arguments);
    var nodes = this.state.graph ? this.state.graph.nodes : [];
    for (var index = 0; index < candidates.length; index += 1) {
      var match = nodes.find(function (node) { return node.id.indexOf(candidates[index]) === 0 || node.id === candidates[index]; });
      if (match) { this.scene.focus(match.id); this.scene.select(match.id); return; }
    }
  }

  async manualDemoStep(direction) {
    await this.goToDemoStep(this.state.demoIndex + direction);
  }

  async goToDemoStep(index) {
    this.stopDemo(false);
    var next = Math.max(0, Math.min(DEMO_STEPS.length - 1, Number(index) || 0));
    this.state.demoIndex = next;
    this.state.demo = true;
    this.state.demoToken += 1;
    var token = this.state.demoToken;
    await this.executeDemoStep(DEMO_STEPS[next], next, token);
    this.syncPlayback(DEMO_STEPS[next].label);
  }

  togglePause() {
    this.state.paused = !this.state.paused;
    this.scene.setPaused(this.state.paused);
    var button = document.getElementById('dtw-pause');
    if (button) {
      button.setAttribute('aria-pressed', String(this.state.paused));
      button.textContent = this.state.paused ? 'Resume' : 'Pause';
    }
    setUploadStatus(this.state.paused ? 'DEMONSTRATION PAUSED' : 'DEMONSTRATION RESUMED');
    this.syncPlayback();
  }

  stopDemo(announce) {
    if (!this.state.demo && announce === false) return;
    this.state.demo = false;
    this.state.paused = false;
    this.state.demoToken += 1;
    this.scene.setPaused(false);
    openUpload(false);
    var button = document.getElementById('dtw-pause');
    if (button) { button.setAttribute('aria-pressed', 'false'); button.textContent = 'Pause'; }
    if (announce !== false) {
      setUploadStatus('DEMONSTRATION MODE EXITED');
      setStatusStrip('selected', 'No node selected');
      this.logEvent('Workflow playback stopped');
    }
    this.syncPlayback('Workflow stopped');
  }
}
