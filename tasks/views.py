"""
Tasks - REST API Views.

Implements:
- GET    /api/tasks/                       list (filter by status)
- POST   /api/tasks/                       create a task
- GET    /api/tasks/<id>/                  detail
- POST   /api/tasks/<id>/dispatch/         run GA and dispatch to online MECs
- POST   /api/tasks/<id>/cancel/           cancel a task
- POST   /api/tasks/<id>/complete/
- POST   /api/tasks/<id>/fail/
- POST   /api/tasks/dispatch/              run GA over the whole queue
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .models import Task
from .serializers import TaskSerializer
from .services import run_ga_dispatch, requeue_tasks_with_offline_agents
from mec_manager.services import refresh_mec_status


class TaskViewSet(viewsets.ViewSet):
    """Task queue management."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request, message=None, code=None):
        from engine.hospital_workloads import record_security_event

        ip = request.META.get("REMOTE_ADDR", "")
        details = {}
        if hasattr(request, "data") and isinstance(request.data, dict):
            details = dict(request.data)
        record_security_event(
            event_type="UNAUTHORIZED_TASK_SUBMISSION",
            severity="HIGH",
            description=f"Unauthorized client attempted task queue access from {ip}",
            source_ip=ip,
            details=details,
            blocked=True,
        )
        super().permission_denied(request, message=message, code=code)

    def list(self, request):
        refresh_mec_status()
        requeue_tasks_with_offline_agents()
        q = Task.objects.select_related("assigned_mec").all()
        status_filter = request.query_params.get("status")
        if status_filter:
            q = q.filter(status=status_filter.upper())
        limit = request.query_params.get("limit")
        if limit:
            q = q[: int(limit)]
        return Response(TaskSerializer(q, many=True).data)

    def retrieve(self, request, pk=None):
        refresh_mec_status()
        try:
            task = Task.objects.get(task_id=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)
        return Response(TaskSerializer(task).data)

    def create(self, request):
        serializer = TaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        task = serializer.save(status="QUEUED")
        task.record_history("PENDING", "QUEUED", changed_by=request.user.username)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def dispatch_tasks(self, request):
        """Run the GA over every queued task and assign to online MECs."""
        refresh_mec_status()
        population = int(request.data.get("population", 40))
        generations = int(request.data.get("generations", 30))
        result = run_ga_dispatch(population=population, generations=generations)
        return Response(result)

    def cancel(self, request, pk=None):
        try:
            task = Task.objects.get(task_id=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)
        if task.status in ("COMPLETED", "CANCELLED"):
            return Response(TaskSerializer(task).data)
        previous = task.status
        task.status = "CANCELLED"
        task.save(update_fields=["status", "updated_at"])
        task.record_history(previous, "CANCELLED", changed_by=request.user.username)
        return Response(TaskSerializer(task).data)

    def complete(self, request, pk=None):
        try:
            task = Task.objects.get(task_id=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)
        previous = task.status
        task.status = "COMPLETED"
        task.execution_time = request.data.get("execution_time", task.execution_time)
        task.estimated_energy = request.data.get("estimated_energy", task.estimated_energy)
        task.result_location = request.data.get("result_location", task.result_location)
        task.save()
        task.record_history(previous, "COMPLETED", changed_by=request.user.username)
        return Response(TaskSerializer(task).data)

    def fail(self, request, pk=None):
        try:
            task = Task.objects.get(task_id=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)
        previous = task.status
        task.error_message = request.data.get("error_message", "")
        task.status = "QUEUED"
        task.assigned_mec = None
        task.save(update_fields=["status", "assigned_mec", "error_message", "updated_at"])
        task.record_history(previous, "QUEUED", changed_by=request.user.username)
        return Response(TaskSerializer(task).data)


# ---------------------------------------------------------------------------
# Phase 7 & 8 Hospital Schedulers Benchmark API Views
# ---------------------------------------------------------------------------
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, HttpResponse


@api_view(["GET"])
@permission_classes([AllowAny])
def hospital_benchmark_summary_api(request):
    """Retrieve latest hospital benchmark experiment summary and metrics."""
    from tasks.models import ExperimentRun
    from engine.benchmark_runner import run_hospital_benchmark

    latest = ExperimentRun.objects.order_by("-created_at").first()
    if not latest:
        result = run_hospital_benchmark(tasks_count=5, population=15, generations=10)
        return JsonResponse(result)

    return JsonResponse({
        "experiment_id": latest.experiment_id,
        "name": latest.name,
        "seed": latest.seed,
        "tasks_count": latest.tasks_count,
        "configuration": json.loads(latest.configuration_json) if latest.configuration_json else {},
        "summary": json.loads(latest.results_json) if latest.results_json else {},
        "created_at": latest.created_at.isoformat(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def hospital_benchmark_run_api(request):
    """Trigger a new comparative benchmark run across hospital workloads."""
    from engine.benchmark_runner import run_hospital_benchmark

    data = request.data if hasattr(request, "data") else {}
    tasks_count = int(data.get("tasks_count", 14))
    population = int(data.get("population", 30))
    generations = int(data.get("generations", 20))
    seed = int(data.get("seed", 42))

    result = run_hospital_benchmark(
        tasks_count=tasks_count,
        population=population,
        generations=generations,
        seed=seed,
    )
    return JsonResponse(result, status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def hospital_benchmark_export_csv_api(request):
    """Download comparative benchmark results CSV."""
    from tasks.models import ExperimentRun
    from engine.benchmark_runner import export_benchmark_csv, run_hospital_benchmark

    latest = ExperimentRun.objects.order_by("-created_at").first()
    if not latest or not latest.results_json:
        res = run_hospital_benchmark(tasks_count=14, population=20, generations=15)
        csv_path = export_benchmark_csv(res)
        filename = f"benchmark_results_{res['experiment_id']}.csv"
    else:
        res = {
            "experiment_id": latest.experiment_id,
            "tasks_count": latest.tasks_count,
            "summary": json.loads(latest.results_json),
        }
        csv_path = export_benchmark_csv(res)
        filename = f"benchmark_results_{latest.experiment_id}.csv"

    with open(csv_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response