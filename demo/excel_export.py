"""
Generador de archivos Excel (.xlsx) para el Sistema de Horarios utilizando XlsxWriter.
Incluye logos institucionales (UNAH Campus Choluteca e Ingeniería en Sistemas) y
datos de censo estudiantil por clase.
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any, Iterable

import xlsxwriter

# Ruta base del proyecto (dos niveles arriba de este archivo)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_logo(nombre_archivo: str) -> str:
    """Busca un logo preferentemente en formato .png y luego .jpg."""
    img_dir = os.path.join(_BASE_DIR, 'static', 'img')
    for ext in ('.png', '.jpg', '.jpeg'):
        path = os.path.join(img_dir, f'{nombre_archivo}{ext}')
        if os.path.isfile(path):
            return path
    return ''


_LOGO_INGENIERIA = _find_logo('logo_ingenieria')
_LOGO_UNAH = _find_logo('logo_unah')


def _get_censo_counts(horarios_lista: list[Any]) -> dict[str, int]:
    """Retorna un dict {clase_id: total_censo} para los slots dados."""
    try:
        from django.db.models import Count
        from demo.models import CensoEstudiante  # importación local para evitar circulares
        clase_ids = [slot.idClase_id for slot in horarios_lista]
        return {
            row['clase_id']: row['total']
            for row in CensoEstudiante.objects.filter(clase_id__in=clase_ids)
                                               .values('clase_id')
                                               .annotate(total=Count('id'))
        }
    except Exception:
        return {}


def generar_excel_horario(horarios_qs: Iterable[Any], filtros_str: str = 'Todos los registros') -> io.BytesIO:
    """
    Genera un archivo Excel en memoria con dos hojas:
    1. 'Horario Semanal': Matriz visual de horas vs días de la semana.
    2. 'Listado Detallado': Tabla con el desglose completo de cada clase asignada.
    Ambas hojas incluyen logos institucionales y datos de censo estudiantil.
    """
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})

    # ── Formatos ──────────────────────────────────────────────────────────────
    title_fmt = wb.add_format({
        'bold': True,
        'font_size': 15,
        'font_color': '#1E3A8A',
        'font_name': 'Segoe UI',
        'valign': 'vcenter',
    })
    subtitle_fmt = wb.add_format({
        'italic': True,
        'font_size': 9,
        'font_color': '#64748B',
        'font_name': 'Segoe UI',
        'valign': 'vcenter',
    })
    header_fmt = wb.add_format({
        'bold': True,
        'font_size': 11,
        'font_color': '#FFFFFF',
        'bg_color': '#1E3A8A',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#CBD5E1',
        'font_name': 'Segoe UI',
    })
    hour_col_fmt = wb.add_format({
        'bold': True,
        'font_size': 10,
        'font_color': '#0F172A',
        'bg_color': '#EFF6FF',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#CBD5E1',
        'font_name': 'Segoe UI',
    })
    cell_card_fmt = wb.add_format({
        'text_wrap': True,
        'valign': 'top',
        'align': 'left',
        'border': 1,
        'border_color': '#E2E8F0',
        'bg_color': '#F8FAFC',
        'font_size': 9,
        'font_name': 'Segoe UI',
    })
    empty_cell_fmt = wb.add_format({
        'border': 1,
        'border_color': '#F1F5F9',
    })
    table_cell_fmt = wb.add_format({
        'border': 1,
        'border_color': '#E2E8F0',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Segoe UI',
    })
    table_cell_center_fmt = wb.add_format({
        'border': 1,
        'border_color': '#E2E8F0',
        'valign': 'vcenter',
        'align': 'center',
        'font_size': 10,
        'font_name': 'Segoe UI',
    })
    censo_fmt = wb.add_format({
        'border': 1,
        'border_color': '#E2E8F0',
        'valign': 'vcenter',
        'align': 'center',
        'font_size': 10,
        'font_name': 'Segoe UI',
        'bg_color': '#DBEAFE',
        'font_color': '#1E40AF',
        'bold': True,
    })

    horarios_lista = list(horarios_qs)

    # Mapa de censo {clase_id: total_estudiantes}
    censo_map = _get_censo_counts(horarios_lista)

    # ── Dimensiones de logos ──────────────────────────────────────────────────
    LOGO_ING_H  = 70   # px alto  logo ingeniería (redondo)
    LOGO_UNAH_H = 48   # px alto  logo UNAH barra

    # ─── Hoja 1: Horario Semanal ───────────────────────────────────────────────
    ws_matriz = wb.add_worksheet('Horario Semanal')
    ws_matriz.set_column('A:A', 16)
    ws_matriz.set_column('B:F', 30)

    # Fila de logos: ocupamos las primeras 5 filas (altura total ~80 px)
    ws_matriz.set_row(0, 20)
    ws_matriz.set_row(1, 20)
    ws_matriz.set_row(2, 20)
    ws_matriz.set_row(3, 16)
    ws_matriz.set_row(4, 16)

    # Logo Ingeniería (columna A, filas 0-3)
    if os.path.isfile(_LOGO_INGENIERIA):
        ws_matriz.insert_image(
            0, 0, _LOGO_INGENIERIA,
            {
                'x_offset': 4, 'y_offset': 4,
                'x_scale': LOGO_ING_H / 1000,
                'y_scale': LOGO_ING_H / 1000,
                'positioning': 1,
            },
        )

    # Título (columnas B-D, filas 0-1)
    ws_matriz.merge_range('B1:E2', 'SISTEMA DE HORARIOS UNIVERSITARIO', title_fmt)
    ws_matriz.merge_range('B3:E3', 'Ingeniería en Sistemas — UNAH Campus Choluteca', subtitle_fmt)
    ws_matriz.merge_range(
        'B4:E5',
        f'Filtros: {filtros_str}  |  Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        subtitle_fmt,
    )

    # Logo UNAH (columna F, filas 0-2)
    if os.path.isfile(_LOGO_UNAH):
        ws_matriz.insert_image(
            0, 5, _LOGO_UNAH,
            {
                'x_offset': 4, 'y_offset': 10,
                'x_scale': LOGO_UNAH_H / 335,
                'y_scale': LOGO_UNAH_H / 335,
                'positioning': 1,
            },
        )

    # Cabecera de días (fila 6, índice 5 → row_offset = 6)
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    HEADER_ROW = 6
    ws_matriz.write(HEADER_ROW, 0, 'Hora', header_fmt)
    for col_idx, dia in enumerate(dias_semana, start=1):
        ws_matriz.write(HEADER_ROW, col_idx, dia, header_fmt)

    # Datos de la matriz
    matriz_datos: dict[tuple[int, int], list[str]] = {}
    for slot in horarios_lista:
        hora = slot.hora
        uv = slot.idClase.uv
        docente_str = f'{slot.idDocente.nombre} {slot.idDocente.apellido}'
        aula_str = f'{slot.idAula.nombreAula}'
        censo_total = censo_map.get(slot.idClase_id, slot.idClase_id and 0)
        censo_str = f'Censo: {censo_total} est.' if censo_total else ''
        contenido = (
            f"[{slot.idClase.id}] {slot.idClase.clase}\n"
            f"Docente: {docente_str}\n"
            f"Aula: {aula_str} (Cap: {slot.idAula.capacidad})"
        )
        if censo_str:
            contenido += f"\n{censo_str}"
        for dia_idx in range(5):
            if uv > dia_idx:
                matriz_datos.setdefault((hora, dia_idx), []).append(contenido)

    row_num = HEADER_ROW + 1
    for hora in range(7, 19):
        hora_label = f'{hora:02d}:00 – {hora + 1:02d}:00'
        ws_matriz.write(row_num, 0, hora_label, hour_col_fmt)

        max_altura = 1
        for dia_idx in range(5):
            bloques = matriz_datos.get((hora, dia_idx), [])
            if bloques:
                texto_celda = '\n───\n'.join(bloques)
                ws_matriz.write(row_num, dia_idx + 1, texto_celda, cell_card_fmt)
                max_altura = max(max_altura, len(bloques))
            else:
                ws_matriz.write(row_num, dia_idx + 1, '', empty_cell_fmt)

        ws_matriz.set_row(row_num, max(48, max_altura * 48))
        row_num += 1

    # ─── Hoja 2: Listado Detallado ─────────────────────────────────────────────
    ws_lista = wb.add_worksheet('Listado de Clases')

    # Misma cabecera con logos
    ws_lista.set_row(0, 20)
    ws_lista.set_row(1, 20)
    ws_lista.set_row(2, 20)
    ws_lista.set_row(3, 16)
    ws_lista.set_row(4, 16)

    if os.path.isfile(_LOGO_INGENIERIA):
        ws_lista.insert_image(
            0, 0, _LOGO_INGENIERIA,
            {
                'x_offset': 4, 'y_offset': 4,
                'x_scale': LOGO_ING_H / 1000,
                'y_scale': LOGO_ING_H / 1000,
                'positioning': 1,
            },
        )

    ws_lista.merge_range('B1:I2', 'LISTADO COMPLETO DE ASIGNACIONES', title_fmt)
    ws_lista.merge_range('B3:I3', 'Ingeniería en Sistemas — UNAH Campus Choluteca', subtitle_fmt)
    ws_lista.merge_range(
        'B4:I5',
        f'Total asignaciones: {len(horarios_lista)} | '
        f'Total est. en censo: {sum(censo_map.values())} | '
        f'{datetime.now().strftime("%d/%m/%Y %H:%M")}',
        subtitle_fmt,
    )

    if os.path.isfile(_LOGO_UNAH):
        ws_lista.insert_image(
            0, 9, _LOGO_UNAH,
            {
                'x_offset': 4, 'y_offset': 10,
                'x_scale': LOGO_UNAH_H / 335,
                'y_scale': LOGO_UNAH_H / 335,
                'positioning': 1,
            },
        )

    columnas_lista = [
        ('Código', 12, table_cell_center_fmt),
        ('Nombre de la Clase', 32, table_cell_fmt),
        ('UV', 8, table_cell_center_fmt),
        ('Censo (Demanda)', 15, censo_fmt),
        ('Docente Asignado', 28, table_cell_fmt),
        ('Aula', 20, table_cell_fmt),
        ('Tipo Aula', 14, table_cell_center_fmt),
        ('Hora', 14, table_cell_center_fmt),
        ('Días', 18, table_cell_center_fmt),
    ]

    header_row = HEADER_ROW  # = 6
    for col_idx, (col_name, col_width, _) in enumerate(columnas_lista):
        ws_lista.write(header_row, col_idx, col_name, header_fmt)
        ws_lista.set_column(col_idx, col_idx, col_width)

    for row_idx, slot in enumerate(horarios_lista, start=header_row + 1):
        uv = slot.idClase.uv
        dias_str = (
            'Lunes a Viernes' if uv >= 5 else
            ('Lunes a Jueves' if uv == 4 else f'Primeros {uv} días')
        )
        hora_str = f'{slot.hora:02d}:00 – {slot.hora + 1:02d}:00'
        censo_total = censo_map.get(slot.idClase_id, 0)

        ws_lista.write(row_idx, 0, slot.idClase.id, table_cell_center_fmt)
        ws_lista.write(row_idx, 1, slot.idClase.clase, table_cell_fmt)
        ws_lista.write(row_idx, 2, slot.idClase.uv, table_cell_center_fmt)
        ws_lista.write(row_idx, 3, censo_total, censo_fmt)
        ws_lista.write(row_idx, 4, f'{slot.idDocente.nombre} {slot.idDocente.apellido}', table_cell_fmt)
        ws_lista.write(row_idx, 5, f'{slot.idAula.nombreAula}', table_cell_fmt)
        ws_lista.write(
            row_idx, 6,
            slot.idAula.get_tipo_display() if hasattr(slot.idAula, 'get_tipo_display') else slot.idAula.tipo,
            table_cell_center_fmt,
        )
        ws_lista.write(row_idx, 7, hora_str, table_cell_center_fmt)
        ws_lista.write(row_idx, 8, dias_str, table_cell_center_fmt)

    wb.close()
    output.seek(0)
    return output
