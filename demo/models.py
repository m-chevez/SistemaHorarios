from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Docente(models.Model):
    id = models.CharField(max_length=30, primary_key=True, verbose_name='Identidad')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    hora_inicio = models.PositiveSmallIntegerField(
        default=7,
        validators=(MinValueValidator(7), MaxValueValidator(18)),
        verbose_name='Hora inicio disponibilidad',
    )
    hora_fin = models.PositiveSmallIntegerField(
        default=18,
        validators=(MinValueValidator(8), MaxValueValidator(19)),
        verbose_name='Hora fin disponibilidad',
    )

    class Meta:
        ordering = ('apellido', 'nombre')
        verbose_name = 'docente'
        verbose_name_plural = 'docentes'

    def __str__(self):
        return f'{self.nombre} {self.apellido}'


class Aula(models.Model):
    class Tipo(models.TextChoices):
        AULA = 'aula', 'Aula'
        LABORATORIO = 'laboratorio', 'Laboratorio'

    idAula = models.CharField(max_length=30, primary_key=True, verbose_name='Código')
    nombreAula = models.CharField(max_length=100, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    capacidad = models.PositiveIntegerField(validators=(MinValueValidator(1),))

    class Meta:
        ordering = ('idAula',)
        verbose_name = 'aula'
        verbose_name_plural = 'aulas'

    def __str__(self):
        return f'{self.idAula} - {self.nombreAula}'


class Clase(models.Model):
    id = models.CharField(max_length=30, primary_key=True, verbose_name='Código')
    clase = models.CharField(max_length=120, verbose_name='Nombre')
    uv = models.PositiveIntegerField(
        validators=(MinValueValidator(1),),
        verbose_name='Unidades valorativas',
    )
    cantidadEM = models.PositiveIntegerField(verbose_name='Estudiantes matriculados')

    class Meta:
        ordering = ('id',)
        verbose_name = 'clase'
        verbose_name_plural = 'clases'

    def __str__(self):
        return f'{self.id} - {self.clase}'


class Horario(models.Model):
    idClase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Clase',
    )
    idDocente = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Docente',
    )
    idAula = models.ForeignKey(
        Aula,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Aula',
    )
    hora = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(7), MaxValueValidator(18)),
    )

    class Meta:
        ordering = ('hora', 'id')
        constraints = (
            models.UniqueConstraint(fields=('idClase',), name='unique_class_schedule'),
            models.UniqueConstraint(fields=('idDocente', 'hora'), name='unique_teacher_hour'),
            models.UniqueConstraint(fields=('idAula', 'hora'), name='unique_room_hour'),
        )
        verbose_name = 'asignación de horario'
        verbose_name_plural = 'asignaciones de horario'

    def __str__(self):
        return f'{self.idClase} - {self.hora}:00'


class PreferenciaDocenteClase(models.Model):
    class Prioridad(models.IntegerChoices):
        ALTA = 1, 'Alta'
        MEDIA = 2, 'Media'
        BAJA = 3, 'Baja'

    docente = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name='preferencias_clases',
        verbose_name='Docente',
    )
    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name='preferencias_docentes',
        verbose_name='Clase',
    )
    prioridad = models.PositiveSmallIntegerField(
        choices=Prioridad.choices,
        default=Prioridad.ALTA,
        verbose_name='Preferencia',
    )

    class Meta:
        ordering = ('prioridad', 'clase__clase')
        constraints = (
            models.UniqueConstraint(fields=('docente', 'clase'), name='unique_docente_clase'),
        )
        verbose_name = 'preferencia de clase por docente'
        verbose_name_plural = 'preferencias de clases por docentes'

    def __str__(self):
        return f'{self.docente} - {self.clase} ({self.get_prioridad_display()})'
