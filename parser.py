from lexer import *
import sys

# Parser gets token and checks if the code matches specified grammar.
class Parser:
  def __init__(self, lexer, emitter):
    self.lexer = lexer
    self.emmiter = emitter

    self.symbols = set() # storing variables declared so far.
    self.label_declared = set() # storing LABELS declared so far
    self.label_gotoed = set() # storing goto'ed LABELS.
    
    self.cur_token = None
    self.peek_token = None
    # double call to get both current and peek token.
    self.next_token()
    self.next_token()

  # token matching helper function. return True if token matched.
  def check_token(self, kind):
    return kind == self.cur_token.type
  
  # lookahead matching of token 
  def check_peek(self, kind):
    return kind == self.peek_token.type

  # Try to match current token. if no match, throw error. Advance to next token.
  def match_token(self, token):
    if not self.check_token(token):
      self.abort("Expected " + token.name + " but got " + self.cur_token.type.name)
    self.next_token()
  
  # get next token
  def next_token(self):
    self.cur_token = self.peek_token
    self.peek_token = self.lexer.get_token()
    # no error handling as lexer does that.

  # error throw
  def abort(self, message):
    sys.exit("Parsing error : " + message)


  #----- Language Grammar (Production rules) ----------- #

  # Program ::= {statement}
  def program(self):

    # c header files comes already includes for emission
    self.emmiter.header_line("#include <stdio.h>")
    self.emmiter.header_line("int main(void){")

    # since some newlines are required, we can skip excess.
    while self.check_token(Token_Type.NEWLINE):
      self.next_token()

    # parse all statements in the program.
    while not self.check_token(Token_Type.EOF):
      self.statement()
    
    # finishing emission (ending of c code)
    self.emmiter.emit_line("return 0;")
    self.emmiter.emit_line("}")

    # check if all labels goto'ed are declared (for referenceError)
    for label in self.label_gotoed:
      if label not in self.label_declared:
        self.abort("Attempting to GOTO to undeclared LABEL :" + self.cur_token.text)

  # various statements grammars (total 7)
  def statement(self):

    # statement ::= "PRINT" (expression | string) nl
    if self.check_token(Token_Type.PRINT):
      self.next_token()

      if self.check_token(Token_Type.STRING): # string
        self.emmiter.emit_line("printf(\"" + self.cur_token.text + "\\n\");") # emission of simple strings
        self.next_token() 
      else:
        self.emmiter.emit("printf(\"%" + ".2f\\n\", (float)(") # expression emitted as float
        self.expression() # expression
        self.emmiter.emit_line("));")

    # statement ::= "IF" comparison "THEN" nl {statement} "ENDIF" nl
    elif self.check_token(Token_Type.IF):
      self.next_token()
      self.emmiter.emit("if(")
      self.comparison()
      self.match_token(Token_Type.THEN)
      self.nl()
      self.emmiter.emit_line("){")
      while not self.check_token(Token_Type.ENDIF): # while endif not found check all statements inside
        self.statement()

      self.match_token(Token_Type.ENDIF) 
      self.emmiter.emit_line("}")

    # statement ::= "WHILE" comparison "REPEAT" nl {statement nl} "ENDWHILE" nl
    elif self.check_token(Token_Type.WHILE):
      self.next_token()
      self.emmiter.emit("while(")
      self.comparison()
      self.match_token(Token_Type.REPEAT)
      self.nl()
      self.emmiter.emit_line("){")

      while not self.check_token(Token_Type.ENDWHILE):
        self.statement()

      self.match_token(Token_Type.ENDWHILE)
      self.emmiter.emit_line("}")
    
    # statement ::= "LABEL" ident nl
    elif self.check_token(Token_Type.LABEL):
      self.next_token()
      # checking if already declared 
      if self.cur_token.text in self.label_declared:
        self.abort("Label already exists " + self.cur_token.text)
      else:
        self.label_declared.add(self.cur_token.text)
      
      self.emmiter.emit_line(self.cur_token.text + ":")
      self.match_token(Token_Type.IDENT)

    # statement ::= "GOTO" ident nl
    elif self.check_token(Token_Type.GOTO):
      self.next_token()
      self.label_gotoed.add(self.cur_token.text)
      self.emmiter.emit_line("goto " + self.cur_token.text + ";")
      self.match_token(Token_Type.IDENT)

    # statement ::= "LET" ident "=" expression nl
    elif self.check_token(Token_Type.LET):
      self.next_token()
      # add identifier into known variables set
      if self.cur_token.text not in self.symbols:
        self.symbols.add(self.cur_token.text)
        """
        the first time a variable is referenced in Teeny Tiny it should emit a variable declaration in C,
        and place it at the top of the main function (this is an old C convention). 
        Teeny Tiny doesn't differentiate between variable declarations and assignments, but C does
        """
        self.emmiter.header_line("float " + self.cur_token.text + ";")
      self.emmiter.emit(self.cur_token.text + " = ")

      self.match_token(Token_Type.IDENT)
      self.match_token(Token_Type.EQ)
      self.expression()
      self.emmiter.emit_line(";")

    # statement ::= "INPUT" ident nl
    elif self.check_token(Token_Type.INPUT):
      self.next_token()
      # add identifier into known variables set
      if self.cur_token.text not in self.symbols:
        self.symbols.add(self.cur_token.text)
        """
        if the variable being referenced doesn't already exist, then
        we should declare it by using emitter.headerLine. Second, 
        we have to include some C specific code because of how scanf works. 
        We could just emit scanf("%f", &foo);, but that won't handle invalid input, 
        such as when a user enters a letter. So we must also check if scanf returns 0. 
        If it does, we clear the input buffer and we set the input variable to 0.

        Note: This will be a limitation of Teeny Tiny. You can't tell if the
        user input was the value 0 or an invalid input. They are treated the same. 
        There are ways to fix this though. You could modify it such that an
        invalid input results in an obscure value, like -999, or prints an error message
        and asks for a valid input in a loop, or sets an error code in a flag. 
        Every programming language handles these types of scenarios differently. 
        The value of 0 will work for now though.
        """
        self.emmiter.header_line("float " + self.cur_token.text + ";")

      # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
      self.emmiter.emit_line("if(0 == scanf(\"%" + "f\", &" + self.cur_token.text + ")) {")
      self.emmiter.emit_line(self.cur_token.text + " = 0;")
      self.emmiter.emit("scanf(\"%")
      self.emmiter.emit_line("*s\");")
      self.emmiter.emit_line("}")
      self.match_token(Token_Type.IDENT)
    
    # not matching grammar for any statement so return Error
    else:
      self.abort("Invalid statement at : " + self.cur_token.text + " (" + self.cur_token.type.name + ")")

    self.nl() # newline
  
  def is_comparison_operator(self):
    return ( self.check_token(Token_Type.GT) or self.check_token(Token_Type.GTEQ) or 
        self.check_token(Token_Type.LT) or self.check_token(Token_Type.LTEQ) or
        self.check_token(Token_Type.EQEQ) or self.check_token(Token_Type.NOTEQ))
  # comparison grammar
  def comparison(self):
    # comparison ::= expression (("==" | "<" | ">" | ">=" | "<=" | "!=") expression ) +
    self.expression()
    if self.is_comparison_operator(): # expression must be followed by comparison operator
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
      self.expression()
    else:
      self.abort("Expected comparison operator at " + self.cur_token.text)
    
    # can have 0 or more comparison operator(s)
    while self.is_comparison_operator():
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
      self.expression()

    # expression grammar
    """To achieve different levels of precedence, we organize the grammar rules sequentially.
      Operators with higher precedence need to be "lower" in the grammar, such that they are 
      lower in the parse tree. The operators closest to the tokens in the parse tree 
      (i.e., closest to the leaves of the tree) will have the highest precedence. 
      The multiplication operator will always be lower in the tree than the plus operator.
      The unary negation operator will be even lower. If there are more operators with the same precedence,
      then they will be processed left to right. More precedence levels (and operators) can be added by following this pattern.
    """
  def expression(self):
    # expression ::= term {("-" | "+") term }
    self.term()
    while self.check_token(Token_Type.PLUS) or self.check_token(Token_Type.MINUS):  # 0 or more
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
      self.term()

  # term and unary
  def term(self):
    # term ::= unary {("/" | "*") unary}
    self.unary()
    while self.check_token(Token_Type.ASTERISK) or self.check_token(Token_Type.SLASH):  # 0 or more
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
      self.unary()

  def unary(self):
    # unary ::= ["+" | "-"] primary
    if self.check_token(Token_Type.PLUS) or self.check_token(Token_Type.MINUS): # optional
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
    self.primary()
  
  # primary
  def primary(self):
    # primary ::= ident | number
    if self.check_token(Token_Type.NUMBER):
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
    elif self.check_token(Token_Type.IDENT):
      if self.cur_token.text not in self.symbols:
        self.abort("Referencing variable before assignment :" + self.cur_token.text)
      self.emmiter.emit(self.cur_token.text)
      self.next_token()
    else:
      # Error
      self.abort("Unexpected token at " + self.cur_token.text)

  # newline 
  def nl(self):
    self.match_token(Token_Type.NEWLINE)
    # to handle multiple newline tokens
    while self.check_token(Token_Type.NEWLINE):
      self.next_token()