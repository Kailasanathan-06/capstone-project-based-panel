"""
Comprehensive Integration Tests for SecureDT UI Redesign and Dataset Storage Analysis Pipeline
"""

import io
import zipfile
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
            ('/digital-twin/', 'Digital Twin Resource State Monitor'),
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

    def test_digital_twin_page_includes_3d_panel_and_assets(self):
        """The existing page keeps its heading and embeds the scoped 3D visualization."""
        resp = self.client.get('/digital-twin/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Digital Twin Resource State Monitor')
        self.assertContains(resp, 'Interactive 3D Digital Twin Operations Map')
        self.assertContains(resp, 'Protection Policy Visualization')
        self.assertContains(resp, 'id="dt3d-stage"')
        self.assertContains(resp, 'id="dt3d-details"')
        self.assertContains(resp, 'Close Details')
        self.assertContains(resp, 'id="dt3d-details-body"')
        self.assertContains(resp, 'data-scene-url="/api/digital-twin/scene/"')
        self.assertContains(resp, 'Run Transfer Simulation')
        self.assertContains(resp, 'Run Attack Simulation')
        self.assertContains(resp, 'vendor/three.min.js')
        self.assertContains(resp, 'js/digital_twin_3d.js')

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

    def test_digital_twin_page_includes_guided_workflow_controls(self):
        """The page includes every guided workflow, status, and security panel hook."""
        resp = self.client.get('/digital-twin/')
        self.assertEqual(resp.status_code, 200)
        for needle in [
            'id="dt3d-run-mode"',
            'DEMONSTRATION MODE — SIMULATED DATA',
            'id="dt3d-workflow-status"',
            'id="dt3d-workflow-progress"',
            'data-dt3d-action="workflow-play"',
            'data-dt3d-action="workflow-prev"',
            'data-dt3d-action="workflow-next"',
            'data-dt3d-action="workflow-restart"',
            'id="dt3d-workflow-speed"',
            'id="dt3d-workflow-steps"',
            'id="dt3d-current-source"',
            'id="dt3d-current-destination"',
            'id="dt3d-current-task"',
            'id="dt3d-current-artifact"',
            'id="dt3d-security-layers"',
            'id="dt3d-attack-scenario"',
            'data-dt3d-action="show-details"',
            'data-dt3d-action="show-security"',
        ]:
            self.assertContains(resp, needle)
