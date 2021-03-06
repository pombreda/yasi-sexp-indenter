#-*- encoding: utf-8 -*-
# @started "20th November 2013"

__author__  = "nkmathew <kipkoechmathew@gmail.com>"
__date__    = "4th December 2013"

import re
import os
import sys
import time     # to tell you the last time you indented a file.
import shutil   # to create backup file
import hashlib  # to determine if a file has already been formatted
import pprint   # for debugging

def read_file(fname):
    """ read_file(fname : str) -> str

    example: read_file(r"C:\mine\\test.lisp")
                ==> r'(print "No, no, there\'s \\r\\nlife in him!. ")\\r\\n\\r\\n'
    The file is read in binary mode in order to preserve original line endings.
        Line ending    Binary mode Text mode
            CRLF            CRLF    LF 
            CR              CR      LF
    """
    assert os.path.exists(fname), "\n--%s-- Warning: File `%s' does not exist. . ." \
            % (current_time(), fname)
    with open(fname, "rb") as fp:
            return fp.read()

def issue_warning(warning_message, format_tuple, warn, exit_after_warning, fname):
    '''
    Issues all the warning messages.
    '''
    if warn:
        sys.stderr.write(warning_message % format_tuple)
    if exit_after_warning:
        exit("\n--%s-- Exiting. File `%s' unchanged. . ." % (current_time(), fname))


def current_time():
    ''' current_time() -> str

    example: current_time() 
                ==> 14:28:04
    Returns the current local time in 24 clock system.
    '''
    return time.strftime("%X", (time.localtime()))

def lisp_dialect(lst):
    ''' lisp_dialect(lst : [list]) -> str

    example: lisp_dialect(["quicklisp.lisp", "--no-backup", "--clojure"])
    Find the lisp dialect specified in the list(sys.argv). The lisp
    dialect determines the keywords to be used.
    '''
    if "--clojure" in lst:
        return "Clojure"
    elif "--scheme" in lst:
        return "Scheme"
    elif "--lisp" in lst:
        return "Common Lisp"
    elif "--newlisp" in lst:
        return "newLISP"
    else:
        return "All"

def backup_source_file(fname, backup_dir = "."):
    ''' backup_source_file(fname : str)

    example: backup_source_file("~/Desktop/lisp/test.lisp")
    Create a backup copy of the source file.
    '''
    assert os.path.exists(fname), \
            ("\n--%s-- Warning: File `%s' does not exist. . ." % (current_time(), fname))
    assert os.path.exists(os.path.abspath(backup_dir)), \
            ("\n--%s-- Warning: Directory `%s' does not exist. . ." % (current_time(), fname))
    backup_name = backup_dir + os.sep + os.path.split(fname)[1] + ".yasi.bak~"
    try:
        shutil.copyfile(fname, backup_name)
    except IOError:
        message = "\n--%s-- Warning: Couldn't backup the file `%s' in `%s', check if you have enough permissions. "
        tpl = (current_time(), fname, backup_dir)
        issue_warning(message, tpl, WARN, EXIT, fname)

def get_backup_directory(lst, fname):
    ''' get_backup_directory(lst : list, fname : str) -> str

    get_backup_directory(['--no-warning', '--no-output', '--backup-dir', 'desktop'])
            ==> 'desktop'
    Returns the backup directory, assuming it's always after the '--backup-dir'
    parameter. The filename is not really necessary, it's just for issuing the
    error message.
    '''
    if '--backup-dir' in lst:
        index = lst.index('--backup-dir') + 1
        if len(lst) <= index:
            message = "\n--%s-- `%s': Warning: Backup option specified but no backup directory provided.\n"
            tpl = (current_time(), fname)
            issue_warning(message, tpl, WARN, False, None)
            return False
        backup_dir=lst[index]
        if not os.path.exists(os.path.abspath(backup_dir)):
            message = "\n--%s-- `%s': Warning: The directory `%s' does not exist and can't be used as a backup directory."
            tpl = (current_time(), fname, backup_dir)
            issue_warning(message, tpl, WARN, True, fname)
        else:
            return backup_dir
    else:
        return False


def md5sum(content):
    ''' md5sum(content : str) -> str

    example: md5sum("Keyboard not found!! Press F1 to continue...")
                ==> 'ad98cde09016d2e99a726966a4291acf'
    Returns a checksum to be used to determine whether the file has changed.
    A simple textual comparison can still do the work
    '''
    return hashlib.md5(content).hexdigest()


