# analise_experimentos.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from typing import Optional

# Regex para extrair informações do log no formato do MONITOR do Redis
LOG_REGEX = re.compile(
    r'^(?P<timestamp>\d+\.\d+)\s+'
    r'\[(?P<db>\d+)\s+(?P<client_ip>[^\]]+)\]\s+'
    r'"(?P<command>\w+)"(\s+(?P<args>.*))?$'
)

def parse_log_to_dataframe(filepath: str) -> Optional[pd.DataFrame]:
    """Lê um arquivo de log e o converte para um DataFrame do Pandas."""
    records = []
    print(f"Analisando o arquivo: {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                match = LOG_REGEX.match(line.strip())
                if match:
                    data = match.groupdict()
                    records.append({
                        'timestamp': float(data['timestamp']),
                        'command': data['command'].upper(),
                    })
        
        if not records:
            print(f"AVISO: Nenhum registro válido encontrado em {filepath}.")
            return None

        df = pd.DataFrame(records)
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        # Calcula o tempo entre as ações (inter-arrival time) em milissegundos
        df['inter_arrival_ms'] = df['timestamp'].diff() * 1000
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {filepath}")
        return None

def calculate_metrics(df: pd.DataFrame, name: str):
    """Calcula e imprime as métricas estatísticas para um DataFrame."""
    if df is None or df.empty:
        print(f"\n--- Métricas para {name} ---")
        print("DataFrame vazio, não foi possível calcular as métricas.")
        return

    duration_s = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
    total_ops = len(df)
    throughput = total_ops / duration_s if duration_s > 0 else 0
    
    # Proporção de comandos
    proportions = df['command'].value_counts(normalize=True)
    
    print(f"\n--- Métricas para {name} ---")
    print(f"Duração Total: {duration_s:.2f} segundos")
    print(f"Total de Operações: {total_ops}")
    print(f"Vazão (Throughput): {throughput:.2f} ops/segundo")
    
    print("\nPercentis de Tempo entre Ações (ms):")
    print(df['inter_arrival_ms'].describe(percentiles=[.5, .9, .95, .99]))
    
    print("\nProporção das Operações:")
    print(proportions)
    print("-" * 30)

def plot_comparisons(logs: dict):
    """Gera e salva gráficos comparativos para os logs analisados."""
    print("\nGerando gráficos comparativos...")
    
    # --- Gráfico 1: Comparação da Proporção de Comandos ---
    plt.figure(figsize=(12, 7))
    
    all_commands = set()
    for df in logs.values():
        if df is not None:
            all_commands.update(df['command'].unique())

    df_proportions = pd.DataFrame({
        name: df['command'].value_counts(normalize=True) for name, df in logs.items() if df is not None
    }).fillna(0)

    df_proportions.plot(kind='bar', ax=plt.gca())
    plt.title('Comparação da Proporção de Comandos')
    plt.ylabel('Proporção')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('comparacao_proporcao_comandos.png')
    print("Salvo: comparacao_proporcao_comandos.png")

# --- Gráfico 2: Distribuição dos Tempos de Chegada (Histograma) ---
    plt.figure(figsize=(12, 7))
    for name, df in logs.items():
        if df is not None and not df.empty:
            # Usaremos o log dos dados para melhor visualização,
            # adicionando um valor pequeno para evitar log(0).
            inter_arrival_data = df['inter_arrival_ms'].dropna()
            # Filtra valores negativos ou zero que podem ocorrer
            inter_arrival_data = inter_arrival_data[inter_arrival_data > 0]
            
            # Cria bins em escala logarítmica
            bins = np.logspace(np.log10(inter_arrival_data.min()),
                              np.log10(inter_arrival_data.max()), 100)
            
            plt.hist(inter_arrival_data, bins=bins, alpha=0.6, label=name, density=True)

    plt.xscale('log')
    plt.title('Distribuição dos Tempos entre Ações (Escala Log)')
    plt.xlabel('Tempo (ms)')
    plt.ylabel('Densidade de Probabilidade')
    plt.legend()
    plt.tight_layout()
    plt.savefig('comparacao_distribuicao_tempos_logscale.png')
    print("Salvo: comparacao_distribuicao_tempos_logscale.png")

# --- Gráfico 3: Operações ao Longo do Tempo (CORRIGIDO) ---
    plt.figure(figsize=(12, 7))
    
    # Encontra a duração máxima entre todos os logs para alinhar os eixos
    max_duration = 0
    for df in logs.values():
        if df is not None and not df.empty:
            duration = int(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0])
            if duration > max_duration:
                max_duration = duration

    for name, df in logs.items():
        if df is not None and not df.empty:
            relative_time = df['timestamp'] - df['timestamp'].iloc[0]
            ops_over_time = relative_time.groupby(relative_time.astype(int)).count()
            
            # --- CORREÇÃO: Garante que todos os segundos estejam presentes ---
            # Cria um novo índice com todos os segundos de 0 até a duração máxima
            full_index = pd.RangeIndex(start=0, stop=max_duration + 1)
            # Reindexa os dados, preenchendo os segundos sem operações com 0
            ops_over_time = ops_over_time.reindex(full_index, fill_value=0)
            # --- FIM DA CORREÇÃO ---

            plt.plot(ops_over_time.index, ops_over_time.values, label=name, alpha=0.8, linewidth=1.5)

    plt.title('Operações por Segundo ao Longo do Tempo')
    plt.xlabel('Tempo (segundos)')
    plt.ylabel('Número de Operações')
    plt.legend()
    plt.tight_layout()
    plt.savefig('comparacao_vazao_temporal_corrigido.png')
    print("Salvo: comparacao_vazao_temporal_corrigido.png")
    plt.close('all')

if __name__ == '__main__':
    # --- CONFIGURE OS CAMINHOS DOS ARQUIVOS AQUI ---
    # Log original gerado pelo YCSB + MONITOR
    path_log_inicial = 'logs/input/trace.log' 
    
    # Log sintético gerado pela sua ferramenta (Python)
    path_log_gerado = 'logs/output/synthetic_trace.log'
    
    # Log capturado no notebook enquanto o executor C++ rodava
    # Você precisará gerar este arquivo usando 'redis-cli MONITOR > log_recebido.log'
    # no notebook durante o experimento.
    path_log_recebido = 'logs/output/executor_heatmap_final.log'
    # --- FIM DA CONFIGURAÇÃO ---

    df_inicial = parse_log_to_dataframe(path_log_inicial)
    df_gerado = parse_log_to_dataframe(path_log_gerado)
    df_recebido = parse_log_to_dataframe(path_log_recebido)

    logs_data = {
        'Inicial (YCSB)': df_inicial,
        'Gerado (Ferramenta)': df_gerado,
        'Recebido (Executor)': df_recebido,
    }
    
    for name, df in logs_data.items():
        calculate_metrics(df, name)
        
    plot_comparisons(logs_data)