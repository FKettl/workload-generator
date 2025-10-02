#include "redis.h"
#include <sw/redis++/redis++.h>
#include <chrono>
#include <vector>
#include <iterator>
#include <iostream>

RedisExecutorStrategy::RedisExecutorStrategy() = default;
RedisExecutorStrategy::~RedisExecutorStrategy() = default;

void RedisExecutorStrategy::connect() {
    m_redis_client = std::make_unique<sw::redis::Redis>("tcp://127.0.0.1:6379");
}

ExecutionResult RedisExecutorStrategy::execute(const Command& command) {
    try {
        auto op_start = std::chrono::steady_clock::now();

        const auto& args_map = command.additional_data;
        const auto it = args_map.find("raw_args");
        const std::vector<std::string> raw_args = (it != args_map.end()) ? it->second : std::vector<std::string>();

        if (command.op_type == "HMSET") {
            if (!raw_args.empty() && raw_args.size() % 2 == 0) {
                std::vector<std::pair<std::string, std::string>> field_values;
                for (size_t i = 0; i < raw_args.size(); i += 2) {
                    field_values.emplace_back(raw_args[i], raw_args[i + 1]);
                }
                m_redis_client->hmset(command.target, field_values.begin(), field_values.end());
            }
        } else if (command.op_type == "SET") {
            if (!raw_args.empty()) {
                m_redis_client->set(command.target, raw_args[0]);
            }
        } else if (command.op_type == "GET") {
            m_redis_client->get(command.target);
        } else if (command.op_type == "HGETALL") {
            std::vector<std::pair<std::string, std::string>> result;
            // Passamos o container para a função usando um std::back_inserter.
            m_redis_client->hgetall(command.target, std::back_inserter(result));
        } else if (command.op_type == "DEL") {
            m_redis_client->del(command.target);
        } else if (command.op_type == "ZADD") {
            // ZADD espera (score, member). O rastro do YCSB pode ter score científico.
            if (raw_args.size() >= 2) {
                // A biblioteca espera (member, score)
                m_redis_client->zadd(command.target, raw_args[1], std::stod(raw_args[0]));
            }
        }
        // Adicione outros comandos do Redis aqui conforme necessário...

        auto op_end = std::chrono::steady_clock::now();
        auto latency = std::chrono::duration_cast<std::chrono::nanoseconds>(op_end - op_start).count();
        return {latency, true};
    } catch (const std::exception& e) {
        std::cerr << "ERRO ao executar comando [" << command.op_type << "] no alvo [" << command.target << "]: " << e.what() << std::endl;
        return {0, false};
    }
}