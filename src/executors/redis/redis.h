#pragma once
#include "base.h"
#include <memory>

namespace sw { namespace redis { class Redis; } }

class RedisExecutorStrategy : public IExecutorStrategy {
public:
    RedisExecutorStrategy();
    ~RedisExecutorStrategy();

    void connect() override;
    ExecutionResult execute(const Command& command) override;

private:
    std::unique_ptr<sw::redis::Redis> m_redis_client;
};