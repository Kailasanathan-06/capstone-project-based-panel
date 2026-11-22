import { display, escapeHtml } from './api_client.js';

const COLORS = {
  central: 0x38bdf8,
  enforced: 0x34d399,
  partial: 0xf59e0b,
  policyOnly: 0xa78bfa,
  event: 0xfb7185,
  attacker: 0xfb7185,
  offline: 0x64748b
};

export function buildSecurityGraph(data, inspection) {
  var layers = (data && data.security_layers) || [];
  var events = (data && data.security_events) || [];
  var datasetEvents = (inspection && inspection.dataset_security_events) || [];
  var policies = (data && data.policies) || {};
  var dataset = (inspection && inspection.dataset) || {};
  var nodes = [];
  var links = [];

  nodes.push({
    id: 'SECURITY_CORE',
    label: 'PROTECTION POLICY VISUALIZATION',
    type: 'core',
    shape: 'server',
    status: 'online',
    color: COLORS.central,
    size: 1.1,
    position: { x: 0, y: 0, z: 0 },
    meta: {
      kicker: 'PROTECTION POLICY VISUALIZATION',
      sections: [{
        title: 'Security Information',
        rows: [
          ['Policy enforcement', (data && data.capabilities && data.capabilities.policy_enforcement) ? 'ENFORCED' : 'UNKNOWN'],
          ['Encryption', 'NOT VERIFIED'],
          ['Shield meaning', 'Policy enforcement only'],
          ['Selected dataset', display(dataset.dataset_name, 'None selected')],
          ['Dataset events', display(datasetEvents.length, 0)],
          ['Recent backend events', display(events.length, 0)]
        ]
      }]
    }
  });

  layers.forEach(function (layer, index) {
    var angle = (index / Math.max(1, layers.length)) * Math.PI * 2;
    var color = layer.status === 'ENFORCED' ? COLORS.enforced : layer.status === 'PARTIAL' ? COLORS.partial : COLORS.policyOnly;
    nodes.push({
      id: 'LAYER:' + layer.id,
      label: layer.label,
      type: 'layer',
      shape: 'octahedron',
      status: layer.status === 'PARTIAL' ? 'partial' : 'online',
      color: color,
      size: 0.8,
      position: { x: Math.cos(angle) * 7, y: 1 + (index % 2) * 1.4, z: Math.sin(angle) * 7 },
      meta: {
        kicker: 'SECURITY CONTROL',
        sections: [{
          title: 'Control Information',
          rows: [
            ['Control', display(layer.label, 'Unknown')],
            ['Status', display(layer.status, 'Unknown')],
            ['Evidence', display(layer.evidence, 'Not available')],
            ['Encryption', 'NOT VERIFIED']
          ]
        }]
      }
    });
    links.push({ from: 'SECURITY_CORE', to: 'LAYER:' + layer.id, color: color, opacity: 0.65 });
  });

  Object.keys(policies).forEach(function (policy, index) {
    var info = policies[policy] || {};
    var eligible = (info.eligible_resources || []).slice(0, 8);
    nodes.push({
      id: 'POLICY:' + policy,
      label: policy,
      type: 'policy',
      shape: 'torus',
      status: 'online',
      color: COLORS.policyOnly,
      size: 0.65,
      position: { x: (index - (Object.keys(policies).length - 1) / 2) * 3.2, y: -3.2, z: 5 },
      meta: {
        kicker: 'PRIVACY POLICY',
        sections: [{
          title: 'Policy Information',
          rows: [
            ['Policy', policy],
            ['Allowed tiers', (info.allowed_tiers || []).join(', ') || 'NONE'],
            ['Eligible resources', eligible.join(', ') || 'NONE'],
            ['Scope', 'Backend policy engine snapshot']
          ]
        }]
      }
    });
    links.push({ from: 'SECURITY_CORE', to: 'POLICY:' + policy, color: COLORS.policyOnly, opacity: 0.5 });
  });

  datasetEvents.slice(0, 8).forEach(function (event, index) {
    var blocked = !!event.blocked;
    nodes.push({
      id: 'DATASET_EVENT:' + (event.event_id || index),
      label: display(event.event_type, 'DATASET EVENT'),
      type: event.type || 'dataset-event',
      shape: blocked ? 'torus' : 'file',
      status: blocked ? 'blocked' : 'online',
      color: blocked ? COLORS.event : COLORS.enforced,
      size: 0.55,
      position: { x: Math.cos(index * 2.1) * 8, y: 5 + index * 0.45, z: Math.sin(index * 2.1) * 8 },
      meta: {
        kicker: 'SELECTED DATASET SECURITY',
        sections: [{
          title: 'Dataset Event',
          rows: [
            ['Dataset', display(dataset.dataset_name, 'Unknown')],
            ['Event ID', display(event.event_id, 'Unknown')],
            ['Type', display(event.event_type, 'Unknown')],
            ['Severity', display(event.severity, 'Unknown')],
            ['Verdict', display(event.verdict, 'Unknown')],
            ['Recorded at', display(event.recorded_at, 'Unknown')]
          ]
        }]
      }
    });
    links.push({ from: 'SECURITY_CORE', to: 'DATASET_EVENT:' + (event.event_id || index), color: blocked ? COLORS.event : COLORS.enforced, opacity: 0.55 });
  });

  events.slice(0, Math.max(0, 8 - datasetEvents.length)).forEach(function (event, index) {
    var blocked = !!event.blocked;
    nodes.push({
      id: 'EVENT:' + (event.event_id || index),
      label: event.event_type,
      type: 'event',
      shape: 'file',
      status: blocked ? 'blocked' : 'online',
      color: blocked ? COLORS.event : COLORS.offline,
      size: 0.5,
      position: { x: Math.cos(index * 2.1) * 10, y: 4 + index * 0.45, z: Math.sin(index * 2.1) * 10 },
      meta: {
        kicker: blocked ? 'BLOCKED EVENT' : 'AUDIT EVENT',
        sections: [{
          title: 'Event Information',
          rows: [
            ['Event ID', display(event.event_id, 'Unknown')],
            ['Type', display(event.event_type, 'Unknown')],
            ['Severity', display(event.severity, 'Unknown')],
            ['Verdict', display(event.verdict, 'Unknown')],
            ['Task', display(event.task_id, 'Unknown')],
            ['Device', display(event.device_id, 'Unknown')],
            ['Recorded at', display(event.recorded_at, 'Unknown')]
          ]
        }]
      }
    });
    links.push({ from: 'SECURITY_CORE', to: 'EVENT:' + (event.event_id || index), color: blocked ? COLORS.event : COLORS.offline, opacity: 0.4 });
  });

  nodes.push({
    id: 'SIMULATED_ATTACKER',
    label: 'SIMULATED ATTACKER',
    type: 'attacker',
    shape: 'attacker',
    status: 'simulated',
    color: COLORS.attacker,
    size: 0.95,
    position: { x: 0, y: 7, z: -11 },
    meta: {
      kicker: 'EXTERNAL THREAT SIMULATOR',
      sections: [{
        title: 'Simulator Information',
        rows: [
          ['Scope', 'Local visualization only'],
          ['Network access', 'None'],
          ['Encryption', 'NOT VERIFIED'],
          ['Note', 'No real attack is performed.']
        ]
      }]
    }
  });
  links.push({ from: 'SIMULATED_ATTACKER', to: 'SECURITY_CORE', color: COLORS.attacker, opacity: 0.4 });

  return { nodes: nodes, links: links };
}

