# Circuit Breaker Pattern Implementation

## Overview

The Circuit Breaker pattern is implemented to prevent cascading failures when external services (like CoinGecko API) become unavailable. Our implementation provides both in-memory and persistent storage options.

## Why Circuit Breaker without Redis?

For production environments, an in-memory Circuit Breaker is often the best choice when:

1. **Single-instance applications** - No need for distributed state
2. **Microservices architecture** - Each service protects itself independently
3. **Stateless applications** - Each instance manages its own circuit breakers
4. **Simplicity is key** - No external dependencies, lower latency

## Implementation Options

### 1. In-Memory Circuit Breaker (Default)

```python
from src.infrastructure.circuit_breaker.breaker import CircuitBreaker

# Create a simple in-memory circuit breaker
breaker = CircuitBreaker(
    name="external-api",
    failure_threshold=5,
    recovery_timeout=60
)
```

**Advantages:**
- Zero external dependencies
- Minimal latency
- Simple and reliable
- Perfect for most use cases

**Use when:**
- Running single instances
- Each instance can have independent state
- You want maximum performance

### 2. Persistent Circuit Breaker

```python
from src.infrastructure.circuit_breaker.persistent_breaker import PersistentCircuitBreaker

# Create a circuit breaker with file-based persistence
breaker = PersistentCircuitBreaker(
    name="external-api",
    failure_threshold=5,
    recovery_timeout=60,
    state_dir="/var/lib/app/circuit_breakers"
)
```

**Advantages:**
- Survives application restarts
- Can share state via shared filesystem
- Good for scheduled jobs

**Use when:**
- Need to maintain state across restarts
- Running batch jobs or scheduled tasks
- Want to analyze historical patterns

### 3. Circuit Breaker Factory

```python
from src.infrastructure.circuit_breaker.factory import CircuitBreakerFactory

# Create circuit breakers using factory
breaker = CircuitBreakerFactory.create(
    name="coingecko",
    failure_threshold=5,
    recovery_timeout=60,
    persistent=False  # or True for persistent
)

# Get statistics for all breakers
stats = CircuitBreakerFactory.get_all_stats()
```

## Circuit Breaker States

1. **CLOSED** - Normal operation, requests pass through
2. **OPEN** - Failure threshold exceeded, requests fail immediately
3. **HALF_OPEN** - Testing if service recovered, limited requests allowed

## Configuration

Environment variables:
```bash
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5  # Failures before opening
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60  # Seconds before trying recovery
```

## Monitoring

### Prometheus Metrics

The circuit breaker exposes these metrics:
- `circuit_breaker_state{service="name"}` - Current state (0=closed, 1=open, 2=half-open)

### API Endpoints

```bash
# Get all circuit breakers status
GET /api/v1/circuit-breakers/stats

# Get specific circuit breaker status
GET /api/v1/circuit-breakers/stats/{name}

# Reset circuit breaker (admin only)
POST /api/v1/circuit-breakers/reset/{name}
```

## Example Response

```json
{
  "name": "coingecko",
  "state": "closed",
  "failure_count": 0,
  "success_count": 150,
  "total_calls": 150,
  "failure_threshold": 5,
  "recovery_timeout": 60,
  "last_failure_time": null
}
```

## Best Practices

1. **Set appropriate thresholds** - Too low causes unnecessary opens, too high defeats the purpose
2. **Monitor circuit breaker metrics** - Track state changes and failure patterns
3. **Test failure scenarios** - Ensure your app handles open circuits gracefully
4. **Log state transitions** - Helps with debugging and analysis
5. **Use factory pattern** - Centralizes creation and management

## Production Deployment Strategies

### Single Instance
```yaml
# docker-compose.yml
services:
  app:
    image: crypto-api
    environment:
      - CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
      - CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Multiple Instances (Independent State)
```yaml
# docker-compose.yml
services:
  app:
    image: crypto-api
    deploy:
      replicas: 3
    # Each replica has its own circuit breaker state
```

### Multiple Instances (Shared State via Files)
```yaml
# docker-compose.yml
services:
  app:
    image: crypto-api
    deploy:
      replicas: 3
    volumes:
      - circuit-breaker-state:/var/lib/app/circuit_breakers
    environment:
      - CIRCUIT_BREAKER_PERSISTENT=true
```

## When to Use Redis-backed Circuit Breaker

Consider Redis only when you need:

1. **Strongly consistent state** across all instances
2. **Real-time synchronization** of circuit state
3. **Complex distributed systems** with shared dependencies
4. **Cross-service circuit breaking** (Service A opens circuit for Service B)

For most applications, the in-memory implementation is sufficient and provides better performance with less complexity.

## Testing Circuit Breakers

```python
# Unit test example
async def test_circuit_breaker():
    breaker = CircuitBreaker(name="test", failure_threshold=2)
    
    # Simulate failures
    with pytest.raises(Exception):
        await breaker.call(failing_function)
    
    # Check state
    assert breaker.get_stats()["state"] == "open"
```

## Troubleshooting

### Circuit breaker stays open
- Check recovery timeout setting
- Verify the external service is actually recovered
- Check logs for state transition attempts

### Too many false positives
- Increase failure threshold
- Check if timeouts are too aggressive
- Verify expected exceptions are configured correctly

### Performance impact
- Use in-memory implementation
- Avoid persistent storage unless necessary
- Monitor circuit breaker overhead in metrics