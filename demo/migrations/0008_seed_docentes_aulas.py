from django.db import migrations


DOCENTES = (
    ('SEED-IBIS-ZAVALA', 'Ibis', 'Zavala', 14, 18, 15),
    ('SEED-OSCAR-PINEDA', 'Oscar', 'Pineda', 8, 13, 15),
    ('SEED-WILSON-VILLANUEVA', 'Wilson', 'Villanueva', 8, 13, 15),
    ('SEED-JESSICA-MENDOZA', 'Jessica', 'Mendoza', 7, 13, 5),
    ('SEED-VICTOR-REYES', 'Victor', 'Reyes', 7, 14, 5),
    ('SEED-DORIAN-OSORTO', 'Dorian', 'Osorto', 7, 13, 5),
)

AULAS = (
    ('SEED-LABMACS', 'LabMacs', 'laboratorio', 20),
    ('SEED-LAB1', 'Lab1', 'laboratorio', 20),
    ('SEED-LAB-INFORMATICA', 'Lab Informática', 'laboratorio', 20),
)


def cargar_docentes_y_aulas(apps, schema_editor):
    alias = schema_editor.connection.alias
    docente_model = apps.get_model('demo', 'Docente')
    aula_model = apps.get_model('demo', 'Aula')

    for codigo, nombre, apellido, hora_inicio, hora_fin, carga_maxima_uv in DOCENTES:
        docentes = docente_model.objects.using(alias)
        if docentes.filter(nombre__iexact=nombre, apellido__iexact=apellido).exists():
            continue
        if docentes.filter(pk=codigo).exists():
            raise RuntimeError(f'No se puede cargar al docente {nombre} {apellido}: el código {codigo} ya está ocupado.')
        docentes.create(
            id=codigo,
            nombre=nombre,
            apellido=apellido,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            carga_maxima_uv=carga_maxima_uv,
        )

    for codigo, nombre, tipo, capacidad in AULAS:
        aulas = aula_model.objects.using(alias)
        if aulas.filter(nombreAula__iexact=nombre).exists():
            continue
        if aulas.filter(pk=codigo).exists():
            raise RuntimeError(f'No se puede cargar el aula {nombre}: el código {codigo} ya está ocupado.')
        aulas.create(
            idAula=codigo,
            nombreAula=nombre,
            tipo=tipo,
            capacidad=capacidad,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0007_catalogo_clases_censadas'),
    ]

    operations = [
        migrations.RunPython(cargar_docentes_y_aulas, migrations.RunPython.noop),
    ]
