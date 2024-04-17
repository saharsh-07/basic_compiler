from enum import Enum
import sys


# Lexer is first step of the compiler. It converts source code to tokens for parsing. Lexical analysis.
class Lexer:
  def __init__(self, source):
    self.source = source + "\n"   # append newline to end for easier lexing of last token/statement.
    self.cur_char =  ""
    self.cur_pos = -1
    self.next_char()

  # process next char  
  def next_char(self):
    self.cur_pos += 1

    # if out of bound then add "\0" (full stop)
    if self.cur_pos >= len(self.source):
      self.cur_char = "\0" # End of input EOF
    else:
      self.cur_char = self.source[self.cur_pos]
  
  # return lookahead char (used for multi-char syntax)
  def peek(self):
    if self.cur_pos + 1 >= len(self.source):
      return "\0"
    return self.source[self.cur_pos + 1]
  
  # error for invalid token
  def abort(self, message):
    sys.exit("Lexing error. " + message)

  # skip whitespace except newlines, which is used for indicating end of statement.
  def skip_white_space(self):
    while self.cur_char in (" ", "\t", "\r"):
      self.next_char()

  def skip_comment(self):
    if self.cur_char == "#":
      while self.cur_char != "\n":
        self.next_char()

  # return next token
  def get_token(self):
    # checking for single character syntax so we can convert it to token.
    # if it is multiple-char (combined) syntax like (!=, >=, <=, etc), number, identifier or keyword we will process rest.
    # using match-case (only 3.10 or higher) (can be done similarly by if-else blocks)
    self.skip_white_space()
    self.skip_comment()
    token = None
    
    match self.cur_char:
      case "+":
        token = Token(self.cur_char, Token_Type.PLUS)
      case "-":
        token = Token(self.cur_char, Token_Type.MINUS)
      case "*":
        token = Token(self.cur_char, Token_Type.ASTERISK)
      case "/":
        token = Token(self.cur_char, Token_Type.SLASH)
      case "\n":
        token = Token(self.cur_char, Token_Type.NEWLINE)
      case "\0":
        token = Token("", Token_Type.EOF)
      
      case "=":
        # check whether its "=" or combined "=="
        if self.peek() == "=":
          last_char = self.cur_char
          self.next_char()
          token = Token(last_char + self.cur_char, Token_Type.EQEQ)
        else:
          token = Token(self.cur_char, Token_Type.EQ)
      
      case '>':
        # Check whether this is token is > or >=
        if self.peek() == '=':
            last_char = self.cur_char
            self.next_char()
            token = Token(last_char + self.cur_char, Token_Type.GTEQ)
        else:
            token = Token(self.cur_char, Token_Type.GT)
      
      case '<':
        # Check whether this is token is < or <=
        if self.peek() == '=':
            last_char = self.cur_char
            self.next_char()
            token = Token(last_char + self.cur_char, Token_Type.LTEQ)
        else:
            token = Token(self.cur_char, Token_Type.LT)
      
      case '!':
        if self.peek() == '=':
            last_char = self.cur_char
            self.next_char()
            token = Token(last_char + self.cur_char, Token_Type.NOTEQ)
        else:
        # ! is invalid by itself.
          self.abort("Expected !=, got !" + self.peek())
      
      # Processing string without any special char
      case "\"":
        self.next_char()
        start_pos = self.cur_pos
        while self.cur_char != '\"':
          # Don't allow special characters in the string. No escape characters, newlines, tabs, or %.
          # We will be using C's printf on this string.
          if self.cur_char in ("\r", "\n", "\t", "\\", "%"):
            self.abort("Illegal character in string.")
          self.next_char()
          string = self.source[start_pos : self.cur_pos]
          token = Token(string, Token_Type.STRING)
      
      # processing numbers.
      case self.cur_char if self.cur_char.isdigit():
        # if number check either decimal or int
          start_pos = self.cur_pos
          while self.peek().isdigit():
            self.next_char()
          if self.peek() == ".":  #decimal
            self.next_char()
            if not self.peek().isdigit():
              self.abort("Not a valid number")
            while self.peek().isdigit():
              self.next_char()
          num = self.source[start_pos : self.cur_pos + 1]
          token = Token(num, Token_Type.NUMBER)
          
      # processing keyword or identifier
      case self.cur_char if self.cur_char.isalpha():
        # Leading character is a letter, so this must be an identifier or a keyword.
        # Get all consecutive alpha numeric characters.
        start_pos = self.cur_pos
        while self.peek().isalpha():
          self.next_char()
        text = self.source[start_pos : self.cur_pos + 1] # get substring
        keyword = Token.check_if_keyword(text) #
        if keyword == None: # not a keyword 
          token = Token(text, Token_Type.IDENT)
        else:
          token = Token(text, keyword)

      case _:   #default case
        self.abort("Unknown token : " + self.cur_char)  # unknown token (error)
    
    self.next_char()
    return token if token else self.abort("Something went wrong")
  

class Token:
  def __init__(self, token_text, token_type):
    self.text = token_text # actual text. Used for identifier, number and strings
    self.type = token_type # which type this token is classified as.

  @staticmethod
  def check_if_keyword(token_text):
    for kind in Token_Type:
      if kind.name == token_text and 100 <= kind.value < 200:
        return kind
    return None

class Token_Type(Enum):
  # TokenType is our enum for all the types of tokens.
	EOF = -1
	NEWLINE = 0
	NUMBER = 1
	IDENT = 2
	STRING = 3
	# Keywords.
	LABEL = 101
	GOTO = 102
	PRINT = 103
	INPUT = 104
	LET = 105
	IF = 106
	THEN = 107
	ENDIF = 108
	WHILE = 109
	REPEAT = 110
	ENDWHILE = 111
	# Operators.
	EQ = 201  
	PLUS = 202
	MINUS = 203
	ASTERISK = 204
	SLASH = 205
	EQEQ = 206
	NOTEQ = 207
	LT = 208
	LTEQ = 209
	GT = 210
	GTEQ = 211