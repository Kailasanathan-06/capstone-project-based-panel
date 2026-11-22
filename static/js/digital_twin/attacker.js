import { display, escapeHtml } from './api_client.js';

const COLORS = {
  attacker: 0xfb7185,
  target: 0xf59e0b,
  protected: 0x34d399,
  policy: 0xa78bfa,
  offline: 0x64748b
};

export function buildAttackGraph(data, result, scenario, inspection, defense) {
  var before = (result && result.before) || {};
  var after = (result && result.after) || {};
  var targetId = display(after.resource_id || before.resource_id, 'TARGET');
  var dataset = (inspection && inspection.dataset) || {};
  var nodes = [];
  var links = [];
  var targetZones = {
    LOCAL: { x: -36, y: -3, z: 10 },
    MEC_STORAGE: { x: 30, y: -2, z: 8 },
    CLOUD_STORAGE: { x: 0, y: 18, z: 42 }
  };
  var targetZone = targetZones[targetId] || { x: 0, y: 0, z: 0 };
  var quarantined = !!(defense && defense.quarantine);

  nodes.push({
    id: 'SIMULATED_ATTACKER',
    label: 'SIMULATED ATTACKER',
    type: 'attacker',
    shape: 'attacker',
    status: 'simulated',
    color: COLORS.attacker,
    size: 1,
    position: { x: 0, y: 5, z: -48 },
    meta: {
      kicker: 'EXTERNAL THREAT SIMULATOR',
      sections: [{
        title: 'Simulation Information',
        rows: [
          ['Scenario', display(scenario && scenario.label, 'Unknown')],
          ['Backend evidence', display(scenario && scenario.backend_evidence, 'Unknown')],
          ['Dataset context', display(dataset.dataset_name, 'None selected')],
          ['Scope', 'Local visualization only'],
          ['Network access', 'None']
        ]
      }]
    }
  });

  nodes.push({
    id: 'ATTACK_TARGET',
    label: quarantined ? targetId + ' — ISOLATED' : targetId,
    type: quarantined ? 'quarantined' : 'target',
    shape: quarantined ? 'torus' : 'server',
    status: quarantined ? 'quarantined' : 'online',
    color: quarantined ? COLORS.policy : COLORS.target,
    size: 1,
    position: { x: targetZone.x, y: targetZone.y, z: targetZone.z },
    meta: {
      kicker: 'SIMULATED TARGET',
      sections: [{
        title: 'Target State',
        rows: [
          ['Resource ID', targetId],
          ['Status before', display(before.status, 'Unknown')],
          ['Status after', display(after.status, 'Unknown')],
          ['CPU before', display(before.cpu_utilization, 'Unknown')],
          ['CPU after', display(after.cpu_utilization, 'Unknown')],
          ['Memory before', display(before.memory_utilization, 'Unknown')],
          ['Memory after', display(after.memory_utilization, 'Unknown')],
          ['Risk before', display(before.security_risk, 'Unknown')],
          ['Risk after', display(after.security_risk, 'Unknown')],
          ['Dataset context', display(dataset.dataset_name, 'None selected')],
          ['Encryption', 'NOT VERIFIED']
        ]
      }]
    }
  });
  links.push({ from: 'SIMULATED_ATTACKER', to: 'ATTACK_TARGET', color: COLORS.attacker, opacity: 0.85 });

  nodes.push({
    id: 'PROTECTION_POLICY',
    label: 'PROTECTION POLICY VISUALIZATION',
    type: 'policy',
    shape: 'octahedron',
    status: 'online',
    color: COLORS.policy,
    size: 0.9,
    position: { x: 9, y: 1.5, z: 0 },
    meta: {
      kicker: 'PROTECTION POLICY VISUALIZATION',
      sections: [{
        title: 'Control Information',
        rows: [
          ['Policy enforcement', (data && data.capabilities && data.capabilities.policy_enforcement) ? 'ENFORCED' : 'UNKNOWN'],
          ['Shield meaning', 'Policy enforcement only'],
          ['Encryption', 'NOT VERIFIED'],
          ['Mitigation', 'Available through the simulated quarantine endpoint']
        ]
      }]
    }
  });
  links.push({ from: 'PROTECTION_POLICY', to: 'ATTACK_TARGET', color: COLORS.protected, opacity: 0.65 });

  nodes.push({
    id: 'TRUSTED_BOUNDARY',
    label: 'TRUSTED SECURITY BOUNDARY',
    type: 'boundary',
    shape: 'torus',
    status: 'online',
    color: COLORS.policy,
    size: 1.6,
    position: { x: 0, y: 2, z: -2 },
    meta: {
      kicker: 'TRUSTED BOUNDARY',
      sections: [{
        title: 'Boundary Information',
        rows: [
          ['Meaning', 'Visual policy boundary only'],
          ['Encryption', 'NOT VERIFIED']
        ]
      }]
    }
  });

  if (inspection) {
    nodes.push({
      id: 'DATASET_FILES',
      label: display(dataset.dataset_name, 'SELECTED DATASET'),
      type: 'dataset-root',
      shape: 'folder',
      status: 'online',
      color: COLORS.policy,
      size: 0.9,
      position: { x: -18, y: -8, z: 24 },
      meta: {
        kicker: 'DATASET CONTEXT',
        sections: [{
          title: 'Selected Dataset',
          rows: [
            ['Dataset', display(dataset.dataset_name, 'Unknown')],
            ['Report', display(inspection.report_id, 'Unknown')],
            ['Role', 'Only this dataset drives the security demonstration']
          ]
        }]
      }
    });
    links.push({ from: 'DATASET_FILES', to: 'ATTACK_TARGET', color: COLORS.policy, opacity: 0.45 });
  }

  if (defense) {
    nodes.push({
      id: 'QUARANTINED:' + targetId,
      label: 'ISOLATED · ' + targetId,
      type: 'quarantine',
      shape: 'storage',
      status: 'quarantined',
      color: COLORS.policy,
      size: 0.8,
      position: { x: targetZone.x + 5, y: targetZone.y - 3, z: targetZone.z + 4 },
      meta: {
        kicker: 'ISOLATED RESOURCE',
        sections: [{
          title: 'Quarantine Result',
          rows: [
            ['Resource', targetId],
            ['Status', display(defense.quarantine && (defense.quarantine.status || defense.quarantine.message), 'ISOLATED')],
            ['Scope', 'Simulated digital twin state only']
          ]
        }]
      }
    });
    links.push({ from: 'PROTECTION_POLICY', to: 'QUARANTINED:' + targetId, color: COLORS.policy, opacity: 0.9 });

    (defense.proposals || []).forEach(function (resource, index) {
      var id = 'REASSESSMENT_PROPOSAL:' + resource;
      nodes.push({
        id: id,
        label: 'PROPOSED · ' + resource,
        type: 'reassessment',
        shape: 'resource',
        status: 'proposed',
        color: COLORS.protected,
        size: 0.6,
        position: { x: -8 + index * 5, y: -10, z: 26 + index * 2 },
        meta: {
          kicker: 'POLICY-COMPLIANT REASSESSMENT',
          sections: [{
            title: 'Proposal',
            rows: [
              ['Resource', resource],
              ['Meaning', 'Proposed alternate resource; no live dispatch verified'],
              ['Encryption', 'NOT VERIFIED']
            ]
          }]
        }
      });
      links.push({ from: 'DATASET_FILES', to: id, color: COLORS.protected, opacity: 0.65 });
    });
  }

  return { nodes: nodes, links: links, targetId: targetId };
}