class Indenter():
    ''' The class simply serves to group methods that indent 
    the string.
    example: indenter = Indenter()
             indenter.trim(" ( ( (  ) ) ) ")
             ==> '((()))'
    '''

    def trim(self, string):
        ''' trim(string : str) -> str

        Uses every usefull hack to try and reduce extra whitespace without 
        messing with character literals
        '''
        ## turn "(print(+ 1 1))" to "(print (+ 1 1))"
        string = re.sub(r'''([^\\(\[, {@~`'#^])(\(|\[|{)''', r'\1 \2', string, re.X)
        ## turn  ")(" to ") ("
        string = re.sub(r'(\)|\]|})(\[|\(|{)', r'\1 \2', string)
        ## Remove any space before closing brackets "(print 12   )" ==> "(print 12)"
        string = re.sub('[ \t]*(\)|\]|})', r'\1', string)
        ## remove extra whitespace "(print     'this) ==> "(print 'this)"
        string = re.sub('[ \t]{2, }', ' ', string)
        ## turn ") ) ) " into "))) "
        string = re.sub(r"(\))[ \t]*(?=(\)))", r"\1", string)
        string = re.sub(r"(\])[ \t]*(?=(\]))", r"\1", string)
        string = re.sub(r"(})[ \t]*(?=(}))", r"\1", string)
        ## turn "( ( ( " into "((( "
        string = re.sub(r"(\()[ \t]*(?=(\())", r"\1", string)
        string = re.sub(r"(\[)[ \t]*(?=(\[))", r"\1", string)
        string = re.sub(r"({)[ \t]*(?=({))", r"\1", string)
        ## remove leading whitespace "   print" ==> "print"
        string = re.sub('^[ \t]*', '', string)
        ## Remove space before list literal, " ' (1 2 3)" ==> " '(1 2 3)"
        string = re.sub(r" ('|`) (\(|\[|{)", r" \1\2", string)
        return string

    def find_trim_limit(self, string):
        ''' find_trim_limit(string : str) -> int

        examples: find_trim_limit(r'(list #\; #\")')
                    ==> 14
                  find_trim_limit(r'(list ; ")')
                    ==> 6
                  find_trim_limit(r'(list " ;)')
                    ==> 7
        The function attempts to identify upto which point we are supposed to trim
        so that we don't mess with strings or any aligned comments.
        It does this by comparing the positions of semicolons and double 
        quotes. It doesn't consider the multiline comment marker. If your
        code uses multiline comments, you'll have to use --no-compact mode'''
        ## Find position of the first unescaped semi colon
        comment_start = re.search(r'([^\\];)|(^;)', string)
        ## Find position of the first unescaped double quote
        limit = re.search(r'([^\\]")|(^")', string)
        ## Assign -1 if there's no match
        limit = limit.end() if limit else -1
        comment_start = comment_start.end() if comment_start else -1
        if comment_start != -1:
            ## If semi colon is found, include all the whitespace before it so
            ## just in case someone had 'prettified' and aligned the comments
            comment_start = re.search("[ \t]*;", string).start() + 1

        if comment_start != -1 and limit != -1:
            if comment_start < limit:
                ## If the semicolon comes before the comma, it means the string
                ## has been commented out
                limit = comment_start
        elif comment_start != -1 and limit == -1:
            ## If there's a semicolon but no quote, use the semicolon position
            ## as the limit
            limit = comment_start
        elif limit == -1:
            ## If neither a semicolon nor a double quote have been found, use
            ## the length of the string as the limit
             limit = len(string)
        return limit

    def is_macro_name(self, form, dialect):
        ''' is_macro_name(form : str, dialect : str) -> bool

        example: is_macro_name("yacc:define-parser")
                    True
            Tests if a word is a macro using the language's/dialect's convention, 
            e.g macros in Lisp usually start with 'def' and 'with' in Scheme. Saves
            the effort of finding all the macros in Lisp/Scheme/Clojure/newLISP and storing
            them in a list.
        '''
        if not form:
            return form
        if dialect =='Common Lisp':
            return re.search('macro|def|do|with-', form, re.I)
        if dialect == 'Scheme':
            return re.search('call-|def|with-', form)
        if dialect == 'Clojure':
            return re.search('def|with', form)
        if dialect == 'newLISP':
            return re.search('macro|def', form)

    def all_whitespace(self, string):
        ''' all_whitespace(string : str) -> bool

        example: all_whitespace("      ") 
                    ==> True
        Returns True if a string has only whitespace.
        '''
        return re.search("^[ \t]*(\r|\n|$)", string)

    def pad_leading_whitespace(self, string, zero_level, compact, blist):
        ''' pad_leading_whitespace(string : str, current_level : int, zero_level : int) -> str

        example: pad_leading_whitespace("(print 'Yello)")
                    ==> "         (print 'Yello)"
        Takes a string and indents it using the current indentation level 
        and the zero level.
        '''
        if compact:
            ## if compact mode is on, split the string into two, trim the first
            ## position and merge the two portions.
            trim_limit = self.find_trim_limit(string)
            comment_line = re.search("^[ \t]*;", string, re.M)
            if comment_line and INDENT_COMMENTS:
                trim_limit = -1
            substr1 = string[0:trim_limit]
            substr2 = string[trim_limit:]
            substr1 = self.trim(substr1)
            string = substr1 + substr2
        else:
            ## if in nocompact mode, pad with zero_level spaces.
            string = re.sub("^[ \t]+", '', string, count=0, flags=re.M)
            string = ' ' * zero_level + string

        if blist:
            ## if there are unclosed blocks, you pad the line with the
            ## current indent level minus the zero level that was
            ## added earlier
            current_level = blist[-1]['indent_level']
            string = ' ' * (current_level - zero_level) + string
            return string, current_level
        else:
            ## Otherwise(all blocks finished), return the string as it is since
            ## it's the head of a new block
            return string, 0


    def split_preserve(self, string, sep):
        ''' split_preserve(string : str, sep : str)  -> [str]

        example: split_preserve("""
        "My dear Holmes, " said I, "this is too much. You would certainly
        have been burned, had you lived a few centuries ago.
                    """, "\\n")
               ==>  ['\\n', 
                     '    "My dear Holmes, " said I, "this is too much. You would certainly\\n', 
                     '    have been burned, had you lived a few centuries ago.\\n', 
                     '                ']
        Splits the string and sticks the separator back to every string in the
        list.
        '''
        # split the whole string into a list so that you can iterate line by line.
        str_list = string.split(sep)
        if str_list[-1] == "":
            # If you split "this\nthat\n" you get ["this", "that", ""] if
            # you add newlines to every string in the list you get
            # ["this\n", "that\n", "\n"]. You've just added
            # another newline at the end of the file.
            del str_list[-1]
            str_list = map(lambda x: x + sep, str_list)
        else:
            # ["this", "that"] will become ["this\n", "that\n"] when
            # mapped. A newline has been added to the file. We don't want
            # this, so we strip it below.
            str_list     = map(lambda x: x + sep, str_list)
            str_list[-1] = str_list[-1].rstrip(sep)
        return str_list

    def line_ending(self, string):
        ''' line_ending(string : str) -> str

        example: line_ending("Elementary my dear Watson. \\r")
                    ==> '\\r'
        Find the line ending in the file so that we can try to preserve it.
        '''
        CR   = "\r"
        LF   = "\n"
        CRLF = CR+LF

        if CRLF in string:
            return CRLF
        elif CR in string:
            return CR
        else:
            return LF

    def indent(self, zerolevel, bracket_list, line, in_comment, in_symbol_region):
        ''' indent(zerolevel : int, bracket_list : list, line : str, in_comment : bool, 
                    in_symbol_region : bool)

        Most important function in the indentation process. It uses the bracket
        locations stored in the list to indent the line.
        '''
        comment_line = re.search("^[ \t]*;", line, re.M)
        if INDENT_COMMENTS:
            ## We are allowed to indent comment lines
            comment_line = False
        if not COMPACT and zerolevel == 0 and bracket_list == [] and not in_comment:
            ## If nocompact mode is on and there are no unclosed blocks, try to
            ## find the zero level by simply counting spaces before a line that
            ## is not empty or has a comment
            leading_spaces = re.search("^[ \t]+[^; )\n\r]", line)
            if leading_spaces:
                ## NOTE: If you don't subtract one here, the zero level will increase 
                ## every time you indent the file because the character at the end of
                ## the regex is part of the capture.
                zerolevel = leading_spaces.end() - 1

        if in_symbol_region:
            # No processing done in strings and comments
            return zerolevel, line, 0
        elif not comment_line and not self.all_whitespace(line):
            # If this is not a comment line indent the line. 
            # If the list is empty, then the current_level defaults
            # to zero
            curr_line, current_level = self.pad_leading_whitespace(line, 
                            zerolevel, COMPACT, bracket_list)
            return zerolevel, curr_line, current_level
        else:
            return zerolevel, line, 0

