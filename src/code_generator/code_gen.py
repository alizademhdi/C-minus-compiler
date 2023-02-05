from code_generator.semantic_stack import SemanticStack
from code_generator.program_block import ProgramBlock, Instruction
from code_generator.data_block import DataBlock
from code_generator.temporaries_block import TemporariesBlock


class CodeGenerator:
    def __init__(self):
        self.semantic_stack = SemanticStack()
        self.program_block = ProgramBlock()
        self.data_block = DataBlock()
        self.temporaries = TemporariesBlock()
        self.break_list = []
        self.args_num = 0
        self.current_call_func = None
        self.function_dict = {
            31: self.jpf,
            32: self.jp,
            33: self.while_end,
            36: self.end_switch,
            39: self.jp_case,
            42: self.assign,
            45: self.array_cell,
            46: self.relop,
            50: self.add,
            54: self.mult,
            28: self.pop_exp,
            68: self.pid,
            69: self.push,
            70: self.push_num,
            71: self.push,
            72: self.break_while,
            73: self.save,
            74: self.jpf_save,
            75: self.func,
            76: self.variable_declaration,
            77: self.array_declaration,
            78: self.label_while,
            79: self.label_switch,
            80: self.output,
            81: self.push_size,
            10: self.end_func,
            15: self.add_param,
            16: self.add_param,
            9: self.push_void,
            67: self.increase_args_num,
            66: self.increase_args_num,
            63: self.reset_args_num,
            82: self.save_func,
            83: self.pid_dec,
        }

    def pid(self, lexeme):
        data = self.data_block.get_data(lexeme)
        self.semantic_stack.push(data.address)

    def pid_dec(self, lexeme):
        typ = self.semantic_stack.pop()
        address = self.data_block.create_data(lexeme, typ)
        self.semantic_stack.push(address)

    def assign(self):
        value = self.semantic_stack.pop()
        address = self.semantic_stack.pop()
        instruction = Instruction('ASSIGN', value, address, ' ')
        self.semantic_stack.push(value)
        self.program_block.add_instruction(instruction)

    def pop_exp(self):
        self.semantic_stack.pop()
        pass

    def variable_declaration(self):
        address = self.semantic_stack.pop()
        instruction = Instruction('ASSIGN', '#0', address, ' ')
        self.program_block.add_instruction(instruction)
        data = self.data_block.get_data_from_address(address)
        data.set_keyword('var')

    def array_declaration(self):
        size = self.semantic_stack.pop()
        address = self.semantic_stack.pop()
        instruction = Instruction('ASSIGN', '#0', address, ' ')
        self.program_block.add_instruction(instruction)
        self.data_block.increase_index(size)
        data = self.data_block.get_data_from_address(address)
        data.set_keyword('array')
        data.set_num_args(size)

    def save(self):
        self.semantic_stack.push(self.program_block.last_index)
        self.program_block.increase_index()

    def push(self, lexeme):
        self.semantic_stack.push(lexeme)

    def push_void(self):
        self.semantic_stack.push('void')

    def push_num(self, lexeme):
        temp = self.temporaries.get_temp()
        instruction = Instruction('ASSIGN', f'#{lexeme}', temp, ' ')
        self.program_block.add_instruction(instruction)
        self.semantic_stack.push(temp)

    def push_size(self, size):
        self.semantic_stack.push(size)

    def add(self):
        op_1 = self.semantic_stack.pop()
        operator = self.semantic_stack.pop()
        op_2 = self.semantic_stack.pop()
        temp = self.temporaries.get_temp()
        if operator == '+':
            instruction = Instruction('ADD', op_2, op_1, temp)
        else:
            instruction = Instruction('SUB', op_2, op_1, temp)
        self.program_block.add_instruction(instruction)
        self.semantic_stack.push(temp)

    def mult(self):
        op_1 = self.semantic_stack.pop()
        operator = self.semantic_stack.pop()
        op_2 = self.semantic_stack.pop()
        temp = self.temporaries.get_temp()
        instruction = None
        if operator == '*':
            instruction = Instruction('MULT', op_2, op_1, temp)
        elif operator == '/':
            instruction = Instruction('DIV', op_2, op_1, temp)
        self.program_block.add_instruction(instruction)
        self.semantic_stack.push(temp)

    def func(self):
        address = self.semantic_stack.get_top()
        data = self.data_block.get_data_from_address(address)
        data.set_keyword('func')
        self.data_block.add_virtual_row()

    def jp(self):
        address = self.semantic_stack.pop()
        instruction = Instruction('JP', self.program_block.last_index, ' ', ' ')
        self.program_block.set_instruction(address, instruction)

    def jpf(self):
        address = self.semantic_stack.pop()
        condition = self.semantic_stack.pop()
        instruction = Instruction('JPF', condition, self.program_block.last_index, ' ')
        self.program_block.set_instruction(address, instruction)

    def relop(self):
        op_1 = self.semantic_stack.pop()
        operator = self.semantic_stack.pop()
        op_2 = self.semantic_stack.pop()
        temp = self.temporaries.get_temp()
        instruction = None
        if operator == '<':
            instruction = Instruction('LT', op_2, op_1, temp)
        elif operator == '==':
            instruction = Instruction('EQ', op_2, op_1, temp)
        self.program_block.add_instruction(instruction)
        self.semantic_stack.push(temp)

    def jpf_save(self):
        instruction_address = self.semantic_stack.pop()
        instruction = Instruction('JPF', self.semantic_stack.pop(), self.program_block.last_index + 1, ' ')
        self.program_block.set_instruction(instruction_address, instruction)
        self.semantic_stack.push(self.program_block.last_index)
        self.program_block.increase_index()

    def label_while(self):
        self.break_list.insert(0, -1)
        self.semantic_stack.push(self.program_block.last_index)
        self.program_block.increase_index()
        temp = self.temporaries.get_temp()
        self.semantic_stack.push(temp)
        self.semantic_stack.push(self.program_block.last_index)

    def while_end(self):
        address_to_jpf = self.semantic_stack.pop()
        expression = self.semantic_stack.pop()
        end_of_while_address = self.program_block.last_index + 1
        instruction = Instruction('JPF', expression, f'#{end_of_while_address}', ' ')
        self.program_block.set_instruction(address_to_jpf, instruction)

        address_to_jp = self.semantic_stack.pop()
        instruction = Instruction('JP', address_to_jp, ' ', ' ')
        self.program_block.add_instruction(instruction)

        temp_address = self.semantic_stack.pop()
        instruction = Instruction('ASSIGN', f'#{end_of_while_address}', temp_address, ' ')
        self.program_block.set_instruction(self.semantic_stack.pop(), instruction)
        self.fill_breaks(self.program_block.last_index)

    def fill_breaks(self, end_address):
        end_index = -1
        for i, address in enumerate(self.break_list):
            if address < 0:
                end_index = i
                break
        if end_index <= -1:
            raise Exception('Error in break list')
        for address in self.break_list[:end_index]:
            instruction = Instruction('JP', end_address, ' ', ' ')
            self.program_block.set_instruction(address, instruction)
        self.break_list = self.break_list[end_index + 1:]

    def break_while(self):
        if len(self.break_list) == 0:
            raise Exception('Break outside of while')
        self.break_list.insert(0, self.program_block.last_index)
        self.program_block.increase_index()

    def array_cell(self):
        index = self.semantic_stack.pop()
        address = self.semantic_stack.pop()
        temp = self.temporaries.get_temp()
        instruction = Instruction('MULT', index, '#4', temp)
        self.program_block.add_instruction(instruction)
        instruction = Instruction('ADD', f'#{address}', temp, temp)
        self.program_block.add_instruction(instruction)
        self.semantic_stack.push(f'@{temp}')

    def output(self):
        arg_result = self.semantic_stack.get_top()
        instruction = Instruction('PRINT', arg_result, ' ', ' ')
        self.program_block.add_instruction(instruction)

    def label_switch(self):
        self.break_list.insert(0, -1)

    def jp_case(self):
        jump_line = self.semantic_stack.pop()
        equal_condition_line = self.semantic_stack.pop()
        case_value = self.semantic_stack.pop()
        switch_value = self.semantic_stack.get_top()

        temp = self.temporaries.get_temp()
        instruction = Instruction('EQ', switch_value, case_value, temp)
        self.program_block.set_instruction(equal_condition_line, instruction)
        instruction = Instruction('JPF', temp, self.program_block.last_index, ' ')
        self.program_block.set_instruction(jump_line, instruction)

    def end_switch(self):
        self.semantic_stack.pop()
        self.fill_breaks(self.program_block.last_index)

    def end_func(self):
        self.data_block.end_scope()
        self.semantic_stack.pop()

    def add_param(self):
        param_address = self.semantic_stack.pop()
        param_data = self.data_block.get_data_from_address(param_address)
        param_data.set_keyword('param')
        func_address = self.semantic_stack.get_top()
        func_data = self.data_block.get_data_from_address(func_address)
        func_data.add_param(len(self.data_block.all_data) - 1)
        # TODO: get index of param from its data

    def increase_args_num(self):
        self.args_num += 1

    def reset_args_num(self):
        func_data = self.data_block.get_data_from_address(self.current_call_func)
        if len(func_data.params) != self.args_num:
            raise Exception('Wrong number of arguments')
        for i in range(self.args_num):
            self.semantic_stack.pop()
        self.current_call_func = None
        self.args_num = 0

    def save_func(self):
        func_addr = self.semantic_stack.get_top()
        self.current_call_func = func_addr