export function renderAttackStatus(container, result, scenario, inspection) {
  if (!container) return;
  if (!result) {
    container.textContent = 'SIMULATION — NO REAL ATTACK PERFORMED · ENCRYPTION NOT VERIFIED';
    return;
  }
  var before = result.before || {};
  var after = result.after || {};
  var dataset = (inspection && inspection.dataset) || {};
  container.innerHTML = [
    '<strong>SIMULATED ATTACKER</strong>',
    'Scenario: ' + escapeHtml(display(scenario && scenario.label, 'Unknown')),
    'Dataset context: ' + escapeHtml(display(dataset.dataset_name, 'None selected')),
    'Target: ' + escapeHtml(display(after.resource_id || before.resource_id, 'Unknown')),
    'Status: ' + escapeHtml(display(before.status, 'Unknown')) + ' → ' + escapeHtml(display(after.status, 'Unknown')),
    'Risk: ' + escapeHtml(display(before.security_risk, 'Unknown')) + ' → ' + escapeHtml(display(after.security_risk, 'Unknown')),
    '<strong>ENCRYPTION NOT VERIFIED</strong>'
  ].join('<br>');
}

export function renderDefenseStatus(container, defense, inspection) {
  if (!container) return;
  if (!defense) {
    container.textContent = 'NO DEFENSIVE ACTION RECORDED';
    return;
  }
  var dataset = (inspection && inspection.dataset) || {};
  var quarantine = defense.quarantine || {};
  var schedule = defense.schedule || {};
  container.innerHTML = [
    '<strong>PROTECTION POLICY VISUALIZATION</strong>',
    'Dataset context: ' + escapeHtml(display(dataset.dataset_name, 'None selected')),
    'Isolated resource: ' + escapeHtml(display(defense.targetId, 'Unknown')),
    'Quarantine status: ' + escapeHtml(display(quarantine.status || quarantine.message, 'ISOLATED')),
    'Reassessment: ' + escapeHtml(display(defense.status, 'PENDING')),
    'Scheduler response: ' + escapeHtml(display(schedule.message || schedule.status, 'SIMULATED RESPONSE')),
    'Proposed alternates: ' + escapeHtml((defense.proposals || []).join(', ') || 'NONE RECORDED'),
    '<strong>NO LIVE DISPATCH · ENCRYPTION NOT VERIFIED</strong>'
  ].join('<br>');
}