# ****************************************************************************************
# GLOBAL CONSTANTS::

# Keywords that indent by two spaces
SCHEME_KEYWORDS=['define', 'local-odd?', 'when', 'begin', 'case', 
'local-even?', 'do', 'call-with-bytevector-output-port', 
'call-with-input-file', 'call-with-port', 
'call-with-current-continuation', 'open-file-input-port', 
'call-with-port', 'call-with-values', 'call-with-output-file', 
'call-with-string-output-port', 'define-syntax', 'if', 'let', 'let*', 
'library', 'unless', 'lambda', 'syntax-rules', 'syntax-case', 
'let-syntax', 'letrec*', 'letrec', 'let-values', 'let*-values', 
'with-exception-handler', 'with-input-from-file', 
'with-interrupts-disabled', 'with-input-from-string', 
'with-output-to-file', 'with-input-from-port', 
'with-output-to-string', 'with-source-path', 'with-syntax', 
'with-implicit', 
'with-error-handler', 'module', 'parameterize']

CLOJURE_KEYWORDS=['defn', 'fn', 'dorun', 'doseq', 'loop', 'when', 
'let', 'defmacro', 'binding', 'doto', 'ns', ':import', 'defstruct', 
'condp', 'comment', 'when', 'when-let', '->', '->>', 
'extend-type', 'reify', 'binding', 'when-not', 'proxy', 'dotimes', 
'try', 'finally', 'for', 'letfn', 'catch', 'iterate', 'while', 
'with-local-vars', 'locking', 'defmulti', 'defmethod', 'extend'
]

