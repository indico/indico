#!python -u

import re, sys, pickle, os, StringIO

class StrToFakeFileHandle:
    '''We need this fake file handle if we encounter Python code inside TPL files
    in which case we need to provide a file handle to the Python convert function.
    Note that the file works in FIFO mode and that is not possible to seek it.
    '''
    def __init__(self,inputstring, name='', startlinenumber=1):
        '''Constructor of the fake file handle
        @param inputstring: The initial content of the file
        '''
        self._str = inputstring
        self.name = name
        self.startlinenumber = startlinenumber

    def read(self, nbchars=-1):
        '''Read nbchars bytes from the file
        @param nbchars The number of bytes to read
        @return: Up to nbchars read from the file
        '''
        if nbchars != -1 and nbchars < len(self._str):
            tmp = self._str[:nbchars]
            self._str = self._str[nbchars:]
            return tmp
        else:
            tmp = self._str
            self._str = ''
            return tmp

    def write(self, string):
        '''Write some content to the file
        @param string: The content to write to the file
        '''
        self._str += string

    def close(self):
        '''More or less a no-op but we need to provide it'''
        self._str = ''

class SinkFile:
    '''We need this if we don't want to produce any output. This is more or
    less the same as writing to /dev/null in GNU/Linux'''
    def __init__(self):
        pass

    def write(self, string):
        pass

    def close(self):
        pass

class AddSpace(object):
    """Very simple class which adds a space to the end of input stream."""
    def __init__(self, fh, name='', startlinenumber=1):
        self._fh = fh
        self._spaceAdded = False

        self.name = name
        self.startlinenumber = startlinenumber

    def read(self, nbchars=-1):
        data = self._fh.read(nbchars)
        if not data and not self._spaceAdded:
            self._spaceAdded = True
            data = ' '
        return data