export function renderSecurityControls(container, data, inspection) {
  if (!container) return;
  var layers = (data && data.security_layers) || [];
  var datasetEvents = (inspection && inspection.dataset_security_events) || [];
  container.textContent = '';
  if (!layers.length && !datasetEvents.length) { container.textContent = 'No security controls are available.'; return; }
  datasetEvents.forEach(function (event) {
    var element = document.createElement('div');
    element.className = 'dtw-security-layer';
    element.innerHTML =
      '<strong>' + escapeHtml(display(event.event_type, 'DATASET EVENT') + ' · ' + display(event.verdict, 'UNKNOWN')) + '</strong>' +
      escapeHtml('Selected dataset report ' + display(inspection && inspection.report_id, 'Unknown'));
    container.appendChild(element);
  });
  layers.forEach(function (layer) {
    var element = document.createElement('div');
    element.className = 'dtw-security-layer';
    element.innerHTML =
      '<strong>' + escapeHtml(layer.label) + ' · ' + escapeHtml(display(layer.status, 'UNKNOWN')) + '</strong>' +
      escapeHtml(display(layer.evidence, 'No evidence recorded.'));
    container.appendChild(element);
  });
}

export function renderCapabilities(container, data, inspection, comparison) {
  if (!container) return;
  var capabilities = (data && data.capabilities) || {};
  var final = (inspection && inspection.final) || {};
  var formats = (inspection && inspection.stats && inspection.stats.formats) || [];
  var ga = comparison && comparison.algorithms && comparison.algorithms.proposed_ga;
  var rows = [
    ['Upload pipeline', 'AVAILABLE'],
    ['Archive validation', 'ENFORCED'],
    ['Policy enforcement', capabilities.policy_enforcement ? 'ENFORCED' : 'UNKNOWN'],
    ['GA scheduler', capabilities.ga_scheduler ? 'AVAILABLE' : 'UNKNOWN'],
    ['Transfer progress', capabilities.transfer_progress_available ? 'AVAILABLE' : 'NOT AVAILABLE'],
    ['Encryption', 'NOT VERIFIED'],
    ['Selected dataset', display(inspection && inspection.dataset && inspection.dataset.dataset_name, 'Not loaded')],
    ['Latest analysis', display(inspection && inspection.report_id, 'Not loaded')],
    ['Final status', display(final.status, 'Not available')],
    ['Detected formats', formats.slice(0, 5).map(function (item) { return item.name; }).join(', ') || 'Not available'],
    ['Simulated comparison', ga ? 'AVAILABLE' : 'Not run']
  ];
  container.textContent = '';
  rows.forEach(function (row) {
    var element = document.createElement('div');
    element.className = 'dtw-capability';
    element.innerHTML = '<strong>' + escapeHtml(row[0]) + '</strong>' + escapeHtml(row[1]);
    container.appendChild(element);
  });
}

