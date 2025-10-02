#pragma once
#include <string>
#include <memory>
#include <vector>
#include <map> 


struct Command {
    std::string op_type;
    std::string target;
    std::string client_id;
    std::map<std::string, std::vector<std::string>> additional_data;
};
struct ExecutionResult {
    long long latency_ns;
    bool success;
};

class IExecutorStrategy {
public:
    virtual ~IExecutorStrategy() = default;
    virtual void connect() = 0;
    virtual ExecutionResult execute(const Command& command) = 0;
};