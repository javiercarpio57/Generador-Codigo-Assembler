from prettytable.prettytable import NONE
from antlr4 import *
from antlr4.tree.Trees import TerminalNode
from antlr4.error.ErrorListener import ErrorListener
from DecafLexer import DecafLexer
from DecafListener import DecafListener
from DecafParser import DecafParser
from itertools import groupby
from utilities import *

import analisisSemantico as sem
import generacionCodigo as gc
import generacionAssembler as ga

class Compilar():
    def __init__(self, url):
        self.printer = None

        input = FileStream(url)
        lexer = DecafLexer(input)
        stream = CommonTokenStream(lexer)
        parser = DecafParser(stream)
        self.myError = sem.MyErrorListener()
        parser.removeErrorListeners()
        parser.addErrorListener(self.myError)
        tree = parser.program()

        # print('HAS ERROR?', self.myError.getHasError())
        if not self.myError.getHasError():
            self.printer = sem.DecafPrinter()
            walker = ParseTreeWalker()
            walker.walk(self.printer, tree)

            if self.printer.node_type[self.printer.root] == 'error' or len(self.printer.errores.errores) > 0:
                print('errores semanticos')
            else:
                print(self.printer.tabla_tipos._types)
                print('podemos generar codigo')
                input = FileStream(url)
                lexer = DecafLexer(input)
                stream = CommonTokenStream(lexer)
                parser = DecafParser(stream)
                self.myError2 = sem.MyErrorListener()
                parser.removeErrorListeners()
                parser.addErrorListener(self.myError2)
                tree = parser.program()
                self.printer2 = gc.GeneracionCodigoPrinter()
                walker = ParseTreeWalker()
                walker.walk(self.printer2, tree)

                print('podemos generar assembler')
                self.ass = ga.Assembler(self.printer2.codigogenerado, self.printer2.tabla_methods._methods)

    def HasLexicalError(self):
        return self.myError.getHasError()

# c = Compilar('fact_array.decaf')
