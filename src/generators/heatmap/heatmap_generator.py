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
    aprendendo tanto a frequência de operações quanto o ritmo (tempos de chegada)
    de forma localizada para cada intervalo.
    """
    def __init__(
        self,
        parser: IParser,
        percentage_interval: float = 5.0,
        simulation_duration_s: int = 30
    ):
        if not (0 < percentage_interval <= 100):
            raise ValueError(f"O intervalo percentual deve estar entre 0 (exclusivo) e 100.: {percentage_interval}")
        
        self.parser = parser
        self.interval = Decimal(str(percentage_interval))
        self.simulation_duration_s = simulation_duration_s
        self.simulation_duration_ms = simulation_duration_s * 1000

    def generate(self, events: List[FEIEvent]) -> List[FEIEvent]:
        model = self._characterize(events)
        synthetic_events = self._synthesize(model)
        return synthetic_events

    def _characterize(self, events: List[FEIEvent]) -> Dict[str, Any]:
        """
        Analisa o rastro real, aprendendo todos os padrões (frequência, comportamento
        e tempos de chegada) em intervalos de PORCENTAGEM.
        """
        print("--- Characterization Phase: Building model with percentage-based intervals for all metrics ---")
        if not events:
            raise ValueError("Cannot characterize an empty list of events.")

        # Configura a precisão para os cálculos de tempo
        getcontext().prec = 28
        events.sort(key=lambda e: e['timestamp'])

        start_ts = Decimal(str(events[0]['timestamp']))
        end_ts = Decimal(str(events[-1]['timestamp']))
        total_duration_ms = (end_ts - start_ts) * 1000
        if total_duration_ms == 0: total_duration_ms = Decimal(1)

        # Estruturas de dados para o modelo
        known_keys: Set[str] = set()
        heatmap_counts = defaultdict(Counter)
        op_behavior_counts = defaultdict(lambda: defaultdict(Counter))
        inter_arrival_times_by_interval = defaultdict(list)
        all_inter_arrival_times_ms = []
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
            
            interval_start = int(percentage_complete // self.interval) * self.interval

            inter_arrival_times_by_interval[interval_start].append(float(delta_ms))
            all_inter_arrival_times_ms.append(float(delta_ms))

            op_type = current_event['op_type']
            target = current_event['target']
            semantic_types = current_event['semantic_type']
            heatmap_counts[interval_start][op_type] += 1

            if (target != ""): all_targets.add(target)
            all_client_ids.add(current_event['client_id'])

            if op_type not in all_op_semantics:
                all_op_semantics[op_type] = semantic_types

            if "CREATE" in semantic_types:
                if target not in known_keys:
                    op_behavior_counts[interval_start][op_type]['CREATE'] += 1
                    known_keys.add(target)
                else:
                    op_behavior_counts[interval_start][op_type]['UPDATE'] += 1
            if "DELETE" in semantic_types and target in known_keys:
                known_keys.remove(target)
    
        heatmap_probabilities = { int(k): {op: v / sum(cnts.values()) for op, v in cnts.items()} for k, cnts in heatmap_counts.items() }
        op_behavior_probabilities = defaultdict(dict)
        for interval, op_counts in op_behavior_counts.items():
            for op, counts in op_counts.items():
                total = sum(counts.values())
                if total > 0:
                    op_behavior_probabilities[int(interval)][op] = { 'CREATE': counts.get('CREATE', 0) / total, 'UPDATE': counts.get('UPDATE', 0) / total }

        print(f"Characterization complete. Model built with {self.interval}% intervals.")

        return {
            "interval_type": "percentage",
            "interval_size": float(self.interval),
            "total_duration_ms": float(total_duration_ms),
            "op_semantics": all_op_semantics,
            "heatmap": heatmap_probabilities,
            "inter_arrival_times_by_interval": {int(k): v for k, v in inter_arrival_times_by_interval.items()},
            "global_inter_arrival_times_ms": all_inter_arrival_times_ms or [1.0],
            "initial_resource_pool": list(all_targets),
            "client_ids": list(all_client_ids) or ["default_client_1"],
            "op_behavior_probabilities": dict(op_behavior_probabilities),
        }


    def _synthesize(self, model: Dict[str, Any]) -> List[FEIEvent]:
        """Sintetiza um novo traço de eventos usando padrões percentuais e localizados."""
        print(f"--- Synthesis Phase: Generating events for {self.simulation_duration_ms / 1000} seconds ---")
        synthetic_events: List[FEIEvent] = []
        unseen_pool: Set[str] = set(model['initial_resource_pool'])
        # Pool de chaves que existem na simulação e podem ser usadas.
        available_pool: Set[str] = set()
        # Pool de chaves que foram deletadas e podem ser recriadas.
        deleted_pool: Set[str] = set()

        current_time_ms = 0.0
        start_ts_sec = 0 
        original_duration_ms = model['total_duration_ms']
        interval_size = model['interval_size']

        while current_time_ms < self.simulation_duration_ms:
            # Determine current time interval (logic remains the same)
            timestamp = start_ts_sec + (current_time_ms / 1000.0)

            # A lógica para escolher o intervalo e a ação continua a mesma
            looping_percentage = (current_time_ms % original_duration_ms) / original_duration_ms * 100 if original_duration_ms > 0 else 0
            interval_start = int(looping_percentage // interval_size) * interval_size
            
            # Lógica de fallback
            while interval_start not in model['heatmap'] and interval_start > 0:
                interval_start -= interval_size
            if interval_start not in model['heatmap']:
                interval_start = min(model['heatmap'].keys())
            action_dist = model['heatmap'].get(interval_start)
            if not action_dist:
                interval_start = min(model['heatmap'].keys())
                action_dist = model['heatmap'][interval_start]

            op_type = random.choices(list(action_dist.keys()), list(action_dist.values()))[0]
            semantic_type_list = model['op_semantics'][op_type]
            target = None

            # Handle ambiguous operations that can be either CREATE or UPDATE
            if "CREATE" in semantic_type_list and "UPDATE" in semantic_type_list:
                # Look up the learned behavior probabilities for this specific time interval and op_type
                interval_behaviors = model['op_behavior_probabilities'].get(int(interval_start), {})
                op_behaviors = interval_behaviors.get(op_type, {'CREATE': 1.0}) # Default to CREATE if no data
                create_prob = op_behaviors.get('CREATE', 0)

                if random.random() < create_prob:
                    if unseen_pool:
                        target = unseen_pool.pop()
                    elif deleted_pool:
                        target = deleted_pool.pop()
                    else:
                        continue
                    
                    available_pool.add(target)
                else:
                    if not available_pool: continue
                    target = random.choice(list(available_pool))

            elif "READ" in semantic_type_list:
                if not available_pool: continue
                target = random.choice(list(available_pool))
            
            # Handle unambiguous DELETE operations
            elif "DELETE" in semantic_type_list:
                if not available_pool: continue
                target = random.choice(list(available_pool))
                available_pool.remove(target)
                deleted_pool.add(target)

            if target is None: continue

            new_raw_args = self.parser.generate_args(
                op_type, target, available_pool=list(available_pool)
            )
            additional_data = {"raw_args": new_raw_args}

            new_event = FEIEvent(
                timestamp=timestamp,
                client_id=random.choice(model['client_ids']),
                op_type=op_type,
                semantic_type=semantic_type_list,
                target=target,
                additional_data=additional_data
            )
            synthetic_events.append(new_event)

            interval_specific_deltas = model['inter_arrival_times_by_interval'].get(interval_start)
            if interval_specific_deltas:
                delta_ms = random.choice(interval_specific_deltas)
            else:
                delta_ms = random.choice(model['global_inter_arrival_times_ms'])
            
            # Avança o tempo da simulação para a próxima iteração.
            current_time_ms += delta_ms

        print("TIme", current_time_ms)
        print(f"Synthesis complete. Generated {len(synthetic_events)} events.")
        return synthetic_events

