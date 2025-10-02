#include "factory.h"
#include <stdexcept>

#ifdef BUILD_REDIS_STRATEGY
    #include "redis/redis.h"
#endif

#ifdef BUILD_HTTP_STRATEGY
    #include "http/http.h"
#endif


std::unique_ptr<IExecutorStrategy> ExecutorFactory::create(const std::string& type) {
    
    // ---- LÓGICA CONDICIONAL ----
    #ifdef BUILD_REDIS_STRATEGY
        if (type == "redis") {
            return std::make_unique<RedisExecutorStrategy>();
        }
    #endif

    #ifdef BUILD_HTTP_STRATEGY
        if (type == "http") {
            return std::make_unique<HttpExecutorStrategy>();
        }
    #endif

    throw std::runtime_error("Tipo de executor desconhecido ou não compilado: " + type);
}