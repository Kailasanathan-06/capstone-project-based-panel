"""
Main views for SecureDT project.
"""

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def csrf_token(request):
    """Return CSRF token for API clients."""
    return JsonResponse({'csrf_token': get_token(request)})


def api_state(request):
    """Return API state for frontend initialization."""
    from mec_manager.models import MECAgent
    from tasks.models import Task
    from engine.risk_engine import RiskEngine
    from engine.digital_twin import DigitalTwin
    
    # Get basic stats
    total_mecs = MECAgent.objects.count()
    online_mecs = MECAgent.objects.filter(is_online=True).count()
    
    # Threat level from digital twin
    dt = DigitalTwin()
    risk_engine = RiskEngine()
    max_risk = 0
    for resource in dt.states():
        max_risk = max(max_risk, resource.get('security_risk', 0))
    
    threat_level = 'LOW'
    if max_risk >= 0.8:
        threat_level = 'CRITICAL'
    elif max_risk >= 0.6:
        threat_level = 'HIGH'
    elif max_risk >= 0.3:
        threat_level = 'MEDIUM'
    
    return JsonResponse({
        'csrf_token': get_token(request),
        'total_mecs': total_mecs,
        'online_mecs': online_mecs,
        'offline_mecs': total_mecs - online_mecs,
        'current_risk': max_risk,
        'risk_label': threat_level,
        'threat_level': threat_level,
        'data_source_label': 'LIVE API',
        'ga_generation': 0,
        'best_fitness': 0,
        'attack_count': 0,
        'detected_count': 0,
        'mitigations': 0,
    })


def register(request):
    """User registration - renders the form and creates authenticated users."""
    from django.contrib.auth.models import User
    from django.contrib.auth import login
    from django.shortcuts import render, redirect
    from django.contrib import messages

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        confirm = request.POST.get("confirm") or ""

        errors = []
        if not username or not (3 <= len(username) <= 32):
            errors.append("Username must be 3-32 characters.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password and password != confirm:
            errors.append("Passwords do not match.")
        if username and User.objects.filter(username=username).exists():
            errors.append("That username is already registered.")
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(
                request,
                "registration/register.html",
                {"username": username},
            )

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        messages.success(request, f"Welcome, {username}. Your SecureDT workspace is ready.")
        return redirect("/")

    return render(request, "registration/register.html")