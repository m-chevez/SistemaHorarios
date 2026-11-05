"""
Algoritmo Genético para la Generación Automática de Horarios Universitarios.

Optimización combinatoria jerárquica:
1. Prioridad 1: Minimizar/eliminar traslapes de clases para los estudiantes (Censo).
2. Prioridad 2: Respetar disponibilidad horaria de docentes y evitar colisiones físicas
   (mismo docente o misma aula a la misma hora). Respetar capacidad de aula.
3. Prioridad 3: Respetar la carga académica máxima (UV) de cada docente.
4. Prioridad 4: Maximizar la satisfacción de preferencias de asignación de docentes por clase
   (Prioridad Alta > Media > Baja > Sin preferencia).
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Constantes de Penalización Jerárquica ─────────────────────────────────────
PENALTY_STUDENT_CONFLICT = 1_000_000  # Máxima prioridad: traslape de estudiante
PENALTY_TEACHER_COLLISION = 100_000   # Docente asignado a 2 clases a la misma hora
PENALTY_ROOM_COLLISION = 100_000      # Aula ocupada por 2 clases a la misma hora
PENALTY_TEACHER_AVAILABILITY = 50_000 # Clase fuera del rango de horas del docente
PENALTY_ROOM_CAPACITY = 25_000        # Capacidad de aula menor a matrícula
PENALTY_UV_EXCESS_PER_UNIT = 2_500    # Cada UV excedida sobre la carga máxima
PENALTY_PREFERENCE_NONE = 600         # Docente sin preferencia registrada para la clase
PENALTY_PREFERENCE_BAJA = 250         # Docente con preferencia baja
PENALTY_PREFERENCE_MEDIA = 80         # Docente con preferencia media
PENALTY_PREFERENCE_ALTA = 0           # Docente con preferencia alta (ideal)
BONUS_TENTATIVE_HOUR = -15            # Bonificación leve si coincide con la hora tentativa del censo


@dataclass
class DocenteData:
    id: str
    nombre_completo: str
    hora_inicio: int
    hora_fin: int
    carga_maxima_uv: Optional[int]


@dataclass
class AulaData:
    id: str
    nombre: str
    capacidad: int
    tipo: str


@dataclass
class ClaseData:
    id: str
    nombre: str
    uv: int
    matricula: int


@dataclass
class CensoEntry:
    estudiante_cuenta: str
    estudiante_nombre: str
    clase_id: str
    hora_tentativa: int


@dataclass
class ScheduleGene:
    clase_id: str
    hora: int
    docente_id: str
    aula_id: str


@dataclass
class ScheduleChromosome:
    genes: List[ScheduleGene]
    fitness: float = float('inf')
    detalles: Dict[str, Any] = field(default_factory=dict)


class GeneticScheduleOptimizer:
    """
    Optimizador genético para el problema de horarios universitarios.
    """

    def __init__(
        self,
        clases: List[ClaseData],
        docentes: List[DocenteData],
        aulas: List[AulaData],
        preferencias: Dict[Tuple[str, str], int],
        censo: List[CensoEntry],
        horas_disponibles: Optional[List[int]] = None,
        pop_size: int = 70,
        max_generations: int = 140,
        mutation_rate: float = 0.22,
        elitism_count: int = 4,
        tournament_size: int = 4,
    ):
        self.clases = {c.id: c for c in clases}
        self.clases_list = list(clases)
        self.docentes = {d.id: d for d in docentes}
        self.docentes_list = list(docentes)
        self.aulas = {a.id: a for a in aulas}
        self.aulas_list = list(aulas)
        self.preferencias = preferencias
        self.censo = censo
        self.horas_disponibles = horas_disponibles or list(range(7, 19))
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        self.tournament_size = tournament_size

        self.estudiante_clases: Dict[str, List[Tuple[str, int]]] = {}
        for entry in self.censo:
            self.estudiante_clases.setdefault(entry.estudiante_cuenta, []).append(
                (entry.clase_id, entry.hora_tentativa)
            )

        self.docentes_por_clase: Dict[str, List[DocenteData]] = {}
        for clase in self.clases_list:
            candidatos = list(self.docentes_list)
            def pref_key(d: DocenteData) -> int:
                return self.preferencias.get((d.id, clase.id), 4)
            candidatos.sort(key=pref_key)
            self.docentes_por_clase[clase.id] = candidatos

    def evaluate(self, chromosome: ScheduleChromosome) -> float:
        penalty = 0.0

        clase_hora: Dict[str, int] = {}
        docente_horarios: Dict[str, List[Tuple[int, str]]] = {}
        aula_horarios: Dict[str, List[Tuple[int, str]]] = {}
        docente_uv: Dict[str, int] = {d.id: 0 for d in self.docentes_list}

        detalles_traslapes_estudiantes = []
        colisiones_docente_count = 0
        colisiones_aula_count = 0
        violaciones_horario_docente_count = 0
        violaciones_capacidad_aula_count = 0
        conteo_preferencias = {'alta': 0, 'media': 0, 'baja': 0, 'ninguna': 0}

        for idx, gene in enumerate(chromosome.genes):
            clase = self.clases[gene.clase_id]
            docente = self.docentes[gene.docente_id]
            aula = self.aulas[gene.aula_id]

            clase_hora[clase.id] = gene.hora
            docente_horarios.setdefault(docente.id, []).append((gene.hora, clase.id))
            aula_horarios.setdefault(aula.id, []).append((gene.hora, clase.id))
            docente_uv[docente.id] += clase.uv

            if not (docente.hora_inicio <= gene.hora < docente.hora_fin):
                penalty += PENALTY_TEACHER_AVAILABILITY
                violaciones_horario_docente_count += 1

            if aula.capacidad < clase.matricula:
                penalty += PENALTY_ROOM_CAPACITY
                violaciones_capacidad_aula_count += 1

            # Prioridad 4: Preferencia de docente por clase (con desempate suave por orden de clase)
            pref = self.preferencias.get((docente.id, clase.id))
            peso_posicion = 1.0 + (0.02 * (len(self.clases_list) - idx))
            if pref == 1:
                penalty += PENALTY_PREFERENCE_ALTA * peso_posicion
                conteo_preferencias['alta'] += 1
            elif pref == 2:
                penalty += PENALTY_PREFERENCE_MEDIA * peso_posicion
                conteo_preferencias['media'] += 1
            elif pref == 3:
                penalty += PENALTY_PREFERENCE_BAJA * peso_posicion
                conteo_preferencias['baja'] += 1
            else:
                penalty += PENALTY_PREFERENCE_NONE * peso_posicion
                conteo_preferencias['ninguna'] += 1

        traslapes_estudiantes_count = 0
        for cuenta, items in self.estudiante_clases.items():
            n_items = len(items)
            for i in range(n_items):
                clase_a_id, tentativa_a = items[i]
                hora_a = clase_hora.get(clase_a_id)
                if hora_a is None:
                    continue

                if hora_a == tentativa_a:
                    penalty += BONUS_TENTATIVE_HOUR

                uv_a = self.clases[clase_a_id].uv
                for j in range(i + 1, n_items):
                    clase_b_id, _ = items[j]
                    hora_b = clase_hora.get(clase_b_id)
                    if hora_b is None:
                        continue

                    if hora_a == hora_b and min(uv_a, self.clases[clase_b_id].uv) > 0:
                        traslapes_estudiantes_count += 1
                        penalty += PENALTY_STUDENT_CONFLICT
                        detalles_traslapes_estudiantes.append({
                            'estudiante': cuenta,
                            'clase1': self.clases[clase_a_id].nombre,
                            'clase2': self.clases[clase_b_id].nombre,
                            'hora': hora_a,
                        })

        for doc_id, horas_list in docente_horarios.items():
            horas_vistas: Set[int] = set()
            for hora, _ in horas_list:
                if hora in horas_vistas:
                    colisiones_docente_count += 1
                    penalty += PENALTY_TEACHER_COLLISION
                horas_vistas.add(hora)

        for aula_id, horas_list in aula_horarios.items():
            horas_vistas = set()
            for hora, _ in horas_list:
                if hora in horas_vistas:
                    colisiones_aula_count += 1
                    penalty += PENALTY_ROOM_COLLISION
                horas_vistas.add(hora)

        exceso_uv_total = 0
        detalles_exceso_uv = {}
        for doc_id, uv_asignada in docente_uv.items():
            docente = self.docentes[doc_id]
            if docente.carga_maxima_uv is not None and uv_asignada > docente.carga_maxima_uv:
                exceso = uv_asignada - docente.carga_maxima_uv
                exceso_uv_total += exceso
                penalty += exceso * PENALTY_UV_EXCESS_PER_UNIT
                detalles_exceso_uv[docente.nombre_completo] = {
                    'asignadas': uv_asignada,
                    'maximas': docente.carga_maxima_uv,
                    'exceso': exceso,
                }

        chromosome.fitness = penalty
        chromosome.detalles = {
            'penalty_total': penalty,
            'traslapes_estudiantes': traslapes_estudiantes_count,
            'detalles_traslapes_estudiantes': detalles_traslapes_estudiantes,
            'colisiones_docentes': colisiones_docente_count,
            'colisiones_aulas': colisiones_aula_count,
            'violaciones_horario_docente': violaciones_horario_docente_count,
            'violaciones_capacidad_aula': violaciones_capacidad_aula_count,
            'exceso_uv_total': exceso_uv_total,
            'detalles_exceso_uv': detalles_exceso_uv,
            'conteo_preferencias': conteo_preferencias,
            'es_perfecto': (
                traslapes_estudiantes_count == 0
                and colisiones_docente_count == 0
                and colisiones_aula_count == 0
                and violaciones_horario_docente_count == 0
                and violaciones_capacidad_aula_count == 0
                and exceso_uv_total == 0
            ),
        }
        return penalty

    def _generar_gen_inteligente(self, clase: ClaseData) -> ScheduleGene:
        candidatos = self.docentes_por_clase[clase.id]
        if candidatos and random.random() < 0.85:
            # Favorecer fuertemente al docente con mayor prioridad (Alta)
            docente = candidatos[0] if random.random() < 0.70 else random.choice(candidatos[:min(2, len(candidatos))])
        else:
            docente = random.choice(self.docentes_list)

        horas_validas = [
            h for h in self.horas_disponibles
            if docente.hora_inicio <= h < docente.hora_fin
        ]
        hora = random.choice(horas_validas) if horas_validas else random.choice(self.horas_disponibles)

        aulas_adecuadas = [a for a in self.aulas_list if a.capacidad >= clase.matricula]
        aula = random.choice(aulas_adecuadas) if aulas_adecuadas else random.choice(self.aulas_list)

        return ScheduleGene(
            clase_id=clase.id,
            hora=hora,
            docente_id=docente.id,
            aula_id=aula.id,
        )

    def _inicializar_poblacion(self) -> List[ScheduleChromosome]:
        poblacion = []
        for _ in range(self.pop_size):
            genes = [self._generar_gen_inteligente(c) for c in self.clases_list]
            chrom = ScheduleChromosome(genes=genes)
            self.evaluate(chrom)
            poblacion.append(chrom)
        return poblacion

    def _seleccion_torneo(self, poblacion: List[ScheduleChromosome]) -> ScheduleChromosome:
        aspirantes = random.sample(poblacion, min(self.tournament_size, len(poblacion)))
        aspirantes.sort(key=lambda c: c.fitness)
        return aspirantes[0]

    def _cruce_uniforme(
        self,
        padre1: ScheduleChromosome,
        padre2: ScheduleChromosome,
    ) -> Tuple[ScheduleChromosome, ScheduleChromosome]:
        hijo1_genes = []
        hijo2_genes = []
        for g1, g2 in zip(padre1.genes, padre2.genes):
            if random.random() < 0.5:
                hijo1_genes.append(copy.deepcopy(g1))
                hijo2_genes.append(copy.deepcopy(g2))
            else:
                hijo1_genes.append(copy.deepcopy(g2))
                hijo2_genes.append(copy.deepcopy(g1))
        return ScheduleChromosome(genes=hijo1_genes), ScheduleChromosome(genes=hijo2_genes)

    def _mutar(self, individuo: ScheduleChromosome) -> None:
        for gene in individuo.genes:
            if random.random() < self.mutation_rate:
                clase = self.clases[gene.clase_id]
                tipo_mutacion = random.choice(['hora', 'docente', 'aula', 'ambos'])

                if tipo_mutacion in ('hora', 'ambos'):
                    docente = self.docentes[gene.docente_id]
                    horas_docente = [
                        h for h in self.horas_disponibles
                        if docente.hora_inicio <= h < docente.hora_fin
                    ]
                    gene.hora = random.choice(horas_docente) if horas_docente else random.choice(self.horas_disponibles)

                if tipo_mutacion in ('docente', 'ambos'):
                    candidatos = self.docentes_por_clase[clase.id]
                    if candidatos and random.random() < 0.8:
                        gene.docente_id = random.choice(candidatos[:min(3, len(candidatos))]).id
                    else:
                        gene.docente_id = random.choice(self.docentes_list).id

                if tipo_mutacion == 'aula':
                    aulas_adecuadas = [a for a in self.aulas_list if a.capacidad >= clase.matricula]
                    gene.aula_id = (random.choice(aulas_adecuadas) if aulas_adecuadas else random.choice(self.aulas_list)).id

    def _reparacion_heuristica_local(self, individuo: ScheduleChromosome) -> None:
        docente_ocupado: Dict[Tuple[str, int], str] = {}
        aula_ocupada: Dict[Tuple[str, int], str] = {}

        clase_estudiantes: Dict[str, Set[str]] = {}
        for entry in self.censo:
            clase_estudiantes.setdefault(entry.clase_id, set()).add(entry.estudiante_cuenta)

        for gene in individuo.genes:
            doc_key = (gene.docente_id, gene.hora)
            aula_key = (gene.aula_id, gene.hora)

            hay_conflicto = False
            if doc_key in docente_ocupado or aula_key in aula_ocupada:
                hay_conflicto = True

            if hay_conflicto:
                docente = self.docentes[gene.docente_id]
                estudiantes_gen = clase_estudiantes.get(gene.clase_id, set())

                mejores_horas = []
                for h in self.horas_disponibles:
                    if not (docente.hora_inicio <= h < docente.hora_fin):
                        continue
                    if (gene.docente_id, h) in docente_ocupado:
                        continue
                    if (gene.aula_id, h) in aula_ocupada:
                        continue
                    choca_estudiante = False
                    for otro_gene in individuo.genes:
                        if otro_gene.clase_id != gene.clase_id and otro_gene.hora == h:
                            otros_estudiantes = clase_estudiantes.get(otro_gene.clase_id, set())
                            if estudiantes_gen & otros_estudiantes:
                                choca_estudiante = True
                                break
                    if not choca_estudiante:
                        mejores_horas.append(h)

                if mejores_horas:
                    gene.hora = random.choice(mejores_horas)

            docente_ocupado[(gene.docente_id, gene.hora)] = gene.clase_id
            aula_ocupada[(gene.aula_id, gene.hora)] = gene.clase_id

    def optimize(self) -> Tuple[ScheduleChromosome, Dict[str, Any]]:
        if not self.clases_list:
            raise ValueError('No hay clases censadas para programar.')
        if not self.docentes_list or not self.aulas_list:
            raise ValueError('Debe existir al menos un docente y un aula registrados.')

        poblacion = self._inicializar_poblacion()
        poblacion.sort(key=lambda c: c.fitness)
        mejor_global = copy.deepcopy(poblacion[0])

        historial_fitness = [mejor_global.fitness]
        generaciones_sin_mejora = 0

        for gen in range(1, self.max_generations + 1):
            if mejor_global.detalles.get('es_perfecto'):
                break

            nueva_poblacion = []
            for i in range(min(self.elitism_count, len(poblacion))):
                nueva_poblacion.append(copy.deepcopy(poblacion[i]))

            while len(nueva_poblacion) < self.pop_size:
                p1 = self._seleccion_torneo(poblacion)
                p2 = self._seleccion_torneo(poblacion)
                h1, h2 = self._cruce_uniforme(p1, p2)

                self._mutar(h1)
                self._mutar(h2)

                if random.random() < 0.40:
                    self._reparacion_heuristica_local(h1)
                if random.random() < 0.40:
                    self._reparacion_heuristica_local(h2)

                self.evaluate(h1)
                self.evaluate(h2)

                nueva_poblacion.append(h1)
                if len(nueva_poblacion) < self.pop_size:
                    nueva_poblacion.append(h2)

            poblacion = nueva_poblacion
            poblacion.sort(key=lambda c: c.fitness)

            if poblacion[0].fitness < mejor_global.fitness:
                mejor_global = copy.deepcopy(poblacion[0])
                generaciones_sin_mejora = 0
            else:
                generaciones_sin_mejora += 1

            historial_fitness.append(mejor_global.fitness)

            if generaciones_sin_mejora >= 30:
                for idx in range(self.elitism_count, len(poblacion)):
                    if random.random() < 0.6:
                        poblacion[idx] = ScheduleChromosome(
                            genes=[self._generar_gen_inteligente(c) for c in self.clases_list]
                        )
                        self.evaluate(poblacion[idx])
                poblacion.sort(key=lambda c: c.fitness)
                generaciones_sin_mejora = 0

        self.evaluate(mejor_global)
        diagnostico = self._generar_reporte_diagnostico(mejor_global, len(historial_fitness))
        return mejor_global, diagnostico

    def _generar_reporte_diagnostico(
        self,
        mejor: ScheduleChromosome,
        generaciones_ejecutadas: int,
    ) -> Dict[str, Any]:
        detalles = mejor.detalles
        es_optimo = detalles.get('es_perfecto', False)

        total_uv_clases = sum(c.uv for c in self.clases_list)
        total_capacidad_uv_docentes = sum(
            d.carga_maxima_uv if d.carga_maxima_uv is not None else 999
            for d in self.docentes_list
        )

        observaciones = []
        if total_uv_clases > total_capacidad_uv_docentes:
            observaciones.append(
                f'Falta de capacidad de docentes: La carga total requerida ({total_uv_clases} UV) '
                f'supera la suma máxima que los docentes pueden impartir ({total_capacidad_uv_docentes} UV).'
            )

        if len(self.clases_list) > len(self.horas_disponibles) * len(self.aulas_list):
            observaciones.append(
                'Falta de aulas: No hay suficientes espacios físicos/horas para albergar todas las clases.'
            )

        if detalles.get('traslapes_estudiantes', 0) > 0:
            observaciones.append(
                f'Existen {detalles["traslapes_estudiantes"]} traslapes de estudiantes inevitables '
                'debido a alta coincidencia de clases censadas en la misma franja o escasez de docentes/aulas.'
            )

        if detalles.get('colisiones_docentes', 0) > 0:
            observaciones.append(
                'Conflicto de docente simultáneo: No hay suficientes docentes distintos para cubrir las materias requeridas.'
            )

        return {
            'es_optimo': es_optimo,
            'fitness_final': mejor.fitness,
            'generaciones': generaciones_ejecutadas,
            'traslapes_estudiantes': detalles.get('traslapes_estudiantes', 0),
            'detalles_traslapes_estudiantes': detalles.get('detalles_traslapes_estudiantes', []),
            'colisiones_docentes': detalles.get('colisiones_docentes', 0),
            'colisiones_aulas': detalles.get('colisiones_aulas', 0),
            'violaciones_horario_docente': detalles.get('violaciones_horario_docente', 0),
            'violaciones_capacidad_aula': detalles.get('violaciones_capacidad_aula', 0),
            'exceso_uv_total': detalles.get('exceso_uv_total', 0),
            'detalles_exceso_uv': detalles.get('detalles_exceso_uv', {}),
            'conteo_preferencias': detalles.get('conteo_preferencias', {}),
            'observaciones': observaciones,
            'total_clases': len(self.clases_list),
            'total_docentes': len(self.docentes_list),
            'total_aulas': len(self.aulas_list),
            'total_estudiantes_censo': len(self.estudiante_clases),
        }