LISP_KEYWORDS=[':implementation', ':method', 'case', 'defclass', 
'defconstant', 'defgeneric', 'defimplementation', 
'define-condition', 'define-implementation-package', 
'definterface', 'defmacro', 'defmethod', 'defpackage', 
'defproject', 'deftype', 'defun', 'defvar', 'do-external-symbols', 
'dolist', 'dotimes', 'ecase', 'etypecase', 'flet', 'handler-bind', 
'if', 'lambda', 'let', 'let*', 'print-unreadable-object', 
'macrolet', 'defparameter', 'with-slots', 'typecase', 'loop', 'when', 'prog1', 
'unless', 'with-open-file', 'with-output-to-string', 'with-input-from-string', 
'block', 'handler-case', 'defstruct', 'eval-when', 'tagbody', 'ignore-errors', 
'labels', 'multiple-value-bind'
]
 
NEWLISP_KEYWORDS=['while', 'if', 'case', 'dotimes', 'define', 'dolist', 'catch', 
'throw', 'lambda', 'lambda-macro', 'when', 'unless', 'letex', 'letn', 'begin', 
'dostring', 'let', 'letn', 'doargs', "define-macro", 'until', 'do-until', 
'do-while', 'for-all', 'find-all', 'for' 
]

## Keywords that indent by one space
ONE_SPACE_INDENTERS = ['call-with-port']


## Assign default values here depending on the command line arguments 
BACKUP   =  False if '--no-backup'  in sys.argv or '-nb' in sys.argv else True
COMPACT  =  False if '--no-compact' in sys.argv or '-nc' in sys.argv else True
EXIT     =  False if '--no-exit'    in sys.argv or '-ne' in sys.argv else True
MODIFY   =  False if '--no-modify'  in sys.argv or '-nm' in sys.argv else True
OUTPUT   =  False if '--no-output'  in sys.argv or '-no' in sys.argv else True
UNIFORM  =  True  if '--uniform'    in sys.argv or '-uni' in sys.argv else False
WARN     =  False if '--no-warning' in sys.argv or '-nw' in sys.argv else True
INDENT_COMMENTS = True if '--indent-comments' in sys.argv or '-ic' in sys.argv else False

DEFAULT_INDENT = 1
if '--default-indent' in sys.argv:
    ## The default is the value to be used in case a functions's argument is in
    ## the next line and that function is not a two or one space indenter
    pos = sys.argv.index('--default-indent')
    if len(sys.argv) > pos:
        try:
            DEFAULT_INDENT = int(sys.argv[pos + 1])
        except:
            DEFAULT_INDENT = 1

# The 'if' and 'else' part of an if block should have different indent levels so
# that they can stand out since there's no else Keyword in Lisp/Scheme to make
# this explicit.  list IF_LIKE helps us track these keywords.
IF_LIKE=['if']

DIALECT = lisp_dialect(sys.argv)

if DIALECT == 'Common Lisp': # Lisp
    TWO_SPACE_INDENTERS = LISP_KEYWORDS
    IF_LIKE += ['multiple-value-bind', 'destructuring-bind', 'do', 'do*']
elif DIALECT == 'Scheme': # Scheme
    TWO_SPACE_INDENTERS = SCHEME_KEYWORDS
    IF_LIKE += ['with-slots', 'do', 'do*']
elif DIALECT == 'Clojure': # Clojure
    TWO_SPACE_INDENTERS = CLOJURE_KEYWORDS
    IF_LIKE += []
elif DIALECT == 'newLISP': # newLISP
    TWO_SPACE_INDENTERS = NEWLISP_KEYWORDS
    IF_LIKE += []
elif DIALECT == 'All':
    TWO_SPACE_INDENTERS = LISP_KEYWORDS + SCHEME_KEYWORDS + CLOJURE_KEYWORDS + \
                          NEWLISP_KEYWORDS

# ************************************************************************************* #

