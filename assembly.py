from prettytable import PrettyTable

class Assembler():
    def __init__(self):
        self.register_descriptor = {}
        self.address_descriptor = {}
        self.pool_registers = []

        self.registers = []

        self.init()

    def init(self):
        for i in range(3):
            self.pool_registers.append(f'r{i}')
            self.register_descriptor[f'r{i}'] = []

            self.registers.append(f'r{i}')

    def is_number(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def getReg(self, x, y, z = None):
        Rx, Ry, Rz = [None, None, None]
        # print(I)
        # I_ = I.split()

        # x, y, z = [I_[0], I_[2], I_[4]]
        self.addAddressDescriptor(x, x)
        print('GET REG:', x, y, z)

        # PARTE DE Ry
        if self.is_number(y):
            Ry = self.getRegister(x, y, z, 'y', None, None)
        else:
            self.addAddressDescriptor(y, y)
            result, register = self.checkVariableInRegister(y)
            if result:
                Ry = register
            else:
                register = self.getRegister(x, y, z, 'y', None, None)

                Ry = register
        self.register_descriptor[Ry] = [y]
        self.addAddressDescriptor(y, Ry)

        # PARTE DE Rz
        if z:
            if self.is_number(z):
                Rz = f'#{int(z)}'
            else:
                self.addAddressDescriptor(z, z)
                result, register = self.checkVariableInRegister(z)
                if result:
                    Rz = register
                else:
                    register = self.getRegister(x, y, z, 'z', Ry, None)
                    
                    Rz = register
                self.register_descriptor[Rz] = [z]
                self.addAddressDescriptor(z, Rz)

        # PARTE DE Rx
            result, register = self.checkVariableInRegister(x)
            if result:
                Rx = register
            else:
                Rx = self.getRegister(x, y, z, 'x', Ry, Rz)
                self.register_descriptor[Rx] = [x]
                self.addAddressDescriptor(x, Rx)

        else:
            Rx = Ry
            self.register_descriptor[Ry].append(x)
            self.address_descriptor[x] = [Ry]

        print(f'Rx: {Rx}, Ry: {Ry}, Rz: {Rz}')
        return Rx, Ry, Rz

    def checkVariableInRegister(self, var):
        for key, value in self.register_descriptor.items():
            if var in value:
                return True, key
        return False, ''

    def getRegister(self, x, y, z, selection, Ry, Rz):
        for key, value in self.register_descriptor.items():
            if len(value) == 0:
                return key

        if selection == 'x':
            for key, value in self.register_descriptor.items():
                if len(value) == 1 and x in value:
                    return key

            self.removeRegisterFromAddressDescriptor(y, Ry)
            return Ry

        # CASO 1
        for key, value in self.address_descriptor.items():
            if len(value) > 1:
                for v in value:
                    if selection == 'y':
                        if v in self.registers:
                            self.address_descriptor[key].remove(v)
                            return v
                    elif selection == 'z':
                        if v in self.registers and v != Ry:
                            self.address_descriptor[key].remove(v)
                            return v

        
        # CASO 2 para Y y Z 
        for key, value in self.register_descriptor.items():
            if len(value) == 1:
                v = value[0]
                if selection == 'y':
                    if v == x and x != z:
                        return key

                elif selection == 'z':
                    if v == x and x != y and key != Ry:
                        return key

        # CASO 3
        # Falta implementar el DERRAME ?

        return None

    def addAddressDescriptor(self, value, register):
        if value in self.address_descriptor.keys():
            if register not in self.address_descriptor[value]:
                self.address_descriptor[value].append(register)
        else:
            self.address_descriptor[value] = [register]

    def removeRegisterFromAddressDescriptor(self, value, register):
        self.address_descriptor[value].remove(register)

    def ToTable(self):
        pretty_table = PrettyTable()
        pretty_table.field_names = list(self.register_descriptor.keys())
        pretty_table.add_row(list(self.register_descriptor.values()))

        print(' ** REGISTER DESCRIPTOR **')
        print(pretty_table)
        pretty_table.clear_rows()

        pretty_table = PrettyTable()
        pretty_table.field_names = self.address_descriptor.keys()
        pretty_table.add_row(self.address_descriptor.values())

        print(' ** ADDRESS DESCRIPTOR **')
        print(pretty_table)
        pretty_table.clear_rows()

# ass = Assembler()
# inst = [
#     't0 = 4 * 2',
# 	't1 = t0 + 0',
# 	't0 = y * t1',
# 	'y = x + t1',
# 	't0 = 4 * 1',
# 	't1 = t0 + 0'
# ]
# for I in inst:
#     ass.getReg(I)
#     ass.ToTable()