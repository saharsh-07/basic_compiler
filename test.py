from lexer import *
from parser import *
from emitter import *
import sys

def main():
  print("Working compiler/interpreter")

  if len(sys.argv) != 2:
    sys.exit("Error : Compiler needs source file as argument")
  
  with open(sys.argv[1], "r") as inputFile:
    src = inputFile.read()

  # Initialize lexer, emmiter and parser
  lex = Lexer(src)
  emit = Emitter("out.c")
  parse = Parser(lex, emit)
  parse.program() # start the program execution
  emit.write_file() # write out the output
  print("Parsing completed successfully")

main()