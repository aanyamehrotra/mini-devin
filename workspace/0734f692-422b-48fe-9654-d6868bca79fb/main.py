def print_greeting(name='World'): 
  greeting_message = f'Hello, {name}!' 
  print(greeting_message) 

name = 'John'  # sample user name 
import sys 
if len(sys.argv) > 1: 
  name = sys.argv[1] 
print_greeting(name)