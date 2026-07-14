import sys

def divide_numbers(dividend, divisor):
    try:
        quotient = dividend / divisor
        return quotient
    except ZeroDivisionError:
        return 'Error: Division by zero is not allowed'

def main():
    try:
        dividend = float(input('Enter the dividend: '))
        divisor = float(input('Enter the divisor: '))
    except EOFError:
        print('Error: No input provided')
        sys.exit(1)
    result = divide_numbers(dividend, divisor)
    print('Result:', result)

if __name__ == '__main__':
    main()