class i18nUtil:
    def __init__(self, chunksize=32):
        self._chunksize = chunksize
        self._re_only_whitespace = re.compile(r'\A[\W\n]*\Z', re.MULTILINE)
        self._re_spaces_after_parentesis = re.compile(r'\(\s*', re.MULTILINE)
        # Strips away whitespace that comes before and after. Note that %(foo)s is also
        # considered as being a whitespace here
        re_splitter = r'\A(?:[\s]|%\([^\)]*\)s|&nbsp;)*([\s\S]*?)(?:[\s]|%\([^\)]*\)s|&nbsp;)*\Z'
        self._re_whitespace_splitter = re.compile(re_splitter)
        # These variables were used in the old-old Indico template engine
        self._re_tpl_python_var = re.compile(r'%\([^\)]*\)s', re.MULTILINE)
        self._html_space_equivalent = re.compile(r'[\n\r \t]+', re.MULTILINE)
        self._pkl_save_path = os.path.dirname(__file__)
        self._translatableAttributes = ['value', 'title', 'summary', 'alt']
        try:
            ld_file = open(os.path.join(self._pkl_save_path, 'learning_dict.pkl'), 'rb')
            self._learning_dict = pickle.load(ld_file)
            ld_file.close()
        except IOError, e:
            self._learning_dict = {}
        try:
            nd_file = open(os.path.join(self._pkl_save_path, 'no_dict.pkl'), 'rb')
            self._no_dict = pickle.load(nd_file)
            nd_file.close()
        except IOError:
            self._no_dict = {}
        except EOFError, e:
            self._no_dict = {}
            print("EOFError:%s" % e)

    def _saveLearningDict(self):
        '''Serialize the dictionary containing answers (y/n) for every string.
        This allows us to propose default values when the same string is encountered elsewhere'''
        ld_file = open(os.path.join(self._pkl_save_path, 'learning_dict.pkl'), 'wb')
        pickle.dump(self._learning_dict, ld_file)
        ld_file.close()

    def _saveNoDict(self):
        '''Serialize the dictionary containing (string, file, linenumber) for which
        no has been answered. This allows us to directly say no next time we see the same triplet'''
        nd_file = open(os.path.join(self._pkl_save_path, 'no_dict.pkl'), 'wb')
        pickle.dump(self._no_dict, nd_file)
        nd_file.close()

    def _askYesNo(self, question, default=None):
        '''Prompts for an answer to a given question, that can be answered by yes or by no
        @param question: The question to ask
        @return True or False depending on the user's input
        '''
        answ = '-'
        while not (answ in ['Y', 'y', 'N', 'n']) and (answ != '' or default == None):
            print question + " (y/Y/n/N)" + ((default == True) * " [y]") + ((default == False) * " [n]")
            answ = raw_input()
        if default != None and answ == '':
            return default
        if answ in ['Y', 'y']:
            return True
        else:
            return False

    def _isTranslatableAttribute(self, attributeName):
        '''Tells us by looking at the attribute name if this will be a text that
        will be displayed, like for example value.
        Answers False by default if the tag is unknown
        @param attributeName: The name of the attribute we want to examine
        @return: True if attribute will be displayed, False otherwise
        '''
        return (attributeName in self._translatableAttributes)

    def _countNewlines(self,string):
        '''Counts how many newlines can be found in a given string
        @param string: The string to examine
        '''
        pos = None
        count = 0
        while pos != -1:
            if pos == None:
                pos = -1
            pos = string.find('\n',pos + 1)
            if pos != -1:
                count += 1
        return count

    def _getInnerI18nFromStr(self, strAndLineNb):
        '''Searches for _() inside a string, and return a list of inner strings,
        or return a list with the main string if no inner strings where found'''
        (string, nb) = strAndLineNb
        begin = string.find('_("', 0)
        inner_strings = []
        while begin != -1:
            end = string.find('")', begin)
            inner_strings.append((string[begin + 3: end], nb))
            begin = string.find('_("', end)
        if len(inner_strings) == 0:
            return [strAndLineNb]
        else:
            return inner_strings

    def _replaceDecide(self, toreplace, interactive, filename,
                       linenumber, always_ask=False, dont_use_default=False):
        '''Determines if a given string needs to be replaced by its _("...") counter part
        @param toreplace: The string to be decided about
        @param interactive: Whether to ask the user or not
        @return A Boolean
        '''
        if interactive:
            return self._replaceDecideInteractive(toreplace, filename, linenumber, always_ask, dont_use_default)
        else:
            return self._replaceDecideHeuristics(toreplace)

    def _replaceDecideInteractive(self, toreplace, filename, linenumber,
                                  always_ask=False, dont_use_default=False):
        '''Decide whether a given string needs to be replaced based on user input
        @param toreplace: The string to be decided about
        @return: A Boolean
        '''
        default = None
        if self._learning_dict.has_key(toreplace) and not dont_use_default:
            default = self._learning_dict[toreplace]
        answer = None
        if self._no_dict.has_key((filename, linenumber, toreplace)) and not always_ask:
            answer = False
        else:
            answer = self._askYesNo('\nFile = "%s", Line = %s\nFound text "%s"\nDo you want this text to be internationalized?' % (filename, linenumber, toreplace), default)
        if not dont_use_default:
            self._learning_dict[toreplace] = answer
        if not answer and not always_ask:
            self._no_dict[(filename, linenumber, toreplace)] = False
        return answer

    def _replaceDecideHeuristics(self, toreplace):
        '''Decide whether a string may be replaced by using heuristics, without any user interaction
        @param toreplace: The string that has to be checked
        @return: A Boolean
        '''
        raise Exception("Not implemented")

    def _isSubjectToReplacement(self, toreplace):
        '''Performs a very basic check if this string may have to be replaced.
        If it is only constituted by spaces, and newlines, forget it
        @param toreplace: The string to check
        @return: A Boolean
        '''
        # Feel free to add some more if you have ideas.
        # You can put string an regular expressions
        filter_out = ['&nbsp;', self._re_tpl_python_var]
        for f in filter_out:
            if isinstance(f, str):
                toreplace = toreplace.replace(f, '')
            else:
                toreplace = re.sub(f, '', toreplace)
        return not re.search(self._re_only_whitespace, toreplace)

    def _findFirst(self, string, needles, begin=0):
        '''Searches for the first string in needles that appears in string
        @param string: The string where to perform the search
        @param needles: The strings we want to find
        @return: A tuple containing the string that has been found and its position
        '''
        poss = map(lambda n: string.find(n, begin), needles)
        pmin = -1
        nmin = None
        for (n, p) in zip(needles, poss):
            if (pmin == -1 or p < pmin) and p != -1:
                pmin = p
                nmin = n
        return (nmin, pmin)

    def _splitAwayLeadingAndTrailingWhitespaces(self, string):
        '''Splits a given string into tree parts: The leading spaces, The text and The trailing spaces
        @param string: The string to split
        @return: (leading_spaces, text, trailing_spaces)
        '''
        m = re.match(self._re_whitespace_splitter, string)
        if m == None:
            raise Exception("No match found, this should never happen")
        else:
            left = string[:m.start(1)]
            text = string[m.start(1):m.end(1)]
            right = string[m.end(1):]
            # Special case, only blanks
            if text == '':
                return ('', left + right, '')
            return (left, text, right)

    def _strToI18nTpl(self, toreplace):
        '''Replaces the given text by a function call able to translate this string
        @param toreplace: The string that has to be translated
        @return: The function call
        '''
        if not ('\n' in toreplace):
            return '${_("' + toreplace.replace('"', '\\"') + '")}'
        else:
            return '${_("""' + toreplace.replace('"""', '\\"\\"\\"') + '""")}'

    def _strToI18nPy(self, toreplace, delimiter, ur):
        '''Replaces the given text by a function call able to translate this string
        @param toreplace: The string that has to be translated
        @return: The function call
        '''
        return '_(' + ur + delimiter + toreplace + delimiter + ')'

    def getI18nStringsPY(self, filein):
        '''Retrieves the list of all string that have _( ) around them in a python file
        @param filein: The file to take as input
        @return: An array of tuples of strings and line numbers
        '''
        strings = []
        sinkfile = SinkFile()
        self.convertPY(filein, sinkfile, False, strings, True, True)
        return strings

    def getI18nStringsTPL(self, filein):
        '''Retrieves the list of all strings that have _( ) around them in a tpl file
        @param filein: The file to take as input
        @return: An array of tuples of strings and line numbers
        '''
        strings = []
        sinkfile = SinkFile()
        self.convertTPL(filein, sinkfile, False, strings, True, True)
        return strings

    def _convertJSString(self, string, filename, linenumber, interactive=True,
                         recordI18nStr=False, always_ask=False, dont_use_default=False):
        '''Finds translatable strings in a Javascript string. This is not so
        much complicated, but we have to deal with ${ ... } constructs
        @param string: The Javascript string to convert
        @param filename: The name of the file where the conversion takes place.
        @param linenumber: The line number where our string is. Remember, Javascript has no multiline strings, so no need to count newlines.
        @param interactive: Whether we ask the user if he wants to replace a string or whether to use heuristics
        @param recordI18nStr: False or a list where to put all i18n'ed strings
        @return: The transformed Javascript string
        '''
        # Input buffer
        inputBuffer = string
        # Output buffer
        outputBuffer = ''
        while inputBuffer != '':
            beg = inputBuffer.find('${')
            if beg != 0:
                if beg == -1:
                    beg = len(inputBuffer)
                string = inputBuffer[:beg]
                inputBuffer = inputBuffer[beg:]
                (left, text, right) = self._splitAwayLeadingAndTrailingWhitespaces(string)
                if (recordI18nStr == False) and self._replaceDecide(text, interactive, filename, linenumber, always_ask, dont_use_default):
                    newstring = left + self._strToI18nTpl(text) + right
                    outputBuffer += newstring
                else:
                    outputBuffer += string
            else:
                end = inputBuffer.find('}')
                opencodetag = inputBuffer[:2]
                pythoncode = inputBuffer[2:end]
                inputBuffer = inputBuffer[end + 1:]
                inputFakeFile = StrToFakeFileHandle(pythoncode, filename, linenumber)
                outputFakeFile = StrToFakeFileHandle("")
                self.convertPY(inputFakeFile, outputFakeFile, interactive, recordI18nStr)
                outputBuffer += opencodetag
                outputBuffer += outputFakeFile.read()
                outputBuffer += '}'
        return outputBuffer

    def _convertJS(self, jscode, filename, linenumber, interactive=True, recordI18nStr=False,
                   always_ask=False, dont_use_default=False):
        '''Finds all strings in Javascript code embedded in a template file and
        replaces them using this syntax '${_('string')}' or "${_("string")}"
        @param jscode: The Javascript code to transform
        @param interactive: Whether to ask the user if he wants to replace a string or whether to do it based on heuristics
        @param recordI18nStr: False or an array where to record internationalized strings
        @return: The transformed Javascript code
        '''
        # The delimiter of the string, ' or "
        delimiter = None
        # Wether we are recording a string or not
        recordString = False
        # Wether we are in a comment
        inComment = False
        # Comment end sequence '\n' or '*/'
        commentEndSeq = None
        # Input buffer
        inputBuffer = jscode
        # Output buffer
        outputBuffer = ''
        while inputBuffer != '':
            if recordString:
                (first, pos) = (None, -1)
                while first != delimiter:
                    (first, pos) = self._findFirst(inputBuffer, ['\\' + delimiter, delimiter, '${'], pos + 1)
                    if first == '${':
                        pos = inputBuffer.find('}', pos)
                    elif first == '\\' + delimiter:
                        pos += 1
                string = inputBuffer[:pos]
                # Process the Javascript string
                output = self._convertJSString(string, filename, linenumber, interactive,
                                               recordI18nStr, always_ask, dont_use_default)
                outputBuffer += output
                linenumber += self._countNewlines(string)
                outputBuffer += delimiter
                inputBuffer = inputBuffer[pos + 1:]
                pos = -1
                recordString = False
            elif inComment:
                pos = inputBuffer.find(commentEndSeq)
                if pos == -1:
                    pos = len(inputBuffer)
                outputBuffer += inputBuffer[:pos]
                linenumber += self._countNewlines(inputBuffer[:pos])
                inputBuffer = inputBuffer[pos:]
                pos = -1
                inComment = False
            else:
                (first, pos) = self._findFirst(inputBuffer, ['/*', '//', '"', "'"])
                if first in ['/*', '//']:
                    inComment = True
                    if first == '//':
                        commentEndSeq = '\n'
                    else:
                        commentEndSeq = '*/'
                elif first in ['"', "'"]:
                    recordString = True
                    delimiter = first
                else:
                    first = ''
                    pos = len(inputBuffer)
                outputBuffer += inputBuffer[:pos + len(first)]
                linenumber += self._countNewlines(inputBuffer[:pos + len(first)])
                inputBuffer = inputBuffer[pos + len(first):]
                pos = -1
        return outputBuffer

    def convertPY(self, filein, outputFile=sys.stdout, interactive=True,
                  recordI18nStr=False, always_ask=False, dont_use_default=False):
        '''Finds all strings in a .py file and replaces them using this syntax _("...")
        @param filein: An open file descriptor to a tpl file, will be used as input
        @param outputFile: An open file descriptor where to send the output
        @param interactive: Whether to ask the user if he wants to replace a string or to replace it directly
        @param recordI18nStr: False or an array where to record internationalized strings
        '''
        # True when we are reading a short string ( '...' or "..." )
        recordShortString = False
        # True when we are reading a long string ( '''...''' or """...""" )
        recordLongString = False
        # True when we a reading a comment
        inComment = False
        # ' or "
        delimiter = ''
        # How many delimiters have we found one after another
        countDelimiter = 0
        # The string we are currently reading
        string = ''
        # Buffer for stuff we want to write to output later
        towrite = ''
        # Buffer of already written stuff with spaces stripped
        outNoSpaces = ''
        # Do we have to find strings of this form _('...') ?
        recordOnly = (recordI18nStr != False)
        # Start line number. This is useful when the convertTPL() function
        # started reading the file and has to tell us where we begin
        linenumber = 1
        if hasattr(filein, 'startlinenumber'):
            linenumber = filein.startlinenumber

        # This is needed to solve an issue when the last empty string in the input
        # is being ignored. We append a space to the input and later remove it.
        filein = AddSpace(filein, filein.name, linenumber)
        fileout = StrToFakeFileHandle('')

        def unwriteUR(writebuffer):
            '''Looks at the two last written chars, and removes them if they are a
            possible prefix from a string. We need this because it is only at the moment
            we know that we have a string, that we can know that these letters have a special meaning
            @param writebuffer: The buffer where the unwritten data is. We need to have a buffer policy that always keeps 2 characters at least for this to work
            @return: A tuple containing the prefix and the buffer with the prefix removed
            '''
            Rr = ['R', 'r']
            Uu = ['U', 'u']
            if (len(writebuffer) >= 2) and (writebuffer[-1] in Rr) and (writebuffer[-2] in Uu):
                tmp = writebuffer[-2:]
                writebuffer = writebuffer[:-2]
                return (tmp, writebuffer)
            elif len(writebuffer) >= 1:
                if (writebuffer[-1] in Rr):
                    tmp = writebuffer[-1]
                    writebuffer = writebuffer[:-1]
                    return (tmp, writebuffer)
                elif (writebuffer[-1] in Uu):
                    tmp = writebuffer[-1]
                    writebuffer = writebuffer[:-1]
                    return (tmp, writebuffer)
                else:
                    return ('', writebuffer)
            else:
                return ('', writebuffer)

        def checkI18n(prefixnospaces, suffixwithspaces):
            '''Searches for _( at the end of the buffer. We need to have a second buffer
            with spaces removed, in case there are too much spaces and _( disappears from inside the buffer
            @param prefixnospaces: A second buffer with no spaces,tabs, etc in it (contains already written data)
            @param suffixwithspaces: The normal buffer for unwritten data
            @return: True if found False otherwise
            '''
            writebuffer = re.sub(self._re_spaces_after_parentesis, '(', prefixnospaces + suffixwithspaces)
            if writebuffer == '_(':
                return True
            elif len(writebuffer) < 3:
                return False
            else:
                chars = writebuffer[-3:]
                if chars[1:] == '_(':
                    # Check also that the previous character
                    # can not be part of an identifier
                    c = chars[0]
                    if ('a' <= c <= 'z') or ('A' <= c <= 'Z') or (c == '_') or ('0' <= c <= '9'):
                        return False
                    else:
                        return True
                else:
                    return False
        read = filein.read(self._chunksize)
        tryParsing = True
        while read != '' or string:
            # Process newly read data
            while read != '' or tryParsing:
                tryParsing = False
                nextSingleQuote = read.find("'")
                nextDoubleQuote = read.find('"')
                nextQuote = { "'" : nextSingleQuote, '"' : nextDoubleQuote }
                nextEscapeChar = read.find("\\")
                nextComment = read.find("#")
                nextNewline = read.find("\n")
                if inComment:
                    if nextNewline == -1:
                        towrite += read
                        read = ''
                    else:
                        towrite += read[:nextNewline]
                        read = read[nextNewline:]
                        inComment = False
                elif (not recordShortString) and (not recordLongString):
                    if countDelimiter == 0:
                        # Check whether the '#' is the first interesting symbol,
                        # and whether we did already start a string
                        if (nextComment != -1) and ((nextSingleQuote == -1) or (nextComment < nextSingleQuote)) and ((nextDoubleQuote == -1) or (nextComment < nextDoubleQuote)) and (countDelimiter == 0):
                            inComment = True
                            towrite += read[:nextComment + 1]
                            read = read[nextComment + 1:]
                        elif nextSingleQuote == -1:
                            if nextDoubleQuote == -1:
                                # Not recording, no delimiter
                                towrite += read
                                read = ''
                            else:
                                # Not recording, found first "
                                delimiter = '"'
                                countDelimiter = 1
                                towrite += read[:nextDoubleQuote]
                                read = read[nextDoubleQuote + 1:]
                        else:
                            if nextDoubleQuote == -1:
                                # Not recording, found first '
                                delimiter = "'"
                                countDelimiter = 1
                                towrite += read[:nextSingleQuote]
                                read = read[nextSingleQuote + 1:]
                            else:
                                if nextSingleQuote < nextDoubleQuote:
                                    # Not recording, found first '
                                    delimiter = "'"
                                    countDelimiter = 1
                                    towrite += read[:nextSingleQuote]
                                    read = read[nextSingleQuote + 1:]
                                else:
                                    # Not recording, found first "
                                    delimiter = '"'
                                    countDelimiter = 1
                                    towrite += read[:nextDoubleQuote]
                                    read = read[nextDoubleQuote + 1:]
                    elif read and read[0] == delimiter and countDelimiter <= 6:
                        # Not recording, found next delimiter
                        countDelimiter += 1
                        read = read[1:]
                    else:
                        # Not recording found last delimiter
                        if countDelimiter == 1:
                            # Short string, start recording
                            recordShortString = True
                        elif countDelimiter == 2:
                            # String is empty, no need to record it
                            # and no need to internationalize it
                            towrite += (delimiter * 2)
                        elif countDelimiter == 3:
                            # Long string, start recording
                            recordLongString = True
                        elif countDelimiter == 6:
                            # Empty long string, no need to record it
                            # and no need to internationalize it
                            towrite += delimiter * 6
                        countDelimiter = 0
                elif recordShortString:
                    if countDelimiter == 0:
                        if nextEscapeChar == -1:
                            if nextQuote[delimiter] == -1:
                                # Recording short string found no delimiter
                                string += read
                                read = ''
                            else:
                                # Recording short string found first delimiter
                                q = nextQuote[delimiter]
                                string += read[:q]
                                read = read[q + 1:]
                                countDelimiter = 1
                        else:
                            if nextQuote[delimiter] == -1:
                                # Recording short string found escape char
                                # we need to ensure that we have enough chars
                                # in our buffer
                                if len(read) < nextEscapeChar + 2:
                                    read += filein.read(self._chunksize)
                                string += read[:nextEscapeChar + 2]
                                read = read[nextEscapeChar + 2:]
                            else:
                                if nextQuote[delimiter] < nextEscapeChar:
                                    # Recording short string found first delimiter
                                    q = nextQuote[delimiter]
                                    string += read[:q]
                                    read = read[q + 1:]
                                    countDelimiter = 1
                                else:
                                    # Recording short string found escape char
                                    # we need to ensure that we have enough chars
                                    # in our buffer
                                    if len(read) < nextEscapeChar + 2:
                                        read += filein.read(self._chunksize)
                                    string += read[:nextEscapeChar + 2]
                                    read = read[nextEscapeChar + 2:]
                    else:
                        # Remember, this is a short string and we have one delimiter
                        # so the string ends here
                        (left, text, right) = self._splitAwayLeadingAndTrailingWhitespaces(string)
                        (ur, towrite) = unwriteUR(towrite)
                        d = delimiter
                        chk = checkI18n(outNoSpaces, towrite)
                        # If we are asked to list all i18n string, do it
                        if chk and recordOnly:
                            strAndLineNb = (string, linenumber + self._countNewlines(towrite))
                            recordI18nStr += self._getInnerI18nFromStr(strAndLineNb)
                        if (not chk) and (not recordOnly) and self._isSubjectToReplacement(text) and self._replaceDecide(string, interactive, filein.name, linenumber + self._countNewlines(towrite), always_ask, dont_use_default):
                            if left != '':
                                towrite += (ur + d + left + d)
                                towrite += ' + '
                            towrite += self._strToI18nPy(text, d, ur)
                            if right != '':
                                towrite += ' + '
                                towrite += (ur + d + right + d)
                        else:
                            towrite += (ur + d + string + d)
                        string = ''
                        countDelimiter = 0
                        recordShortString = False
                elif recordLongString:
                    if countDelimiter == 0:
                        if nextEscapeChar == -1:
                            if nextQuote[delimiter] == -1:
                                # Recording long string found no delimiter
                                string += read
                                read = ''
                            else:
                                # Recording long string found first delimiter
                                q = nextQuote[delimiter]
                                string += read[:q]
                                read = read[q + 1:]
                                countDelimiter = 1
                        else:
                            if nextQuote[delimiter] == -1:
                                # Recording long string found escape char
                                # we need to ensure that we have enough chars
                                # in our buffer
                                if len(read) < nextEscapeChar + 2:
                                    read += filein.read(self._chunksize)
                                string += read[:nextEscapeChar + 2]
                                read = read[nextEscapeChar + 2:]
                            else:
                                if nextQuote[delimiter] < nextEscapeChar:
                                    # Recording long string found first delimiter
                                    q = nextQuote[delimiter]
                                    string += read[:q]
                                    read = read[q + 1:]
                                    countDelimiter = 1
                                else:
                                    # Recording long string found escape char
                                    # we need to ensure that we have enough chars
                                    # in our buffer
                                    if len(read) < nextEscapeChar + 2:
                                        read += filein.read(self._chunksize)
                                    string += read[:nextEscapeChar + 2]
                                    read = read[nextEscapeChar + 2:]
                    elif read and read[0] == delimiter and countDelimiter <= 3:
                        countDelimiter += 1
                        read = read[1:]
                    else:
                        if countDelimiter < 3:
                            string += (delimiter * countDelimiter)
                        elif countDelimiter == 3:
                            (left, text, right) = self._splitAwayLeadingAndTrailingWhitespaces(string)
                            (ur, towrite) = unwriteUR(towrite)
                            d = (delimiter * 3)
                            chk = checkI18n(outNoSpaces, towrite)
                            # If we are asked to list all i18n string, do it
                            if chk and recordOnly:
                                strAndLineNb = (string, linenumber + self._countNewlines(towrite))
                                recordI18nStr += self._getInnerI18nFromStr(strAndLineNb)
                            if (not chk) and (not recordOnly) and self._isSubjectToReplacement(text) and self._replaceDecide(string, interactive, filein.name, linenumber + self._countNewlines(towrite), always_ask, dont_use_default):
                                if left != '':
                                    towrite += (ur + d + left + d)
                                    towrite += ' + '
                                towrite += self._strToI18nPy(text, d, ur)
                                if right != '':
                                    towrite += ' + '
                                    towrite += (ur + d + right + d)
                            else:
                                towrite += (ur + d + string + d)
                            recordLongString = False
                            string = ''
                        else:
                            raise Exception("Hey this is a bug, fix it please")
                        countDelimiter = 0
                else:
                    raise Exception("Actually we should never land here...")
                # We need to keep at least 2 characters in the write buffer
                # Because we need to be able to 'unwrite' the ur, u, r prefixes
                if len(towrite) > 2:
                    fileout.write(towrite[:-2])
                    linenumber += self._countNewlines(towrite[:-2])
                    outNoSpaces += re.sub(self._re_spaces_after_parentesis, '(', towrite[:-2], re.MULTILINE)
                    towrite = towrite[-2:]
                # We should also empty the outNoSpaces buffer if needed
                if len(outNoSpaces) > 3:
                    outNoSpaces = outNoSpaces[-3:]
            # Read next block of bytes
            read += filein.read(self._chunksize)
            tryParsing = True
        # Flush buffer
        fileout.write(towrite)

        # Write the result without the last space character
        outputFile.write(fileout.read()[:-1])

        # Write out learning dict
        self._saveLearningDict()
        # Write out no dict
        self._saveNoDict()

    def convertTPL(self, inputFile, outputFile=sys.stdout, interactive=True,
                   recordI18nStr=False, always_ask=False, dont_use_default=False):
        '''Finds all strings in a .tpl file and replaces them using this syntax _("...")
        @param inputFile: An open file descriptor to a tpl file, will be used as input
        @param outputFile: An open file descriptor where to send the output
        @param interactive: Whether to ask the user if he wants to replace a string or to replace it directly
        @param recordI18nStr: False or an array where to record internationalized strings
        '''
        # Starting line number.
        linenumber = 1
        if hasattr(inputFile, 'startlinenumber'):
            linenumber = inputFile.startlinenumber

        # Mako has special constructs `% if expr:`, `% endif` and etc
        # There are no translatable strings in those constructs, so in order
        # to make the life easier for the script, we replace them with
        # simple ${}. After the script has been run, we undo the changes.
        originalLines = {}
        correctedLines = []
        stringFileHandle = StringIO.StringIO(inputFile.read())
        for lineNumber, line in enumerate(stringFileHandle.readlines()):
            if re.match('^\s*%[^>].*$', line):
                correctedLines.append('${}\n')
                originalLines[lineNumber] = line
            else:
                correctedLines.append(line)
        filein = StrToFakeFileHandle(''.join(correctedLines), inputFile.name, linenumber)
        fileout = StrToFakeFileHandle('')

        # Have we found the start of a string?
        recordString = True
        # The content of the string we have found
        string = ''
        # Do we have to find strings of this form _('...') ?
        # or convert the file otherwise
        recordOnly = (recordI18nStr != False)

        # End of file detection
        seenEOF = False
        # Current attribute name
        attributeName = ''
        # Determines whether the last tag examined was an opening script tag
        isScriptTag = False
        # While reading a tag, tells us if we have already seen it's name
        readTagName = False

        read = filein.read(self._chunksize)
        while read != '':
            # Process the newly read data
            while read != '':
                if recordString:
                    if isScriptTag:
                        opentag = -1
                        while opentag == -1:
                            opentag = read.find('</script>')
                            if opentag == -1:
                                read += filein.read(self._chunksize)
                    else:
                        # Make sure we do not miss ${
                        while read.find('${') == -1 and read.endswith('$'):
                            newData = filein.read(self._chunksize)
                            if newData == '':
                                break
                            read += newData
                        opentag = read.find('<')
                        expression = read.find('${')
                        if expression != -1:
                            if opentag == -1:
                                opentag = expression
                            else:
                                opentag = min([opentag, expression])

                    if seenEOF:
                        read = ''
                    if opentag != -1:
                        string += read[:opentag]
                        read = read[opentag:]
                        recordString = False
                        readTagName = False
                        # We have finished reading a string
                        if isScriptTag:
                            output = self._convertJS(string, filein.name, linenumber, interactive, recordI18nStr, always_ask, dont_use_default)
                            fileout.write(output)
                            linenumber += self._countNewlines(output)
                        elif self._isSubjectToReplacement(string):
                            (left, text, right) = self._splitAwayLeadingAndTrailingWhitespaces(string)
                            # If we are listing i18n'ed strings we don't want and modification to be done
                            if (not recordOnly) and self._replaceDecide(text, interactive, filein.name, linenumber, always_ask, dont_use_default):
                                newstring = left + self._strToI18nTpl(text) + right
                                fileout.write(newstring)
                                linenumber += self._countNewlines(newstring)
                            else:
                                fileout.write(string)
                                linenumber += self._countNewlines(string)
                        else:
                            fileout.write(string)
                            linenumber += self._countNewlines(string)
                        string = ''

                        # Detect presence of ${, <% or <!--
                        if len(read) < opentag + 4:
                            read += filein.read(self._chunksize)
                        if read[:4] == '<!--':
                            end = read.find('-->')
                            while end == -1:
                                read += filein.read(self._chunksize)
                                end = read.find('-->')
                            fileout.write(read[:end + 3])
                            read = read[end + 3:]
                            recordString = True
                        elif read[:2] == '${' or re.match("<%\s", read[:3]) is not None:
                            # Search for end tag, we don't have to worry if the Python
                            # code contains theses characters since Indico's implementation
                            # of templates does not allow this
                            endTag = '}' if read[:2] == '${' else '%>'
                            end = read.find(endTag)
                            r = None
                            while end == -1 and r != '':
                                r = filein.read(self._chunksize)
                                read += r
                                end = read.find(endTag)
                            if end != -1:
                                opencodetag = read[:2]
                                pythoncode = read[2:end]
                                read = read[end + len(endTag):]
                                inputFakeFile = StrToFakeFileHandle(pythoncode, filein.name, linenumber)
                                outputFakeFile = StrToFakeFileHandle("")
                                self.convertPY(inputFakeFile, outputFakeFile, interactive, recordI18nStr)
                                tmp = opencodetag
                                tmp += outputFakeFile.read()
                                tmp += endTag
                                fileout.write(tmp)
                                linenumber += self._countNewlines(tmp)
                                recordString = True
                            else:
                                raise Exception("Malformed tpl file missing end tag (line:%s)" % (linenumber))
                    else:
                        string += read
                        read = ''
                else:
                    # In HTML tag
                    # The first thing we have to do here is to search if
                    # this is an opening script tag, since it receives a
                    # special treatment
                    if len(read) < 8:
                        read += filein.read(self._chunksize)
                    if not readTagName:
                        if read[1:7] == 'script' and read[7] in ['\n', '\t', '\r', ' ', '>']:
                            isScriptTag = True
                        else:
                            isScriptTag = False
                    readTagName = True
                    (first, firstpos) = self._findFirst(read, ['>', '${', '='])
                    if first == None:
                        fileout.write(read)
                        linenumber += self._countNewlines(read)
                        attributeName = re.split(self._html_space_equivalent, (attributeName + read).rstrip('\r\n\t ="'))[-1]
                        read = ''
                    elif first == '=':
                        pos = firstpos
                        beginatttr = None
                        endattr = None
                        quoted = None
                        while read[pos] in [' ', '\t', '\n', '\r', '=']:
                            pos += 1
                            if len(read) < pos + 1:
                                read += filein.read(self._chunksize)
                        if read[pos] == '"':
                            beginatttr = pos + 1
                            quoted = True
                        else:
                            beginatttr = pos
                            quoted = False
                        pos = beginatttr
                        if len(read) < pos + 2:
                            read += filein.read(self._chunksize)
                        while (quoted and (read[pos] != '"')) or (not quoted and not (read[pos] in [' ', '\n', '\r', '>', '\t'])):
                            if read[pos:pos + 2] == '${':
                                end = -1
                                while end == -1:
                                    read += filein.read(self._chunksize)
                                    end = read.find('}', pos)
                                pos = end + 1
                                if len(read) < pos + 2:
                                    read += filein.read(self._chunksize)
                            else:
                                pos += 1
                                if len(read) < pos + 2:
                                    read += filein.read(self._chunksize)
                        endattr = pos

                        # Write out the part that comes before the attribute
                        html = read[:beginatttr]
                        fileout.write(html)
                        attributeName = re.split(self._html_space_equivalent, (attributeName + html).rstrip('\t\n\r ="'))[-1]
                        linenumber += self._countNewlines(html)

                        # Process the attribute's value
                        # We can use convertTPL() again for the attribute since
                        # it's content is a subset of TPL files (it may contain
                        # ${ '...' } for example )
                        attr = read[beginatttr:endattr]
                        if not self._isTranslatableAttribute(attributeName) and recordI18nStr == False:
                            fileout.write(attr)
                        else:
                            if attributeName[:2].lower() == 'on':
                                # If our attribute starts with on, this means that it is Javascript code, in which case we threat it differently
                                output = self._convertJS(attr, filein.name, linenumber, interactive, recordI18nStr, always_ask, dont_use_default)
                                fileout.write(output)
                            else:
                                inputFakeFile = StrToFakeFileHandle(attr, filein.name)
                                inputFakeFile.startlinenumber = linenumber
                                outputFakeFile = StrToFakeFileHandle('')
                                self.convertTPL(inputFakeFile, outputFakeFile, interactive, recordI18nStr, always_ask, dont_use_default)
                                output = outputFakeFile.read()
                                fileout.write(output)
                        linenumber += self._countNewlines(attr)

                        # Update read buffer
                        read = read[endattr:]

                    elif first == '${':
                        # In HTML tag, found ${
                        html = read[:firstpos]
                        read = read[firstpos:]
                        fileout.write(html)
                        linenumber += self._countNewlines(html)
                        attributeName = ''
                        # Search for end tag, we don't have to worry if the Python
                        # code contains theses characters since Indico's implementation
                        # of templates does not allow this
                        end = read.find('}')
                        r = None
                        while end == -1 and r != '':
                            r = filein.read(self._chunksize)
                            read += r
                            end = read.find('}')
                        if end != -1:
                            opencodetag = read[:2]
                            pythoncode = read[2:end]
                            read = read[end + 1:]
                            inputFakeFile = StrToFakeFileHandle(pythoncode, filein.name, linenumber)
                            outputFakeFile = StrToFakeFileHandle("")
                            self.convertPY(inputFakeFile, outputFakeFile, interactive, recordI18nStr)
                            tmp = opencodetag
                            tmp += outputFakeFile.read()
                            tmp += '}'
                            fileout.write(tmp)
                            linenumber += self._countNewlines(tmp)
                        else:
                            raise Exception("Malformed tpl file missing } (line:%s)" % (linenumber))
                    elif first == '>':
                        # In HTML tag, found >
                        html = read[:firstpos + 1]
                        fileout.write(html)
                        linenumber += self._countNewlines(html)
                        read = read[firstpos + 1:]
                        recordString = True
                        attributeName = ''
                    else:
                        raise Exception("Bug found, please fix it")
            # Read next block of bytes
            read = filein.read(self._chunksize)
            if read == '' and not seenEOF:
                seenEOF = True
                # This is just to force the last string to be written too
                read = '<'

        # Put back the original Mako `% ...` construct lines
        stringFileHandle = StringIO.StringIO(fileout.read())
        for lineNumber, line in enumerate(stringFileHandle.readlines()):
            if lineNumber in originalLines:
                outputFile.write(originalLines[lineNumber])
            else:
                outputFile.write(line)

        # Write learning dict to disk
        self._saveLearningDict()
        # Write out no dict
        self._saveNoDict()

