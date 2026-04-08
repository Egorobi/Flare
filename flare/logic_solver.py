import re

class LogicSolver():
    # class used to solve logic expressions without eval

    @staticmethod
    def solve_expression(expression):
        print_debug = False
        if print_debug: print(expression)
        # strip unnecessary brackets
        while expression[0] == "(" and expression[-1] == ")":
            if print_debug: print("strip brackets")
            expression = expression[1:-1]
        # solve contents of brackets
        while "(" in expression or ")" in expression:
            if print_debug: print("solve brackets")
            expression = re.sub(r"(\([^\(^\)]*\))", lambda m: str(LogicSolver.solve_expression(m.group(1))), expression)
        while " " in expression:
            # if print_debug: print("evaluate operators")
            # evaluate not
            expression = re.sub(r"not not", lambda m: "", expression)
            expression = re.sub(r"not True", lambda m: "False", expression)
            expression = re.sub(r"not False", lambda m: "True", expression)
            # evaluate and
            expression = re.sub(r"(\w*) and (\w*)", lambda m: str(m.group(1) == "True" and m.group(2) == "True"), expression, 1)
            # evaluate or
            expression = re.sub(r"(\w*) or (\w*)", lambda m: str(m.group(1) == "True" or m.group(2) == "True"), expression, 1)
        if expression == "True":
            return True
        elif expression == "False":
            return False
        else:
            raise ValueError("Logic expression could not be parsed")
