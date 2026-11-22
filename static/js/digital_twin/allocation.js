import { display, formatBytes } from './api_client.js';

const COLORS = {
  root: 0x38bdf8,
  partition: 0x22d3ee,
  blocked: 0xfb7185,
  storage: 0x34d399,
  emulator: 0x60a5fa
};

export function buildAllocationGraph(inspection) {
  var allocation = (inspection && inspection.allocation) || {};
  var partitions = ((inspection && inspection.partitions) || []).slice(0, 14);
  var tiers = allocation.tiers || {};
  var nodes = [];
  var links = [];

  nodes.push({
    id: 'DATASET:' + display(inspection && inspection.report_id, 'DATASET'),
    label: display(inspection && inspection.file_name, 'Uploaded Dataset'),
    type: 'dataset',
    shape: 'folder',
    status: 'online',
    color: COLORS.root,
    size: 1.05,
    position: { x: -12, y: 0, z: 0 },
    meta: {
      kicker: 'DATASET SOURCE',
      sections: [{
        title: 'Dataset Information',
        rows: [
          ['File name', display(inspection && inspection.file_name, 'Unknown')],
          ['Report ID', display(inspection && inspection.report_id, 'Unknown')],
          ['Execution mode', display(inspection && inspection.execution_mode, 'Unknown')],
          ['Allocation label', display(allocation.label, 'Unknown')]
        ]
      }]
    }
  });

  var rootId = nodes[0].id;
  var counts = {};
  partitions.forEach(function (partition) {
    var key = partition.proposed_destination || 'UNASSIGNED';
    counts[key] = (counts[key] || 0) + 1;
  });

  partitions.forEach(function (partition, index) {
    var blocked = partition.status === 'BLOCKED';
    var id = 'PARTITION:' + partition.partition_id;
    var destination = partition.proposed_destination || 'UNASSIGNED';
    var slot = counts[destination] > 1 ? (counts[destination] - 1) : 0;
    nodes.push({
      id: id,
      label: partition.partition_id + ' · ' + partition.source,
      type: 'partition',
      shape: 'octahedron',
      status: blocked ? 'blocked' : 'online',
      color: blocked ? COLORS.blocked : COLORS.partition,
      size: 0.8,
      position: {
        x: -2,
        y: 3.2 - index * 1.05,
        z: (slot - 0.5) * 2.2
      },
      meta: {
        kicker: 'ALLOCATION PARTITION',
        sections: [{
          title: 'Partition Information',
          rows: [
            ['Partition ID', display(partition.partition_id, 'Unknown')],
            ['Source', display(partition.source, 'Unknown')],
            ['Strategy', display(partition.strategy, 'Unknown')],
            ['File count', display(partition.file_count, 0)],
            ['Size', display(partition.size_formatted, formatBytes(partition.size_bytes))],
            ['Proposed destination', display(destination, 'UNASSIGNED')],
            ['Privacy policies', (partition.privacy_policies || []).join(', ') || 'Unknown'],
            ['Status', blocked ? 'TASK BLOCKED — NO ELIGIBLE RESOURCE' : 'PROPOSED']
          ]
        }]
      }
    });
    links.push({ from: rootId, to: id, color: COLORS.root, opacity: 0.5, label: 'Dataset partition' });
    if (!blocked && destination !== 'UNASSIGNED') {
      links.push({ from: id, to: destination, color: COLORS.storage, opacity: 0.75, label: 'Proposed placement' });
    } else {
      links.push({ from: id, to: 'BLOCKED', color: COLORS.blocked, opacity: 0.8, label: 'TASK BLOCKED — NO ELIGIBLE RESOURCE' });
    }
  });

  Object.keys(tiers).forEach(function (destinationId, index) {
    var tier = tiers[destinationId] || {};
    nodes.push({
      id: destinationId,
      label: tier.is_emulator ? 'CLOUD EMULATOR' : display(tier.name, destinationId),
      type: 'storage',
      shape: tier.is_emulator ? 'cloud' : 'storage',
      status: 'online',
      color: tier.is_emulator ? COLORS.emulator : COLORS.storage,
      size: 0.95,
      position: { x: 10, y: 3 - index * 2, z: 0 },
      meta: {
        kicker: 'ALLOCATION TARGET',
        sections: [{
          title: 'Storage Information',
          rows: [
            ['Destination ID', display(tier.destination_id, destinationId)],
            ['Name', display(tier.name, destinationId)],
            ['Type', display(tier.type, 'Unknown')],
            ['Capacity', formatBytes(tier.capacity_bytes)],
            ['Used', formatBytes(tier.used_bytes)],
            ['Available', formatBytes(tier.free_bytes)],
            ['Privacy policy', display(tier.privacy_policy, 'Unknown')],
            ['Active', tier.is_active ? 'YES' : 'NO']
          ]
        }]
      }
    });
  });

  nodes.push({
    id: 'BLOCKED',
    label: 'TASK BLOCKED — NO ELIGIBLE RESOURCE',
    type: 'blocked',
    shape: 'attacker',
    status: 'blocked',
    color: COLORS.blocked,
    size: 0.9,
    position: { x: 10, y: 3 - Object.keys(tiers).length * 2, z: 0 },
    meta: {
      kicker: 'POLICY ENFORCEMENT',
      sections: [{
        title: 'Security Information',
        rows: [
          ['Outcome', 'TASK BLOCKED — NO ELIGIBLE RESOURCE'],
          ['Reason', 'No eligible storage destination matched the dataset privacy policy.'],
          ['Policy enforcement', 'Backend policy decision only'],
          ['Encryption', 'NOT VERIFIED']
        ]
      }]
    }
  });

  return { nodes: nodes, links: links, rootId: rootId };
}

export function allocationTargets(inspection) {
  var tiers = ((inspection && inspection.allocation && inspection.allocation.tiers) || {});
  return Object.keys(tiers).map(function (id) {
    return {
      id: id,
      label: tiers[id].is_emulator ? 'CLOUD EMULATOR' : display(tiers[id].name, id)
    };
  });
}
