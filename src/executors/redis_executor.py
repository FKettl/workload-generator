# src/executors/redis_executor.py

import re
import time
import redis
import threading
from typing import List, Tuple
from src.executors.base import IExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed

thread_local = threading.local()

class RedisExecutor(IExecutor):
    _COMMAND_REGEX = re.compile(r'"([^"]*)"')

    def __init__(self, host: str = 'localhost', port: int = 6379, max_workers: int = 1):
        self.redis_host = host
        self.redis_port = port
        self.max_workers = max_workers
        print(f"RedisExecutor inicializado para {host}:{port} com configuração max_workers={max_workers}.")

    def _get_thread_connection(self):
        if not hasattr(thread_local, 'redis_connection'):
            print(f"Thread {threading.get_ident()}: Criando nova conexão com o Redis.")
            thread_local.redis_connection = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                decode_responses=True
            )
        return thread_local.redis_connection

    def _execute_single_command(self, command_parts: List[str]) -> Tuple[float, bool]:
        try:
            r = self._get_thread_connection()
            op_start_time = time.monotonic()
            r.execute_command(*command_parts)
            op_end_time = time.monotonic()
            latency = op_end_time - op_start_time
            return (latency, True)
        except Exception:
            return (0.0, False)

    def _generate_report(self, latencies: List[float], errors: int, duration: float):
        if not latencies:
            print("\n--- RELATÓRIO DE EXECUÇÃO ---")
            print("Nenhuma operação foi executada com sucesso.")
            return

        total_ops = len(latencies)
        throughput = total_ops / duration
        latencies.sort()
        
        avg_latency_ms = (sum(latencies) / total_ops) * 1000
        min_latency_ms = latencies[0] * 1000
        max_latency_ms = latencies[-1] * 1000
        p50_latency_ms = latencies[int(total_ops * 0.5)] * 1000
        p90_latency_ms = latencies[int(total_ops * 0.9)] * 1000
        p99_latency_ms = latencies[int(total_ops * 0.99)] * 1000

        print("\n--- RELATÓRIO DE EXECUÇÃO ---")
        print(f"Tempo Total:         {duration:.2f} s")
        print(f"Operações Totais:    {total_ops}")
        print(f"Vazão (Throughput):  {throughput:.2f} ops/s")
        print(f"Erros:               {errors}")
        print("-" * 30)
        print("Latência (ms):")
        print(f"  Média:             {avg_latency_ms:.2f}")
        print(f"  Mínima:            {min_latency_ms:.2f}")
        print(f"  Máxima:            {max_latency_ms:.2f}")
        print(f"  Percentil 50 (p50):{p50_latency_ms:.2f}")
        print(f"  Percentil 90 (p90):{p90_latency_ms:.2f}")
        print(f"  Percentil 99 (p99):{p99_latency_ms:.2f}")
        print("-------------------------------\n")


    def execute(self, synthetic_trace_path: str) -> None:
        print(f"Lendo o arquivo de rastro '{synthetic_trace_path}'...")
        with open(synthetic_trace_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            print("Arquivo de rastro está vazio. Nenhuma operação para executar.")
            return

        if self.max_workers > 1:
            self._execute_multithread(lines)
        else:
            self._execute_singlethread(lines)

    def _execute_singlethread(self, lines: List[str]):
        print("Executando em modo single-thread (1 para 1).")
        
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            r.ping()
        except redis.exceptions.ConnectionError as e:
            print(f"ERRO: Não foi possível conectar ao Redis em {self.redis_host}:{self.redis_port}. {e}")
            return

        latencies = []
        errors = 0
        
        try:
            trace_start_timestamp = float(lines[0].strip().split(' ', 1)[0])
        except (ValueError, IndexError):
            print("ERRO: Não foi possível ler o timestamp da primeira linha do rastro.")
            return
            
        benchmark_start_time = time.monotonic()

        for line in lines:
            line_content = line.strip()
            if not line_content: continue
            try:
                timestamp_str, rest_of_line = line_content.split(' ', 1)
                current_trace_timestamp = float(timestamp_str)
            except ValueError: continue
            
            target_elapsed = current_trace_timestamp - trace_start_timestamp
            actual_elapsed = time.monotonic() - benchmark_start_time
            delay = target_elapsed - actual_elapsed

            if delay > 0:
                time.sleep(delay)

            command_parts = self._COMMAND_REGEX.findall(rest_of_line)
            if not command_parts: continue

            op_start_time = time.monotonic()
            try:
                r.execute_command(*command_parts)
                latencies.append(time.monotonic() - op_start_time)
            except Exception:
                errors += 1
        
        total_duration = time.monotonic() - benchmark_start_time
        self._generate_report(latencies, errors, total_duration)

    def _execute_multithread(self, lines: List[str]):
        print(f"Executando em modo multi-thread com {self.max_workers} workers.")
        
        try:
            trace_start_timestamp = float(lines[0].strip().split(' ', 1)[0])
        except (ValueError, IndexError):
            print("ERRO: Não foi possível ler o timestamp da primeira linha do rastro.")
            return

        benchmark_start_time = time.monotonic()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for line in lines:
                line_content = line.strip()
                if not line_content: continue
                try:
                    timestamp_str, rest_of_line = line_content.split(' ', 1)
                    current_trace_timestamp = float(timestamp_str)
                except ValueError: continue
                
                target_elapsed = current_trace_timestamp - trace_start_timestamp
                actual_elapsed = time.monotonic() - benchmark_start_time
                delay = target_elapsed - actual_elapsed
                if delay > 0:
                    time.sleep(delay)

                command_parts = self._COMMAND_REGEX.findall(rest_of_line)
                if command_parts:
                    future = executor.submit(self._execute_single_command, command_parts)
                    futures.append(future)

            print("Rastro completamente despachado. Aguardando conclusão das operações...")
            
            latencies = []
            errors = 0
            for future in as_completed(futures):
                latency, success = future.result()
                if success:
                    latencies.append(latency)
                else:
                    errors += 1
        
        total_duration = time.monotonic() - benchmark_start_time
        self._generate_report(latencies, errors, total_duration)