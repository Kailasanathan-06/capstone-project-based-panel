import { display, escapeHtml } from './api_client.js';

const COLORS = {
  queue: 0xa78bfa,
  resource: 0x34d399,
  tier: 0x22d3ee,
  blocked: 0xfb7185,
  ga: 0xf59e0b
};

export function recordedDecisions(data) {
  return ((data && data.scheduling && data.scheduling.decisions) || []);
}

export function hasRecordedDecision(data) {
  return recordedDecisions(data).length > 0;
}

export function buildSchedulingGraph(data) {
  var decisions = recordedDecisions(data);
  var nodes = [];
  var links = [];
  var tasks = (data && data.tasks) || [];
  var resources = (data && data.resources) || [];

  nodes.push({
    id: 'TASK_QUEUE',
    label: 'TASK QUEUE',
    type: 'queue',
    shape: 'folder',
    status: 'online',
    color: COLORS.queue,
    size: 1,
    position: { x: -10, y: 0, z: 0 },
    meta: {
      kicker: 'TASK QUEUE',
      sections: [{
        title: 'Queue Information',
        rows: [
          ['Recorded tasks', display(tasks.length, 0)],
          ['Decision source', display(data && data.scheduling && data.scheduling.decision_source, 'Unknown')],
          ['Note', 'Normal dispatch decisions are not persisted unless a SchedulingDecision record exists.']
        ]
      }]
    }
  });

  if (!decisions.length) {
    nodes.push({
      id: 'GA_CAPABILITY',
      label: 'GA SERVICE AVAILABLE',
      type: 'capability',
      shape: 'octahedron',
      status: 'online',
      color: COLORS.ga,
      size: 1,
      position: { x: 8, y: 0, z: 0 },
      meta: {
        kicker: 'SCHEDULING CAPABILITY',
        sections: [{
          title: 'Scheduling Information',
          rows: [
            ['Recorded decisions', 0],
            ['Decision status', 'No recorded decision'],
            ['Note', 'The GA service exists, but normal dispatch decisions are not persisted.']
          ]
        }]
      }
    });
    links.push({ from: 'TASK_QUEUE', to: 'GA_CAPABILITY', color: COLORS.ga, opacity: 0.5 });
    return { nodes: nodes, links: links, decision: null };
  }

  var decision = decisions[0];
  var resource = resources.find(function (item) { return item.resource_id === decision.selected_resource; });
  var tierId = 'TIER:' + display(decision.selected_tier, 'UNKNOWN');
  nodes.push({
    id: 'GA_DECISION',
    label: 'RECORDED GA DECISION',
    type: 'decision',
    shape: 'octahedron',
    color: COLORS.ga,
    status: 'online',
    size: 1,
    position: { x: -2, y: 0, z: 0 },
    meta: {
      kicker: 'RECORDED DECISION',
      sections: [{
        title: 'Decision Information',
        rows: [
          ['Task ID', display(decision.task_id, 'Unknown')],
          ['Algorithm', display(decision.algorithm, 'Unknown')],
          ['Selected resource', display(decision.selected_resource, 'Unknown')],
          ['Selected tier', display(decision.selected_tier, 'Unknown')],
          ['Recorded at', display(decision.recorded_at, 'Unknown')],
          ['Rejected candidates', display(decision.rejected_count, 0)],
          ['Objective scores', formatScores(decision.objective_scores)]
        ]
      }]
    }
  });
  nodes.push({
    id: decision.selected_resource,
    label: display(resource && resource.label, decision.selected_resource),
    type: 'resource',
    shape: 'server',
    status: resource && !resource.is_online ? 'offline' : 'online',
    color: resource && !resource.is_online ? 0x64748b : COLORS.resource,
    size: 0.9,
    position: { x: 6, y: 1.2, z: 0 },
    meta: {
      kicker: 'SELECTED RESOURCE',
      sections: [{
        title: 'Resource Information',
        rows: [
          ['Resource ID', display(decision.selected_resource, 'Unknown')],
          ['Resource type', display(resource && resource.resource_type, 'Unknown')],
          ['Status', display(resource && resource.status, 'Unknown')],
          ['CPU', display(resource && resource.cpu_utilization, 'Unknown')],
          ['Memory', display(resource && resource.memory_utilization, 'Unknown')]
        ]
      }]
    }
  });
  nodes.push({
    id: tierId,
    label: display(decision.selected_tier, 'UNKNOWN') + ' TIER',
    type: 'tier',
    shape: 'storage',
    status: 'online',
    color: COLORS.tier,
    size: 0.85,
    position: { x: 10, y: -1.2, z: 0 },
    meta: {
      kicker: 'SELECTED TIER',
      sections: [{
        title: 'Tier Information',
        rows: [
          ['Tier', display(decision.selected_tier, 'Unknown')],
          ['Source', 'Recorded SchedulingDecision']
        ]
      }]
    }
  });

  links.push({ from: 'TASK_QUEUE', to: 'GA_DECISION', color: COLORS.queue, opacity: 0.65 });
  links.push({ from: 'GA_DECISION', to: decision.selected_resource, color: COLORS.ga, opacity: 0.8 });
  links.push({ from: decision.selected_resource, to: tierId, color: COLORS.tier, opacity: 0.7 });
  return { nodes: nodes, links: links, decision: decision };
}

