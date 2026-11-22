import { display, escapeHtml, formatBytes } from './api_client.js';

const NODE_COLORS = {
  root: 0x34d399,
  folder: 0x22d3ee,
  file: 0x38bdf8,
  group: 0xf59e0b
};

export function buildDatasetGraph(inspection) {
  var graphNodes = (inspection && inspection.graph_nodes) || [];
  var graphEdges = (inspection && inspection.graph_edges) || [];
  var visible = graphNodes.slice(0, 220);
  var ids = new Set(visible.map(function (node) { return node.id; }));
  var depthCounts = {};
  var depthIndexes = {};
  visible.forEach(function (node) {
    var depth = node.depth || 0;
    depthCounts[depth] = (depthCounts[depth] || 0) + 1;
    depthIndexes[depth] = (depthIndexes[depth] || 0);
  });

  var nodes = visible.map(function (node) {
    var depth = node.depth || 0;
    var index = depthIndexes[depth] || 0;
    depthIndexes[depth] = index + 1;
    var count = Math.max(1, depthCounts[depth]);
    var angle = depth === 0 ? 0 : (index / count) * Math.PI * 2;
    var radius = depth * 4.6;
    var color = NODE_COLORS[node.type] || 0x38bdf8;
    if (node.type === 'file' && node.privacy_policy === 'UNASSIGNED') color = 0xfb7185;
    return {
      id: node.id,
      label: node.name,
      type: 'dataset-' + node.type,
      shape: node.type === 'folder' || node.type === 'root' ? 'octahedron' : node.type === 'group' ? 'torus' : 'file',
      status: node.privacy_policy === 'UNASSIGNED' ? 'blocked' : 'online',
      color: color,
      size: node.type === 'root' ? 1.1 : depth > 2 ? 0.55 : 0.75,
      position: {
        x: Math.cos(angle) * radius,
        y: -depth * 0.65 + (index % 2) * 0.6,
        z: Math.sin(angle) * radius
      },
      meta: {
        kicker: 'DATASET NODE',
        sections: [
          sectionForNode(node)
        ]
      }
    };
  });

  var links = graphEdges
    .filter(function (edge) { return ids.has(edge.from) && ids.has(edge.to); })
    .map(function (edge) { return { from: edge.from, to: edge.to, color: 0x426996, opacity: 0.55 }; });

  return { nodes: nodes, links: links, truncated: graphNodes.length > visible.length };
}

function sectionForNode(node) {
  var rows = [
    ['Name', display(node.name, 'Unknown')],
    ['Type', display(node.type, 'Unknown')],
    ['Path', display(node.path || '(root)', 'Unknown')],
    ['Depth', display(node.depth, 0)]
  ];
  var source = node.__source || {};
  if (source.format) rows.push(['Format', display(source.format, 'Unknown')]);
  if (source.category) rows.push(['Category', display(source.category, 'Unknown')]);
  if (source.privacy_policy) rows.push(['Privacy policy', display(source.privacy_policy, 'Unknown')]);
  if (source.selected_destination) rows.push(['Selected destination', display(source.selected_destination, 'UNASSIGNED')]);
  if (node.size !== undefined) rows.push(['Size', formatBytes(node.size)]);
  return { title: 'Dataset Information', rows: rows };
}

export function renderTree(container, tree, onSelect, query) {
  if (!container || !tree) return;
  var term = String(query || '').trim().toLowerCase();
  container.textContent = '';
  var list = document.createElement('ul');
  var rendered = appendTreeNode(list, tree, onSelect, term);
  if (rendered) container.appendChild(list);
  else container.textContent = 'No dataset nodes match this search.';
}

function appendTreeNode(parent, node, onSelect, term) {
  if (term && !matches(node, term)) return false;
  var item = document.createElement('li');
  var button = document.createElement('button');
  button.type = 'button';
  button.dataset.nodeId = node.id;
  button.textContent = (node.type === 'folder' || node.type === 'root' ? '▸ ' : '· ') + node.name;
  if (node.size !== undefined) button.textContent += '  (' + formatBytes(node.size) + ')';
  button.addEventListener('click', function () {
    var siblings = parent.ownerDocument.querySelectorAll('.dtw-tree button');
    Array.prototype.forEach.call(siblings, function (candidate) { candidate.classList.remove('is-selected'); });
    button.classList.add('is-selected');
    onSelect(node);
  });
  if (term && node.type !== 'file') button.textContent += '  [match]';
  item.appendChild(button);
  var children = node.children || [];
  if (children.length) {
    var list = document.createElement('ul');
    var any = false;
    children.forEach(function (child) {
      if (appendTreeNode(list, child, onSelect, term)) any = true;
    });
    if (any) item.appendChild(list);
  }
  parent.appendChild(item);
  return true;
}

