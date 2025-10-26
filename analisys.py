# analise_experimentos.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from typing import Optional, Tuple, Dict, List # Import Dict, List

# Regex ATUALIZADO para capturar o target (primeiro argumento entre aspas após o comando)
LOG_REGEX = re.compile(
    r'^(?P<timestamp>\d+\.\d+)\s+'
    r'\[(?P<db>\d+)\s+(?P<client_ip>[^\]]+)\]\s+'
    r'"(?P<command>\w+)"'
    r'(?:\s+"(?P<target>[^"]*)")?' # Captura opcional do primeiro argumento como target
    r'(?P<other_args>.*)?$' # Restante (não usado aqui)
)

def parse_log_to_dataframe(filepath: str) -> Optional[pd.DataFrame]:
    """Lê um arquivo de log e o converte para um DataFrame do Pandas, incluindo o target."""
    records = []
    print(f"Analisando o arquivo: {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = LOG_REGEX.match(line.strip())
                if match:
                    data = match.groupdict()
                    # Inclui apenas eventos que possuem um target identificado
                    # e ignora comandos como CLIENT que não são relevantes para workload
                    if data['target'] and data['command'].upper() != 'CLIENT':
                        records.append({
                            'timestamp': float(data['timestamp']),
                            'command': data['command'].upper(),
                            'target': data['target'] # <- NOVO CAMPO EXTRAÍDO
                        })
                # Opcional: Adicionar um else para logar linhas não reconhecidas, se necessário
                # else:
                #     if line.strip(): # Ignora linhas em branco
                #         print(f"[WARN] Linha {line_num} não correspondeu ao padrão regex: {line.strip()}")

        if not records:
            print(f"AVISO: Nenhum registro válido com target encontrado em {filepath}.")
            return None

        df = pd.DataFrame(records)
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        # Calcula o tempo entre as ações (inter-arrival time) em milissegundos
        df['inter_arrival_ms'] = df['timestamp'].diff() * 1000
        # Remove a primeira linha NaN criada por diff()
        df = df.iloc[1:]
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {filepath}")
        return None
    except Exception as e:
        print(f"ERRO inesperado ao processar {filepath}: {e}")
        return None


def calculate_metrics(df: pd.DataFrame, name: str):
    """Calcula e imprime as métricas estatísticas para um DataFrame."""
    if df is None or df.empty:
        print(f"\n--- Métricas para {name} ---")
        print("DataFrame vazio, não foi possível calcular as métricas.")
        return

    # Recalcula a duração com base nos timestamps restantes após remover a primeira linha
    duration_s = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0] if len(df) > 1 else 0
    total_ops = len(df)
    throughput = total_ops / duration_s if duration_s > 0 else 0

    # Proporção de comandos
    proportions = df['command'].value_counts(normalize=True)

    print(f"\n--- Métricas para {name} ---")
    print(f"Duração Total (análise): {duration_s:.2f} segundos")
    print(f"Total de Operações (análise): {total_ops}")
    print(f"Vazão (Throughput): {throughput:.2f} ops/segundo")

    # Calcula percentis apenas se houver dados de inter_arrival_ms
    inter_arrival_data = df['inter_arrival_ms'].dropna()
    if not inter_arrival_data.empty:
        print("\nPercentis de Tempo entre Ações (ms):")
        # Mostra mais percentis relevantes
        print(inter_arrival_data.describe(percentiles=[.5, .75, .9, .95, .99, .999]))
    else:
        print("\nPercentis de Tempo entre Ações (ms): Não há dados suficientes.")

    print("\nProporção das Operações:")
    print(proportions)

    # Informação sobre recursos únicos
    if 'target' in df.columns:
         unique_targets = df['target'].nunique()
         print(f"Número de Recursos Únicos Acessados: {unique_targets}")

    print("-" * 30)


