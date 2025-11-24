import random

def generate_random_multiplied(minimum: str, maximum: str, multiplier: str) -> dict:
    """Generates a random number in range and multiplies it."""
    multiplier_int = int(multiplier)
    random_num = random.randint(int(minimum), int(maximum))
    result = random_num * multiplier_int
    
    return {
        "random_number": random_num,
        "multiplier": multiplier,
        "result": result
    }