def find_first_arg_pos(curr_pos, string):
    ''' find_first_arg_pos(curr_pos : int, string : str) -> int

    example: find_first_arg_pos(0, "(     list 'one-sheep 'two-sheep )")
                ==> 11
    Returns the position of the first argument to the function.
    '''
    leading_spaces = 0
    substr=string[curr_pos+1:]
    if re.search("^[ \t]*($|\r)", substr):
        ## whitespace extending to the end of the line means there's no
        ## function in this line. The indentation level defaults to one.
        arg_pos = 1
    else:
        if curr_pos != len(string) - 1 and string[curr_pos+1] == ' ':
            ## control reaches here if we are not at the end of the line
            ## and whitespace follows. We must first find the position of the
            ## function and then the arguments position
            match = re.search(" +[^)\]]| \)", substr) # Find the first non whitespace/bracket character
            if match:
                leading_spaces = match.end() - match.start() - 1
                end = match.end()
            else:
                end = 0
            ## Then use the end of the whitespace group as the first argument
            arg_pos = re.search(" +([^)])|( *(\(|\[))", substr[end:])
            if arg_pos:
                arg_pos = arg_pos.end() + leading_spaces + 1
            else:
                arg_pos = leading_spaces + 1
            if re.match("^[ \t]*(#\||;|$|\r)", 
                substr[(end - 1 + substr[end - 1:].find(' ')):]):
                ## But, if a comment if found after the function name, the
                ## indent level becomes one
                arg_pos = leading_spaces + DEFAULT_INDENT
        else:
            ## If there's no space after the bracket, simply find the end of the
            ## whitespace group
            match = re.search(" +([^)}\n\r])|( *(\(|\[|{))", substr)
            if match: # found the argument
                arg_pos = match.end()
            else: # Either empty list or argument is in the next line
                arg_pos = 1
            if re.match("^[\t ]*(;|$|\r)", substr[substr.find(' '):]):
                ## Again if a comment is found after the function name, the
                ## indent level defaults to 1
                arg_pos = leading_spaces + DEFAULT_INDENT
    return [arg_pos, leading_spaces]


def pop_from_list(bracket, lst, fname, line, real_pos, offset):
    ''' pop_from_list(char : str, lst : [str], fname : str, line : str, 
                        real_pos : int, offset : int)

        The function is called when a closing bracket is encountered. The function 
        simply pops the last pushed item and issues a warning if an error is
        encountered.
    '''
    ## Try to spot a case when a square bracket is used to close a round bracket
    ## block
    if bracket == ']':
        correct_closer = '['
    elif bracket == ')':
        correct_closer = '('
    else:
        correct_closer = '{'
    if lst != []:
        popped = lst.pop()
        popped_char = popped["character"]
        popped_pos = popped["line_number"]
        popped_offset = popped["bracket_pos"]
        if popped_char is not correct_closer:
            message = "\n--%s-- %s: Warning: Bracket `%s' at (%d, %d) does not match `%s' at (%d, %d)"
            tpl = (current_time(), fname, popped_char, popped_pos, popped_offset, bracket, line, real_pos)
            issue_warning(message, tpl, WARN, EXIT, fname)
    else:
        ## If the list if empty and a closing bracket is found, it means we have
        ## excess brackets. That warning is issued here. The coordinates used
        ## will be slightly or largely off target depending on how much your
        ## code was 'messed' up when used with compact mode
        if EXIT:
            bpos = real_pos + 1
        else:
            bpos = offset + 1
        message = "\n--%s-- %s: Warning: Unmatched `%s' near (%d, %d). "
        tpl = (current_time(), fname, bracket, line, bpos)
        issue_warning(message, tpl, WARN, EXIT, fname)
    return lst

def push_to_list(lst, func_name, char, line, offset, first_arg_pos, first_item, 
        in_list_literal, lead_spaces):
    ''' push_to_list(lst : [str], func_name : str, char : str, line : int, offset : int, 
                        first_arg_pos :int , first_item : int, in_list_literal : bool, lead_spaces : int)

    Called when an opening bracket is encountered. A hash containing the
    necessary data to pin point errors and the indentation level is stored in
    the list and the list returned.
    '''
    pos_hash={"character":char, 
              "line_number":line, 
              "bracket_pos":offset, 
              "indent_level":offset + first_arg_pos, # the default value, e.g in normal function
              "func_name":func_name, 
              "spaces":0}

    two_spacer = func_name in TWO_SPACE_INDENTERS or indenter.is_macro_name(func_name, DIALECT)

    if  in_list_literal or char == '{' or (char == '[' \
                and DIALECT == "Clojure"):
        ## found quoted list or clojure hashmap/vector
        pos_hash["indent_level"] = first_item

    elif func_name in IF_LIKE:
        ## We only make the if-clause stand out if not in uniform mode
        pos_hash["indent_level"] = lead_spaces + ((offset+4) if not UNIFORM else (offset + 2))

    elif func_name in ONE_SPACE_INDENTERS and func_name != '':
        pos_hash["indent_level"] = lead_spaces + offset + 1

    elif two_spacer and func_name != '':
        pos_hash["indent_level"] = lead_spaces + offset + 2

    lst.append(pos_hash)
    try:
        # A hack to make flets and labels in Lisp not indent like
        # functions. The 'labels' indentation may not be exactly
        # perfect.
        parent_func = lst[-3]["func_name"]
        if parent_func in ["flet", "labels", "macrolet"]:
            lst[-1]["indent_level"] = offset + 2
    except:
        pass
    return lst

