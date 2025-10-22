# analise_experimentos.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from typing import Optional, Tuple

# Regex ATUALIZADO para capturar o target (assumindo que é o primeiro argumento entre aspas)
LOG_REGEX = re.compile(
    r'^(?P<timestamp>\d+\.\d+)\s+'
    r'\[(?P<db>\d+)\s+(?P<client_ip>[^\]]+)\]\s+'
    r'"(?P<command>\w+)"'
    r'(?:\s+"(?P<target>[^"]*)")?' # Captura opcional do primeiro argumento como target
    r'(?P<other_args>.*)?$' # Restante dos argumentos (não usados nesta análise)
)

def parse_log_to_dataframe(filepath: str) -> Optional[pd.DataFrame]:
    """Lê um arquivo de log e o converte para um DataFrame do Pandas, incluindo o target."""
    records = []
    print(f"Analisando o arquivo: {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                match = LOG_REGEX.match(line.strip())
                if match:
                    data = match.groupdict()
                    # Ignora comandos sem target claro (ex: PING, COMMAND)
                    if data['target']: 
                        records.append({
                            'timestamp': float(data['timestamp']),
                            'command': data['command'].upper(),
                            'target': data['target'] # <- NOVO CAMPO
                        })
        
        if not records:
            print(f"AVISO: Nenhum registro válido com target encontrado em {filepath}.")
            return None

        df = pd.DataFrame(records)
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        df['inter_arrival_ms'] = df['timestamp'].diff() * 1000
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {filepath}")
        return None

# A função calculate_metrics permanece a mesma

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

# --- NOVA FUNÇÃO DE PLOTAGEM ---
def plot_resource_access_cdf(logs: dict):
    """Gera um gráfico CDF da distribuição de acesso aos recursos."""
    plt.figure(figsize=(12, 7))
    
    for name, df in logs.items():
        if df is None or df.empty or 'target' not in df.columns:
            continue
            
        # 1. Calcula a frequência de acesso para cada recurso
        target_counts = df['target'].value_counts()
        
        # 2. Calcula a frequência cumulativa
        cumulative_counts = target_counts.cumsum()
        
        # 3. Normaliza os eixos
        # Eixo Y: Proporção cumulativa de acessos (0 a 1)
        normalized_cumulative_freq = cumulative_counts / cumulative_counts.iloc[-1]
        # Eixo X: Proporção cumulativa de recursos (0 a 1), ordenados por popularidade
        normalized_rank = np.arange(1, len(target_counts) + 1) / len(target_counts)
        
        # 4. Plota a CDF
        plt.plot(normalized_rank, normalized_cumulative_freq, label=name, alpha=0.8, linewidth=1.5)

    plt.title('Distribuição Cumulativa de Acessos aos Recursos (CDF)')
    plt.xlabel('Proporção de Recursos (Ordenados por Popularidade)')
    plt.ylabel('Proporção Cumulativa de Acessos')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    # Adiciona linhas de referência (opcional, mas útil para interpretação)
    plt.axhline(0.8, color='grey', linestyle=':', linewidth=1) 
    plt.axvline(0.2, color='grey', linestyle=':', linewidth=1)
    plt.text(0.21, 0.81, 'Ex: 80% dos acessos nos 20% mais populares', color='grey')
    plt.tight_layout()
    plt.savefig('comparacao_acesso_recursos_cdf.png')
    print("Salvo: comparacao_acesso_recursos_cdf.png")
# --- FIM DA NOVA FUNÇÃO ---

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

    # --- Gráfico 2: Distribuição dos Tempos de Chegada (Histograma Log) ---
    plt.figure(figsize=(12, 7))
    for name, df in logs.items():
        if df is not None and not df['inter_arrival_ms'].dropna().empty:
            inter_arrival_data = df['inter_arrival_ms'].dropna()
            inter_arrival_data = inter_arrival_data[inter_arrival_data > 0]
            if not inter_arrival_data.empty: # Verifica se ainda há dados após filtrar
                 min_val = np.log10(inter_arrival_data.min()) if inter_arrival_data.min() > 0 else 0
                 max_val = np.log10(inter_arrival_data.max()) if inter_arrival_data.max() > 0 else 0
                 if max_val > min_val: # Garante que haja um intervalo para os bins
                     bins = np.logspace(min_val, max_val, 100)
                     plt.hist(inter_arrival_data, bins=bins, alpha=0.6, label=name, density=True)

    plt.xscale('log')
    plt.title('Distribuição dos Tempos entre Ações (Escala Log)')
    plt.xlabel('Tempo (ms)')
    plt.ylabel('Densidade de Probabilidade')
    plt.legend()
    plt.tight_layout()
    plt.savefig('comparacao_distribuicao_tempos_logscale.png')
    print("Salvo: comparacao_distribuicao_tempos_logscale.png")

    # --- Gráfico 3: Operações ao Longo do Tempo ---
    plt.figure(figsize=(12, 7))
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
            full_index = pd.RangeIndex(start=0, stop=max_duration + 1)
            ops_over_time = ops_over_time.reindex(full_index, fill_value=0)
            plt.plot(ops_over_time.index, ops_over_time.values, label=name, alpha=0.8, linewidth=1.5)

    plt.title('Operações por Segundo ao Longo do Tempo')
    plt.xlabel('Tempo (segundos)')
    plt.ylabel('Número de Operações')
    plt.legend()
    plt.tight_layout()
    plt.savefig('comparacao_vazao_temporal_corrigido.png')
    print("Salvo: comparacao_vazao_temporal_corrigido.png")

    # --- NOVO: Chama a função para plotar a CDF de acesso aos recursos ---
    plot_resource_access_cdf(logs)
    # --- FIM DA CHAMADA ---
    
    plt.close('all')

# O __main__ permanece o mesmo
if __name__ == '__main__':
    # --- CONFIGURE OS CAMINHOS DOS ARQUIVOS AQUI ---
    path_log_inicial = 'logs/input/trace.log' 
    path_log_gerado = 'logs/output/synthetic_trace.log'
    path_log_recebido = 'logs/output/executor_heatmap_final.log'
    # --- FIM DA CONFIGURAÇÃO ---

    df_inicial = parse_log_to_dataframe(path_log_inicial)
    df_gerado = parse_log_to_dataframe(path_log_gerado)
    #df_recebido = parse_log_to_dataframe(path_log_recebido)

    logs_data = {
        'Inicial (YCSB)': df_inicial,
        'Gerado (Ferramenta)': df_gerado,
        #'Recebido (Executor)': df_recebido,
    }
    
    for name, df in logs_data.items():
        calculate_metrics(df, name)
        
    plot_comparisons(logs_data) # Agora vai gerar 4 gráficos