export function scenarioOptions(select, data) {
  if (!select) return;
  select.textContent = '';
  var catalog = (data && data.simulation_catalog) || [];
  catalog.forEach(function (scenario) {
    var option = document.createElement('option');
    option.value = scenario.id;
    option.textContent = scenario.label;
    select.appendChild(option);
  });
  if (!catalog.length) {
    var empty = document.createElement('option');
    empty.value = 'UNKNOWN';
    empty.textContent = 'No simulation scenarios available';
    select.appendChild(empty);
  }
}

export function targetOptions(select, data) {
  if (!select) return;
  var current = select.value;
  select.textContent = '';
  var ids = [];
  (data.resources || []).forEach(function (resource) { ids.push(resource.resource_id); });
  (data.mec_devices || []).forEach(function (device) { ids.push(device.device_id); });
  ids.push('CENTRAL');
  Array.from(new Set(ids)).forEach(function (id) {
    var option = document.createElement('option');
    option.value = id;
    option.textContent = id;
    select.appendChild(option);
  });
  if (current && ids.indexOf(current) !== -1) select.value = current;
}

export function attackUrl(root) {
  return new URL('attack/', new URL(root.dataset.sceneUrl, window.location.origin)).pathname;
}

export { COLORS as SECURITY_COLORS };