export function buildDatasetSchedulingGraph(inspection) {
  var decisions = (inspection && inspection.dataset_scheduling) || [];
  var dataset = (inspection && inspection.dataset) || {};
  var nodes = [];
  var links = [];
  var destinations = Array.from(new Set(decisions.map(function (decision) {
    return display(decision.selected_destination, 'UNASSIGNED');
  })));

  nodes.push({
    id: 'DATASET_FILES',
    label: display(dataset.dataset_name, 'SELECTED DATASET'),
    type: 'dataset-root',
    shape: 'folder',
    status: 'online',
    color: COLORS.queue,
    size: 1.05,
    position: { x: -11, y: 0, z: 0 },
    meta: {
      kicker: 'SELECTED DATASET',
      sections: [{
        title: 'Dataset Information',
        rows: [
          ['Dataset', display(dataset.dataset_name, 'Unknown')],
          ['Report ID', display(dataset.report_id, 'Unknown')],
          ['File count', display(dataset.file_count, 0)],
          ['File-level decisions', decisions.length],
          ['Source', 'Persisted dataset analysis report']
        ]
      }]
    }
  });

  destinations.slice(0, 6).forEach(function (destination, index) {
    nodes.push({
      id: 'DESTINATION:' + destination,
      label: destination,
      type: 'resource',
      shape: destination === 'UNASSIGNED' ? 'torus' : 'storage',
      status: destination === 'UNASSIGNED' ? 'blocked' : 'online',
      color: destination === 'UNASSIGNED' ? COLORS.blocked : COLORS.resource,
      size: 0.8,
      position: { x: 8, y: 3 - index * 1.2, z: 0 },
      meta: {
        kicker: 'PROPOSED STORAGE PLACEMENT',
        sections: [{
          title: 'Placement Information',
          rows: [
            ['Destination', destination],
            ['Assigned files', decisions.filter(function (decision) {
              return display(decision.selected_destination, 'UNASSIGNED') === destination;
            }).length],
            ['Meaning', 'Proposed or recorded placement; no live dispatch']
          ]
        }]
      }
    });
  });

  decisions.slice(0, 12).forEach(function (decision, index) {
    var destination = display(decision.selected_destination, 'UNASSIGNED');
    var blocked = destination === 'UNASSIGNED' || decision.result === 'BLOCKED';
    nodes.push({
      id: 'DATASET_DECISION:' + decision.task_id,
      label: blocked ? 'TASK BLOCKED — NO ELIGIBLE RESOURCE' : decision.file_name,
      type: blocked ? 'blocked' : 'decision',
      shape: blocked ? 'attacker' : 'file',
      status: blocked ? 'blocked' : 'online',
      color: blocked ? COLORS.blocked : COLORS.ga,
      size: 0.6,
      position: { x: -2, y: 4 - index * 0.8, z: 0 },
      meta: {
        kicker: 'FILE-LEVEL ALLOCATION DECISION',
        sections: [{
          title: 'Decision Information',
          rows: [
            ['File', display(decision.file_name, 'Unknown')],
            ['Privacy policy', display(decision.privacy_policy, 'UNKNOWN')],
            ['Eligible resources', (decision.candidate_resources || []).join(', ') || 'NONE'],
            ['Selected destination', destination],
            ['Rationale', display(decision.decision_rationale, 'Not recorded')],
            ['Rejected candidates', (decision.rejected_candidates || []).join(', ') || 'NONE'],
            ['Result', display(decision.result, 'PROPOSED')]
          ]
        }]
      }
    });
    links.push({ from: 'DATASET_FILES', to: 'DATASET_DECISION:' + decision.task_id, color: COLORS.queue, opacity: 0.5 });
    links.push({ from: 'DATASET_DECISION:' + decision.task_id, to: 'DESTINATION:' + destination, color: blocked ? COLORS.blocked : COLORS.ga, opacity: 0.7 });
  });

  return { nodes: nodes, links: links, decisions: decisions };
}

