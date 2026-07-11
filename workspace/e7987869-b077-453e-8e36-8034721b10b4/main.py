import operator

# 1. Define core arithmetic functions
def add(a: float, b: float) -> float:
    """Performs addition."""
    return operator.add(a, b)

def subtract(a: float, b: float) -> float:
    """Performs subtraction."""
    return operator.sub(a, b)

def multiply(a: float, b: float) -> float:
    """Performs multiplication."""
    return operator.mul(a, b)

def divide(a: float, b: float) -> float:
    """Performs division, raising an error if division by zero occurs."""
    if b == 0:
        raise ValueError("Error: Division by zero is not allowed.")
    return operator.truediv(a, b)

# Map operators to functions for easy lookup
OPERATIONS = {
    '+': add,
    '-': subtract,
    '*': multiply,
    '/': divide,
}

# 2. & 3. Implement parsing, interpretation, and evaluation of expressions
def evaluate_expression(expression: str) -> float:
    """
    Parses and evaluates a simple arithmetic expression from a string.
    Expected format: "operand1 operator operand2" (e.g., "2 + 3", "5 * 4").

    Args:
        expression (str): The arithmetic expression string.

    Returns:
        float: The result of the evaluated expression.

    Raises:
        ValueError: If the expression format is invalid, operands are not numeric,
                    the operator is unknown, or division by zero occurs.
    """
    parts = expression.strip().split()

    if len(parts) != 3:
        raise ValueError(
            "Error: Invalid expression format. "
            "Expected 'operand1 operator operand2' (e.g., 2 + 3)."
        )

    operand1_str, op_str, operand2_str = parts

    try:
        operand1 = float(operand1_str)
    except ValueError:
        raise ValueError(
            f"Error: Invalid number '{operand1_str}'. Please ensure operands are numeric."
        )

    try:
        operand2 = float(operand2_str)
    except ValueError:
        raise ValueError(
            f"Error: Invalid number '{operand2_str}'. Please ensure operands are numeric."
        )

    if op_str not in OPERATIONS:
        raise ValueError(
            f"Error: Unknown operator '{op_str}'. Supported operators are +, -, *, /."
        )

    operation_func = OPERATIONS[op_str]

    return operation_func(operand1, operand2)

# 4. & 5. Design the user interface and integrate error handling
def main():
    """
    Runs the command-line calculator, prompting for a single expression and displaying the result.
    Handles user input, calls the expression evaluator, and manages error display.
    """
    print("Welcome to the Command-Line Calculator!")
    print("Enter an expression like '2 + 3', '10 * 5.5', or '-7 / 2'.")

    try:
        user_input = input("> ").strip()

        if not user_input:
            print("No input provided. Exiting.")
            return

        result = evaluate_expression(user_input)
        print(f"Result: {result}")

    except ValueError as e:
        # Catch specific errors from evaluate_expression
        print(e)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()