from django.db import migrations


CLASES_CATALOGO = (
    ('ISC-101', 'Introducción a la Ingeniería en Sistemas Computacionales', 4),
    ('ISC-102', 'Programación Estructurada', 4),
    ('ISC-103', 'Programación Orientada a Objetos', 5),
    ('ISC-204', 'Paradigmas de Programación', 4),
    ('ISC-211', 'Estructuras de Datos', 4),
    ('ISC-321', 'Fundamentos de Base de Datos', 5),
    ('ISC-351', 'Contabilidad Financiera', 4),
    ('ISC-331', 'Redes de Datos I', 4),
    ('ISC-333', 'Sistemas Operativos I', 4),
    ('ISC-312', 'Teoría de la Computación', 4),
    ('ISC-341', 'Sistemas de Información', 4),
    ('ISC-332', 'Redes de Datos II', 4),
    ('ISC-334', 'Sistemas Operativos II', 4),
    ('ISC-305', 'Programación Web', 4),
    ('ISC-313', 'Compiladores', 4),
    ('ISC-306', 'Análisis de Requerimientos', 4),
    ('ISC-336', 'Diseño Digital', 4),
    ('ISC-407', 'Programación Móvil', 5),
    ('ISC-414', 'Inteligencia Artificial', 4),
    ('ISC-435', 'Administración de Servidores', 4),
    ('ISC-437', 'Arquitectura de Computadoras', 4),
    ('ISC-408', 'Ingeniería del Software', 4),
    ('ISC-422', 'Administración de Base de Datos', 4),
    ('ISC-442', 'Seguridad Informática', 4),
    ('ISC-443', 'Industria de TI', 4),
    ('ISC-409', 'Calidad de Software', 4),
    ('ISC-423', 'Ciencia de Datos', 4),
    ('ISC-415', 'Tecnologías Emergentes', 4),
    ('ISC-445', 'Proyectos de TI', 4),
)


def cargar_catalogo(apps, schema_editor):
    clase_model = apps.get_model('demo', 'Clase')
    clases = clase_model.objects.using(schema_editor.connection.alias)
    codigos = [codigo for codigo, _, _ in CLASES_CATALOGO]

    clases.exclude(pk__in=codigos).delete()
    for codigo, nombre, uv in CLASES_CATALOGO:
        clases.update_or_create(
            pk=codigo,
            defaults={'clase': nombre, 'uv': uv},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0006_estudiante_censoestudiante'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clase',
            name='cantidadEM',
        ),
        migrations.RunPython(cargar_catalogo, migrations.RunPython.noop),
    ]