indenter = Indenter()

def indent_code(original_code, fpath=None):
    ''' indented_code(string : str, fname : str) -> [...]

    example: indented_code("(print\\n'Hello)")
                ==> [False, False, False, [], [], None, "(print\\n'Hello)", "(print\\n 'Hello)"]
    The last entry in the list is the indented string.
    '''
    # get the filename only not its full path
    fname = os.path.split(fpath)[1]

    # Safeguards against processing brackets inside strings
    in_string = False

    # newLISP use curly brackets as a syntax for multiline strings 
    # this variable here tries to keep track of that
    in_newlisp_string = 0
    in_newlisp_tag_string = False
    newlisp_brace_locations = []
    first_tag_string = ()

    # zero_level helps us get the same results as Sitaram's indenter when in
    # --no-compact mode.
    zero_level = 0

    # The two variables prevent formatting comment regions or symbols with whitespace
    in_comment = 0
    in_symbol_with_space = False
    comment_locations = []
    last_symbol_location = ()

    # A in_symbol_region is the region between pipes(|   |) or in strings. This
    # includes the comment region. This region is not to be messed with.
    in_symbol_region = in_string or in_comment or in_symbol_with_space or \
                        in_newlisp_string or in_newlisp_tag_string

    # we need to know the line number in order to issue almost accurate messages about
    # unclosed brackets and string
    line_number = 1

    # Stores the last position a quote was encountered so that in case there are
    # any unclosed strings, we can pinpoint them
    last_quote_location = ()

    code_lines = indenter.split_preserve(original_code, 
                                indenter.line_ending(original_code))

    indented_code=""

    bracket_locations = []
    for line in code_lines:
        escaped      = False
        curr_line    = line
        
        ## Get the indent level and the indented line
        zero_level, curr_line, indent_level = indenter.indent(zero_level, bracket_locations, 
                                    line, in_comment, in_symbol_region)
        ## Build up the indented string.
        indented_code += curr_line
        offset = 0
        for curr_char in curr_line:
            next_char     = curr_line[offset+1:offset+2]
            prev_char     = curr_line[offset-1:offset]

            substr = curr_line[offset+1:] # slice to the end

            if escaped:
                # Move to the next character if the current one has been escaped
                escaped = False
                offset += 1
                continue

            if curr_char == "\\" and not in_newlisp_string and not in_newlisp_tag_string:
                # the next character has been escaped
                escaped = True
            
            if curr_char == ';' and not in_symbol_region and not ((prev_char == "#"
                    and DIALECT == "Scheme")):
                # a comment has been found, go to the next line
                # A sharp sign(#) before a semi-colon in Scheme is used to
                # comment out sections or code. We don't treat it as a comment
              break

            # ----------------------------------------------------------
            # Comments are dealt with here. Clojure and newLISP don't have Lisp
            # style multiline comments so don't include them.
            if DIALECT not in ["Clojure", "newLISP"] and curr_char == '|' and not in_string:
                if prev_char == "#" and not in_symbol_with_space:
                    comment_locations.append((line_number, offset))
                    in_comment += 1
                elif in_comment and next_char == "#":
                    in_comment -= 1
                    comment_locations.pop()
                elif not in_comment:
                    if in_symbol_with_space:
                        last_symbol_location = ()
                        in_symbol_with_space = False
                    else:
                        last_symbol_location = (line_number, offset)
                        in_symbol_with_space = True

            # ----------------------------------------------------------

            ## Strings are dealt with here only if we are not comment
            if not (in_symbol_with_space or in_comment or in_newlisp_tag_string):
                if curr_char == '"':
                    last_quote_location = (fname, line_number, offset)
                    in_string = True if not in_string else False
                if DIALECT == 'newLISP' and not in_string:
                    # We handle newLISP's multiline strings here
                    if curr_char == '{':
                        newlisp_brace_locations.append((line_number, offset))
                        in_newlisp_string += 1
                    elif curr_char == '}':
                        if newlisp_brace_locations:
                            newlisp_brace_locations.pop()
                        else:
                            message = "\n--%s-- `%s': Warning: Attempt to close a non-existent newLISP string"
                            tpl = (current_time(), fname)
                            issue_warning(message, tpl, WARN, EXIT, fname)
                        in_newlisp_string -= 1

            if curr_char == "[" and DIALECT == "newLISP" and not \
                (in_newlisp_string or in_string):
                ## We have to handle tag strings in newLISP here.
                if re.match("\[text\]", curr_line[offset:offset+7]):
                    in_newlisp_tag_string = True
                    if first_tag_string == ():
                        first_tag_string = (line_number, offset)
                elif re.match("\[/text\]", curr_line[offset:offset+7]):
                    in_newlisp_tag_string = False
                    first_tag_string = ()

            in_symbol_region = in_string or in_comment or in_symbol_with_space \
                                or in_newlisp_string or in_newlisp_tag_string

            if in_symbol_region:
                # move on if you are in a string, a symbol with space or a comment
                # altogether known as the symbol region
                offset += 1
                continue

            # Finds the real position of a bracket to be used in pinpointing where
            # the unclosed bracket is. The real position is different from the offset 
            # because current offset is the position of the bracket in the
            # trimmed string not the original.
            real_position = (offset - zero_level) + len(re.findall("^[ \t]*", line)[0]) - indent_level
            if curr_char in ['(', '[', '{']:
                if curr_char in ['[', '{'] and DIALECT in ["Common Lisp", "newLISP"]:
                    ## Square/Curly brackets are used should not contribute to
                    ## the indentation in CL and newLISP
                    offset += 1
                    continue

                first_arg_pos, leading_spaces = find_first_arg_pos(offset, curr_line)
                func_name = substr[0:first_arg_pos-1].strip(')]\t\n\r ').lower()
                in_list_literal = False
                if re.search("('|`|#)([ \t]*\(|\[)($|\r)", curr_line[0:offset+1]):
                    in_list_literal = True
            
                if re.search("^[^ \t]+[ \t]*($|\r)", substr):
                    ## The function is the last symbol/form in the line
                    func_name = substr.strip(')]\t\n\r ').lower()
                if func_name == '' or in_list_literal:
                    # an empty string is always in a non-empty string, we don't want
                    # this. We set False as the func_name because it's not a string
                    # in_list_literal prevents an keyword in a list literal from
                    # affecting the indentation
                    func_name = False

                if func_name in ["define-macro", "defmacro"]:
                    # Macro names are part of TWO_SPACE_INDENTERS space indenters.
                    # This part tries to find the name so that it is not indented
                    # like a function the next time it's used. 
                    end_of_space = re.search("^[ \t]*", substr).end()
                    substr = substr[end_of_space:]
                    substr = substr[re.search("[ \t]*", substr).start():].strip()
                    macro_name = substr[:substr.find(" ")] # macro name is delimeted by whitespace
                    if macro_name != '':
                        TWO_SPACE_INDENTERS.append(macro_name)

                # first_item stores the position of the first item in the literal list
                # it's necessary so that we don't assume that the first item is always 
                # after the opening bracket.
                first_item = re.search("[ \t]*", curr_line[offset+1:]).end() + offset + 1
                bracket_locations = push_to_list(bracket_locations[:], func_name, curr_char, line_number, 
                        offset, first_arg_pos, first_item, in_list_literal, 
                        leading_spaces)

            elif curr_char in [']', ')', '}']:
                if curr_char in [']', '}'] and DIALECT in ["Common Lisp", "newLISP"]:
                    ## Square/Curly brackets are used should not contribute to
                    ## the indentation in CL and newLISP
                    offset += 1
                    continue

                bracket_locations = pop_from_list(curr_char, bracket_locations[:], fname, line_number, real_position, offset)

            if bracket_locations and curr_char in [' ', '\t'] and bracket_locations[-1]['func_name'] in IF_LIKE:
                ''' This part changes the indentation level of a then clause so that
                    we can achieve something like: 
                            (if (= this that)
                                'then-form
                              'else-form)
                    This is done by keeping track of the number of spaces found. If
                    you find two spaces it means that, for example that we have just
                    passed the then-form and hence should decrease the indentation
                    level by 2.(I shamelessly copied this algorithm from Dorai's
                    indenter)
                '''
                if prev_char not in [' ', '\t', ''] or  not \
                        re.search("^[ \t]*(;|#\||$|\r)", curr_line):
                    # The level shouldn't be decreased if the line is a comment
                    # line. The regex above takes care of that.
                    bracket_locations[-1]['spaces'] +=1
                if bracket_locations[-1]['spaces'] == 2:
                    bracket_locations[-1]['indent_level'] -= 0 if UNIFORM else 2
                    bracket_locations[-1]['spaces'] = 999 # some dummy value to prevent it
                                                # from coming here again

            offset += 1
        line_number += 1
    return [first_tag_string, in_newlisp_tag_string, last_symbol_location, comment_locations,
            newlisp_brace_locations, in_string, in_comment,
            in_symbol_with_space, bracket_locations, 
            last_quote_location, fpath, original_code, indented_code]

