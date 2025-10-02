#pragma once
#include "base.h" // Atualizado
#include <string>
#include <memory>

class ExecutorFactory {
public:
    static std::unique_ptr<IExecutorStrategy> create(const std::string& type);
};