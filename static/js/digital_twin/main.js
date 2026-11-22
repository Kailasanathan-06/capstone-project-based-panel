import { WorkflowController } from './workflow.js';

function start() {
  var root = document.getElementById('dtw-root');
  if (!root) return;
  var controller = new WorkflowController(root);
  window.secureDtDigitalTwin = controller;
  controller.boot();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
else start();
