from operator import add, sub, mul, truediv as floordiv, pow


class Expr:
    operation = None

    def derive(self):
        pass

    def simplify(self):
        return self

    def __repr__(self):
        return str(self)


class UnaryExpr(Expr):
    symbol = None
    expr = None

    def lisp(self):
        return f'({self.symbol} {self.expr.lisp()})'


class BinaryExpr(Expr):
    left = None
    right = None
    symbol = None

    def lisp(self):
        return f'({self.symbol} {self.left.lisp()} {self.right.lisp()})'

    def simplify(self):
        if isinstance(self.left, Val) and isinstance(self.right, Val):
            return Val(self.operation(self.left.val, self.right.val))
        return self


class Var(Expr):
    def derive(self):
        return Val(1)

    def __str__(self):
        return 'x'

    def lisp(self):
        return str(self)


class Val(Expr):
    def __init__(self, val):
        self.val = val

    def derive(self):
        return Val(0)

    def __str__(self):
        return str(self.val)

    def __eq__(self, other):
        if isinstance(other, Val):
            return self.val == other.val
        return False

    def lisp(self):
        return str(self)


class Add(BinaryExpr):
    symbol = '+'
    operation = add

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def derive(self):
        return Add(self.left.derive(), self.right.derive())

    def simplify(self):
        self.left = self.left.simplify()
        self.right = self.right.simplify()

        if Val(0) in [self.left, self.right]:
            if self.left == Val(0):
                return self.right
            return self.left
        return super(Add, Add(self.left, self.right)).simplify()

    def __str__(self):
        return f'{self.left} + {self.right}'


class Neg(UnaryExpr):
    symbol = '-'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Neg(self.expr.derive())

    def simplify(self):
        if isinstance(self.expr, Neg):
            return self.expr.expr

    def __str__(self):
        return f'-{self.expr}'

    def lisp(self):
        return f'-{self.expr}'


class Minus(BinaryExpr):
    symbol = '-'
    operation = sub

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def derive(self):
        return Minus(self.left.derive(), self.right.derive())

    def simplify(self):
        self.left = self.left.simplify()
        self.right = self.right.simplify()

        if Val(0) in [self.left, self.right]:
            if self.left == Val(0):
                return Neg(self.right)
            return self.left
        return super(Minus, Minus(self.left, self.right)).simplify()

    def __str__(self):
        return f'{self.left} - {self.right}'


class Mul(BinaryExpr):
    symbol = '*'
    operation = mul

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def derive(self):
        return Add(Mul(self.left, self.right.derive()), Mul(self.left.derive(), self.right))

    def simplify(self):
        if Val(0) in [self.left, self.right]:
            return Val(0)
        self.left = self.left.simplify()
        self.right = self.right.simplify()
        if Val(1) in [self.left, self.right]:
            if self.left == Val(1):
                return self.right
            return self.left

        if isinstance(self.right, Div):
            # so it looks like Mul(self.left, Div(1, ..) which is the same as Div(self.left, self.right.right)
            if self.right.left == Val(1):
                div = Div(self.left, self.right.right).simplify()
                return super(Div, div).simplify()

        return super(Mul, Mul(self.left, self.right)).simplify()

    def __str__(self):
        return f'{self.left} * {self.right}'


class Cos(UnaryExpr):
    symbol = 'cos'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Mul(self.expr.derive(), Mul(Val(-1), Sin(self.expr)))

    def __str__(self):
        return f'cos({str(self.expr)})'

    def simplify(self):
        return Cos(self.expr.simplify())


class Sin(UnaryExpr):
    symbol = 'sin'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Mul(self.expr.derive(), Cos(self.expr))

    def __str__(self):
        return f'sin({str(self.expr)})'

    def simplify(self):
        return Sin(self.expr.simplify())


class Tan(UnaryExpr):
    symbol = 'tan'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Div(self.expr.derive(), Power(Cos(self.expr), Val(2)))

    def __str__(self):
        return f'tan({self.expr})'


class Div(BinaryExpr):
    symbol = '/'
    operation = floordiv

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def derive(self):
        return Div(
            Minus(
                Mul(
                    self.left.derive(),
                    self.right),
                Mul(
                    self.left,
                    self.right.derive()
                )
            ),
            Power(
                self.right,
                Val(2)
            )
        )

    def __str__(self):
        return f'{self.left} / {self.right}'

    def simplify(self):
        self.left = self.left.simplify()
        self.right = self.right.simplify()

        if self.right in [Val(1), Val(-1)]:
            if self.right == Val(-1):
                return Neg(self.left)
            return self.left
        return super(Div, self).simplify()


class Exp(UnaryExpr):
    symbol = 'exp'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Mul(self.expr.derive(), Exp(self.expr))

    def __str__(self):
        return f'Exp({self.expr})'


class Ln(UnaryExpr):
    symbol = 'ln'

    def __init__(self, expr):
        self.expr = expr

    def derive(self):
        return Mul(self.expr.derive(), Div(Val(1), self.expr))

    def __str__(self):
        return f'ln({self.expr})'


class Power(BinaryExpr):
    symbol = '^'
    operation = pow

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def derive(self):
        return Mul(self.right,
                   Power(
                       Mul(self.left.derive(),
                           self.left),
                       Minus(self.right, Val(1))))

    def simplify(self):
        self.left = self.left.simplify()
        self.right = self.right.simplify()
        if self.right == Val(0):
            return Val(1)

        if self.right == Val(1):
            return self.left.simplify()

        self.left = self.left.simplify()
        self.right = self.right.simplify()

        return super(Power, self).simplify()

    def __str__(self):
        return f'{self.left} ^ ({self.right})'


# Add(parseLeft(), parseRight())
operands_map = {
    '*': Mul,
    '/': Div,
    '+': Add,
    '^': Power,
    '-': Minus,
    'cos': Cos,
    'sin': Sin,
    'exp': Exp,
    'tan': Tan,
    'ln': Ln
}


def parse_expression(s):
    operands = s.split(' ')

    if len(operands) == 1:
        argument = operands[0]
        if argument == 'x':
            return Var(), []
        return Val(int(argument)), []

    argument = operands[1]

    if '(' not in argument:
        # just a simple val
        if argument.strip('()') == 'x':
            left, rest = Var(), operands[2:]
        else:
            left, rest = Val(int(argument)), operands[2:]
    else:
        left, rest = parse_expression(' '.join(operands[1:]))

    operand = operands[0][1:]
    op = operands_map[operand]

    if operand in ('cos', 'sin', 'exp', 'tan', 'ln'):
        return op(left), rest

    argument = rest[0]

    if '(' not in argument:
        # just a simple val
        argument = argument.strip(')')
        if argument == 'x':
            right = Var()
        else:
            right = Val(int(argument))
    else:
        right, rest = parse_expression(' '.join(rest))
    return op(left, right), rest[1:]


def diff(s):
    parsed = parse_expression(s)[0]
    return parsed.derive().simplify().lisp()
