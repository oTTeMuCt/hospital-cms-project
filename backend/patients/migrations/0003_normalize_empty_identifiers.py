from django.db import migrations


def normalize_empty_identifiers(apps, schema_editor):
    patients = apps.get_model("patients", "Patient").objects.using(schema_editor.connection.alias)
    patients.filter(pinfl="").update(pinfl=None)
    patients.filter(passport="").update(passport=None)


class Migration(migrations.Migration):
    dependencies = [("patients", "0002_add_passport_unique_constraint")]
    operations = [migrations.RunPython(normalize_empty_identifiers, migrations.RunPython.noop)]
