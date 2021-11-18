import assembly as a
import re

class Assembler():
    def __init__(self, codigo, methods):
        self.code_assembler = ['.global _start', '']
        self._methods = methods
        self.current_size = -1

        self.operators = {
            '+': 'add',
            '-': 'sub',
            '*': 'mul',
            '/': 'div'
        }

        assember = a.Assembler()
        local_pattern = r'L\[([0-9]*)\]'        

        tag = []
        prologo = []
        codigo_medio = []
        epilogo = []
        isLeaf = True

        for c in codigo:

            estructura = c.split()
            if len(estructura) > 0:
                if estructura[0] == 'DEF':
                    prologo = []
                    codigo_medio = []
                    epilogo = []
                    isLeaf = True

                    self.current_size = self.look_up(estructura[1])['Size']

                    if estructura[1] == 'main':
                        tag = ['_start:']
                    else:
                        tag = [f'{estructura[1]}:']
                    
                elif estructura[0] == 'EXIT':
                    if isLeaf:
                        prologo = ['push\t{r11, lr}']
                        epilogo = ['pop\t{r11}'] + ['bx\tlr']
                    else:
                        prologo = ['push\t{r11}']
                        epilogo = ['pop\t{r11, pc}']

                    prologo += ['mov\tr11, sp'] + [f'sub\tsp, sp, #{self.current_size}']
                    epilogo = ['mov\tr11, sp'] + epilogo
                
                    prologo = ['\t' + i for i in prologo]
                    codigo_medio = ['\t' + i for i in codigo_medio]
                    epilogo = ['\t' + i for i in epilogo]
                    self.code_assembler += tag + prologo + codigo_medio + epilogo + ['']

                elif estructura[0] == 'CALL':
                    isLeaf = False

                elif len(estructura) == 5:
                    x, y, z = [estructura[0], estructura[2], estructura[4]]
                    rx, ry, rz = assember.getReg(x, y, z)

                    code1 = []
                    code2 = []
                    code3 = []
                    if re.match(local_pattern, y):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, y).group(1)
                        code1 = [f'ldr\t{ry}, [sp, #{num}]']
                    elif self.is_number(y):
                        code1 = [f'mov\t{ry}, #{y}']
                    
                    if re.match(local_pattern, z):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, z).group(1)
                        code2 = [f'ldr\t{rz}, [sp, #{num}]']
                    elif not self.is_number(z):
                        code2 = [f'mov\t{rz}, #{z}']

                    operator = estructura[3]

                    code3 = [f'{self.operators[operator]}\t{rx}, {ry}, {rz}']
                    # offset = self.current_size - ()
                    # code = [f'ldr\t{ry}, [sp, ]']

                    codigo_medio += code1 + code2 + code3
                    # print(c, rx, ry, rz, code)
                    # assember.ToTable()

                elif len(estructura) == 3:
                    x, y = [estructura[0], estructura[2]]
                    rx, ry, _ = assember.getReg(x, y)

                    code1 = []
                    if self.is_number(y):
                        code1 = [f'mov\t{ry}, #{y}']
                        
                    pat = r'\[(.*)\]'
                    num = re.search(pat, x).group(1)    
                    code1 += [f'str\t{ry}, [sp, #{num}]']
                    # assember.ToTable()
                    codigo_medio += code1


    def look_up(self, name):
        for method in self._methods:
            if method['Id'] == name:
                return method

    def is_number(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False