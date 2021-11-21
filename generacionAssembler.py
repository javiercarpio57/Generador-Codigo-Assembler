import assembly as a
import re

class Assembler():
    def __init__(self, codigo, methods, global_size):
        self.code_assembler = ['.global _start', '']
        self._methods = methods
        self.global_size = global_size
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

                    metodo = self.look_up(estructura[1])
                    self.current_size = metodo['Size']

                    if estructura[1] == 'main':
                        tag = ['_start:']
                    else:
                        tag = [f'{estructura[1]}:']

                    code1 = []
                    for i in range(len(metodo['Parameters'])):
                        code1 += [f'str\tr{i}, [sp, #{i * 4}]']
                    codigo_medio += ['\t' + i for i in code1]

                elif estructura[0] == 'EXIT':
                    if isLeaf:
                        prologo = []
                        epilogo = ['bx\tlr']
                    else:
                        prologo = ['push\t{r11, lr}'] + ['mov\tr11, sp']
                        epilogo = ['mov\tsp, r11'] + ['pop\t{r11, lr}'] + ['bx\tlr']

                    prologo += [f'sub\tsp, sp, #{self.current_size}']
                    # epilogo += epilogo
                
                    prologo = ['\t' + i for i in prologo]
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
                            assember.removeVariable(num, temp)

                    elif re.match(global_pattern, value):
                        pass
                    elif value[0] == 't':
                        temp = assember.findTemp(value)
                        code1 += [f'mov\t{registro}, {temp}']
                    elif self.is_number(value):
                        code1 += [f'mov\t{registro}, #{value}']

                    # assember.register_descriptor[registro] = [value]
                    # assember.addAddressDescriptor(value, registro)
                    codigo_medio += ['\t' + i for i in code1]

                elif estructura[0] == 'CALL':
                    isLeaf = False
                    code1 = [f'bl\t{estructura[1][:-1]}']
                    metodo = self.look_up(estructura[1][:-1])
                    if metodo['Tipo'] != 'void':
                        assember.addAddressDescriptor('R', 'R')
                        assember.register_descriptor['r0'] = ['R']

                    codigo_medio += ['\t' + i for i in code1]
                
                elif estructura[0] == 'RETURN':
                    value = estructura[1]
                    registro = 'r0'
                    code1 = []
                    
                    if re.match(local_pattern, value):
                        num = re.search(local_pattern, value).group(1)
                        if self.is_number(num):
                            code1 = [f'ldr\t{registro}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 = [f'ldr\t{registro}, [sp, {temp}]']
                            assember.removeVariable(num, temp)

                    elif re.match(global_pattern, value):
                        pass
                    elif value[0] == 't':
                        temp = assember.findTemp(value)
                        code1 = [f'mov\t{registro}, {temp}']
                    elif self.is_number(value):
                        code1 = [f'mov\t{registro}, #{value}']

                    codigo_medio += ['\t' + i for i in code1]
                
                elif estructura[0] == 'GOTO':
                    code1 = [f'b\t{estructura[1]}']

                    codigo_medio += ['\t' + i for i in code1]

                elif estructura[0] == 'IF':
                    _, op1, op, op2, _, branch = estructura
                    code1 = []
                    operando1, op, operando2 = [None, op, None]
                    _, ry, rz = assember.getReg(None, op1, op2)
                    
                    if re.match(local_pattern, op1):
                        num = re.search(local_pattern, op1).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']
                            assember.removeVariable(num, temp)
                    elif re.match(global_pattern, op1):
                        pass
                    elif op1[0] == 't':
                        temp = assember.findTemp(op1)
                        code1 += [f'mov\t{ry}, {temp}']
                    elif self.is_number(op1):
                        code1 += [f'mov\t{ry}, #{op1}']


                    if re.match(local_pattern, op2):
                        num = re.search(local_pattern, op2).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{rz}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{rz}, [sp, {temp}]']
                            assember.removeVariable(num, temp)
                    elif re.match(global_pattern, op2):
                        pass
                    elif op2[0] == 't':
                        temp = assember.findTemp(op2)
                        code1 += [f'mov\t{rz}, {temp}']
                    elif self.is_number(op2):
                        code1 += [f'mov\t{rz}, #{op2}']


                    result, b = self.getConditional(ry, op, rz)
                    codigo_medio += ['\t' + i for i in code1] + ['\t' + i for i in result] + [f'\t{b}\t{branch}']

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
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']

                    elif re.match(global_pattern, y):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = assember.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{ry}, [{address_reg}, {temp}]']
                        
                    elif self.is_number(y):
                        code1 += [f'mov\t{ry}, #{y}']

                    
                    if re.match(local_pattern, z):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, z).group(1)

                        if self.is_number(num):
                            code2 += [f'ldr\t{rz}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code2 += [f'ldr\t{rz}, [sp, {temp}]']

                    elif re.match(global_pattern, z):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = assember.getReg(None, '.global_stack')
                        code2 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, z).group(1)
                        
                        if self.is_number(num):
                            code2 += [f'ldr\t{rz}, [{address_reg}, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code2 += [f'ldr\t{rz}, [{address_reg}, {temp}]']

                    elif self.is_number(z):
                        code2 = [f'mov\t{rz}, #{z}']

                    operator = estructura[3]

                    code3 = [f'{self.operators[operator]}\t{rx}, {ry}, {rz}']

                    assember.removeVariable(y, ry)
                    assember.removeVariable(z, rz)
                    codigo_medio += ['\t' + i for i in code1] + ['\t' + i for i in code2] + ['\t' + i for i in code3]

                elif len(estructura) == 3:
                    x, y = [estructura[0], estructura[2]]
                    rx, ry, _ = assember.getReg(x, y)
                    code1 = []

                    if re.match(local_pattern, y):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']

                    elif re.match(global_pattern, y):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = assember.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'ldr\t{ry}, [{address_reg}, {temp}]']
                        
                    elif self.is_number(y):
                        code1 += [f'mov\t{ry}, #{y}']


                    if re.match(local_pattern, x):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, x).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'str\t{ry}, [sp, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'str\t{ry}, [sp, {temp}]']

                    elif re.match(global_pattern, x):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = assember.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, x).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'str\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = assember.findTemp(num)
                            code1 += [f'str\t{ry}, [{address_reg}, {temp}]']
                    
                    codigo_medio += ['\t' + i for i in code1]
                    assember.removeVariable(y, ry)

                elif len(estructura) == 1:
                    code1 = [f'{estructura[0]}:']
                    codigo_medio += code1

        self.code_assembler += [''] + ['.global_stack:\t.long\tglobal_var'] + [''] + [f'global_var:\t.zero\t{self.global_size}']

    def getConditional(self, op1, operador, op2):
        code = []
        branch = None

        if operador == '==':
            code = [f'cmp\t{op1}, {op2}']
            branch = 'beq'

        elif operador == '<':
            code = [f'cmp\t{op1},{op2}']
            branch = 'blt'

        elif operador == '>':
            code = [f'cmp\t{op1},{op2}']
            branch = 'bgt'

        return code, branch

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