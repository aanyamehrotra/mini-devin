utils.py
```python
def get_user_input(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number.")

def print_result(result):
    print(f"Result: {result}")
```

calculator.py
```python
class Calculator:
    def add(self, num1, num2):
        return num1 + num2

    def subtract(self, num1, num2):
        return num1 - num2

    def multiply(self, num1, num2):
        return num1 * num2

    def divide(self, num1, num2):
        if num2 == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return num1 / num2
```

main.py
```python
from calculator import Calculator
from utils import get_user_input, print_result

def main():
    calculator = Calculator()

    while True:
        print("\nCalculator App")
        print("1. Addition")
        print("2. Subtraction")
        print("3. Multiplication")
        print("4. Division")
        print("5. Quit")

        choice = input("Choose an operation (1/2/3/4/5): ")

        if choice == "5":
            break

        if choice not in ["1", "2", "3", "4"]:
            print("Invalid choice. Please choose a valid operation.")
            continue

        num1 = get_user_input("Enter the first number: ")
        num2 = get_user_input("Enter the second number: ")

        if choice == "1":
            result = calculator.add(num1, num2)
        elif choice == "2":
            result = calculator.subtract(num1, num2)
        elif choice == "3":
            result = calculator.multiply(num1, num2)
        elif choice == "4":
            try:
                result = calculator.divide(num1, num2)
            except ZeroDivisionError as e:
                print(str(e))
                continue

        print_result(result)

if __name__ == "__main__":
    main()
```