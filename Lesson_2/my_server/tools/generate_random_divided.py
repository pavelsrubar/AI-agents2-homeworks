import random

def generate_random_divided(minimum: str, maximum: str, divisor: str) -> dict:
    """Generates a random number in range and divides it."""
    divisor_int = int(divisor)
    random_num = random.randint(int(minimum), int(maximum))
    result = random_num / divisor_int
    
    return {
        "random_number": random_num,
        "divisor": divisor,
        "result": result
    }