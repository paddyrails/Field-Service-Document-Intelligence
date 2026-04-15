import pybreaker

bu1_breaker = pybreaker.CircuitBreaker(
    fail_max=5, # open after 5 failures
    reset_timeout=30,
    name="bu1"
)
bu2_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="bu2")
bu3_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="bu2")
bu4_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="bu2")
bu5_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30, name="bu2")