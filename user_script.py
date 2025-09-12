from executor import entrypoint

@entrypoint
def greet(name, age, city="Unknown"):
    return f"Hello {name} ({age}) from {city}!"