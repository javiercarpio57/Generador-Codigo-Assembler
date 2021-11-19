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
        local_pattern = r'L\[(.*)\]'
        global_pattern = r'G\[(.*)\]'

        tag = []
        prologo = []
        codigo_medio = []
        epilogo = []
        isLeaf = True
        params = 0

        for c in codigo:

            estructura = c.split()
            if len(estructura) > 0:
                if estructura[0] == 'DEF':
                    prologo = []
                    codigo_medio = []
                    epilogo = []
                    params = 0
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

                elif estructura[0] == 'PARAM':
                    code1 = []
                    value = estructura[1]
                    registro = f'r{params}'
                    params += 1
                    old = assember.register_descriptor[registro]

                    for o in old:
                        if o[0] in 'LG':
                            if o[0] == 'L':
                                print('PARAM', o)
                                num = re.search(local_pattern, o).group(1)

                                if self.is_number(num):
                                    code1 += [f'str\t{registro}, [sp, #{num}]']
                                else:
                                    temp = assember.findTemp(num)
                                    # TODO: Buscar otro registro disponible para asignarlo ahi
                                    code1 += [f'str\t{registro}, [sp, {temp}]']

                                assember.address_descriptor[o] = [o]
                            else:
                                # TODO: Programar lo global
                                pass
                        elif o[0] in 't':
                            assember.address_descriptor[o] = [o]


                    if re.match(local_pattern, value):
                        num = re.search(local_pattern, value).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{registro}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{registro}, [sp, {temp}]']

                    elif re.match(global_pattern, value):
                        pass
                    elif value[0] == 't':
                        temp = assember.findTemp(value)
                        code1 += [f'mov\t{registro}, {temp}']
                    elif self.is_number(value):
                        code1 += [f'mov\t{registro}, #{value}']

                    assember.register_descriptor[registro] = [value]
                    assember.addAddressDescriptor(value, registro)
                    codigo_medio += code1

                elif estructura[0] == 'CALL':
                    isLeaf = False
                    codigo_medio += [f'bl\t{estructura[1][:-1]}']

                elif len(estructura) == 5:
                    x, y, z = [estructura[0], estructura[2], estructura[4]]
                    rx, ry, rz = assember.getReg(x, y, z)

                    code1 = []
                    code2 = []
                    code3 = []
                    if re.match(local_pattern, y):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 = [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 = [f'ldr\t{ry}, [sp, {temp}]']
                        
                    elif self.is_number(y):
                        code1 = [f'mov\t{ry}, #{y}']
                    
                    if re.match(local_pattern, z):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, z).group(1)

                        if self.is_number(num):
                            code2 = [f'ldr\t{rz}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code2 = [f'ldr\t{rz}, [sp, {temp}]']

                    elif self.is_number(z):
                        code2 = [f'mov\t{rz}, #{z}']

                    operator = estructura[3]

                    code3 = [f'{self.operators[operator]}\t{rx}, {ry}, {rz}']

                    codigo_medio += code1 + code2 + code3

                elif len(estructura) == 3:
                    x, y = [estructura[0], estructura[2]]
                    code1 = []

                    if re.match(local_pattern, x):
                        num = re.search(local_pattern, x).group(1)
                        if self.is_number(num):
                            rx, ry, _ = assember.getReg(x, y)
                            code1 += [f'str\t{ry}, [sp, #{num}]']
                        else:
                            rx, ry, _ = assember.getReg(num, y)
                            code1 += [f'str\t{ry}, [sp, {rx}]']
                    else:
                        rx, ry, _ = assember.getReg(x, y)
                        code1 += [f'str\t{ry}, [sp, {rx}]']

                    if self.is_number(y):
                        code1 = [f'mov\t{ry}, #{y}'] + code1
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