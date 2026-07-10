def factorial(n):
    """
    Calculates the factorial of a given non-negative integer using an iterative approach.

    Args:
        n (int): A non-negative integer.

    Returns:
        int: The factorial of 'n'.

    Raises:
        TypeError: If 'n' is not an integer.
        ValueError: If 'n' is a negative integer.
    """
    # 1. Input validation
    if not isinstance(n, int):
        raise TypeError("Input 'n' must be an integer.")
    if n < 0:
        raise ValueError("Input 'n' must be a non-negative integer.")

    # 2. Base cases
    if n == 0 or n == 1:
        return 1

    # 3. Iterative calculation for n > 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

if __name__ == "__main__":
    print("--- Factorial Calculation Examples ---")

    # Valid inputs
    print(f"Factorial of 0: {factorial(0)}")
    print(f"Factorial of 1: {factorial(1)}")
    print(f"Factorial of 5: {factorial(5)}")   # Expected: 120
    print(f"Factorial of 7: {factorial(7)}")   # Expected: 5040
    print(f"Factorial of 10: {factorial(10)}") # Expected: 3628800

    print("\n--- Invalid Input Scenarios ---")

    # Invalid input: negative integer
    try:
        print(f"Factorial of -3: {factorial(-3)}")
    except ValueError as e:
        print(f"Error calculating factorial of -3: {e}")

    # Invalid input: float
    try:
        print(f"Factorial of 3.5: {factorial(3.5)}")
    except TypeError as e:
        print(f"Error calculating factorial of 3.5: {e}")

    # Invalid input: string
    try:
        print(f"Factorial of 'abc': {factorial('abc')}")
    except TypeError as e:
        print(f"Error calculating factorial of 'abc': {e}")

    # Invalid input: None
    try:
        print(f"Factorial of None: {factorial(None)}")
    except TypeError as e:
        print(f"Error calculating factorial of None: {e}")