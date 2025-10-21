import random
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set
from decimal import Decimal, getcontext
from ..interfaces import IGenerator
from ...models.fei import FEIEvent
from ...parsers.interfaces import IParser


class HeatmapGenerator(IGenerator):
    """
    Gera uma carga de trabalho sintética com base em um heatmap percentual,
    aprendendo padrões localizados para frequência de operações, popularidade de
    recursos por comando, e ritmo de chegada para cada intervalo.
    """
    def __init__(
        self,
        parser: IParser,
        percentage_interval: float = 5.0,
        simulation_duration_s: int = 30,
        time_expansion_strategy: str = 'cyclic'
    ):
        if not (0 < percentage_interval <= 100):
            raise ValueError(f"O intervalo percentual deve estar entre 0 (exclusivo) e 100.: {percentage_interval}")
        if time_expansion_strategy not in ['cyclic', 'expand']:
            raise ValueError(f"time_expansion_strategy must be 'cyclic' or 'stretch', not '{time_expansion_strategy}'")

        self.parser = parser
        self.interval = Decimal(str(percentage_interval))
        self.simulation_duration_s = simulation_duration_s
        self.simulation_duration_ms = simulation_duration_s * 1000
        self.time_expansion_strategy = time_expansion_strategy

    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        model = self._characterize(events)
        synthetic_events = self._synthesize(model)
        return synthetic_events

    def _characterize(self, events: List[FEIEvent]) -> Dict[str, Any]:
        """
        Analisa o rastro real, aprendendo a probabilidade de recursos DADO
        um tipo de operação e um intervalo de tempo.
        """
        print("--- Characterization Phase: Building model with command-specific resource patterns ---")
        if not events:
            raise ValueError("Cannot characterize an empty list of events.")

        getcontext().prec = 28
        events.sort(key=lambda e: e['timestamp'])

        start_ts = Decimal(str(events[0]['timestamp']))
        end_ts = Decimal(str(events[-1]['timestamp']))
        total_duration_ms = (end_ts - start_ts) * 1000
        if total_duration_ms == 0: total_duration_ms = Decimal(1)

        target_counts = defaultdict(lambda: defaultdict(Counter))
        inter_arrival_counts = defaultdict(Counter)
        all_op_semantics = {}
        all_targets: Set[str] = set()
        all_client_ids: Set[str] = set()

        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i+1]

            relative_ts_ms = (Decimal(str(current_event['timestamp'])) - start_ts) * 1000
            delta_ms = (Decimal(str(next_event['timestamp'])) - Decimal(str(current_event['timestamp']))) * 1000

            percentage_complete = (relative_ts_ms / total_duration_ms) * 100
            if percentage_complete >= 100:
                percentage_complete = Decimal("99.9999999999")

            interval_index = int(percentage_complete // self.interval)

            op_type = current_event['op_type']
            target = current_event['target']

            # Popula a nova estrutura de contagem aninhada
            target_counts[interval_index][op_type][target] += 1

            rounded_delta = round(float(delta_ms), 3)
            inter_arrival_counts[interval_index][rounded_delta] += 1

            all_targets.add(target)
            all_client_ids.add(current_event['client_id'])
            if op_type not in all_op_semantics:
                all_op_semantics[op_type] = current_event['semantic_type']

        # --- CONVERSÃO PARA PROBABILIDADES COM CORREÇÃO DE TIPO ---
        heatmap_probabilities = {}
        for interval, op_data in target_counts.items():
            total_ops_in_interval = sum(sum(op.values()) for op in op_data.values())
            if total_ops_in_interval > 0:
                # Converte a chave do intervalo para int aqui
                heatmap_probabilities[int(interval)] = {
                    op: sum(targets.values()) / total_ops_in_interval
                    for op, targets in op_data.items()
                }

        target_probabilities = defaultdict(dict)
        for interval, op_data in target_counts.items():
            # Converte a chave do intervalo para int aqui
            int_interval = int(interval)
            target_probabilities[int_interval] = {}
            for op_type, targets in op_data.items():
                total_for_op = sum(targets.values())
                if total_for_op > 0:
                    target_probabilities[int_interval][op_type] = {
                        target: count / total_for_op for target, count in targets.items()
                    }

        inter_arrival_probabilities = {
            # Converte a chave do intervalo para int aqui
            int(k): {delta: v / sum(cnts.values()) for delta, v in cnts.items()}
            for k, cnts in inter_arrival_counts.items()
        }

        print("Characterization complete.")
        return {
            "total_duration_ms": float(total_duration_ms),
            "op_semantics": all_op_semantics,
            "heatmap": heatmap_probabilities,
            "target_probabilities_by_op": dict(target_probabilities),
            "inter_arrival_probabilities": inter_arrival_probabilities,
            "initial_resource_pool": list(all_targets),
            "client_ids": list(all_client_ids) or ["default_client_1"],
        }

    def _synthesize(self, model: Dict[str, Any]) -> List[FEIEvent]:
        """Sintetiza um novo traço de eventos usando modelos de probabilidade localizados e por comando."""
        print(f"--- Synthesis Phase: Generating events for {self.simulation_duration_ms / 1000}s (strategy: {self.time_expansion_strategy}) ---")
        synthetic_events: List[FEIEvent] = []
        available_pool: Set[str] = set()

        current_time_ms = 0.0
        original_duration_ms = model['total_duration_ms']
        interval_size = float(self.interval)

        while current_time_ms < self.simulation_duration_ms:
            if self.time_expansion_strategy == 'stretch' and self.simulation_duration_ms > original_duration_ms:
                stretch_ratio = original_duration_ms / self.simulation_duration_ms
                mapped_time_ms = current_time_ms * stretch_ratio
                percentage_complete = (mapped_time_ms / original_duration_ms) * 100
            else: # Padrão é 'cyclic'
                percentage_complete = (current_time_ms % original_duration_ms) / original_duration_ms * 100

            interval_start = int(percentage_complete // interval_size) * interval_size

            valid_intervals = list(model['heatmap'].keys())
            while interval_start not in valid_intervals and interval_start > 0:
                interval_start -= int(interval_size)
            if not valid_intervals: continue
            if interval_start not in valid_intervals:
                interval_start = min(valid_intervals)

            # --- SORTEIO EM DUAS ETAPAS: OP_TYPE -> TARGET ---
            action_dist = model['heatmap'][interval_start]
            op_type = random.choices(list(action_dist.keys()), list(action_dist.values()))[0]

            target_dist = model['target_probabilities_by_op'][interval_start].get(op_type)
            if not target_dist: continue # Pula se não houver alvos aprendidos para esta operação neste intervalo
            target = random.choices(list(target_dist.keys()), list(target_dist.values()))[0]

            semantic_type_list = model['op_semantics'][op_type]

            # --- LÓGICA DE CREATE/UPDATE/DELETE BASEADA EM ESTADO ---
            is_create_update = "CREATE" in semantic_type_list and "UPDATE" in semantic_type_list
            if is_create_update:
                if target not in available_pool:
                    available_pool.add(target) # CREATE implícito

            elif "READ" in semantic_type_list:
                if target not in available_pool: continue # Não pode ler uma chave que ainda não foi criada

            elif "DELETE" in semantic_type_list:
                if target in available_pool:
                    available_pool.remove(target)
                else:
                    continue # Não pode deletar uma chave que não existe

            new_raw_args = self.parser.generate_args(op_type, target, available_pool=list(available_pool))

            synthetic_events.append(FEIEvent(
                timestamp=(current_time_ms / 1000.0),
                client_id=random.choice(model['client_ids']),
                op_type=op_type,
                semantic_type=semantic_type_list,
                target=target,
                additional_data={"raw_args": new_raw_args}
            ))

            delta_dist = model['inter_arrival_probabilities'][interval_start]
            delta_ms = random.choices(list(delta_dist.keys()), list(delta_dist.values()))[0]
            current_time_ms += delta_ms

        print(f"Synthesis complete. Generated {len(synthetic_events)} events.")
        return synthetic_events
