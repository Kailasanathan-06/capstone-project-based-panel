import { display, formatBytes } from './api_client.js';

const COLORS = {
  central: 0x38bdf8,
  storage: 0x22d3ee,
  mec: 0x34d399,
  device: 0xa78bfa,
  cloud: 0x60a5fa,
  attacker: 0xfb7185,
  offline: 0x64748b,
  link: 0x426996,
  threat: 0xfb7185
};

function statusColor(isOnline, color) {
  return isOnline ? color : COLORS.offline;
}

function section(title, rows) {
  return { title: title, rows: rows };
}

export function buildNetwork(data) {
  var nodes = [];
  var links = [];
  var server = data.server || {};
  var resources = data.resources || [];
  var mecDevices = data.mec_devices || [];
  var tiers = data.tiers || [];
  var clients = data.client_devices || [];
  var details = data.device_details || {};
  var mecCount = Math.max(mecDevices.length, 1);
  var radius = Math.max(8, mecCount * 1.9);

  var serverDetail = details.CENTRAL || {};
  nodes.push({
    id: 'CENTRAL',
    label: 'SecureDT Central Server',
    type: 'server',
    shape: 'server',
    status: display(server.status, 'ONLINE').toLowerCase(),
    color: COLORS.central,
    size: 1.15,
    position: { x: 0, y: 0, z: 0 },
    meta: {
      kicker: 'CONTROL PLANE',
      sections: [
        section('Device Information', [
          ['Device name', display(server.label, 'SecureDT Central Server')],
          ['Resource ID', display(server.id, 'CENTRAL')],
          ['Connection type', 'Backend control plane'],
          ['Status', display(server.status, 'Unknown')]
        ]),
        section('Current Activity', [
          ['Registered MECs', display(server.registered_mecs, 0)],
          ['Connected MECs', display(server.connected_mecs, 0)],
          ['Active tasks', display(server.active_tasks, 0)],
          ['Active transfers', display(server.active_transfers, 0)],
          ['Policy enforcement', display(serverDetail.policy_enforcement, 'Unknown')]
        ]),
        section('Security Information', [
          ['Encryption', 'NOT VERIFIED'],
          ['Telemetry mode', display(serverDetail.telemetry_mode, 'BACKEND_SNAPSHOT')],
          ['Note', display(serverDetail.details_note, 'Backend snapshot only.')]
        ])
      ]
    }
  });

  var local = tiers.find(function (tier) { return tier.destination_id === 'LOCAL_STORAGE'; });
  var mecStorage = tiers.find(function (tier) { return tier.destination_id === 'MEC_STORAGE'; });
  var cloud = tiers.find(function (tier) { return tier.destination_id === 'CLOUD_STORAGE'; });

  function storageNode(tier, id, label, x, y, z, color) {
    if (!tier) return null;
    var detail = details[id] || {};
    var online = tier.destination_type !== 'MEC' || (server.connected_mecs || 0) > 0;
    return {
      id: id,
      label: label,
      type: 'storage',
      shape: tier.destination_type === 'CLOUD' ? 'cloud' : 'storage',
      status: online ? 'online' : 'offline',
      color: statusColor(online, color),
      size: 1,
      position: { x: x, y: y, z: z },
      meta: {
        kicker: 'STORAGE NODE',
        sections: [
          section('Device Information', [
            ['Device name', display(tier.name, label)],
            ['Resource ID', display(tier.destination_id, id)],
            ['Resource type', display(tier.destination_type, 'STORAGE')],
            ['Connection type', tier.is_emulator ? 'Cloud emulator' : 'Configured storage destination'],
            ['Status', online ? 'ONLINE' : 'OFFLINE']
          ]),
          section('Storage Information', [
            ['Total capacity', formatBytes(tier.capacity_bytes)],
            ['Used storage', formatBytes(tier.used_bytes)],
            ['Available storage', formatBytes(tier.free_bytes !== undefined ? tier.free_bytes : Number(tier.capacity_bytes || 0) - Number(tier.used_bytes || 0))],
            ['Utilization', detail.utilization_percent === null || detail.utilization_percent === undefined ? 'Unknown' : detail.utilization_percent + '%'],
            ['Stored datasets', display(detail.replica_count, 'Unknown')],
            ['Inventory files', display(detail.inventory_item_count, 0)]
          ]),
          section('Security Information', [
            ['Allowed policy', display(tier.privacy_tier_allowed, 'Unknown')],
            ['Trust state', display(detail.status, 'Unknown')],
            ['Protection mechanisms', 'Privacy policy enforcement only'],
            ['Encryption', 'NOT VERIFIED'],
            ['Last heartbeat', display(detail.freshness_seconds, 'Unknown')]
          ]),
          section('Current Activity', [
            ['Assigned tasks', display(detail.assigned_task_count, 0)],
            ['Telemetry mode', display(detail.telemetry_mode, 'Unknown')],
            ['Note', display(detail.details_note, 'Unknown')]
          ])
        ]
      }
    };
  }

  var localNode = storageNode(local, 'LOCAL', 'LOCAL STORAGE', -radius, 0.5, 2.5, COLORS.storage);
  var mecStorageNode = storageNode(mecStorage, 'MEC_STORAGE', 'MEC STORAGE', 0, -0.5, -radius, COLORS.mec);
  var cloudNode = storageNode(cloud, 'CLOUD', cloud && cloud.is_emulator ? 'CLOUD EMULATOR' : 'CLOUD STORAGE', radius, 0.5, 2.5, COLORS.cloud);
  [localNode, mecStorageNode, cloudNode].forEach(function (node) { if (node) nodes.push(node); });

  mecDevices.forEach(function (device, index) {
    var angle = (index / Math.max(1, mecDevices.length)) * Math.PI * 2;
    var detail = details[device.device_id] || {};
    var online = device.connection_state === 'CONNECTED';
    nodes.push({
      id: device.device_id,
      label: device.device_id,
      type: 'mec',
      shape: 'server',
      status: online ? 'online' : 'offline',
      color: statusColor(online, COLORS.mec),
      size: 0.9,
      position: {
        x: Math.cos(angle) * radius,
        y: 1.4 + (index % 2) * 1.5,
        z: Math.sin(angle) * radius
      },
      meta: {
        kicker: 'MEC RESOURCE',
        sections: [
          section('Device Information', [
            ['Device name', display(detail.label, device.device_id)],
            ['Resource ID', display(device.device_id, 'Unknown')],
            ['Resource type', 'EDGE_AGENT'],
            ['Connection type', display(device.connection_state, 'Unknown')],
            ['Status', display(device.connection_state, 'Unknown')]
          ]),
          section('Storage Information', [
            ['Storage utilization', 'Shared MEC tier'],
            ['Shared storage ID', display(detail.shared_storage_tier_id, 'MEC_STORAGE')],
            ['Current task count', display(device.active_tasks, 0)]
          ]),
          section('Security Information', [
            ['Approval / trust', display(device.connection_state, 'Unknown')],
            ['Telemetry mode', display(device.telemetry_mode, 'Unknown')],
            ['Heartbeat freshness', display(device.heartbeat_freshness_seconds, 'Unknown')],
            ['Encryption', 'NOT VERIFIED']
          ]),
          section('Current Activity', [
            ['CPU utilization', display(device.cpu_utilization, 'Unknown')],
            ['Memory utilization', display(device.memory_utilization, 'Unknown')],
            ['Note', display(detail.details_note, 'Unknown')]
          ])
        ]
      }
    });
  });

  clients.forEach(function (client, index) {
    var assigned = client.assigned_mec || null;
    var anchor = assigned ? nodes.find(function (node) { return node.id === assigned; }) : null;
    var position = anchor
      ? { x: anchor.position.x + 1.8, y: anchor.position.y - 1.8, z: anchor.position.z + 1.8 }
      : { x: (index - (clients.length - 1) / 2) * 2.6, y: -3.6, z: 6.5 };
    nodes.push({
      id: client.client_id,
      label: client.client_id,
      type: 'device',
      shape: 'device',
      status: 'online',
      color: COLORS.device,
      size: 0.7,
      position: position,
      meta: {
        kicker: 'CONNECTED DEVICE',
        sections: [
          section('Device Information', [
            ['Device name', display(client.label, client.client_id)],
            ['Resource ID', display(client.client_id, 'Unknown')],
            ['Resource type', display(client.client_type, 'WEB_CLIENT')],
            ['Connection state', 'Backend upload client'],
            ['Assigned MEC', display(assigned, 'NOT RECORDED')]
          ]),
          section('Security Information', [
            ['Encryption', 'NOT VERIFIED'],
            ['Note', display(client.note, 'Upload client reported by the backend.')]
          ])
        ]
      }
    });
    links.push({
      from: 'CENTRAL',
      to: client.client_id,
      color: COLORS.link,
      opacity: 0.7,
      label: assigned ? 'Assigned MEC link' : 'Device connection; MEC assignment not recorded'
    });
  });

  resources.filter(function (resource) {
    return resource.resource_type === 'MEC' && !nodes.some(function (node) { return node.id === resource.resource_id; });
  }).forEach(function (resource, index) {
    nodes.push({
      id: resource.resource_id,
      label: resource.resource_id,
      type: 'mec',
      shape: 'server',
      status: resource.is_online ? 'online' : 'offline',
      color: statusColor(resource.is_online, COLORS.mec),
      size: 0.9,
      position: { x: Math.cos(index) * radius, y: 2 + index % 3, z: Math.sin(index) * radius },
      meta: {
        kicker: 'RESOURCE SNAPSHOT',
        sections: [
          section('Device Information', [['Resource ID', display(resource.resource_id, 'Unknown')], ['Status', display(resource.status, 'Unknown')]]),
          section('Current Activity', [['Active tasks', display(resource.active_tasks, 0)], ['CPU', display(resource.cpu_utilization, 'Unknown')], ['Memory', display(resource.memory_utilization, 'Unknown')]])
        ]
      }
    });
  });

  nodes.push({
    id: 'ATTACKER',
    label: 'SIMULATED ATTACKER',
    type: 'attacker',
    shape: 'attacker',
    status: 'simulated',
    color: COLORS.attacker,
    size: 1,
    position: { x: 0, y: 7, z: -radius - 7 },
    meta: {
      kicker: 'EXTERNAL THREAT SIMULATOR',
      sections: [
        section('Device Information', [
          ['Device name', display((details.ATTACKER || {}).label, 'SIMULATED ATTACKER')],
          ['Resource ID', 'ATTACKER'],
          ['Resource type', 'SIMULATION'],
          ['Status', 'SIMULATED']
        ]),
        section('Security Information', [
          ['Scope', 'Local visualization only'],
          ['Network access', 'None'],
          ['Encryption', 'NOT VERIFIED'],
          ['Note', display((details.ATTACKER || {}).details_note, 'No real attack is performed.')]
        ])
      ]
    }
  });

  function link(from, to, color, opacity, label) {
    if (nodes.some(function (node) { return node.id === from; }) && nodes.some(function (node) { return node.id === to; })) {
      links.push({ from: from, to: to, color: color || COLORS.link, opacity: opacity || 0.65, label: label });
    }
  }

  link('CENTRAL', 'LOCAL', COLORS.link, 0.8, 'Control plane to local storage');
  link('CENTRAL', 'MEC_STORAGE', COLORS.link, 0.8, 'Control plane to MEC storage');
  link('CENTRAL', 'CLOUD', COLORS.link, 0.8, 'Control plane to cloud emulator');
  mecDevices.forEach(function (device) {
    link('CENTRAL', device.device_id, COLORS.link, 0.6, 'MEC registration');
    link(device.device_id, 'MEC_STORAGE', COLORS.mec, 0.45, 'Shared MEC tier');
  });
  link('CENTRAL', 'ATTACKER', COLORS.threat, 0.35, 'Simulated threat vector');

  return { nodes: nodes, links: links };
}

export function storageTargets(data) {
  return (data.tiers || []).map(function (tier) {
    return {
      id: tier.destination_id === 'LOCAL_STORAGE' ? 'LOCAL' : tier.destination_id === 'CLOUD_STORAGE' ? 'CLOUD' : tier.destination_id,
      label: tier.is_emulator ? 'CLOUD EMULATOR' : display(tier.name, tier.destination_id)
    };
  });
}

export function nodeById(nodes, id) {
  return nodes.find(function (node) { return node.id === id; }) || null;
}

export { COLORS };