function matches(node, term) {
  var haystack = [node.name, node.path, node.format, node.category, node.type].filter(Boolean).join(' ').toLowerCase();
  if (haystack.indexOf(term) !== -1) return true;
  return (node.children || []).some(function (child) { return matches(child, term); });
}

export function renderStats(container, inspection) {
  if (!container) return;
  var stats = (inspection && inspection.stats) || {};
  var analysis = (inspection && inspection.analysis) || {};
  var security = (inspection && inspection.security) || {};
  var cards = [
    card('Total files', display(stats.total_files, 0)),
    card('Total folders', display(stats.total_folders, 0)),
    card('Analyzed size', display(stats.total_size_formatted, formatBytes(stats.total_size_bytes))),
    card('Metadata files', display(stats.metadata_files, 0)),
    card('Integrity', security.integrity_verified ? 'VERIFIED' : 'NOT VERIFIED'),
    card('Policy blocks', display(security.blocked_policy_violations, 0)),
    card('Analysis method', display(analysis.method_recorded, 'Not available')),
    card('Analysis runtime', analysis.runtime_ms ? analysis.runtime_ms + ' ms' : 'Not recorded'),
    card('Energy estimate', display(analysis.energy_formatted, 'Not available'))
  ];
  var formats = (stats.formats || []).slice(0, 5).map(function (item) { return item.name + ': ' + item.count; });
  var categories = (stats.categories || []).slice(0, 5).map(function (item) { return item.name + ': ' + item.count; });
  if (formats.length) cards.push(card('Top formats', formats.join(', ')));
  if (categories.length) cards.push(card('Top categories', categories.join(', ')));
  container.textContent = '';
  cards.forEach(function (item) { container.appendChild(item); });
}

function card(label, value) {
  var element = document.createElement('div');
  element.className = 'dtw-stat-card';
  element.innerHTML = '<strong>' + escapeHtml(label) + '</strong>' + escapeHtml(value);
  return element;
}

export function renderSelection(container, node, inspection) {
  if (!container) return;
  if (!node) { container.textContent = 'No node selected.'; return; }
  var source = findSourceNode(inspection, node.id);
  var rows = [
    ['Name', display(node.name, 'Unknown')],
    ['Type', display(node.type, 'Unknown')],
    ['Path', display(node.path || '(root)', 'Unknown')],
    ['Depth', display(node.depth, 0)],
    ['Size', formatBytes(node.size)]
  ];
  if (source) {
    rows.push(['Format', display(source.format, 'Unknown')]);
    rows.push(['Category', display(source.category, 'Unknown')]);
    rows.push(['Privacy policy', display(source.privacy_policy, 'Unknown')]);
    rows.push(['Selected destination', display(source.selected_destination, 'UNASSIGNED')]);
  }
  container.innerHTML = '<strong>' + escapeHtml(node.name) + '</strong><br>' + rows.map(function (row) {
    return escapeHtml(row[0]) + ': ' + escapeHtml(row[1]);
  }).join('<br>');
}

function findSourceNode(inspection, id) {
  var result = null;
  function walk(node) {
    if (result) return;
    if (node.id === id) { result = node; return; }
    (node.children || []).forEach(walk);
  }
  if (inspection && inspection.tree) walk(inspection.tree);
  return result;
}

export function renderPartitions(container, inspection) {
  if (!container) return;
  var allocation = (inspection && inspection.allocation) || {};
  var partitions = (inspection && inspection.partitions) || [];
  container.textContent = '';
  if (!partitions.length) { container.textContent = 'No partitions loaded.'; return; }
  partitions.forEach(function (partition) {
    var element = document.createElement('div');
    var blocked = partition.status === 'BLOCKED';
    element.className = 'dtw-partition' + (blocked ? ' is-blocked' : '');
    element.innerHTML =
      '<strong>' + escapeHtml(partition.partition_id + ' · ' + partition.source) + '</strong>' +
      escapeHtml(partition.file_count + ' files · ' + partition.size_formatted + ' · ' + partition.strategy) + '<br>' +
      '<span>' + escapeHtml('Proposed: ' + display(partition.proposed_destination, 'UNASSIGNED')) + '</span><br>' +
      '<span>' + escapeHtml('Policies: ' + (partition.privacy_policies || []).join(', ')) + '</span>' +
      (blocked ? '<br><span>TASK BLOCKED — NO ELIGIBLE RESOURCE</span>' : '');
    container.appendChild(element);
  });
  if (allocation.label) {
    var label = document.createElement('div');
    label.className = 'dtw-callout';
    label.textContent = allocation.label;
    container.appendChild(label);
  }
}