def after_indentation(indentation_state):
    ''' after_indentation(indentation_state : lst): 

    Called after the string has been indented appropriately. 
    It takes care of writing the file and checking for unclosed strings 
    or comments.
    '''
    ## Receive all the state variables. *This is the price you for modularity*
    first_tag_string, in_newlisp_tag_string, last_symbol_location, comment_locations, \
    newlisp_brace_locations, in_string, in_comment, in_symbol_with_space, \
    bracket_locations, last_quote_location, fpath, original_code, indented_code \
    = indentation_state

    fname = os.path.split(fpath)[1]

    if bracket_locations:
        # If the bracket_locations list is not empty it means that there are some
        # brackets(opening) that haven't been closed. 
        for bracket in bracket_locations:
            y = bracket["line_number"]
            x = bracket["bracket_pos"]
            character=bracket["character"]
            # The bracket_locations are not very accurate. The warning might be
            # misleading because it considers round and square brackets to be
            # the same.
            message = "\n--%s-- `%s': Warning : Unmatched `%s' near (%d, %d). "
            tpl = (current_time(), fname, character, y, x)
            issue_warning(message, tpl, WARN, EXIT, fname)

    if newlisp_brace_locations:
        for brace in newlisp_brace_locations:
            message = "\n--%s-- `%s': Warning: Unclosed newLISP string near: (%d, %d)"
            tpl = (current_time(), fname) + brace
            issue_warning(message, tpl, WARN, EXIT, fname)

    if comment_locations:
        for comment in comment_locations:
            message = "\n--%s-- `%s': Warning: Unclosed comment near: (%d, %d)"
            tpl = (current_time(), fname) + comment
            issue_warning(message, tpl, WARN, EXIT, fname)

    if last_symbol_location:
        message = "\n--%s-- `%s': Warning: Unclosed symbol near: (%d, %d). "
        tpl = (current_time(), fname) + last_symbol_location
        issue_warning(message, tpl, WARN, EXIT, fname)

    if in_string:
        message = "\n--%s-- `%s': Warning: The string starting from (%d, %d) extends to end-of-file. "
        tpl = ((current_time(), ) + last_quote_location)
        issue_warning(message, tpl, WARN, EXIT, fname)

    if in_newlisp_tag_string:
        message = "\n--%s-- `%s': Warning: The tag string starting from (%d, %d) extends to end-of-file. "
        tpl = (current_time(), fname) + first_tag_string
        issue_warning(message, tpl, WARN, EXIT, fname)

    if hashlib.md5(indented_code).hexdigest() == md5sum(original_code):
        message = "\n--%s-- File `%s' has already been formatted. Leaving it unchanged. . .\n"
        tpl = (current_time(), fname)
        issue_warning(message, tpl, True, False, fname)
    else:
        if OUTPUT:
            print indented_code

        if MODIFY:
            # write in binary mode to preserve the original line ending
            with open(fpath, "wb") as indented_file:
                indented_file.write(indented_code)

