"""
Generador de archivos Excel (.xlsx) para el Sistema de Horarios utilizando XlsxWriter.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Iterable
import xlsxwriter


def generar_excel_horario(horarios_qs: Iterable[Any], filtros_str: str = 'Todos los registros') -> io.BytesIO:
    """
    Genera un archivo Excel en memoria con dos hojas:
    1. 'Horario Semanal': Matriz visual de horas vs días de la semana.
    2. 'Listado Detallado': Tabla con el desglose completo de cada clase asignada.
    """
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})

    # Estilos / Formatos
    title_fmt = wb.add_format({
        'bold': True,
        'font_size': 16,
        'font_color': '#1E3A8A',
        'font_name': 'Segoe UI',
    })
    subtitle_fmt = wb.add_format({
        'italic': True,
        'font_size': 10,
        'font_color': '#64748B',
        'font_name': 'Segoe UI',
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
        'bg_color': '#F1F5F9',
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

    horarios_lista = list(horarios_qs)

    # ─── Hoja 1: Horario Semanal ───────────────────────────────────────────────
    ws_matriz = wb.add_worksheet('Horario Semanal')
    ws_matriz.set_column('A:A', 16)
    ws_matriz.set_column('B:F', 28)

    ws_matriz.write('A1', 'SISTEMA DE HORARIOS UNIVERSITARIO', title_fmt)
    ws_matriz.write('A2', f'Filtros: {filtros_str} | Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}', subtitle_fmt)

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    ws_matriz.write('A4', 'Hora', header_fmt)
    for col_idx, dia in enumerate(dias_semana, start=1):
        ws_matriz.write(3, col_idx, dia, header_fmt)

    matriz_datos = {}
    for slot in horarios_lista:
        hora = slot.hora
        uv = slot.idClase.uv
        docente_str = f'{slot.idDocente.nombre} {slot.idDocente.apellido}'
        aula_str = f'{slot.idAula.nombreAula}'
        contenido = (
            f"[{slot.idClase.id}] {slot.idClase.clase}\n"
            f"Docente: {docente_str}\n"
            f"Aula: {aula_str} (Cap: {slot.idAula.capacidad})"
        )
        for dia_idx in range(5):
            if uv > dia_idx:
                matriz_datos.setdefault((hora, dia_idx), []).append(contenido)

    row_num = 4
    for hora in range(7, 19):
        hora_label = f'{hora:02d}:00 - {hora + 1:02d}:00'
        ws_matriz.write(row_num, 0, hora_label, hour_col_fmt)

        max_altura = 1
        for dia_idx in range(5):
            bloques = matriz_datos.get((hora, dia_idx), [])
            if bloques:
                texto_celda = '\n---\n'.join(bloques)
                ws_matriz.write(row_num, dia_idx + 1, texto_celda, cell_card_fmt)
                max_altura = max(max_altura, len(bloques))
            else:
                ws_matriz.write(row_num, dia_idx + 1, '', empty_cell_fmt)

        ws_matriz.set_row(row_num, max(42, max_altura * 38))
        row_num += 1

    # ─── Hoja 2: Listado Detallado ─────────────────────────────────────────────
    ws_lista = wb.add_worksheet('Listado de Clases')
    columnas_lista = [
        ('Código', 12, table_cell_center_fmt),
        ('Nombre de la Clase', 32, table_cell_fmt),
        ('UV', 8, table_cell_center_fmt),
        ('Estudiantes', 12, table_cell_center_fmt),
        ('Docente Asignado', 28, table_cell_fmt),
        ('Aula', 20, table_cell_fmt),
        ('Tipo Aula', 14, table_cell_center_fmt),
        ('Hora', 14, table_cell_center_fmt),
        ('Días', 18, table_cell_center_fmt),
    ]

    ws_lista.write('A1', 'LISTADO COMPLETO DE ASIGNACIONES', title_fmt)
    ws_lista.write('A2', f'Total asignaciones: {len(horarios_lista)} | {datetime.now().strftime("%d/%m/%Y %H:%M")}', subtitle_fmt)

    header_row = 3
    for col_idx, (col_name, col_width, _) in enumerate(columnas_lista):
        ws_lista.write(header_row, col_idx, col_name, header_fmt)
        ws_lista.set_column(col_idx, col_idx, col_width)

    for row_idx, slot in enumerate(horarios_lista, start=header_row + 1):
        uv = slot.idClase.uv
        dias_str = 'Lunes a Viernes' if uv >= 5 else ('Lunes a Jueves' if uv == 4 else f'Primeros {uv} días')
        hora_str = f'{slot.hora:02d}:00 - {slot.hora + 1:02d}:00'

        ws_lista.write(row_idx, 0, slot.idClase.id, table_cell_center_fmt)
        ws_lista.write(row_idx, 1, slot.idClase.clase, table_cell_fmt)
        ws_lista.write(row_idx, 2, slot.idClase.uv, table_cell_center_fmt)
        ws_lista.write(row_idx, 3, slot.idClase.cantidadEM, table_cell_center_fmt)
        ws_lista.write(row_idx, 4, f'{slot.idDocente.nombre} {slot.idDocente.apellido}', table_cell_fmt)
        ws_lista.write(row_idx, 5, f'{slot.idAula.nombreAula}', table_cell_fmt)
        ws_lista.write(row_idx, 6, slot.idAula.get_tipo_display() if hasattr(slot.idAula, 'get_tipo_display') else slot.idAula.tipo, table_cell_center_fmt)
        ws_lista.write(row_idx, 7, hora_str, table_cell_center_fmt)
        ws_lista.write(row_idx, 8, dias_str, table_cell_center_fmt)

    wb.close()
    output.seek(0)
    return output