def plot_combined_comparisons(logs: Dict[str, Optional[pd.DataFrame]], experiment_name: str, path):
    """
    Gera e salva UMA figura contendo os 4 gráficos comparativos
    para os logs analisados (Inicial, Gerado, Recebido).
    
    --- MODIFICADO para melhor visibilidade de sobreposição ---
    """
    print(f"\nGerando gráfico combinado para o experimento: {experiment_name}...")

    # --- NOVO: Mapa de estilos para controlar a visualização ---
    # Define estilos específicos para cada log para resolver a sobreposição
    style_map = {
        'Inicial': {
            'color': 'C0', # Azul
            'hist_kwargs': {'alpha': 0.6, 'histtype': 'bar'},
            'line_kwargs': {'linestyle': '-', 'alpha': 0.7, 'linewidth': 1.5}
        },
        'Gerado': {
            'color': 'C1', # Laranja
            'hist_kwargs': {'alpha': 0.9, 'histtype': 'step', 'linewidth': 2.0}, # Contorno
            'line_kwargs': {'linestyle': '--', 'alpha': 1.0, 'linewidth': 2.0} # Tracejado e grosso
        },
        'Recebido': {
            'color': 'C2', # Verde
            'hist_kwargs': {'alpha': 0.9, 'histtype': 'step', 'linewidth': 1.5}, # Contorno
            'line_kwargs': {'linestyle': '-', 'alpha': 0.9, 'linewidth': 1.5} # Sólido
        }
    }
    # Estilo padrão caso um nome de log não esteja no mapa
    default_style = style_map['Inicial']
    # --- FIM DA ADIÇÃO ---


    # Cria a grade 2x2 de subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12)) 
    fig.suptitle(f'Análise Comparativa - Experimento: {experiment_name}', fontsize=16)

    # --- Gráfico 1: Comparação da Proporção de Comandos (axes[0, 0]) ---
    ax1 = axes[0, 0]
    all_commands = set()
    plot_data_g1 = {}
    valid_logs_g1 = {name: df for name, df in logs.items() if df is not None and not df.empty and 'command' in df.columns}

    if not valid_logs_g1:
        ax1.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
        print("Aviso: Não há dados para gerar o gráfico de proporção de comandos.")
    else:
        for df in valid_logs_g1.values():
            all_commands.update(df['command'].unique())
        df_proportions = pd.DataFrame({
            name: df['command'].value_counts(normalize=True) for name, df in valid_logs_g1.items()
        }).fillna(0)
        
        # --- MODIFICADO: Adiciona 'edgecolor' para melhor distinção ---
        df_proportions.plot(kind='bar', ax=ax1, title='Proporção de Comandos', 
                            edgecolor='black', linewidth=0.7)
        ax1.set_ylabel('Proporção')
        ax1.tick_params(axis='x', rotation=45, labelsize=8)
        ax1.legend(fontsize=9)

    # --- Gráfico 2: Distribuição dos Tempos de Chegada (Histograma Log) (axes[0, 1]) ---
    ax2 = axes[0, 1]
    plot_successful_g2 = False
    for name, df in logs.items():
        if df is not None and not df['inter_arrival_ms'].dropna().empty:
            inter_arrival_data = df['inter_arrival_ms'].dropna()
            inter_arrival_data = inter_arrival_data[inter_arrival_data > 0]
            if not inter_arrival_data.empty:
                 min_val = np.log10(inter_arrival_data.min()) if inter_arrival_data.min() > 0 else -6 
                 max_val = np.log10(inter_arrival_data.max()) if inter_arrival_data.max() > 0 else 5 

                 if np.isfinite(min_val) and np.isfinite(max_val) and max_val > min_val:
                     bins = np.logspace(min_val, max_val, 50)
                     
                     # --- MODIFICADO: Usa o style_map para plotar ---
                     style = style_map.get(name, default_style)
                     ax2.hist(inter_arrival_data, bins=bins, label=name, density=True,
                              color=style['color'], 
                              **style['hist_kwargs']) # Desempacota os kwargs (histtype, alpha, etc)
                     plot_successful_g2 = True
                     
                 elif not inter_arrival_data.empty:
                      # Fallback para escala linear
                      style = style_map.get(name, default_style)
                      ax2.hist(inter_arrival_data, bins=10, label=f"{name} (linear)", density=True,
                               color=style['color'],
                               **style['hist_kwargs'])
                      print(f"Aviso: Usando escala linear para hist de '{name}' devido a dados limitados.")
                      plot_successful_g2 = True

    if not plot_successful_g2:
         ax2.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
         print("Aviso: Não há dados válidos para gerar o histograma de tempos de chegada.")
    else:
        ax2.set_xscale('log')
        ax2.set_title('Distribuição Tempos Chegada (Escala Log)')
        ax2.set_xlabel('Tempo (ms)')
        ax2.set_ylabel('Densidade de Probabilidade')
        ax2.legend(fontsize=9)

    # --- Gráfico 3: Operações ao Longo do Tempo (axes[1, 0]) ---
    ax3 = axes[1, 0]
    max_duration = 0
    plot_successful_g3 = False
    valid_logs_g3 = {name: df for name, df in logs.items() if df is not None and not df.empty and len(df) > 1}

    if not valid_logs_g3:
         ax3.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax3.transAxes)
         print("Aviso: Não há dados válidos para gerar o gráfico de operações ao longo do tempo.")
    else:
        for df in valid_logs_g3.values():
            duration = int(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0])
            if duration > max_duration:
                max_duration = duration
        if max_duration == 0 and any(df is not None and not df.empty for df in valid_logs_g3.values()):
            max_duration = 1 

        for name, df in valid_logs_g3.items():
            relative_time = df['timestamp'] - df['timestamp'].iloc[0]
            ops_counts = relative_time.astype(int).value_counts().sort_index()
            full_index = pd.RangeIndex(start=0, stop=max_duration + 1)
            ops_over_time = ops_counts.reindex(full_index, fill_value=0)
            if not ops_over_time.empty:
                 
                 # --- MODIFICADO: Usa o style_map para plotar ---
                 style = style_map.get(name, default_style)
                 ax3.plot(ops_over_time.index, ops_over_time.values, label=name,
                          color=style['color'],
                          **style['line_kwargs']) # Desempacota os kwargs (linestyle, alpha, etc)
                 plot_successful_g3 = True
        
        if plot_successful_g3:
             ax3.set_title('Operações por Segundo')
             ax3.set_xlabel('Tempo (segundos)')
             ax3.set_ylabel('Número de Operações')
             ax3.legend(fontsize=9)
        else:
             ax3.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax3.transAxes)
             print("Aviso: Não há dados válidos para gerar o gráfico de operações ao longo do tempo.")


    # --- Gráfico 4: CDF Acesso a Recursos (axes[1, 1]) ---
    ax4 = axes[1, 1]
    plot_successful_g4 = False
    for name, df in logs.items():
        if df is not None and not df.empty and 'target' in df.columns:
            target_counts = df['target'].value_counts()
            if not target_counts.empty:
                cumulative_counts = target_counts.cumsum()
                normalized_cumulative_freq = cumulative_counts / cumulative_counts.iloc[-1]
                normalized_rank = np.arange(1, len(target_counts) + 1) / len(target_counts)
                
                # --- MODIFICADO: Usa o style_map para plotar ---
                style = style_map.get(name, default_style)
                ax4.plot(normalized_rank, normalized_cumulative_freq.values, label=name,
                         color=style['color'],
                         **style['line_kwargs']) # Desempacota os kwargs (linestyle, alpha, etc)
                plot_successful_g4 = True

    if not plot_successful_g4:
        ax4.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax4.transAxes)
        print("Erro: Nenhum dado válido encontrado para plotar a CDF de acesso aos recursos.")
    else:
        ax4.set_title('CDF Acesso a Recursos')
        ax4.set_xlabel('Proporção Recursos (Popularidade)')
        ax4.set_ylabel('Proporção Cumulativa Acessos')
        ax4.grid(True, linestyle='--', alpha=0.6)
        ax4.legend(fontsize=9)
        ax4.axhline(0.8, color='grey', linestyle=':', linewidth=0.8)
        ax4.axvline(0.2, color='grey', linestyle=':', linewidth=0.8)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)

    # Ajusta espaçamento geral e salva a figura combinada
    plt.tight_layout(rect=[0, 0.03, 1, 0.97]) 
    
    # Cria um nome de arquivo seguro
    safe_exp_name = "".join(c if c.isalnum() else "_" for c in experiment_name)
    output_filename = f'{path}/comparacao_combinada_{safe_exp_name}.png'
    plt.savefig(output_filename)
    print(f"Salvo: {output_filename}")
    plt.close(fig) # Fecha a figura