def indent_file(fname):
    ''' indent_file(fname : str)

        1. Creates a backup of the source file(backup_source_file())
        2. Reads the files contents(read_file())
        3. Indents the code(indent_code())
        4. Writes the file or print the indented code(after_indentation())
    '''
    fname = os.path.abspath(fname)
    code = read_file(fname)
    indent_result = indent_code(code, fname)
    after_indentation(indent_result)

    backup_dir = get_backup_directory(sys.argv[1:], fname)
    if BACKUP and not backup_dir:
        # The backup directory hasn't been specified, default
        # to the current directory
        backup_source_file(fname)
    elif BACKUP and backup_dir:
        # Create a backup file in the directory specified
        backup_source_file(fname, backup_dir)

if __name__ == '__main__':
    # Print the help menu if no arguments are passed to the file.
    if sys.argv[1:] == []:
        print  '''
 _________________________________________________________________________________________________________________
|    Usage: newlisp yasi.lsp [[<file>] [--backup-dir<directory>] [--no-compact] [--no-backup] [--no-warning]      |
|                   [--clojure] [--lisp] [--scheme] [--default-indent <num>]]                                     |
|            -nb,    --no-backup     # Don't create a backup file even if --backup-dir is specified               |
|            -nc,    --no-compact    # Try to preserve the structure of the file.                                 |
|            -nw,    --no-warning    # Don't issue warnings                                                       |
|            -ne,    --no-exit       # Instructs the program not to exit when a warning is raised. True by default|
|            -uni,   --uniform       # Dictates whether the if-clause and else-clause of an if-like block should  |
|                                       have the same indent level. False by default                              |
|            -no,    --no-output     # Suppress output of the indented code                                       |
|            -nm,    --no-modify     # Don't modify the file                                                      |
|            --backup-dir            # The directory where the backup file is to be written                       |
|            --clojure               # Use Clojure keywords                                                       |
|            --lisp                  # Use Lisp keywords                                                          |
|            --newlisp               # Use newLISP keywords                                                       |
|            --scheme                # Use Scheme keywords                                                        |
|            --default-indent <num>  # The indent level to be used in case a                                      |
|                                    function's argument is in the next line. Vim uses 2, the most common being 1.|
|            --indent-comments, -ic  # False by default. If true, comment lines will be indented possibly         |
|                                        messing with any deliberate comment layout                               |
+-----------------------------------------------------------------------------------------------------------------+
'''
    else:
        indent_file(sys.argv[1])



