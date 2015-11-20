from ply import lex, yacc
import os
import re


class MergeError(Exception):
    def __init__(self, reason, error=None):
        self.reason = reason
        self.error = error

    def __str__(self):
        ostr = "Checkpoint merge aborted:"
        if self.error:
            ostr += "\n%s" % (self.error,)
        ostr += "\n%s" % (self.reason,)
        return ostr


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
    print "Illegal character '%s'" % (t.value[0],)
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


####
def init_parser():
    # lextab and write_tables arguments makes it not try to create
    # files in current working directory.
    lex.lex(debug=0, optimize=1, lextab=None)
    yacc.yacc(debug=0, optimize=1, write_tables=False)


def attr_string(a):
    if isinstance(a, data_list):
        return "[" + " ".join(attr_string(v) for v in a) + "]"
    elif isinstance(a, list):
        return "(" + ",".join(attr_string(v) for v in a) + ")"
    elif isinstance(a, dict):
        return "{" + ",".join(attr_string(k) + ":" + attr_string(a[k])
                              for k in a) + "}"
    return a


def open_config(filename, mode):
    return open(filename, mode)


def write_configuration(conf, bundle_dirname, gz):
    filename = os.path.join(bundle_dirname, "config.gz" if gz else "config")
    with open_config(filename, "wb") as f:
        f.write("#SIMICS-CONF-1\n")
        for o in conf:
            (typ, attrs) = conf[o]
            f.write("OBJECT %s TYPE %s {\n" % (o, typ))
            for a in attrs:
                f.write("\t%s: %s\n" % (a, attr_string(attrs[a])))
            f.write("}\n")


def read_configuration(filename):
    if os.path.isdir(filename):
        conffile = os.path.join(filename, "config.gz")
        if not os.path.isfile(conffile):
            conffile = os.path.join(filename, "config")
            if not os.path.isfile(conffile):
                raise MergeError("No config[.gz] in %s" % filename)
        filename = conffile
    try:
        with open_config(filename, "rb") as f:
            txt = f.read()
    except EnvironmentError, e:
        raise MergeError("Error reading checkpoint: %s" % (e,))

    init_parser()
    try:
        return yacc.parse(txt)
    except RuntimeError, ex:
        raise MergeError("Parse error in %s" % (filename,), ex)
    except ParseError, ex:
        if ex.args and ex.args[0]:
            raise MergeError("Syntax error in %s:%d"
                             % (filename, ex.args[0].lineno), ex)
        raise MergeError("Unknown parse error in %s" % filename, ex)


def get_attr(conf, o, a):
    if o in conf:
        (typ, attrs) = conf[o]
        if a in attrs:
            return attrs[a]
    return None


def set_attr(conf, o, a, v):
    if o in conf:
        (typ, attrs) = conf[o]
        attrs[a] = v

escape_to_char = {
    'a': '\a',
    'b': '\b',
    't': '\t',
    'n': '\n',
    'v': '\v',
    'f': '\f',
    'r': '\r',
    '"': '"',
    '\\': '\\',
    }


def parse_escape_char(m):
    c = m.group(1)
    if c in escape_to_char:
        return escape_to_char[c]
    else:
        return chr(int(c, 8))


# Convert a quoted string (from the config file) to its actual contents.
def parse_quoted_string(quoted):
    assert quoted.startswith('"') and quoted.endswith('"')
    return re.sub(r'\\(["\\abtnvfr]|[0-7]{1,3})', parse_escape_char,
                  quoted[1: -1])


assert parse_quoted_string('"ab\\\\c\\"d\\ne\\033f"') == 'ab\\c"d\ne\033f'

char_to_escape = {c: e for (e, c) in escape_to_char.items()}


# Quote a string in a way appropriate for the config file.
def make_quoted_string(s):
    q = '"'
    for c in s:
        o = ord(c)
        if c in char_to_escape:
            q += '\\' + char_to_escape[c]
        elif o < 32 or o == 127:
            q += '\\%03o' % o
        else:
            q += c
    return q + '"'

assert make_quoted_string('ab\\c"d\ne\033f') == '"ab\\\\c\\"d\\ne\\033f"'
