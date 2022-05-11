from __future__ import annotations
from typing import Optional

from ast_nodes import *

import ply.yacc as yacc
from errors import e_SyntaxError
from lexer import MyLexer
import errors



class MyParser:
    tokens = MyLexer.tokens

    def __init__(self, lexer: MyLexer, debug=False) -> None:
        self.lexer = lexer
        self.parser = yacc.yacc(module=self)
        self.debug = debug

        self.source_code: str = ""
        self.syntax_errors: list[e_SyntaxError] = []

        self.incomplete_blocks: list[str] = []


    def parse(self, source_code: str) -> Program:
        self.source_code = source_code
        errors.set_source_code(source_code)


        result = self.parser.parse(source_code, debug=self.debug)
        print(self.incomplete_blocks)

        return result



    def add_error(self, error):
        self.syntax_errors.append(error)
        if self.debug:
            print(error)

    def add_syntax_error(self, bad_token, expected: Optional[str] = None, error_type: Optional[str] = None, details: Optional[str] = None):
        
        # Suppress errors about unexpected "FinTq" and "FinPour" if we have encountered un incomplete block of the corresponding type
        if len(self.incomplete_blocks) > 0:
            if self.incomplete_blocks[-1] == "pour" and bad_token.type == "FINPOUR":
                self.incomplete_blocks.pop()
                return
            if self.incomplete_blocks[-1] == "tant_que" and bad_token.type == "FINTQ":
                self.incomplete_blocks.pop()
                return

        self.add_error(e_SyntaxError(bad_token, expected, error_type, details))


    def p_program_def(self, p):
        '''program_def : main_algo_definition opt_sub_algo_defs_list EOF'''
        p[0] = Program(p[1], p[2])

    def p_program_error(self, p):
        '''program_def : main_algo_definition sub_algo_defs_list error'''
        self.add_syntax_error(p[3], "Sous-algo")


    def p_main_algo_definition(self, p):
        '''main_algo_definition : main_algo_header opt_type_defs_section variables_section statements_section main_algo_footer'''
        p[0] = MainAlgorithm(p[1], p[2], p[3], p[4])


    def p_main_algo_header(self, p):
        '''main_algo_header : algorithme id newline'''
        self.incomplete_blocks.append("main_algo")
        p[0] = p[2]

    def p_main_algo_footer(self, p):
        '''main_algo_footer : FINALGO newline'''
        assert self.incomplete_blocks.pop() == "main_algo"

    def p_main_algo_footer_error(self, p):
        '''main_algo_footer : error'''
        self.add_syntax_error(p[1], "Mot clé 'FinAlgo'")
        assert self.incomplete_blocks.pop() == "main_algo"

        

    def p_main_algo_definition_error_finalgo(self, p):
        '''main_algo_definition : main_algo_header opt_type_defs_section variables_section statements_section error main_algo_footer'''
        self.add_syntax_error(p[5], "Instruction ou 'FinAlgo'")

    def p_main_algo_definition_error_statements(self, p):
        '''main_algo_definition : main_algo_header opt_type_defs_section variables_section error main_algo_footer'''
        self.add_syntax_error(p[4], "Déclaration de variable ou section instructions")

    def p_main_algo_definition_error_variables(self, p):
        '''main_algo_definition : main_algo_header type_defs_section error main_algo_footer'''
        self.add_syntax_error(p[3], "Déclaration de type ou section variables")

    def p_main_algo_definition_error_typedef(self, p):
        '''main_algo_definition : main_algo_header error main_algo_footer'''
        self.add_syntax_error(p[2], "Section types ou section variables")


    def p_opt_type_defs_section(self, p):
        '''opt_type_defs_section : type_defs_section
                                 | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_type_defs_section(self, p):
        '''type_defs_section : types_header'''
        p[0] = p[1]


    def p_opt_sub_algo_defs_list(self, p):
        '''opt_sub_algo_defs_list : sub_algo_defs_list
                                  | empty'''

        p[0] = p[1] if p[1] is not None else []

    def p_sub_algo_defs_list(self, p):
        '''sub_algo_defs_list : sub_algo_definition'''
        p[0] = [p[1]]
    
    def p_sub_algo_defs_list_append(self, p):
        '''sub_algo_defs_list : sub_algo_defs_list sub_algo_definition'''
        p[0] = p[1] + [p[2]]


    def p_sub_algo_definition(self, p):
        '''sub_algo_definition : sub_algo_header inputs_section outputs_section variables_section statements_section sub_algo_footer'''
        p[0] = SubAlgorithm(p[1], p[2], p[3], p[4], p[5])


    def p_sub_algo_header(self, p):
        '''sub_algo_header : sa id newline'''
        self.incomplete_blocks.append("sub_algo")
        p[0] = p[2]

    def p_sub_algo_footer(self, p):
        '''sub_algo_footer : FINSA newline'''
        assert self.incomplete_blocks.pop() == "sub_algo"


    def p_sub_algo_definition_error_statements(self, p):
        '''sub_algo_definition : sub_algo_header inputs_section outputs_section variables_section error sub_algo_footer'''
        self.add_syntax_error(p[5], "Déclaration de variable ou section instructions")

    def p_sub_algo_definition_error_variables(self, p):
        '''sub_algo_definition : sub_algo_header inputs_section outputs_section error sub_algo_footer'''
        self.add_syntax_error(p[4], "Déclaration de paramètre de sortie ou section variables")

    def p_sub_algo_definition_error_outputs(self, p):
        '''sub_algo_definition : sub_algo_header inputs_section error sub_algo_footer'''
        self.add_syntax_error(p[3], "Déclaration variable d'entrée ou section paramètres de sortie")

    def p_sub_algo_definition_error_inputs(self, p):
        '''sub_algo_definition : sub_algo_header error sub_algo_footer'''
        self.add_syntax_error(p[2], "Section paramètres d'entrée")


    def p_variables_section(self, p):
        '''variables_section : variables_header opt_var_declaration_list'''
        p[0] = p[2]

    def p_inputs_section(self, p):
        '''inputs_section : inputs_header opt_var_declaration_list'''
        p[0] = p[2]

    def p_outputs_section(self, p):
        '''outputs_section : outputs_header opt_var_declaration_list'''
        p[0] = p[2]

    def p_opt_var_declaration_list(self, p):
        '''opt_var_declaration_list : var_declaration_list
                                    | empty
        '''
        p[0] = p[1] if p[1] is not None else []
    
    def p_var_declaration_list(self, p):
        '''var_declaration_list : var_declaration_line'''
        p[0] = [p[1]]
    
    def p_var_declaration_list_append(self, p):
        '''var_declaration_list : var_declaration_list var_declaration_line'''
        p[0] = p[1] + [p[2]]


    def p_var_declaration_line(self, p):
        '''var_declaration_line : id_list ':' complex_type newline'''
        p[0] = VariableDeclarationLine(p[1], p[3])

    def p_var_declaration_line_error_type(self, p):
        '''var_declaration_line : id_list ':' error NEWLINE'''
        self.add_syntax_error(p[3], "Type")

    def p_var_declaration_line_error_colon(self, p):
        '''var_declaration_line : id_list error NEWLINE'''
        self.add_syntax_error(p[2], "':'")


    def p_complex_type(self, p):
        '''complex_type : basetype
                        | table_type
                        | pointer_type
        '''
        p[0] = p[1]


    def p_basetype(self, p):
        '''basetype : id
                    | REEL
                    | ENTIER'''
        p[0] = p[1]

    def p_pointer_type(self, p):
        '''pointer_type : POINTEUR opt_sur complex_type'''
        p[0] = PtrType(p[3], p=p)

    def p_pointer_type_error_type(self, p):
        '''pointer_type : POINTEUR SUR error'''
        self.add_syntax_error(p[3], "Type pointé")

    def p_pointer_type_error(self, p):
        '''pointer_type : POINTEUR error'''
        self.add_syntax_error(p[2], "Mot clé 'sur' ou type pointé")


    

    def p_table_range(self, p):
        '''table_range : lit_int POINTS lit_int
                       | lit_int POINTS empty'''
        p[0] = p[1], p[3]

    def p_table_range_error_points(self, p):
        '''table_range : lit_int error'''
        self.add_syntax_error(p[2], "Séparateur d'indices '..'")


    def p_table_range_list(self, p):
        '''table_range_list : table_range'''
        p[0] = [p[1]]
        
    def p_table_range_list_append(self, p):
        '''table_range_list : table_range_list ',' table_range'''
        p[0] = p[1] + [p[3]]

    def p_table_range_list_error(self, p):
        '''table_range_list : table_range_list ',' error'''
        self.add_syntax_error(p[3], "Dimmensions du tableau après virgule ',' '")


    def p_table_type(self, p):
        '''table_type : TABLEAU '[' table_range_list ']' opt_de complex_type  '''
        p[0] = TableType(p[3], p[6], p=p)

    def p_table_type_error_type(self, p):
        '''table_type : TABLEAU '[' table_range_list ']' DE error'''
        self.add_syntax_error(p[6], "Type des éléments du tableau")

    def p_table_type_error_de(self, p):
        '''table_type : TABLEAU '[' table_range_list ']' error'''
        self.add_syntax_error(p[5], "Mot clé 'de' ou type des éléments du tableau")

    def p_table_type_error_closing(self, p):
        '''table_type : TABLEAU '[' table_range_list error'''
        self.add_syntax_error(p[4], "Virgule ',' suivie de dimmensions du tableau ou de crochet droit ']'")

    def p_table_type_error_range(self, p):
        '''table_type : TABLEAU '[' error'''
        self.add_syntax_error(p[3], "Dimmensions du tableau")


    def p_table_type_error_opening(self, p):
        '''table_type : TABLEAU error'''
        self.add_syntax_error(p[2], "Crochet gauche '['")


    def p_statements_section(self, p):
        '''statements_section : instructions_header opt_statements_list'''
        p[0] = p[2]

    def p_opt_statements_list(self, p):
        '''opt_statements_list : statements_list
                               | empty'''
        p[0] = p[1] if p[1] is not None else []


    def p_statements_list(self, p):
        '''statements_list : statement'''
        p[0] = [p[1]]

    def p_statements_list_append(self, p):
        '''statements_list : statements_list statement'''
        p[0] = p[1] + [p[2]]


    def p_statement(self, p):
        '''statement : assignment_statement
                     | expression_statement
                     | function_statement
                     | pour_statement
                     | tq_statement
                     | si_statement'''
        p[0] = p[1]


    def p_assignment_statement(self, p):
        '''assignment_statement : expression L_ARROW expression newline'''
        p[0] = AssignmentStatement(p[1], p[3], s=p[1])

    def p_assignement_statement_error(self, p):
        '''assignment_statement : expression L_ARROW error NEWLINE'''
        self.add_syntax_error(p[3], "Expression")


    def p_expression_statement(self, p):
        '''expression_statement : expression newline'''
        p[0] = ExpressionStatement(p[1], s=p[1])

    
    def p_function_statement(self, p):
        '''function_statement : id '(' function_inputs_list '!' function_outputs_list ')' newline'''
        p[0] = FunctionStatement(p[1], p[3], p[5], s=p[1])

    def p_function_statement_error(self, p):
        '''function_statement : id '(' function_inputs_list '!' error NEWLINE'''
        self.add_syntax_error(p[5], "Paramètres de sortie ou parenthèse droite ')'")

    def p_function_outputs_list(self, p):
        '''function_outputs_list : opt_expression_list'''
        p[0] = p[1]

    def p_function_outputs_list_error(self, p):
        '''function_outputs_list : expression_list ',' error'''
        self.add_syntax_error(p[3], "Paramètre de sortie après virgule ','")


    def p_pour_statement(self, p):
        '''pour_statement : pour_header opt_statements_list pour_footer'''
        _id, start, end = p[1] if p[1] is not None else [None, None, None]
        p[0] = PourStatement(_id, start, end, p[2], p=p)

    def p_pour_header(self, p):
        '''pour_header : POUR ID ALLANT DE expression A expression newline'''
        self.incomplete_blocks.append("pour")
        p[0] = (p[2], p[5], p[7])

    def p_pour_header_error_end_expression(self, p):
        '''pour_header : POUR ID ALLANT DE expression A error NEWLINE'''
        self.add_syntax_error(p[7], "Valeur de fin d'itération")
        self.incomplete_blocks.append("pour")

    def p_pour_header_error_a(self, p):
        '''pour_header : POUR ID ALLANT DE expression error NEWLINE'''
        self.add_syntax_error(p[6], "Mot clé 'a'")
        self.incomplete_blocks.append("pour")

    def p_pour_header_error_start_expression(self, p):
        '''pour_header : POUR ID ALLANT DE error NEWLINE'''
        self.add_syntax_error(p[5], "Valeur de début d'itération")
        self.incomplete_blocks.append("pour")

    def p_pour_header_error_de(self, p):
        '''pour_header : POUR ID ALLANT error NEWLINE'''
        self.add_syntax_error(p[4], "Mot clé 'de'")
        self.incomplete_blocks.append("pour")

    def p_pour_header_error_allant(self, p):
        '''pour_header : POUR ID error NEWLINE'''
        self.add_syntax_error(p[3], "Mot clé 'allant'")
        self.incomplete_blocks.append("pour")

    def p_pour_header_error_variable(self, p):
        '''pour_header : POUR error NEWLINE'''
        self.add_syntax_error(p[2], "Variable d'itération")
        self.incomplete_blocks.append("pour")


    def p_pour_footer(self, p):
        '''pour_footer : FINPOUR newline'''
        assert self.incomplete_blocks.pop() == "pour"

    def p_pour_footer_error(self, p):
        '''pour_footer : error'''
        self.add_syntax_error(p[1], "Mot clé 'FinPour'")
        assert self.incomplete_blocks.pop() == "pour"
        

    def p_tq_statement(self, p):
        '''tq_statement : tq_header opt_statements_list tq_footer'''
        p[0] = TantQueStatement(p[1], p[2])

    def p_tq_header(self, p):
        '''tq_header : TANT QUE expression FAIRE newline'''
        p[0] = p[3]
        self.incomplete_blocks.append("tant_que")

    def p_tq_header_error_faire(self, p):
        '''tq_header : TANT QUE expression error NEWLINE'''
        self.add_syntax_error(p[4], "Mot clé 'Faire'")
        self.incomplete_blocks.append("tant_que")

    def p_tq_header_error_expression(self, p):
        '''tq_header : TANT QUE error NEWLINE'''
        self.add_syntax_error(p[3], "Condition de boucle")
        self.incomplete_blocks.append("tant_que")

    def p_tq_header_error_que(self, p):
        '''tq_header : TANT error NEWLINE'''
        self.add_syntax_error(p[2], "Mot clé 'que'")
        self.incomplete_blocks.append("tant_que")

    def p_tq_footer(self, p):
        '''tq_footer : FINTQ newline'''
        assert self.incomplete_blocks.pop() == "tant_que"
        
    def p_tq_footer_error(self, p):
        '''tq_footer : error'''
        self.add_syntax_error(p[1], "Mot clé 'FinTq'")
        assert self.incomplete_blocks.pop() == "tant_que"


    def p_si_statement(self, p):
        '''si_statement : SI condition_faire_instructions opt_sinonsi_list opt_sinon_section FINSI newline'''
        conditional_blocks = [p[2]] + p[3]
        default_block = p[4]
        p[0] = SiStatement(conditional_blocks, default_block, p=p)

    def p_si_statement_error(self, p):
        '''si_statement : SI condition_faire_instructions opt_sinonsi_list opt_sinon_section error NEWLINE'''
        self.add_syntax_error(p[5], "Instruction ou mot clé 'FinSi'")
        self.incomplete_blocks.append("si")



    
    def p_opt_sinonsi_list(self, p):
        '''opt_sinonsi_list : sinonsi_list
                            | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_opt_sinon_section(self, p):
        '''opt_sinon_section : sinon_section
                             | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_sinon_section(self, p):
        '''sinon_section : SINON newline opt_statements_list'''
        p[0] = p[3]

    def p_sinonsi_list(self, p):
        '''sinonsi_list : sinonsi_section'''
        p[0] = [p[1]]

    def p_sinonsi_list_append(self, p):
        '''sinonsi_list : sinonsi_list sinonsi_section'''
        p[0] = p[1] + [p[2]]

    def p_sinonsi_section(self, p):
        '''sinonsi_section : SINONSI condition_faire_instructions'''
        p[0] = p[2]

    def p_condition_faire_instructions(self, p):
        '''condition_faire_instructions : expression FAIRE newline opt_statements_list'''
        p[0] = ConditionalBlock(p[1], p[4])


    def p_primary_expression(self, p):
        '''primary_expression : id
                              | lit_int
                              | lit_float'''
        p[0] = p[1]


    def p_primary_expression_parens(self, p):
        '''primary_expression : '(' expression ')' '''
        p[0] = SubExpression(p[2], p=p)
        

    def p_primary_expression_parens_error_closing(self, p):
        '''primary_expression : '(' expression error'''
        self.add_syntax_error(p[3], "Parenthèse droite ')'")

    def p_p_primary_expression_parens_error_expression(self, p):
        '''primary_expression : '(' error'''
        self.add_syntax_error(p[2], "Expression")


    def p_expression(self, p):
        '''expression                : logical_or_expression
           expression                : function_expression
           logical_or_expression     : logical_and_expression
           logical_and_expression    : equality_expression
           equality_expression       : relational_expression
           relational_expression     : additive_expression
           additive_expression       : multiplicative_expression
           multiplicative_expression : unary_expression
           unary_expression          : postfix_expression'''
        p[0] = p[1]


    def p_logical_or_expression(self, p):
        '''logical_or_expression  : logical_or_expression OU logical_and_expression'''
        p[0] = BinaryOr(p[1], p[3], s=p[1])

    def p_logical_and_expression(self, p):
        '''logical_and_expression : logical_and_expression ET equality_expression'''
        p[0] = BinaryAnd(p[1], p[3], s=p[1])
            

    def p_relational_expression_lt(self, p):
        '''relational_expression : relational_expression '<' additive_expression'''
        p[0] = BinaryLT(p[1], p[3], s=p[1])

    def p_relational_expression_gt(self, p):
        '''relational_expression : relational_expression '>' additive_expression'''
        p[0] = BinaryLT(p[1], p[3], s=p[1])

    def p_relational_expression_lte(self, p):
        '''relational_expression : relational_expression LTE additive_expression'''
        p[0] = BinaryLT(p[1], p[3], s=p[1])

    def p_relational_expression_gte(self, p):
        '''relational_expression : relational_expression GTE additive_expression'''
        p[0] = BinaryLT(p[1], p[3], s=p[1])

    def p_additive_expression_plus(self, p):
        '''additive_expression : additive_expression '+' multiplicative_expression'''
        p[0] = BinaryPlus(p[1], p[3], s=p[1])

    def p_additive_expression_minus(self, p):
        '''additive_expression : additive_expression '-' multiplicative_expression'''
        p[0] = BinaryMinus(p[1], p[3], s=p[1])


    def p_multiplicative_expression_times(self, p):
        '''multiplicative_expression : multiplicative_expression '*' unary_expression''' 
        p[0] = BinaryTimes(p[1], p[3], s=p[1])

    def p_multiplicative_expression_divide(self, p):
        '''multiplicative_expression : multiplicative_expression '/' unary_expression'''
        p[0] = BinaryDivide(p[1], p[3], s=p[1])

    def p_multiplicative_expression_modulo(self, p):
        '''multiplicative_expression : multiplicative_expression '%' unary_expression'''
        p[0] = BinaryModulo(p[1], p[3], s=p[1])


    def p_binary_expression_error(self, p):
        '''logical_or_expression     : logical_or_expression     OU  error
           logical_and_expression    : logical_and_expression    ET  error
           relational_expression     : relational_expression     '<' error
           relational_expression     : relational_expression     '>' error
           relational_expression     : relational_expression     LTE error
           relational_expression     : relational_expression     GTE error
           additive_expression       : additive_expression       '+' error
           additive_expression       : additive_expression       '-' error
           multiplicative_expression : multiplicative_expression '*' error
           multiplicative_expression : multiplicative_expression '/' error
           multiplicative_expression : multiplicative_expression '%' error'''
        self.add_syntax_error(p[3], "Expression")



    def p_unary_expression_plus(self, p):
        '''unary_expression : '+' unary_expression'''
        p[0] = UnaryPlus(p[2], p=p)

    def p_unary_expression_minus(self, p):
        '''unary_expression : '-' unary_expression'''
        p[0] = UnaryMinus(p[2], p=p)

    def p_unary_expression_pointer(self, p):
        '''unary_expression : '&' unary_expression'''
        p[0] = UnaryDereference(p[2], p=p)

    def p_unary_expression_dereference(self, p):
        '''unary_expression : '^' unary_expression'''
        p[0] = UnaryPointer(p[2], p=p)

    def p_unary_expression_not(self, p):
        '''unary_expression : NON unary_expression'''
        p[0] = UnaryNot(p[2], p=p)

    def p_unary_expression_error(self, p):
        '''unary_expression : '+' error
                            | '-' error
                            | '&' error
                            | '^' error
                            | NON error'''
        self.add_syntax_error(p[2], "Expression")


    def p_postfix_expression(self, p):
        '''postfix_expression : primary_expression'''
        p[0] = p[1]
        

    def p_postfix_expression_attribut(self, p):
        '''postfix_expression : postfix_expression '.' id '''
        p[0] = AttributExpression(p[1], p[3], s=p[1])

    def p_postfix_expression_attribut_error(self, p):
        '''postfix_expression : postfix_expression '.' error'''
        self.add_syntax_error(p[3], "Attribut")

    def p_postfix_expression_table(self, p):
        '''postfix_expression : postfix_expression '[' expression ']' '''
        p[0] = TableExpression(p[1], p[3], s=p[1])

    def p_postfix_expression_table_error_closing(self, p):
        '''postfix_expression : postfix_expression '[' expression error'''
        self.add_syntax_error(p[4], "Crochet droit ']'")

    def p_postfix_expression_table_error_expression(self, p):
        '''postfix_expression : postfix_expression '[' error'''
        self.add_syntax_error(p[3], "Expression")



    def p_function_expression(self, p):
        '''function_expression : id '(' function_inputs_list ')' '''
        p[0] = FunctionExpression(p[1], p[3], s=p[1])

    def p_function_expression_error(self, p):
        '''function_expression : id '(' expression_list error '''
        self.add_syntax_error(p[4], "Virgule ',' suivie de paramètre d'entrée ou parenthèse droite ')'")

    def p_function_expression_error_no_params(self, p):
        '''function_expression : id '(' error ')' '''
        self.add_syntax_error(p[3], "Paramètres d'entrée ou parenthèse droite ')'")

    def p_function_inputs_list(self, p):
        '''function_inputs_list : opt_expression_list'''
        p[0] = p[1]

    def p_function_inputs_list_error(self, p):
        '''function_inputs_list : expression_list ',' error '''
        self.add_syntax_error(p[3], "Paramètre d'entrée après virgule ','")


    

    def p_opt_id_list(self, p):
        '''opt_id_list : id_list
                       | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_id_list(self, p):
        '''id_list : id'''
        p[0] = [p[1]]

    def p_id_list_append(self, p):
        '''id_list : id_list ',' id'''
        p[0] = p[1] + [p[3]]

    def p_id_list_error(self, p):
        '''id_list : id_list ',' error'''
        self.add_syntax_error(p[3], "Nom de variable")


    def p_opt_expression_list(self, p):
        '''opt_expression_list : expression_list
                               | empty'''
        p[0] = p[1] if p[1] is not None else []


    def p_expression_list(self, p):
        '''expression_list : expression'''
        p[0] = [p[1]]


    def p_expression_list_append(self, p):
        '''expression_list : expression_list ',' expression'''
        p[0] = p[1] + [p[3]]


    ### Optional keywords
    def p_opt_de(self, p):
        '''opt_de : DE
                  | empty'''

    def p_opt_sur(self, p):
        '''opt_sur : SUR
                   | empty'''
    ### ### ###

    ### Basics
    def p_lit_int(self, p):
        '''lit_int : LIT_INT'''
        p[0] = LitInt(p[1], p=p)
    
    def p_lit_float(self, p):
        '''lit_float : LIT_FLOAT'''
        p[0] = LitFloat(p[1], p=p)

    def p_empty(self, p):
        '''empty : '''
        pass

    def p_newline(self, p):
        '''newline : NEWLINE'''
        p[0] = "\n"
    
    
    def p_newline_error(self, p):
        '''newline : error NEWLINE'''
        self.add_syntax_error(p[1], "Nouvelle ligne")



    def p_colon(self, p):
        '''colon : ':' '''
    
    def p_colon_error(self, p):
        '''colon : error'''
        self.add_syntax_error(p[1], expected="Deux-points ':'")

    def p_id(self, p):
        '''id : ID'''
        p[0] = ID(p[1], p=p)

    def p_algorithme(self, p):
        '''algorithme : ALGORITHME'''

    def p_finalgo(self, p):
        '''finalgo : FINALGO'''
        

    def p_sa(self, p):
        '''sa : SA
              | SOUS ALGORITHME'''

    def p_finsa(self, p):
        '''finsa : FINSA'''

    def p_pour(self, p):
        '''pour : POUR'''

    def p_tq(self, p):
        '''tq : TANT QUE'''

    def p_fintq(self, p):
        '''fintq : FINTQ'''


    def p_basic_headers(self, p):
        '''types_header        : TYPES colon newline
           variables_header    : VARIABLES colon newline
           instructions_header : INSTRUCTIONS colon newline
           inputs_header       : PE colon newline
           outputs_header      : PS colon newline
        '''
        p[0] = p[1]

    def p_error(self, token):
        if token is None:
            print("eof error") 
            print(self.incomplete_blocks)
            return

        print(token.type)
        print(f"parse error: {token}")