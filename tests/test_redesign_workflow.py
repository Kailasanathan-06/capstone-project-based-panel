"""
Comprehensive Integration Tests for SecureDT UI Redesign and Dataset Storage Analysis Pipeline
"""

import io
import zipfile
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from datasets.models import (
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
