"""
Comprehensive Integration Tests for SecureDT UI Redesign and Dataset Storage Analysis Pipeline
"""

import io
import json
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from mec_manager.models import MECAgent
from datasets.models import (
    DatasetStorageReplica,
    DatasetUpload,
    DatasetInventoryItem,
    DatasetAnalysisReport,
    StorageDestination,
)
from engine.storage_manager import ensure_storage_destinations_initialized


class RedesignWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        ensure_storage_destinations_initialized()

    def test_pages_render_status_200(self):
        """Verify that all redesigned core pages render with HTTP 200."""
        routes = [
            ('/', 'Operations Dashboard'),
            ('/upload/', 'Manual ZIP Dataset Ingestion'),
            ('/digital-twin/', 'SecureDT Digital Twin Workspace'),
            ('/storage-allocation/', 'AI-Based Storage Allocation'),
            ('/reports/', 'Persistent Dataset Analysis Reports'),
            ('/tasks/', 'Task Execution &amp; Scheduling History'),
        ]
        for url, expected_text in routes:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Page {url} failed with status {resp.status_code}")
            self.assertContains(resp, expected_text, msg_prefix=f"Missing text in {url}")

    def test_apis_return_valid_json(self):
        """Verify that newly created APIs return successful JSON payloads."""
        api_endpoints = [
            '/api/app/dashboard-stats/',
            '/api/app/digital-twin/',
            '/api/app/storage-allocations/',
            '/api/app/reports/',
            '/api/app/tasks/',
        ]
        for ep in api_endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, 200, f"API {ep} returned status {resp.status_code}")
            data = resp.json()
            self.assertTrue(data.get('success'), f"API {ep} did not return success=True")

    def test_valid_synthetic_zip_upload_and_report_generation(self):
        """Verify full end-to-end workflow: upload ZIP, validate, analyze, and inspect report."""
        # Create a valid synthetic ZIP containing test files for all 3 tiers
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            # 1. Local workload (Patient vitals EHR)
            z.writestr('patient_ehr_vitals.csv', 'patient_id,heart_rate,bp_sys,bp_dia\nP001,72,120,80\nP002,80,130,85\n')
            # 2. MEC workload (Radiological scan)
            z.writestr('chest_xray_scan.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            # 3. Cloud workload (Administrative schedule batch)
            z.writestr('appointment_schedule.json', '{"schedule_id": "BATCH-01", "records": 45}')

        zip_buffer.seek(0)
        uploaded = SimpleUploadedFile('synthetic_hospital_batch.zip', zip_buffer.read(), content_type='application/zip')

        resp = self.client.post('/api/app/upload-zip/', {
            'file': uploaded,
            'execution_mode': 'SIMULATION',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertIsNotNone(data.get('report_id'))
        report_id = data['report_id']

        summary = data.get('summary', {})
        self.assertIn('total_analysis_duration_ms', summary)
        self.assertIn('scheduler_duration_ms', summary)
        self.assertIn('energy_consumption_j', summary)
        self.assertGreaterEqual(summary['energy_consumption_j'], 0)

        # Verify DB records
        upload = DatasetUpload.objects.get(upload_id=data['upload_id'])
        self.assertEqual(upload.status, 'COMPLETED')
        self.assertEqual(upload.total_files_count, 3)

        items = DatasetInventoryItem.objects.filter(upload=upload)
        self.assertEqual(items.count(), 3)

        # Check report detail page
        detail_resp = self.client.get(f'/reports/{report_id}/')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, report_id)
        self.assertContains(detail_resp, 'Section 1')
        self.assertContains(detail_resp, 'Section 2')
        self.assertContains(detail_resp, 'Section 3')
        self.assertContains(detail_resp, 'Section 4')
        self.assertContains(detail_resp, 'Section 5')
        self.assertContains(detail_resp, 'Section 6')

        # Check CSV download
        csv_resp = self.client.get(f'/reports/{report_id}/csv/')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp['Content-Type'], 'text/csv')
        self.assertIn(report_id, csv_resp.content.decode('utf-8'))

    def test_malicious_path_traversal_zip_is_rejected(self):
        """Security check: Archive with path traversal (e.g. ../evil.txt) must be safely rejected."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            z.writestr('../../../etc/evil.txt', 'malicious escape')

        zip_buffer.seek(0)
        uploaded = SimpleUploadedFile('traversal_attack.zip', zip_buffer.read(), content_type='application/zip')

        resp = self.client.post('/api/app/upload-zip/', {
            'file': uploaded,
            'execution_mode': 'SIMULATION',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertIn('traversal', data.get('error', '').lower())
        self.assertIn('analysis_duration_ms', data)
        self.assertEqual(data.get('energy_consumption_j'), 0.0)

    def test_disallowed_executable_extension_is_rejected(self):
        """Security check: Archive containing executable (.exe, .sh) must be blocked."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            z.writestr('payload.exe', b'MZ\x90\x00')

        zip_buffer.seek(0)
        uploaded = SimpleUploadedFile('executable_exploit.zip', zip_buffer.read(), content_type='application/zip')

        resp = self.client.post('/api/app/upload-zip/', {
            'file': uploaded,
            'execution_mode': 'SIMULATION',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertIn('disallowed', data.get('error', '').lower())

    def test_digital_twin_scene_endpoint_schema(self):
        """The 3D scene API exposes backend records without device secrets or file paths."""
        MECAgent.objects.create(
            device_id='MEC-901',
            auth_token='scene-test-token',
            last_heartbeat=timezone.now(),
            last_seen=timezone.now(),
            is_online=True,
            is_approved=True,
        )

        resp = self.client.get(reverse('digital_twin_scene'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data.get('mode'), 'live')
        self.assertIn('generated_at', data)
        self.assertIn('server', data)
        self.assertIn('resources', data)
        self.assertIn('mec_devices', data)
        self.assertIn('tiers', data)
        self.assertIn('transfers', data)
        self.assertIn('tasks', data)
        self.assertIn('scheduling', data)
        self.assertIn('security_events', data)
        self.assertIn('policies', data)
        self.assertIn('device_details', data)

        details = data['device_details']
        for device_id in ['CENTRAL', 'LOCAL', 'CLOUD', 'MEC_STORAGE', 'MEC-901', 'ATTACKER']:
            self.assertIn(device_id, details)
        self.assertEqual(details['LOCAL']['device_type'], 'STORAGE_TIER')
        self.assertIn('utilization_percent', details['LOCAL'])
        self.assertTrue(details['MEC-901']['storage_is_shared'])

        self.assertFalse(data['capabilities']['encryption_confirmed'])
        self.assertTrue(data['capabilities']['policy_enforcement'])
        self.assertFalse(data['capabilities']['transfer_progress_available'])
        self.assertGreaterEqual(data['server']['registered_mecs'], 1)

        mec_ids = [mec['device_id'] for mec in data['mec_devices']]
        self.assertIn('MEC-901', mec_ids)
        for policy in ['LOCAL_ONLY', 'TRUSTED_EDGE', 'CLOUD_ALLOWED']:
            self.assertIn(policy, data['policies'])
            self.assertIn('allowed_tiers', data['policies'][policy])
            self.assertIn('eligible_resources', data['policies'][policy])

        raw = resp.content.decode('utf-8')
        for forbidden in ['auth_token', 'scene-test-token', 'last_known_ip', 'source_ip', 'description']:
            self.assertNotIn(forbidden, raw)

    def test_digital_twin_scene_device_details_are_sanitized(self):
        """Device details expose aggregate storage fields without file paths or checksums."""
        local = StorageDestination.objects.get(destination_id='LOCAL_STORAGE')
        local.capacity_bytes = 0
        local.used_bytes = 5
        local.save(update_fields=['capacity_bytes', 'used_bytes'])
        DatasetStorageReplica.objects.create(
            replica_id='secret-replica-id',
            dataset_id='SECRET-DATASET',
            storage_destination=local,
            relative_key='patient/chest-xray.dcm',
            absolute_path='/srv/medical/patient/chest-xray.dcm',
            file_size_bytes=1024,
            sha256_checksum='secret-checksum-value',
            replication_status='VERIFIED',
        )

        resp = self.client.get(reverse('digital_twin_scene'))
        self.assertEqual(resp.status_code, 200)
        details = resp.json()['device_details']['LOCAL']
        self.assertIsNone(details['utilization_percent'])
        self.assertEqual(details['free_bytes'], 0)
        self.assertEqual(details['replica_count'], 1)

        raw = resp.content.decode('utf-8')
        for forbidden in [
            'secret-replica-id',
            'patient/chest-xray.dcm',
            'secret-checksum-value',
            '/srv/medical',
        ]:
            self.assertNotIn(forbidden, raw)
        self.assertEqual(
            self.client.get('/api/digital-twin/storage/detail/?destination=LOCAL').status_code,
            404,
        )

    def test_digital_twin_scene_has_no_fabricated_mecs(self):
        """With no registered agents, the scene reports an empty MEC list."""
        resp = self.client.get(reverse('digital_twin_scene'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['mec_devices'], [])
        self.assertEqual(data['server']['registered_mecs'], 0)
        self.assertEqual(data['server']['connected_mecs'], 0)

    def test_digital_twin_page_is_rebuilt_as_full_screen_workspace(self):
        """The rebuilt page owns the viewport and loads only the modular frontend assets."""
        resp = self.client.get('/digital-twin/')
        self.assertEqual(resp.status_code, 200)
        for needle in [
            'SecureDT Digital Twin Workspace',
            'id="dtw-root"',
            'id="dtw-viewport"',
            'id="dtw-canvas"',
            'id="dtw-labels"',
            'id="dtw-steps"',
            'id="dtw-context"',
            'id="dtw-details"',
            'id="dtw-toolbar"',
            'data-scene-url="/api/digital-twin/scene/"',
            'PLAY DATASET WORKFLOW',
            'vendor/three.min.js',
            'js/digital_twin/main.js',
            'css/digital_twin_workspace.css',
        ]:
            self.assertContains(resp, needle)
        for stale in [
            'id="dt3d-stage"',
            'id="swf-start-demo"',
            'digital_twin_3d.js',
            'secure_workflow.js',
            'digital_twin_3d.css',
            'secure_workflow.css',
        ]:
            self.assertNotContains(resp, stale)

    def test_digital_twin_scene_exposes_guided_workflow_metadata(self):
        """The scene API supplies labeled workflow, security, and simulation metadata."""
        resp = self.client.get(reverse('digital_twin_scene'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        workflow = data['workflow']
        self.assertIn('stages', workflow)
        self.assertEqual(len(workflow['stages']), 15)
        for stage in workflow['stages']:
            for field in ['step', 'id', 'title', 'status', 'source', 'destination', 'detail', 'data_source']:
                self.assertIn(field, stage)
        self.assertFalse(workflow['live_mode_available'])

        layers = data['security_layers']
        self.assertEqual(len(layers), 6)
        layer_ids = {layer['id'] for layer in layers}
        self.assertEqual(layer_ids, {
            'upload_validation',
            'authentication_authorization',
            'privacy_aware_scheduling',
            'resource_trust_availability',
            'security_audit',
            'data_protection',
        })
        self.assertTrue(all(layer['status'] and layer['evidence'] for layer in layers))

        scenarios = data['simulation_catalog']
        self.assertEqual(len(scenarios), 8)
        self.assertEqual(len({scenario['id'] for scenario in scenarios}), 8)
        self.assertTrue(all(scenario['label'] and scenario['backend_evidence'] for scenario in scenarios))

        self.assertEqual(data['client_devices'][0]['client_id'], 'CLIENT-LOCAL')
        self.assertFalse(data['client_devices'][0]['is_simulated'])
        self.assertFalse(data['capabilities']['encryption_confirmed'])

    def test_digital_twin_page_includes_workflow_controls(self):
        """The page exposes all seven stages plus demo, data, and attack controls."""
        resp = self.client.get('/digital-twin/')
        self.assertEqual(resp.status_code, 200)
        for needle in [
            'data-stage="upload"',
            'data-stage="analyze"',
            'data-stage="allocate"',
            'data-stage="schedule"',
            'data-stage="transfer"',
            'data-stage="security"',
            'data-stage="results"',
            'id="dtw-start-demo"',
            'id="dtw-dataset-select"',
            'id="dtw-dataset-info"',
            'id="dtw-timeline"',
            'id="dtw-stage-label"',
            'id="dtw-elapsed"',
            'id="dtw-event-log"',
            'id="dtw-tree-expand"',
            'id="dtw-tree-collapse"',
            'id="dtw-open-upload"',
            'id="dtw-prev"',
            'id="dtw-next"',
            'id="dtw-jump"',
            'id="dtw-speed"',
            'id="dtw-pause"',
            'id="dtw-restart"',
            'id="dtw-exit"',
            'id="dtw-dropzone"',
            'id="dtw-file"',
            'id="dtw-search"',
            'id="dtw-tree"',
            'id="dtw-confirm-allocation"',
            'id="dtw-run-schedule"',
            'id="dtw-run-transfer"',
            'id="dtw-attack-scenario"',
            'id="dtw-attack-target"',
            'id="dtw-run-attack"',
            'id="dtw-final-report"',
            'DEMONSTRATION MODE — SIMULATED DATA',
            'ENCRYPTION NOT VERIFIED',
        ]:
            self.assertContains(resp, needle)

    def test_digital_twin_page_loads_workflow_api_urls(self):
        resp = self.client.get('/digital-twin/')
        self.assertEqual(resp.status_code, 200)
        for needle in [
            'data-upload-url="/api/app/upload-zip/"',
            'data-demo-url="/api/app/upload-demo-zip/"',
            'data-datasets-url="/api/app/dataset-workflow-datasets/"',
            'data-inspect-url="/api/app/dataset-inspect/"',
            'data-confirm-url="/api/app/dataset-allocation-confirm/"',
            'data-compare-url="/api/digital-twin/compare/"',
        ]:
            self.assertContains(resp, needle)

    def test_required_simulation_labels_are_present_in_workspace_modules(self):
        module_dir = Path(settings.BASE_DIR) / 'static' / 'js' / 'digital_twin'
        template_path = Path(settings.BASE_DIR) / 'templates' / 'digital_twin.html'
        source = '\n'.join(
            path.read_text(encoding='utf-8') for path in sorted(module_dir.glob('*.js'))
        ) + '\n' + template_path.read_text(encoding='utf-8')
        for label in [
            'SIMULATION MODE',
            'DEMONSTRATION MODE — SIMULATED DATA',
            'SIMULATED ATTACKER',
            'EXTERNAL THREAT SIMULATOR',
            'CLOUD EMULATOR',
            'PROTECTION POLICY VISUALIZATION',
            'ENCRYPTION NOT VERIFIED',
            'TASK BLOCKED — NO ELIGIBLE RESOURCE',
        ]:
            self.assertIn(label, source)

    def test_workspace_modules_bind_the_selected_dataset_to_every_view(self):
        module_dir = Path(settings.BASE_DIR) / 'static' / 'js' / 'digital_twin'
        source = '\n'.join(
            path.read_text(encoding='utf-8') for path in sorted(module_dir.glob('*.js'))
        )
        for marker in [
            'datasetsUrl',
            'dataset_transfers',
            'dataset_scheduling',
            'dataset_security_events',
            'buildDatasetSchedulingGraph',
            'renderDatasetSelector',
            'renderDatasetInfo',
            'renderEventLog',
            'updatePlayback',
            "focusFirst('DATASET_EVENT:')",
            'collapsed',
        ]:
            self.assertIn(marker, source)

    def test_legacy_digital_twin_assets_are_removed(self):
        static_dir = Path(settings.BASE_DIR) / 'static'
        for relative_path in [
            'js/digital_twin_3d.js',
            'css/digital_twin_3d.css',
            'js/secure_workflow.js',
            'css/secure_workflow.css',
        ]:
            self.assertFalse((static_dir / relative_path).exists(), relative_path)

    def _upload_workflow_zip(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as archive:
            archive.writestr('clinical/patient_vitals.csv', 'patient_id,heart_rate\nP001,72\n')
            archive.writestr('imaging/chest_xray.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            archive.writestr('admin/appointment_schedule.json', '{"records": 45}')
        zip_buffer.seek(0)
        uploaded = SimpleUploadedFile('workflow_batch.zip', zip_buffer.read(), content_type='application/zip')
        resp = self.client.post('/api/app/upload-zip/', {
            'file': uploaded,
            'execution_mode': 'SIMULATION',
        })
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def _create_manual_report(self, report_id, item_status, execution_mode='EXECUTION'):
        upload = DatasetUpload.objects.create(
            upload_id='UP-' + report_id,
            file_name='manual.zip',
            status='COMPLETED',
            execution_mode=execution_mode,
            total_files_count=1,
            total_uncompressed_bytes=10,
        )
        inventory = [{
            'file_name': 'manual.csv',
            'relative_path': 'clinical/manual.csv',
            'size': 10,
            'size_formatted': '10 B',
            'format': 'CSV',
            'category': 'CLINICAL',
            'declared_source': 'MANUAL',
            'privacy_policy': 'LOCAL_ONLY',
            'local_eligible': True,
            'mec_eligible': False,
            'cloud_eligible': False,
            'selected_destination': 'LOCAL_STORAGE',
            'decision_rationale': 'Recorded policy decision',
            'status': item_status,
            'sha256': 'secret-checksum-value',
        }]
        DatasetInventoryItem.objects.create(
            upload=upload,
            file_name='manual.csv',
            relative_path='clinical/manual.csv',
            file_size=10,
            format='CSV',
            detected_category='CLINICAL',
            privacy_policy='LOCAL_ONLY',
            local_eligible=True,
            mec_eligible=False,
            cloud_eligible=False,
            selected_destination='LOCAL_STORAGE',
            decision_rationale='Recorded policy decision',
            status=item_status,
            sha256_checksum='secret-checksum-value',
        )
        return DatasetAnalysisReport.objects.create(
            report_id=report_id,
            upload=upload,
            title='Manual workflow report',
            summary_json=json.dumps({'file_name': 'manual.zip', 'total_files': 1}),
            inventory_json=json.dumps(inventory),
            ai_analysis_json=json.dumps({'method': 'recorded', 'runtime_ms': 1}),
            allocation_json=json.dumps({'capacity_snapshot': {'recorded': True}}),
            security_audit_json=json.dumps({'integrity_verified': True, 'blocked_policy_violations': 0}),
            final_result_json=json.dumps({'status': 'COMPLETED'}),
        )

    def test_dataset_workflow_apis_validate_report_id(self):
        inspect = self.client.get(reverse('api_dataset_workflow_inspect'))
        self.assertEqual(inspect.status_code, 400)
        self.assertFalse(inspect.json()['success'])

        missing_inspect = self.client.get(reverse('api_dataset_workflow_inspect'), {'report_id': 'MISSING'})
        self.assertEqual(missing_inspect.status_code, 404)

        confirm = self.client.post(reverse('api_dataset_allocation_confirm'), {})
        self.assertEqual(confirm.status_code, 400)

        missing_confirm = self.client.post(reverse('api_dataset_allocation_confirm'), {'report_id': 'MISSING'})
        self.assertEqual(missing_confirm.status_code, 404)

    def test_dataset_workflow_datasets_api_requires_auth_and_lists_real_uploads(self):
        url = reverse('api_dataset_workflow_datasets')
        anonymous = self.client.get(url)
        self.assertEqual(anonymous.status_code, 403)

        user = get_user_model().objects.create_user(username='digital-twin-user', password='test-pass-123')
        self.client.force_login(user)
        upload = self._upload_workflow_zip()

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        record = next(
            item for item in data['datasets'] if item['upload_id'] == upload['upload_id']
        )
        self.assertEqual(record['report_id'], upload['report_id'])
        self.assertEqual(record['dataset_name'], 'workflow_batch')
        self.assertEqual(record['file_count'], 3)
        self.assertEqual(record['analysis_status'], 'COMPLETED')
        self.assertTrue(record['report_available'])

        raw = resp.content.decode('utf-8')
        for forbidden in ['absolute_path', 'sha256_checksum', 'auth_token', 'source_ip', 'C:\\']:
            self.assertNotIn(forbidden, raw)

    def test_dataset_workflow_inspect_returns_sanitized_simulation_payload(self):
        upload = self._upload_workflow_zip()
        report_id = upload['report_id']

        resp = self.client.get(reverse('api_dataset_workflow_inspect'), {'report_id': report_id})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['report_id'], report_id)
        self.assertEqual(data['execution_mode'], 'SIMULATION')
        self.assertEqual(data['dataset']['upload_id'], upload['upload_id'])
        self.assertEqual(data['dataset']['report_id'], report_id)
        self.assertEqual(len(data['dataset_scheduling']), 3)
        self.assertEqual(len(data['dataset_transfers']), 3)
        self.assertTrue(data['dataset_security_events'])
        for decision in data['dataset_scheduling']:
            self.assertIn(decision['selected_destination'], ['LOCAL_STORAGE', 'MEC_STORAGE', 'CLOUD_STORAGE', 'UNASSIGNED'])
            self.assertIn(decision['result'], ['PROPOSED', 'COMPLETED', 'BLOCKED', 'FAILED'])
        for transfer in data['dataset_transfers']:
            self.assertEqual(transfer['source'], 'CENTRAL')
        self.assertEqual(data['tree']['id'], 'root')
        self.assertGreaterEqual(len(data['graph_nodes']), 4)
        self.assertGreaterEqual(len(data['graph_edges']), 3)
        self.assertEqual(data['stats']['total_files'], 3)
        self.assertEqual(data['stats']['total_size_bytes'], sum(
            int(item['size']) for item in json.loads(
                DatasetAnalysisReport.objects.get(report_id=report_id).inventory_json
            )
        ))
        self.assertEqual(len(data['partitions']), 3)
        self.assertEqual(data['allocation']['label'], 'PROPOSED ALLOCATION — SIMULATION MODE')
        self.assertTrue(data['allocation']['simulated'])
        for tier_id in ['LOCAL_STORAGE', 'MEC_STORAGE', 'CLOUD_STORAGE']:
            self.assertIn(tier_id, data['allocation']['tiers'])
            self.assertIn(tier_id, data['allocation']['proposed'])

        replicas_before = DatasetStorageReplica.objects.count()
        confirm = self.client.post(reverse('api_dataset_allocation_confirm'), {'report_id': report_id})
        self.assertEqual(confirm.status_code, 200)
        confirm_data = confirm.json()
        self.assertTrue(confirm_data['simulated'])
        self.assertEqual(confirm_data['label'], 'SIMULATED ALLOCATION CONFIRMATION — NO FILES WRITTEN')
        self.assertEqual(DatasetStorageReplica.objects.count(), replicas_before)

        raw = resp.content.decode('utf-8')
        for forbidden in [
            'absolute_path',
            'base_path',
            'sha256_checksum',
            'secret-checksum-value',
            'auth_token',
            'source_ip',
            '/srv/',
            'C:\\',
        ]:
            self.assertNotIn(forbidden, raw)

    def test_dataset_workflow_labels_recorded_execution_states(self):
        verified = self._create_manual_report('R-EXEC-VERIFIED', 'STORED_AND_VERIFIED')
        pending = self._create_manual_report('R-EXEC-PENDING', 'RECOMMENDED')

        verified_inspect = self.client.get(
            reverse('api_dataset_workflow_inspect'), {'report_id': verified.report_id}
        ).json()
        self.assertEqual(verified_inspect['allocation']['label'], 'ACTUAL STORAGE DISTRIBUTION')
        self.assertFalse(verified_inspect['allocation']['simulated'])
        self.assertEqual(verified_inspect['allocation']['verified_count'], 1)

        verified_confirm = self.client.post(
            reverse('api_dataset_allocation_confirm'), {'report_id': verified.report_id}
        ).json()
        self.assertEqual(verified_confirm['label'], 'ACTUAL STORAGE DISTRIBUTION')
        self.assertFalse(verified_confirm['simulated'])

        pending_inspect = self.client.get(
            reverse('api_dataset_workflow_inspect'), {'report_id': pending.report_id}
        ).json()
        self.assertEqual(pending_inspect['allocation']['label'], 'EXECUTION RECORDED — VERIFICATION PENDING')
        self.assertTrue(pending_inspect['allocation']['simulated'])

        raw = self.client.get(
            reverse('api_dataset_workflow_inspect'), {'report_id': verified.report_id}
        ).content.decode('utf-8')
        self.assertNotIn('secret-checksum-value', raw)
