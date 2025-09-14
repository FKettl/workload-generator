# src/generators/replay_generator.py
import json
from src.generators.base import IGenerator

class ReplayGenerator(IGenerator):
    """
    Uma estratégia de geração simples que recria o log original
    a partir de um arquivo FEI. É um gerador de 'replay' 1 para 1.
    """
    def generate(self, input_fei_path: str, output_log_path: str):
        print(f"Usando ReplayGenerator para gerar '{output_log_path}'...")
        
        # Carrega os eventos do arquivo JSON
        with open(input_fei_path, 'r', encoding='utf-8') as f:
            events = json.load(f)

        print(f"Lidos {len(events)} eventos de '{input_fei_path}'.")

        # Gera o novo arquivo de log
        with open(output_log_path, 'w', encoding='utf-8') as f:
            for event in events:
                op = f'"{event["tipo_operacao"]}"'
                alvo = f'"{event["recurso_alvo"]}"'
                additional_args = event['dados_adicionais'].get('raw_args', [])
                formatted_args = [f'"{arg}"' for arg in additional_args]
                full_command = ' '.join([op, alvo] + formatted_args)
                
                new_line = f"{event['timestamp']:.6f} [info] {full_command.strip()}"
                f.write(new_line + '\n')