"""SecureDT API smoke tests against the real consolidated stack.

Run with:
    python manage.py test tests -v 2
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "securedt.settings")

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client, TestCase, override_settings  # noqa: E402
from rest_framework.authtoken.models import Token  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from mec_manager.models import PairingCode, MECAgent  # noqa: E402
from mec_manager.services import process_heartbeat  # noqa: E402
from tasks.models import Task  # noqa: E402


def register_and_heartbeat(client, system_name="Test Edge PC"):
    code = PairingCode.generate_new()
    res = client.post(
        "/api/mec/register/",
        {
            "pairing_code": code.code,
            "system_name": system_name,
            "server_url": "http://127.0.0.1:8000",
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    device_id = res.data["device_id"]
    agent = MECAgent.objects.get(device_id=device_id)
    process_heartbeat(
        device_id=device_id,
        auth_token=res.data["auth_token"],
        payload={
            "mec_id": device_id,
            "cpu_usage": 40.0,
            "ram_usage": 50.0,
            "disk_usage": 20.0,
            "network_latency": 14.0,
            "energy_estimate": 1.2,
            "current_task": "",
            "task_count": 0,
        },
    )
    agent.refresh_from_db()
    assert agent.is_online
    return agent, res.data


def create_basic_task(client, name="Lifecycle"):
    res = client.post(
        "/api/tasks/",
        {
            "name": name,
            "priority": 2,
            "data_size_mb": 50,
            "cpu_cycles_giga": 2.5,
            "memory_mb": 512,
            "deadline_ms": 5000,
            "privacy_sensitivity": 0.3,
            "security_sensitivity": 0.2,
        },
        format="json",
    )
    assert res.status_code == 201, res.data
    return res


class SecureDTAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="op", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_api_state_and_auth_enforcement(self):
        anon = APIClient()
        self.assertEqual(anon.get("/api/state/").status_code, 200)
        self.assertIn(anon.get("/api/tasks/").status_code, (401, 403))
        self.assertEqual(self.client.get("/api/tasks/").status_code, 200)

    def test_pages_render(self):
        urls = [
            "", "task-routing/", "mec-infrastructure/", "digital-twin/",
            "genetic-algorithm/", "ai-intelligence/", "security-monitor/",
            "attack-simulation/", "storage-attack/", "datasets/",
            "cloud-storage/", "data-flow/", "analytics/", "performance/",
            "energy-monitor/",
        ]
        for u in urls:
            r = self.client.get("/" + u)
            self.assertEqual(r.status_code, 200, u)
            self.assertIn(b"SecureDT", r.content)

    def test_register_heartbeat_and_mec_list(self):
        register_and_heartbeat(self.client)
        mecs = self.client.get("/api/mec/").data
        found = mecs[0]
        self.assertTrue(found["is_online"])
        self.assertGreater(found["cpu"], 0)
        self.assertGreater(found["task_count"], -1)

    def test_full_task_lifecycle(self):
        agent, reg = register_and_heartbeat(self.client)
        create = create_basic_task(self.client)
        task_id = create.data["task_id"]

        dispatch = self.client.post("/api/tasks/dispatch/", {"population": 40, "generations": 25}, format="json")
        self.assertEqual(dispatch.status_code, 200, dispatch.data)

        task = Task.objects.get(task_id=task_id)
        self.assertEqual(task.status, "ASSIGNED", task.status)
        self.assertEqual(task.assigned_mec.device_id, agent.device_id)

        token = Token.objects.get(user=agent.user).key
        mec_client = APIClient()
        report = mec_client.post(
            f"/api/mec/{agent.device_id}/report-result/",
            {
                "task_id": task_id,
                "execution_time": 3.2,
                "cpu_usage": 35.0,
                "ram_usage": 45.0,
                "network_latency": 12.0,
                "estimated_energy": 0.8,
                "success": True,
            },
            format="json",
            HTTP_AUTHORIZATION=f"Token {token}",
            HTTP_X_MEC_ID=agent.device_id,
        )
        self.assertEqual(report.status_code, 200, report.data)
        self.assertEqual(Task.objects.get(task_id=task_id).status, "COMPLETED")

    def test_revoked_mec_never_receives_tasks(self):
        agent, reg = register_and_heartbeat(self.client)
        r = self.client.post(f"/api/mec/{agent.device_id}/revoke/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        create = create_basic_task(self.client, name="RevokedTask")
        task_id = create.data["task_id"]
        self.client.post("/api/tasks/dispatch/", {"population": 20, "generations": 10}, format="json")
        task = Task.objects.get(task_id=task_id)
        self.assertNotEqual(task.status, "ASSIGNED")

    def test_twin_storage_analytics_endpoints(self):
        for path in [
            "/api/digital-twin/",
            "/api/digital-twin/resources/",
            "/api/digital-twin/security/",
            "/api/digital-twin/storage/status/",
            "/api/analytics/overview/",
            "/api/analytics/mec-metrics/",
            "/api/analytics/task-metrics/",
            "/api/analytics/energy-metrics/",
            "/api/analytics/security-metrics/",
            "/api/analytics/cloud-metrics/",
            "/api/analytics/history/",
            "/api/analytics/ai-status/",
            "/api/analytics/benchmark/",
            "/api/analytics/data-flow/",
            "/api/cloud/files/",
            "/api/cloud/folders/",
        ]:
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, (path, getattr(r, "data", None)))

        r = self.client.get("/api/digital-twin/security/")
        self.assertIn("threat_level", r.data)

        attack = self.client.post(
            "/api/digital-twin/storage/attack/",
            {"storage_id": "STORAGE-A", "severity": 0.9},
            format="json",
        )
        self.assertEqual(attack.status_code, 200)
        self.assertTrue(attack.data["ok"])

        recover = self.client.post(
            "/api/digital-twin/storage/recover/",
            {"storage_id": "STORAGE-A"},
            format="json",
        )
        self.assertEqual(recover.status_code, 200)
        self.assertTrue(recover.data["ok"])

    def test_analytics_ai_status_post_train_roundtrip(self):
        get = self.client.get("/api/analytics/ai-status/")
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.data["status"], "READY")
        self.assertIn("samples", get.data)
        self.assertIn("metrics", get.data)
        post = self.client.post("/api/analytics/ai-status/", {"train": True}, format="json")
        self.assertEqual(post.status_code, 200, getattr(post, "data", None))


class SecureDTExtendedTests(TestCase):
    """Offline detection, task reassignment, multi-MEC scaling and cloud I/O."""

    def setUp(self):
        self.user = User.objects.create_user(username="op2", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_heartbeat_requires_valid_credentials(self):
        res = self.client.post(
            "/api/mec/heartbeat/",
            {"mec_id": "MEC-999", "auth_token": "wrong-token", "cpu_usage": 10},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_offline_mec_never_receives_tasks_and_requeues(self):
        # MEC-002 (online) stays eligible; MEC-003 goes offline mid-flight.
        m2 = register_and_heartbeat(self.client, "Edge Node A")
        m3 = register_and_heartbeat(self.client, "Edge Node B")
        create = create_basic_task(self.client, name="RequeueTask")
        task_id = create.data["task_id"]

        self.client.post("/api/tasks/dispatch/", {"population": 40, "generations": 25}, format="json")
        task = Task.objects.get(task_id=task_id)
        first = task.assigned_mec.device_id
        self.assertIn(first, {m2[0].device_id, m3[0].device_id})

        # Simulate that MEC going offline: stale last_seen, force requeue.
        agent = MECAgent.objects.get(device_id=first)
        agent.is_online = False
        agent.last_seen = None
        agent.save(update_fields=["is_online", "last_seen"])
        from mec_manager.services import requeue_orphaned_tasks, refresh_mec_status

        refresh_mec_status()
        requeue_orphaned_tasks()
        task.refresh_from_db()
        self.assertEqual(task.status, "QUEUED")

        self.client.post("/api/tasks/dispatch/", {"population": 40, "generations": 25}, format="json")
        task.refresh_from_db()
        self.assertEqual(task.status, "ASSIGNED")
        self.assertNotEqual(task.assigned_mec.device_id, first)

    def test_multi_mec_dashboard_scales_dynamically(self):
        ids = set()
        for n in range(3):
            agent, _ = register_and_heartbeat(self.client, f"Scale Node {n}")
            ids.add(agent.device_id)
        self.assertEqual(len(ids), 3)

        mecs = self.client.get("/api/mec/").data
        self.assertEqual(len(mecs), 3)
        overview = self.client.get("/api/analytics/overview/").data
        self.assertEqual(overview["total_mecs"], 3)
        self.assertEqual(overview["online_mecs"], 3)

    @override_settings(GOOGLE_SERVICE_ACCOUNT_FILE="")
    def test_cloud_upload_list_and_download_failure(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        payload = SimpleUploadedFile("result_1.json", b'{"status": "done"}', content_type="application/json")
        up = self.client.post("/api/cloud/upload/", {"file": payload, "result_type": "result"}, format="multipart")
        self.assertEqual(up.status_code, 201, getattr(up, "data", None))

        listing = self.client.get("/api/cloud/files/").data
        self.assertEqual(listing["mode"].lower(), "simulation")
        self.assertTrue(any(f["file_name"] == "result_1.json" for f in listing["files"]))

        missing = self.client.get("/api/cloud/download/does-not-exist/")
        self.assertEqual(missing.status_code, 404)

    def test_web_auth_login_register_flow(self):
        web = Client()
        reg = web.post(
            "/register/",
            {"username": "webbie", "password": "very-secret-pass", "confirm": "very-secret-pass"},
        )
        self.assertEqual(reg.status_code, 302)
        reg2 = web.get("/")
        self.assertEqual(reg2.status_code, 200)

        web2 = Client()
        bad = web2.post("/login/", {"username": "webbie", "password": "wrong-pass"})
        self.assertEqual(bad.status_code, 200)
        self.assertContains(bad, "correct username and password", status_code=200)
        ok = web2.post("/login/", {"username": "webbie", "password": "very-secret-pass"})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(web2.get("/analytics/").status_code, 200)