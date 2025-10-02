#include "factory.h" // Inclui a fábrica com o novo nome
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <fstream>
#include <nlohmann/json.hpp>
#include <yaml-cpp/yaml.h> // Para ler o config.yaml
#include <algorithm>
#include <numeric>

// Estrutura para uma tarefa na fila, combinando o tempo e a ação
struct Task {
    std::chrono::steady_clock::time_point target_time;
    Command command;
};

// Fila segura para comunicação entre threads
template <typename T>
class ThreadSafeQueue {
public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_queue.push(std::move(value));
        m_cond.notify_one();
    }
    T pop() {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_cond.wait(lock, [this]{ return !m_queue.empty(); });
        T value = std::move(m_queue.front());
        m_queue.pop();
        return value;
    }
private:
    std::queue<T> m_queue;
    std::mutex m_mutex;
    std::condition_variable m_cond;
};

// Função para imprimir o relatório final
void generate_report(const std::vector<long long>& latencies_ns, std::chrono::steady_clock::duration total_duration) {
    if (latencies_ns.empty()) {
        std::cout << "\nNenhuma operação foi registrada." << std::endl;
        return;
    }
    auto sorted_latencies = latencies_ns;
    std::sort(sorted_latencies.begin(), sorted_latencies.end());
    long long total_ops = sorted_latencies.size();
    double duration_s = std::chrono::duration<double>(total_duration).count();
    double throughput = total_ops / duration_s;
    long long sum = std::accumulate(sorted_latencies.begin(), sorted_latencies.end(), 0LL);
    double avg_ns = static_cast<double>(sum) / total_ops;
    std::cout << "\n--- RELATÓRIO DE EXECUÇÃO ---" << std::endl;
    std::cout << "Tempo Total:         " << duration_s << " s" << std::endl;
    std::cout << "Operações Totais:    " << total_ops << std::endl;
    std::cout << "Vazão (Throughput):  " << throughput << " ops/s" << std::endl;
    std::cout << "------------------------------" << std::endl;
    std::cout << "Latência (ms):" << std::endl;
    std::cout << "  Média:             " << avg_ns / 1e6 << std::endl;
    std::cout << "  Mínima:            " << sorted_latencies.front() / 1e6 << std::endl;
    std::cout << "  Máxima:            " << sorted_latencies.back() / 1e6 << std::endl;
    std::cout << "  Percentil 50 (p50):" << sorted_latencies[total_ops * 0.5] / 1e6 << std::endl;
    std::cout << "  Percentil 90 (p90):" << sorted_latencies[total_ops * 0.9] / 1e6 << std::endl;
    std::cout << "  Percentil 99 (p99):" << sorted_latencies[total_ops * 0.99] / 1e6 << std::endl;
    std::cout << "------------------------------\n" << std::endl;
}

// A função da thread trabalhadora, genérica
void worker_function(int id, std::string executor_type, ThreadSafeQueue<Task>& queue, std::mutex& results_mutex, std::vector<long long>& latencies_ns) {
    try {
        std::unique_ptr<IExecutorStrategy> executor = ExecutorFactory::create(executor_type);
        executor->connect();
        while (true) {
            Task task = queue.pop();
            if (task.command.op_type == "POISON_PILL") break;
            std::this_thread::sleep_until(task.target_time);
            ExecutionResult result = executor->execute(task.command);
            if (result.success) {
                std::lock_guard<std::mutex> lock(results_mutex);
                latencies_ns.push_back(result.latency_ns);
            }   
        }
    } catch (const std::exception &e) {
        std::cerr << "Erro na Thread " << id << ": " << e.what() << std::endl;
    }
}

int main() {
    // Carrega o arquivo de configuração principal (config.yaml)
    YAML::Node config;
    try {
        // Assume que o executável será rodado de `src/cpp/build/`
        config = YAML::LoadFile("../../config.yaml"); 
    } catch (const std::exception& e) {
        std::cerr << "Erro ao carregar config.yaml: " << e.what() << std::endl;
        return 1;
    }
    
    const std::string fei_path = config["pipeline"]["fei_file"].as<std::string>();
    const std::string executor_type = config["components"]["executor"]["type"].as<std::string>();
    const int num_workers = config["components"]["executor"]["max_workers"].as<int>();

    std::ifstream f( "../../" + fei_path);
    if (!f.is_open()) {
        std::cerr << "Erro: Não foi possível abrir o arquivo FEI: " << fei_path << std::endl;
        return 1;
    }
    nlohmann::json events = nlohmann::json::parse(f);
    if (!events.is_array() || events.empty()) {
        std::cerr << "Arquivo FEI está vazio ou não é uma lista de eventos." << std::endl;
        return 0;
    }
    
    // Setup das Threads
    std::vector<ThreadSafeQueue<Task>> queues(num_workers);
    std::vector<std::thread> workers;
    std::mutex results_mutex;
    std::vector<long long> latencies_ns;

    for (int i = 0; i < num_workers; ++i) {
        workers.emplace_back(worker_function, i, executor_type, std::ref(queues[i]), std::ref(results_mutex), std::ref(latencies_ns));
    }

    // Lógica da Thread Gerente (Modo Replay)
    std::cout << "Iniciando despacho de " << events.size() << " eventos do arquivo FEI..." << std::endl;
    
    auto benchmark_start = std::chrono::steady_clock::now();
    double trace_start_timestamp = events[0]["timestamp"].get<double>();

    int worker_idx = 0;
    for (const auto& event : events) {
        Command cmd;
        cmd.op_type = event["tipo_operacao"];
        cmd.target = event["recurso_alvo"];
        cmd.client_id = event["client_id"];
        
        if (event.contains("dados_adicionais") && event["dados_adicionais"].contains("raw_args")) {
            cmd.additional_data["raw_args"] = event["dados_adicionais"]["raw_args"].get<std::vector<std::string>>();
        }

        double current_trace_timestamp = event["timestamp"].get<double>();
        long long relative_ns = static_cast<long long>((current_trace_timestamp - trace_start_timestamp) * 1e9);
        auto target_time = benchmark_start + std::chrono::nanoseconds(relative_ns);

        queues[worker_idx % num_workers].push({target_time, cmd});
        worker_idx++;
    }

    // Envia as "pílulas de veneno" para que as trabalhadoras terminem
    for (int i = 0; i < num_workers; ++i) {
        queues[i].push({{}, {"POISON_PILL", "", ""}});
    }

    // Espera todas as threads terminarem
    for (auto& worker : workers) {
        worker.join();
    }
    auto benchmark_end = std::chrono::steady_clock::now();
    
    // Gera o relatório final
    generate_report(latencies_ns, benchmark_end - benchmark_start);

    return 0;
}