export function buildComparisonGraph(comparison) {
  var algorithms = (comparison && comparison.algorithms) || {};
  var ga = algorithms.proposed_ga || {};
  var assignments = ga.assignments || [];
  var history = ga.history || [];
  var nodes = [];
  var links = [];
  var selected = Array.from(new Set(assignments.filter(function (value) { return value && value !== 'BLOCKED'; })));

  nodes.push({
    id: 'BENCHMARK_TASKS',
    label: 'BENCHMARK TASKS',
    type: 'queue',
    shape: 'folder',
    status: 'online',
    color: COLORS.queue,
    size: 1,
    position: { x: -10, y: 0, z: 0 },
    meta: {
      kicker: 'BENCHMARK WORKLOAD',
      sections: [{
        title: 'Comparison Information',
        rows: [
          ['Tasks', display(comparison && comparison.metadata && comparison.metadata.tasks_count, 0)],
          ['Population', display(comparison && comparison.metadata && comparison.metadata.population, 0)],
          ['Generations', display(comparison && comparison.metadata && comparison.metadata.generations, 0)],
          ['Seed', display(comparison && comparison.metadata && comparison.metadata.seed, 0)],
          ['Source', 'Generated benchmark tasks; not a live dispatch decision']
        ]
      }]
    }
  });

  nodes.push({
    id: 'PROPOSED_GA',
    label: 'PROPOSED GA',
    type: 'decision',
    shape: 'octahedron',
    status: 'online',
    color: COLORS.ga,
    size: 1.05,
    position: { x: -2, y: 0, z: 0 },
    meta: {
      kicker: 'SIMULATED COMPARISON',
      sections: [{
        title: 'GA Metrics',
        rows: [
          ['Best fitness', display(ga.metrics && ga.metrics.best_fitness, 'Unknown')],
          ['Generations', display(ga.metrics && ga.metrics.generations, 0)],
          ['Avg latency', display(ga.metrics && ga.metrics.avg_latency_ms, 'Unknown') + ' ms'],
          ['Energy', display(ga.metrics && ga.metrics.total_energy_j, 'Unknown') + ' J'],
          ['Policy compliance', formatScore(ga.metrics && ga.metrics.policy_compliance_rate)],
          ['Blocked tasks', display(ga.metrics && ga.metrics.blocked_tasks, 0)]
        ]
      }]
    }
  });
  links.push({ from: 'BENCHMARK_TASKS', to: 'PROPOSED_GA', color: COLORS.queue, opacity: 0.65 });

  selected.slice(0, 10).forEach(function (resourceId, index) {
    var blocked = resourceId === 'BLOCKED';
    nodes.push({
      id: 'CANDIDATE:' + resourceId,
      label: blocked ? 'TASK BLOCKED — NO ELIGIBLE RESOURCE' : resourceId,
      type: blocked ? 'blocked' : 'resource',
      shape: blocked ? 'attacker' : 'server',
      status: blocked ? 'blocked' : 'online',
      color: blocked ? COLORS.blocked : COLORS.resource,
      size: 0.8,
      position: { x: 6, y: 3 - index * 1.1, z: 0 },
      meta: {
        kicker: blocked ? 'POLICY ENFORCEMENT' : 'ASSIGNED RESOURCE',
        sections: [{
          title: 'Assignment Information',
          rows: [
            ['Resource ID', display(resourceId, 'Unknown')],
            ['Assignment count', assignments.filter(function (value) { return value === resourceId; }).length],
            ['Source', 'Simulated benchmark comparison']
          ]
        }]
      }
    });
    links.push({ from: 'PROPOSED_GA', to: 'CANDIDATE:' + resourceId, color: blocked ? COLORS.blocked : COLORS.resource, opacity: 0.7 });
  });

  if (!history.length) {
    nodes.push({
      id: 'NO_HISTORY',
      label: 'NO GENERATION HISTORY',
      type: 'note',
      shape: 'file',
      status: 'online',
      color: 0x64748b,
      size: 0.6,
      position: { x: -2, y: -3, z: 0 },
      meta: { kicker: 'NOTE', sections: [{ title: 'History', rows: [['Status', 'No generation history returned.']] }] }
    });
  }

  return { nodes: nodes, links: links, comparison: comparison };
}

