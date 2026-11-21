from django.db import migrations, models
from django.utils import timezone


def approve_existing_agents(apps, schema_editor):
    MECAgent = apps.get_model("mec_manager", "MECAgent")
    MECAgent.objects.all().update(is_approved=True, approved_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ("mec_manager", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mecagent",
            name="is_approved",
            field=models.BooleanField(default=False, verbose_name="Approved by Server"),
        ),
        migrations.AddField(
            model_name="mecagent",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Approved At"),
        ),
        migrations.RunPython(approve_existing_agents, migrations.RunPython.noop),
    ]
