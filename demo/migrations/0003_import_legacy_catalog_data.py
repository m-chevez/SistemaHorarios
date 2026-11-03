import json
from pathlib import Path

from django.conf import settings
from django.db import migrations


def import_legacy_catalog_data(apps, schema_editor):
    docente_model = apps.get_model('demo', 'Docente')
    clase_model = apps.get_model('demo', 'Clase')
    data_dir = Path(settings.BASE_DIR) / 'data'

    with (data_dir / 'docentes.json').open(encoding='cp1252') as source:
        docentes = json.load(source)
    with (data_dir / 'clases.json').open(encoding='cp1252') as source:
        clases = json.load(source)

    for docente in docentes:
        docente_model.objects.using(schema_editor.connection.alias).get_or_create(
            id=docente['id'],
            defaults={
                'nombre': docente['nombre'],
                'apellido': docente['apellido'],
            },
        )

    for clase in clases:
        clase_model.objects.using(schema_editor.connection.alias).get_or_create(
            id=clase['id'],
            defaults={
                'clase': clase['clase'],
                'uv': clase['uv'],
                'cantidadEM': clase['cantidadEM'],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0002_alter_aula_capacidad_alter_clase_uv'),
    ]

    operations = [
        migrations.RunPython(import_legacy_catalog_data, migrations.RunPython.noop),
    ]
