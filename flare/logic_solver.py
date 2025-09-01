import re

class LogicSolver():
    # class used to solve logic expressions without eval

    @staticmethod
    def solve_expression(expression):
        # strip unnecessary brackets
        while expression[0] == "(" and expression[-1] == ")":
            expression = expression[1:-1]
        # solve contents of brackets
        while "(" in expression or ")" in expression:
            expression = re.sub(r"(\([^\(^\)]*\))", lambda m: str(LogicSolver.solve_expression(m.group(1))), expression)

        while " " in expression:
            # evaluate not
            expression = re.sub(r"not (\w*)", lambda m: str(m.group(1) == "False"), expression)
            # evaluate and
            expression = re.sub(r"(\w*) and (\w*)", lambda m: str(m.group(1) == "True" and m.group(2) == "True"), expression)
            # evaluate or
            expression = re.sub(r"(\w*) or (\w*)", lambda m: str(m.group(1) == "True" or m.group(2) == "True"), expression)

        if expression == "True":
            return True
        elif expression == "False":
            return False
        else:
            raise ValueError("Logic expression could not be parsed")
