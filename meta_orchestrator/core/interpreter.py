import time

class Interpreter:
    """
    A mock interpreter for a lightweight language (e.g., L0).

    This class simulates the core components needed for the Meta-Orchestrator,
    including a cache, JIT compilation markers, and timing functions.
    """
    def __init__(self):
        self._cache = {}
        self._jit_seen = set()
        print("Interpreter initialized.")

    # Primitive: Caching
    def cache_put(self, key, value):
        """Stores a value in the cache."""
        print(f"CACHE PUT: key='{key}'")
        self._cache[key] = value

    def cache_get(self, key):
        """Retrieves a value from the cache. Returns None if not found."""
        print(f"CACHE GET: key='{key}'")
        return self._cache.get(key)

    def cache_has(self, key):
        """Checks if a key exists in the cache."""
        return key in self._cache

    # Primitive: Timing
    def current_time_ms(self):
        """Returns the current time in milliseconds."""
        return int(time.time() * 1000)

    # Primitive: JIT Compilation Markers
    def jit_mark_seen(self, item):
        """Marks an item (e.g., a function or code block) as 'seen' for JIT compilation."""
        print(f"JIT MARK SEEN: item='{item}'")
        self._jit_seen.add(item)

    def jit_seen(self, item):
        """Checks if an item has been marked as 'seen' for JIT."""
        return item in self._jit_seen

    def simulate_jit_compile(self, item):
        """Simulates the JIT compilation process for an item."""
        if not self.jit_seen(item):
            print(f"JIT COMPILE: Simulating compilation for '{item}'...")
            time.sleep(0.05)  # Simulate compilation delay
            self.jit_mark_seen(item)
            return "COMPILED"
        else:
            print(f"JIT CACHE: '{item}' already compiled.")
            return "CACHED"

    def eval(self, ast_or_code):
        """
        A mock evaluation function.
        In a real scenario, this would interpret or execute code.
        Here, it just prints the code it receives.
        """
        print(f"EVAL: Executing code -> {ast_or_code}")
        # This is where the logic to interact with primitives would go.
        # For now, we just return a mock success.
        return {"success": True, "result": "mock_result"}

# Example usage:
if __name__ == "__main__":
    interpreter = Interpreter()

    # Demonstrate caching
    interpreter.cache_put("my_key", 123)
    retrieved_value = interpreter.cache_get("my_key")
    print(f"Retrieved value: {retrieved_value}")
    print(f"Has 'my_key': {interpreter.cache_has('my_key')}")
    print(f"Has 'other_key': {interpreter.cache_has('other_key')}")

    # Demonstrate timing
    start_time = interpreter.current_time_ms()
    time.sleep(0.1)
    end_time = interpreter.current_time_ms()
    print(f"Elapsed time: {end_time - start_time} ms")

    # Demonstrate JIT simulation
    interpreter.simulate_jit_compile("my_function")
    interpreter.simulate_jit_compile("my_function") # Should be cached
    print(f"JIT seen 'my_function': {interpreter.jit_seen('my_function')}")
    print(f"JIT seen 'another_function': {interpreter.jit_seen('another_function')}")