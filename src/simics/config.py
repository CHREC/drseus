"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

from ply import lex, yacc


class data_list(list):
    # used to hold list of data strings
    pass


# LEX
tokens = ('COMMENT', 'COLON', 'COMMA', 'ID', 'LBRAC', 'LINECOMMENT', 'LPAR',
          'OBJECT', 'DATASTART', 'DATAEND', 'RBRAC', 'RPAR', 'STRING', 'TYPE')

t_LPAR = r'\('
t_RPAR = r'\)'
t_LBRAC = r'{'
t_RBRAC = r'}'
t_COLON = r':'
t_COMMA = r','
t_DATAEND = r']'
t_DATASTART = r'\['
t_STRING = r'"(?:[^"\\]|\\.)*"'


# use functions for most tokens to keep parse order
def t_COMMENT(t):
    r'/\*.*?\*/'
    pass


def t_LINECOMMENT(t):
    r'\#.*\n'
    pass


def t_ID(t):
    r'(\.|[A-Za-z0-9+/_*-]|\[[0-9]+\])+'
    if t.value in ['OBJECT', 'TYPE']:
        t.type = t.value
    return t


def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)

t_ignore = ' \t\r'


def t_error(t):
    print('Illegal character "{}"'.format(t.value[0]))
    t.skip(1)


# YACC
def p_configuration(p):
    'configuration : objects'
    p[0] = p[1]


def p_objects(p):
    'objects : objects object'
    (name, typ, attrs) = p[2]
    p[0] = p[1]
    p[0][name] = (typ, attrs)


def p_objects_empty(p):
    'objects : empty'
    p[0] = {}


def p_object(p):
    'object : OBJECT ID TYPE ID LBRAC attributes RBRAC'
    p[0] = (p[2], p[4], p[6])


def p_attributes(p):
    'attributes : attributes attribute'
    (name, value) = p[2]
    p[0] = p[1]
    p[0][name] = value


def p_attributes_empty(p):
    'attributes : empty'
    p[0] = {}


def p_attribute(p):
    'attribute : ID COLON value'
    p[0] = (p[1], p[3])


def p_value_id(p):
    'value : ID'
    p[0] = p[1]


def p_value_string(p):
    'value : STRING'
    p[0] = p[1]


def p_value_data(p):
    'value : DATASTART datalist DATAEND'
    p[0] = p[2]


def p_datalist(p):
    'datalist : datalist ID'
    p[0] = data_list(p[1] + [p[2]])


def p_datalist_empty(p):
    'datalist : empty'
    p[0] = data_list()


def p_value_list(p):
    'value : LPAR valuelist RPAR'
    p[0] = p[2]


def p_valuelist(p):
    'valuelist : valuelist COMMA value'
    p[0] = p[1]
    p[0].append(p[3])


def p_valuelist_value(p):
    'valuelist : value'
    p[0] = [p[1]]


def p_valuelist_empty(p):
    'valuelist : empty'
    p[0] = []


def p_value_dict(p):
    'value : LBRAC pairs RBRAC'
    p[0] = p[2]


def p_pairs(p):
    'pairs : pairs COMMA pair'
    p[0] = p[1].copy()
    p[0].update(p[3])


def p_pairs_pair(p):
    'pairs : pair'
    p[0] = p[1]


def p_pair(p):
    'pair : value COLON value'
    p[0] = {p[1]: p[3]}


def p_pair_empty(p):
    'pair : empty'
    p[0] = {}


def p_empty(p):
    'empty :'
    pass


# dummy rule to avoid unused warnings
def p_dummy(p):
    'configuration : COMMENT LINECOMMENT'
    pass


class ParseError(Exception):
    pass


def p_error(p):
    raise ParseError(p)

lex.lex(debug=0, optimize=1)
yacc.yacc(debug=0, optimize=1)


class SimicsConfigError(Exception):
        def __init__(self, reason, error=None):
            self.reason = reason
            self.error = error

        def __str__(self):
            return 'SimicsConfigError: {}{}'.format(
                '{}\n'.format(self.error) if self.error else '', self.reason)


class simics_config(object):
    def __init__(self, checkpoint):
        self.checkpoint = checkpoint

    def __enter__(self):
        try:
            with open('{}/config'.format(self.checkpoint), 'r') as config_file:
                config_contents = config_file.read()
        except EnvironmentError as error:
            raise SimicsConfigError(
                'Error reading checkpoint: {}'.format(error))
        try:
            self.config = yacc.parse(config_contents)
        except RuntimeError as error:
            raise SimicsConfigError('Parse error in {}'.format(self.checkpoint),
                                    error)
        except ParseError as error:
            if error.args and error.args[0]:
                raise SimicsConfigError(
                    'Syntax error in {}:{}'.format(
                        self.checkpoint, error.args[0].lineno),
                    error)
            raise SimicsConfigError(
                'Unknown parse error in {}'.format(self.checkpoint), error)
        return self

    def save(self):

        def attribute_string(attribute):
            if isinstance(attribute, data_list):
                return '['+' '.join(attribute_string(value)
                                    for value in attribute)+']'
            elif isinstance(attribute, list):
                return '('+','.join(attribute_string(value)
                                    for value in attribute)+')'
            elif isinstance(attribute, dict):
                return '{'+','.join(attribute_string(key)+':' +
                                    attribute_string(attribute[key]) for key
                                    in attribute)+'}'
            return attribute

    # def save(self):
        with open(self.checkpoint+'/config', 'w') as config_file:
            config_file.write('#SIMICS-CONF-1\n')
            for object_ in self.config:
                (type_, attirbutes) = self.config[object_]
                config_file.write(
                    'OBJECT {} TYPE {} {}\n'.format(object_, type_, '{'))
                for attribute in attirbutes:
                    config_file.write('\t{}: {}\n'.format(
                        attribute, attribute_string(attirbutes[attribute])))
                config_file.write('}\n')

    def get(self, object_, attribute):
        if object_ in self.config:
            (type_, attirbutes) = self.config[object_]
            if attribute in attirbutes:
                return attirbutes[attribute]
        return None

    def set(self, object_, attribute, value):
        if object_ in self.config:
            (type_, attirbutes) = self.config[object_]
            attirbutes[attribute] = value

    def __exit__(self, type_, value, traceback):
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
