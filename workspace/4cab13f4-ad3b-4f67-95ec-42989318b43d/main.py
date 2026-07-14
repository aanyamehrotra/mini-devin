def divide_numbers(dividend, divisor):
  try:
    result = dividend / divisor
    return result
  except ZeroDivisionError:
    return 'Error: Division by zero'

# Test the function with sample values
num1 = 10
num2 = 2
print(f'{num1} divided by {num2} is: {divide_numbers(num1, num2)}')

# Test the function with division by zero
num3 = 10
num4 = 0
print(f'{num3} divided by {num4} is: {divide_numbers(num3, num4)}')