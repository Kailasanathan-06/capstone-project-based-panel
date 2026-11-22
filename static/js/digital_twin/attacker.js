import { display, escapeHtml } from './api_client.js';

const COLORS = {
  attacker: 0xfb7185,
  target: 0xf59e0b,
  protected: 0x34d399,
  policy: 0xa78bfa,
  offline: 0x64748b
};

export function buildAttackGraph(data, result, scenario) {
  var before = (result && result.before) || {};
  var after = (result && result.after) || {};
  var targetId = display(after.resource_id || before.resource_id, 'TARGET');
  var nodes = [];
  var links = [];

  nodes.push({
    id: 'SIMULATED_ATTACKER',
    label: 'SIMULATED ATTACKER',
    type: 'attacker',
    shape: 'attacker',
    status: 'simulated',
    color: COLORS.attacker,
    size: 1,
    position: { x: -10, y: 3, z: 0 },
    meta: {
      kicker: 'EXTERNAL THREAT SIMULATOR',
      sections: [{
        title: 'Simulation Information',
        rows: [
          ['Scenario', display(scenario && scenario.label, 'Unknown')],
          ['Backend evidence', display(scenario && scenario.backend_evidence, 'Unknown')],
          ['Scope', 'Local visualization only'],
          ['Network access', 'None']
        ]
      }]
    }
  });

  nodes.push({
    id: 'ATTACK_TARGET',
    label: targetId,
    type: 'target',
    shape: 'server',
    status: after.availability === false || after.availability === 'false' ? 'offline' : 'online',
    color: after.availability === false || after.availability === 'false' ? COLORS.offline : COLORS.target,
    size: 1,
    position: { x: 0, y: 0, z: 0 },
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

  return { nodes: nodes, links: links, targetId: targetId };
}

export function renderAttackStatus(container, result, scenario) {
  if (!container) return;
  if (!result) {
    container.textContent = 'SIMULATION — NO REAL ATTACK PERFORMED · ENCRYPTION NOT VERIFIED';
    return;
  }
  var before = result.before || {};
  var after = result.after || {};
  container.innerHTML = [
    '<strong>SIMULATED ATTACKER</strong>',
    'Scenario: ' + escapeHtml(display(scenario && scenario.label, 'Unknown')),
    'Target: ' + escapeHtml(display(after.resource_id || before.resource_id, 'Unknown')),
    'Status: ' + escapeHtml(display(before.status, 'Unknown')) + ' → ' + escapeHtml(display(after.status, 'Unknown')),
    'Risk: ' + escapeHtml(display(before.security_risk, 'Unknown')) + ' → ' + escapeHtml(display(after.security_risk, 'Unknown')),
    '<strong>ENCRYPTION NOT VERIFIED</strong>'
  ].join('<br>');
}
