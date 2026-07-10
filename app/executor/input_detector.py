import ast

def detect_inputs(code:str)-> int:
    tree = ast.parse(code)
    