export function renderGaStatus(container, data, comparison, inspection) {
  if (!container) return;
  var decisions = recordedDecisions(data);
  var datasetDecisions = (inspection && inspection.dataset_scheduling) || [];
  var ga = comparison && comparison.algorithms && comparison.algorithms.proposed_ga;
  var lines = [];
  if (datasetDecisions.length) {
    lines.push('<strong>SELECTED DATASET DECISIONS</strong>');
    lines.push('Files: ' + datasetDecisions.length);
    lines.push('Placed: ' + datasetDecisions.filter(function (item) { return item.result === 'COMPLETED' || item.result === 'PROPOSED'; }).length);
    lines.push('Blocked: ' + datasetDecisions.filter(function (item) { return item.result === 'BLOCKED'; }).length);
    lines.push('Source: persisted analysis report');
  } else {
    lines.push('<strong>NO SELECTED DATASET DECISIONS</strong>');
    lines.push('Select an analyzed dataset to show recorded file-level decisions.');
  }
  if (decisions.length) {
    var decision = decisions[0];
    lines.push('<strong>RECORDED DISPATCH DECISION</strong>');
    lines.push('Task: ' + escapeHtml(decision.task_id));
    lines.push('Algorithm: ' + escapeHtml(display(decision.algorithm, 'Unknown')));
    lines.push('Selected: ' + escapeHtml(display(decision.selected_resource, 'Unknown')) + ' / ' + escapeHtml(display(decision.selected_tier, 'Unknown')));
  }
  if (ga && ga.metrics) {
    lines.push('<strong>SIMULATED COMPARISON</strong>');
    lines.push('Best fitness: ' + escapeHtml(display(ga.metrics.best_fitness, 'Unknown')));
    lines.push('Generations: ' + escapeHtml(display(ga.metrics.generations, 0)));
    lines.push('Policy compliance: ' + escapeHtml(formatScore(ga.metrics.policy_compliance_rate)));
    lines.push('Blocked tasks: ' + escapeHtml(display(ga.metrics.blocked_tasks, 0)));
  }
  container.innerHTML = lines.join('<br>');
}

export function renderGaHistory(container, data, comparison, inspection) {
  if (!container) return;
  var ga = comparison && comparison.algorithms && comparison.algorithms.proposed_ga;
  var history = (ga && ga.history) || [];
  var decisions = recordedDecisions(data);
  var datasetDecisions = (inspection && inspection.dataset_scheduling) || [];
  if (!history.length && !decisions.length && !datasetDecisions.length) {
    container.textContent = 'No scheduling history is available for the selected dataset.';
    return;
  }
  var rows = [];
  datasetDecisions.slice(0, 8).forEach(function (decision) {
    rows.push(decision.file_name + ' → ' + display(decision.selected_destination, 'UNASSIGNED') + ' · ' + display(decision.result, 'PROPOSED'));
  });
  history.slice(-12).forEach(function (item) {
    if (!Array.isArray(item)) return;
    rows.push('Simulated gen ' + display(item[0], '?') + ' · best ' + display(item[1], '?') + ' · avg ' + display(item[2], '?'));
  });
  decisions.slice(0, 6).forEach(function (decision) {
    rows.push('Recorded dispatch · ' + decision.task_id + ' → ' + display(decision.selected_resource, 'Unknown'));
  });
  container.innerHTML = rows.map(escapeHtml).join('<br>');
}

function formatScores(scores) {
  var entries = Object.keys(scores || {}).map(function (key) { return key + '=' + scores[key]; });
  return entries.length ? entries.join(', ') : 'Not recorded';
}

function formatScore(value) {
  if (value === null || value === undefined || value === '') return 'Unknown';
  return String(Math.round(Number(value) * 100)) + '%';
}

export { COLORS as GA_COLORS };
