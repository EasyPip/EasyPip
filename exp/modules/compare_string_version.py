import sys


def compareVersion(*args):
    def checkPythonVersion():
        '''
        it is required python 3. or above
        '''
        if check(trim(sys.version.split(' ')[0]), '3') < 2:
            return True
        return False

    def checkUsage(*args):
        '''
        checking the rules - details below
        '''
        desc = """
            usage:
                from compare import compareVersion
                print(compareVersion(a,b))

            expected return
            when
                a==b: 
                    a is equal to b 
                a>b: 
                    a is greater than b
                a<b: 
                    a is less than b
            Exceptions:

            either a is null and/or b is null:
                Value(s) can not be null: Both values must be string    
            either a and/or b are/is not a string:
                Both must be string

            assumptions:
                a and b are string
                a and b are not null (None)
                both version strings only contain numbers (0...9) and this char '.':
                    123.456.789.012
                    'A..Z','a..z' and any other chars like !@#$%¨&*()[}]{´`~^ç?/;:.>,<\| will be removed from the comparison:
                        some adjustment would be applied after char removal:
                        '..' will be replaced by '.'
                        string ending in '.' will be shorted by 1
                this '..' will not be accepted as it is '.' duplicated:
                        '10..12..13..14' will become '10.12.13.14'
                the comparison would be from the group split by the char '.':
                        10.12.13.14 would be treated as 10 12 13 14
                        01.10.100.001 would be treated as 1 10 100 1
                all the comparison would check the integer part of the version:
                        '10.0' is equal to '010.0.0.0.0.0.0.0' because int('10.0') is equal to int ('010')

                whoever version number has the higher far left group would be named as greater:
                        10.0.0.0.0.1 is greater then 9.9.9.9.9.9.9
                        0.1.0.0.0.0.1 is greater than 0.0.9
                        the same "int" rule will be applied for any other group in the string
                all '0's from the left will be disregarded if its value is '0':
                        1.0.0.0 is equal to 1.0 and it is equal to 1
            """

        if len(args) == 0 or len(args) > 2:
            print('It is required 02 Value(s) and must be string')
            return False
        elif len(args) == 1:
            if '-h' in args[0]:
                print(
                    "Usage: \n\tpython compareVersion(a,b)  \na and b must be strings \nfor aditional info\nPlease use:\npython compareVersion('H')")
            elif '-H' in args[0]:
                print(desc, "\npython compareVersion('-h') for help")
            return False
        elif type(args[0]) != str or type(args[1]) != str:
            print('Both must be string')
            return False
        return True

    def clean(rawString):
        '''
        filtering out all char but numbers (0...9) and this char '.':
        '''
        cleanString = ''
        valid = [46, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
        for i in rawString:
            if ord(i) in valid:
                cleanString += i
        '''
        removing garbage - if any
        '''
        while cleanString.count('..') > 0:
            cleanString = cleanString.replace('..', '.')
        if cleanString[-1] == '.':
            cleanString = cleanString[:-1]
        return cleanString

    def trim(newString, char='.'):
        '''
        this function will reduce the string by removing all zeros
        from the far right position
                10.0.0.0.1.0.0.0.0 will become 10.0.0.0.1
            0.0.1.0.0          will become 0.0.1
            1.2.3.4.5          will remain the same
        '''
        trimString = newString.split(char)
        k = len(trimString) - 1
        i = 0
        while i < k:
            if int(trimString[-1]) == 0:
                trimString.pop()
            else:
                break
            i += 1
        return (trimString)

    def check(a, b):
        '''
        this function will
          return 1 if a>b
                 2 if a<b
                 0 if a==b
        '''
        if a == b:  # after reducing original a and b, it is worth to double check
            return 0

        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                continue
            elif int(a[i]) > int(b[i]):
                return 1
            elif int(a[i]) < int(b[i]):
                return 2

        '''
        at this point - after processing i digits, 
        a is equal to b
        so, since both a and b have been reduced, it means there is 
        no one '0' at the far right position, therefore:
           a will be greater than b if len(a) > len(b)
           otherwise a will be less than b
        '''
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return 2
        # they have the same 'int' value
        return 0

    string = ['is equal to', 'is greater than', 'is less than']
    if checkPythonVersion():
        # python version must be 3. or above
        if checkUsage(*args):
            # Null values are not allowed, args must be string and it is required two strings
            a, b = args[0].strip(), args[1].strip()
            delta = check(trim(clean(a)), trim(clean(b)))
            return a + ' ' + string[delta] + ' ' + b
        else:
            return ('Usage: \n\tpython compareVersion(a,b)  \n\ta and b must be strings')
            return ("python compareVersion('-h') for help")
    else:
        return ('it requires python 3.x or above')