if __name__ == '__main__':
    # --- DEFINA O NOME DO EXPERIMENTO ATUAL ---
    # Exemplos: 'Replay', 'Heatmap_1pct_Original', 'Heatmap_25pct_Original', 'Heatmap_1pct_Double_Cyclic', etc.
    current_experiment_name = 'Heatmap_1pct_Double_Stretch' # <--- MUDE AQUI PARA CADA EXPERIMENTO

    # --- CONFIGURE OS CAMINHOS DOS ARQUIVOS AQUI ---
    # Log original gerado pelo YCSB + MONITOR (geralmente o mesmo para todos)
    path_log_inicial = 'logs/input/trace.log'

    # Log sintético gerado pela sua ferramenta (Python) - Pode mudar por experimento

    # Log capturado no notebook/servidor enquanto o executor C++ rodava - MUDA POR EXPERIMENTO
    # --- FIM DA CONFIGURAÇÃO ---

    print(f"=== Iniciando análise para o experimento: {current_experiment_name} ===")
    for x in range(1, 6):
        path_log_recebido = f'logs/output/test{x}/redis_monitor_received.log' # Exemplo de nomeação
        path_log_gerado = f'logs/output/test{x}/synthetic_trace.log' # Ou um nome específico se você salvou separadamente
        df_inicial = parse_log_to_dataframe(path_log_inicial)
        df_gerado = parse_log_to_dataframe(path_log_gerado)
        df_recebido = parse_log_to_dataframe(path_log_recebido)

        logs_data = {
            'Inicial': df_inicial,         # Legendas mais curtas
            'Gerado': df_gerado,
            'Recebido': df_recebido,
        }

        # Imprime métricas antes de plotar
        for name, df in logs_data.items():
            calculate_metrics(df, f"{current_experiment_name} - {name}") # Adiciona nome do exp às métricas

        # Gera o gráfico combinado
        plot_combined_comparisons(logs_data, current_experiment_name, f'logs/output/test{x}')

    print(f"\n=== Análise concluída para o experimento: {current_experiment_name} ===")