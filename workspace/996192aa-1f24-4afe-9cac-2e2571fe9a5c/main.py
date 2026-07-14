def divide_numbers(num1, num2):
    try:
        result = num1 / num2
        return result
    except ZeroDivisionError:
        return 'Error: Division by zero is not allowed'

def main():
    num1 = float(input('Enter the first number: '))
    num2 = float(input('Enter the second number: '))
    result = divide_numbers(num1, num2)
    if isinstance(result, str):
        print(result)
    else:
        print('The result of the division is: ', result)

if __name__ == '__main__':
    main()