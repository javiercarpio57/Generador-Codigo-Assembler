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
        self.conditions = {
            '==': 'beq',
            '<': 'blt',
            '>': 'bgt',
            '!=': 'bne',
            '<=': 'ble',
            '>=': 'bge'
        }
        self.current_assembler = None
        
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
                    self.current_assembler = a.Assembler()
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
                        epilogo = [f'add\tsp, sp, #{self.current_size}'] + ['bx\tlr']
                    else:
                        prologo = ['push\t{r11, lr}'] + ['mov\tr11, sp']
                        epilogo = ['mov\tsp, r11'] + ['pop\t{r11, lr}'] + ['bx\tlr']

                    prologo += [f'sub\tsp, sp, #{self.current_size}']
                    # epilogo += epilogo
                
                    if estructura[-1] == 'InputInt':
                        codigo_medio = ['\tldr\tr0, =0xFF200050'] + ['\tldr\tr0, [r0]']
                    elif estructura[-1] == 'OutputInt':
                        codigo_medio = ['\tldr\tr1, =0xFF201000'] + ['\tadd\tr0, r0, #48'] + ['\tstr\tr0, [r1]']

                    prologo = ['\t' + i for i in prologo]
                    epilogo = ['\t' + i for i in epilogo]
                    self.code_assembler += tag + prologo + codigo_medio + epilogo + ['']
                    self.current_assembler.ToTable()

                elif estructura[0] == 'PARAM':
                    code1 = []
                    value = estructura[1]
                    registro = f'r{params}'
                    params += 1
                    old = self.current_assembler.register_descriptor[registro]
                    print(' --> PARAMMM ORIGINAL', value, params, old)

                    for o in old:
                        if o != value:
                            print(' --> PARAM', o)
                            if o[0] in 'LG':
                                if o[0] == 'L':
                                    num = re.search(local_pattern, o).group(1)

                                    if self.is_number(num):
                                        code1 += [f'str\t{registro}, [sp, #{num}]']
                                    else:
                                        temp = self.current_assembler.findTemp(num)
                                        code1 += [f'str\t{registro}, [sp, {temp}]']

                                    self.current_assembler.address_descriptor[o] = [o]
                                else:
                                    pat = r'\[(.*)\]'
                                    _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                                    code1 += [f'ldr\t{address_reg}, .global_stack']
                                    num = re.search(global_pattern, o).group(1)
                                    
                                    if self.is_number(num):
                                        code1 += [f'str\t{registro}, [{address_reg}, #{num}]']
                                    else:
                                        temp = self.current_assembler.findTemp(num)
                                        code1 += [f'str\t{registro}, [{address_reg}, {temp}]']
                            elif o[0] in 't' or o == 'R':
                                result, new_reg = self.current_assembler.checkVariableInRegister(o)
                                if not result or new_reg == registro:
                                    new_reg = self.current_assembler.getRegister(None, o, None, 'y', None, None)
                                old_reg = self.current_assembler.findTemp(o)
                                code1 += [f'mov\t{new_reg}, {old_reg}']
                                print(f'DESPLAZANDO TEMP DE {old_reg} A {new_reg}')
                                self.current_assembler.removeVariable(o, old_reg)
                                self.current_assembler.address_descriptor[o] = [o, new_reg]
                                self.current_assembler.register_descriptor[new_reg] = [o]
                                self.current_assembler.ToTable()



                    if re.match(local_pattern, value):
                        num = re.search(local_pattern, value).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{registro}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{registro}, [sp, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif re.match(global_pattern, value):
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(global_pattern, value).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{registro}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{registro}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif value[0] == 't' or value == 'R':
                        self.current_assembler.ToTable()
                        temp = self.current_assembler.findTemp(value)
                        print(f'ASIGNANDO {registro} <- {temp}')
                        code1 += [f'mov\t{registro}, {temp}']
                        self.current_assembler.removeVariable(value, temp)

                    elif self.is_number(value):
                        code1 += [f'mov\t{registro}, #{value}']
                    # else:
                    #     temp = self.current_assembler.findTemp(value)
                    #     code1 += [f'mov\t{registro}, {temp}']
                        # self.current_assembler.removeVariable(value, temp)

                    # self.current_assembler.register_descriptor[registro] = [value]
                    # self.current_assembler.addAddressDescriptor(value, registro)
                    self.current_assembler.register_descriptor[registro] = [value]
                    self.current_assembler.addAddressDescriptor(value, registro)
                    codigo_medio += ['\t' + i for i in code1]

                elif estructura[0] == 'CALL':
                    params = 0
                    isLeaf = False
                    code1 = [f'bl\t{estructura[1][:-1]}']
                    metodo = self.look_up(estructura[1][:-1])
                    if metodo['Tipo'] != 'void':
                        self.current_assembler.addAddressDescriptor('R', 'R')
                        self.current_assembler.addAddressDescriptor('R', 'r0')
                        self.current_assembler.register_descriptor['r0'] = ['R']

                    codigo_medio += ['\t' + i for i in code1]
                
                elif estructura[0] == 'RETURN':
                    value = estructura[1]
                    registro = 'r0'
                    code1 = []
                    
                    if re.match(local_pattern, value):
                        num = re.search(local_pattern, value).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{registro}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{registro}, [sp, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif re.match(global_pattern, value):
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(global_pattern, value).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{registro}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{registro}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif value[0] == 't' or value == 'R':
                        temp = self.current_assembler.findTemp(value)
                        code1 += [f'mov\t{registro}, {temp}']
                        self.current_assembler.removeVariable(value, temp)
                        try:
                            self.current_assembler.removeVariable(value, registro)
                        except ValueError:
                            print('A PRUEBA DE ERRORES')
                            
                    elif self.is_number(value):
                        code1 += [f'mov\t{registro}, #{value}']

                    codigo_medio += ['\t' + i for i in code1]
                
                elif estructura[0] == 'GOTO':
                    code1 = [f'b\t{estructura[1]}']

                    codigo_medio += ['\t' + i for i in code1]

                elif estructura[0] == 'IF':
                    _, op1, op, op2, _, branch = estructura
                    code1 = []
                    operando1, op, operando2 = [None, op, None]
                    _, ry, rz = self.current_assembler.getReg(None, op1, op2)
                    
                    if re.match(local_pattern, op1):
                        num = re.search(local_pattern, op1).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif re.match(global_pattern, op1):
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(global_pattern, op1).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif op1[0] == 't':
                        temp = self.current_assembler.findTemp(op1)
                        code1 += [f'mov\t{ry}, {temp}']
                    elif self.is_number(op1):
                        code1 += [f'mov\t{ry}, #{op1}']


                    if re.match(local_pattern, op2):
                        num = re.search(local_pattern, op2).group(1)
                        if self.is_number(num):
                            code1 += [f'ldr\t{rz}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{rz}, [sp, {temp}]']
                            self.current_assembler.removeVariable(num, temp)
                    elif re.match(global_pattern, op2):
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(global_pattern, op2).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{rz}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{rz}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)
                    elif op2[0] == 't':
                        temp = self.current_assembler.findTemp(op2)
                        code1 += [f'mov\t{rz}, {temp}']
                    elif self.is_number(op2):
                        code1 += [f'mov\t{rz}, #{op2}']

                    self.current_assembler.removeVariable(op1, ry)
                    self.current_assembler.removeVariable(op2, rz)
                    result, b = self.getConditional(ry, op, rz)
                    codigo_medio += ['\t' + i for i in code1] + ['\t' + i for i in result] + [f'\t{b}\t{branch}']

                elif len(estructura) == 5:
                    x, y, z = [estructura[0], estructura[2], estructura[4]]
                    rx, ry, rz = self.current_assembler.getReg(x, y, z)

                    code1 = []
                    code2 = []
                    code3 = []
                    if re.match(local_pattern, y):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']

                    elif re.match(global_pattern, y):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [{address_reg}, {temp}]']
                        
                    elif self.is_number(y):
                        code1 += [f'mov\t{ry}, #{y}']

                    
                    if re.match(local_pattern, z):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, z).group(1)

                        if self.is_number(num):
                            code2 += [f'ldr\t{rz}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code2 += [f'ldr\t{rz}, [sp, {temp}]']

                    elif re.match(global_pattern, z):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code2 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, z).group(1)
                        
                        if self.is_number(num):
                            code2 += [f'ldr\t{rz}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code2 += [f'ldr\t{rz}, [{address_reg}, {temp}]']

                    elif self.is_number(z):
                        code2 = [f'mov\t{rz}, #{z}']

                    operator = estructura[3]

                    code3 = [f'{self.operators[operator]}\t{rx}, {ry}, {rz}']

                    self.current_assembler.removeVariable(y, ry)
                    self.current_assembler.removeVariable(z, rz)
                    codigo_medio += ['\t' + i for i in code1] + ['\t' + i for i in code2] + ['\t' + i for i in code3]

                elif len(estructura) == 3:
                    x, y = [estructura[0], estructura[2]]
                    rx, ry, _ = self.current_assembler.getReg(x, y)
                    code1 = []

                    if re.match(local_pattern, y):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [sp, {temp}]']
                            self.current_assembler.removeVariable(num, temp)

                    elif re.match(global_pattern, y):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, y).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'ldr\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'ldr\t{ry}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)
                        
                    elif self.is_number(y):
                        code1 += [f'mov\t{ry}, #{y}']


                    if re.match(local_pattern, x):
                        pat = r'\[(.*)\]'
                        num = re.search(pat, x).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'str\t{ry}, [sp, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'str\t{ry}, [sp, {temp}]']

                    elif re.match(global_pattern, x):
                        pat = r'\[(.*)\]'
                        _, address_reg, _ = self.current_assembler.getReg(None, '.global_stack')
                        code1 += [f'ldr\t{address_reg}, .global_stack']
                        num = re.search(pat, x).group(1)
                        
                        if self.is_number(num):
                            code1 += [f'str\t{ry}, [{address_reg}, #{num}]']
                        else:
                            temp = self.current_assembler.findTemp(num)
                            code1 += [f'str\t{ry}, [{address_reg}, {temp}]']
                            self.current_assembler.removeVariable(num, temp)
                    
                    codigo_medio += ['\t' + i for i in code1]
                    self.current_assembler.removeVariable(y, ry)

                elif len(estructura) == 1:
                    code1 = [f'{estructura[0]}:']
                    codigo_medio += code1

        self.code_assembler += [''] + ['.global_stack:\t.long\tglobal_var'] + [''] + [f'global_var:\t.zero\t{self.global_size}']

    def getConditional(self, op1, operador, op2):
        code = [f'cmp\t{op1}, {op2}']
        branch = self.conditions[operador]

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