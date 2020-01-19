import sys
import inspect
import time
from decimal import Decimal
from copy import copy

TargetFunc = None
class Debug:    #The debug class
    global TargetFunc

    def __init__(self, frame, event, arg):
        assert event == "call"  # assert that it is a call
        #identify call name, first line, filename
        self.FuncName = frame.f_code.co_name
        self.FirstLine = frame.f_code.co_firstlineno
        self.FileName = frame.f_code.co_filename
        self.prevLine = frame.f_lineno

        #reset dicts
        self.ResetDict()
        if TargetFunc == self.FuncName:self.co = ""
        else: self.co = "co-function "
        print('\n')
        print('Debugging Function:', self.co + self.FuncName, '\n' + 'Located at:', self.FileName, '\n' + 'Starting on Line:', self.FirstLine + 1)
        self.startTime = time.time_ns()
        self.ProgStartTime = time.time_ns()
        self.Lines = 1
        time.sleep(0)



    #Find local line based on function
    def Head(self, frame, end, cont = ""):
        if end:
            return str('Line '+ str(self.prevLine - self.FirstLine) + cont + ' (Programe Line ' + str(self.prevLine) + ') (iteration ' + str(self.UpdateLineNo(self.prevLine)) + ')(Line run time(nano):' +  str("{:.2E}".format(Decimal(time.time_ns() - self.startTime))) + ':') #last line
        else:
            return str('Line '+ str(self.prevLine - self.FirstLine) + ' (Programe Line ' + str(self.prevLine) + ') (iteration ' + str(self.UpdateLineNo(self.prevLine)) + ')(Line run time(nano):' +  str("{:.2E}".format(Decimal(time.time_ns() - self.startTime))) + '): ')
            self.startTime = time.time_ns()        

    #break up a dictionary into something easier to understand
    def Break(self, Type, dictionary):
        ret = ''
        if len(dictionary) > 0: # if it actually exists
            j = 0
            for i in dictionary.keys():
                if j != 0: #if i is not the first key
                    ret = str(str(ret) + '; ')
                ret = str(str(ret) + str(i) + ' has been ' + str(Type) + ' with a value of ' + str(dictionary.get(i)))
                j += 1
        return ret
    
    #tracer gets *called* by the interpreter
    def __call__(self, frame, event, arg):
        if event == "line":
            self.TraceVar(frame, event, arg, False)
            #update last frame
            self.prevLine = frame.f_lineno
            self.Lines += 1

        elif event in ("return", "exception"):
            self.TraceVar(frame, event, arg, True)
            self.trace_exit(frame, event, arg)
        else:
            raise RuntimeError("Invalid event: %r" % event)

    def TraceVar(self, frame, event, arg, end):
        NewVars = {}
        ChangedVars = {}
        for name, value in frame.f_locals.items(): # get the name and value of the variables
            if not name in self.Vars: #if the variable has not been added to the dictionary yet
                self.Vars[name] = copy(value) 
                NewVars[name] = copy(value)
                self.CreLine[name] = self.prevLine
                self.AddValue(name, copy(value))
            elif self.Vars.get(name) != value: #if the variable has changed
                if type(value) is list:
                    ChangedVars = copy(self.checkList(self.Vars[name], value, name))
                    self.Vars[name] = copy(value)
                    self.AddValue(name, copy(value))
                else:  
                    ChangedVars[name] = value
                    self.Vars[name] = value
                    self.AddValue(name, value)
                
        #print results
        if (len(NewVars) != 0 or len(ChangedVars) != 0): #if something happened
                if len(ChangedVars) == 0: # If only new variables are added
                    print(self.Head(frame, end), self.Break('added', NewVars))
                elif len(NewVars) == 0: # If only changes to variables are made
                    print(self.Head(frame, end), self.Break('changed', ChangedVars))
                else: #if both new vars are added and pre-existing vars are changes
                    print(self.Head(frame, end), self.Break('added', NewVars), '\n' + self.Head(frame, end, cont='(cont.)'), self.Break('changed', ChangedVars))
        else: print(self.Head(frame, end), 'No variables were added or changed')
                
    def AddValue(self, name, value):
        #order for dictionary: key = name, value = [(lineno, value)]
        if name in self.VarHistory: # if key is present
            self.VarHistory[name] = [*self.VarHistory[name], (self.prevLine, value)]
        else: #if the key does not yet exist
            self.VarHistory[name] = [(self.prevLine, value)]
            
    def trace_exit(self, frame, event, arg):
        """Report the current trace on exit"""
        print('Exiting', self.co+self.FuncName)
        print('\nHere is the final variable report:')
        for i in self.Vars.keys():
            print(str(i) + ': (Created on', str(self.CreLine[i]) + ') complete value list:')
            for j in self.VarHistory[i]:
                print("\t on line", str(j[0]) + ",", i, "became", j[1])
            if all(type(j) is int for j in [b for a in self.VarHistory[i] for b in a if a.index(b) == 1]): #if all the values are integers
                print("Variable", str(i), "has a range of", str(max([b for a in self.VarHistory[i] for b in a if a.index(b) == 1]) - min(b for a in self.VarHistory[i] for b in a if a.index(b) == 1)) + ", starting at", str(max([b for a in self.VarHistory[i] for b in a if a.index(b) == 1])),  "and ending at", str(min([b for a in self.VarHistory[i] for b in a if a.index(b) == 1])))
            else:
                print("The complete set of values for", str(i), "is", str([b for a in self.VarHistory[i] for b in a if a.index(b) == 1]))
        print('the total run time for function', self.co + self.FuncName, 'is', str(time.time_ns() - self.ProgStartTime), 'nanoseconds, with an average line run time of', str((time.time_ns() - self.ProgStartTime)/self.Lines), 'nanoseconds per line')
        print('Here is the total amount of repetitions for each line')
        for i, j in self.LineRunNo.items():
            print('\t', i, "::", j)
        print('\n')

    #keep track of how many times each line was executed
    def ResetDict(self):
        self.Vars = {}
        self.LineRunNo = {}
        self.CreLine = {}
        self.VarHistory = {}

    def UpdateLineNo(self, line):
        if str(line) in self.LineRunNo:
            self.LineRunNo[str(line)] += 1
            return self.LineRunNo[str(line)]
        else:
            self.LineRunNo[str(line)] = 1
            return self.LineRunNo[str(line)]

    def checkList(self, PList, List, name):
        ret = {}
        for i in List:
            try:
                if i == PList[List.index(i)]:
                    pass
                else:
                    ret["item " + str(List.index(i)) + " of " + name] = copy(i)
            except IndexError:
                ret["item " + str(List.index(i)) + " of " + name] = copy(i)
        return ret
                
        


#Test Functions
def Test1():
    a = [5, 6]
    b = 5
    a.append(4)
    b = 4

def Test2():
    a = 5
    for i in (10, 12):
        a = i

def Test3():
    a , b = 2, 3
    c = foo(a, b)

def foo(m, n):
    c = m*n
    return c
#run
print('Python Debugger - TheConverseEngineer')
opt = None
cmd = None
#while opt == None:
#    ipt = input('Please choose either [a]Run a custom function or [b]run a pre-made function:').lower()
 #   if ipt == 'a' or ipt == 'b': opt = ipt
  #  else: print('please input either "a" or "b"')
#    
#if (opt == 'a'):
    #pass #run a custom function

if (15 == 15): #run a example function
    print('Please select a test function to run from the list: {1: Test1, 2: Test2, 3: Test3}')
    print('Too learn more about a function, put a "h" in front of your choice')
    
    while cmd == None:
        ipt2 = input()
        
        if ipt2 in ['1', '2', '3', 'h1', 'h2', 'h3']:
            
            if ipt2 in ['h1', 'h2', 'h3']: #if it is a help
                
                if ipt2 == 'h1':
                    print('Test1 highlights: Contains 3 variables, two are declared on the same line, two are changed on the same line')

                if ipt2 == 'h2':
                    print('Test2 highlights: Contains 3 variables, two are declared on the same line, one is changed and one is declared  on the same line')

                if ipt2 == 'h3':
                    print('Test3 highlights: Contains 3 variables, two are declared on the same line, contains subfunction')

            else: #run a program
                cmd = str('Test'+ipt2)
        else:
            print('Please enter a valid option: [1, 2, 3, h1, h2, h3]')
                    
if cmd == 'Test1':
    TargetFunc = 'Test1'
    sys.settrace(Debug) 
    Test1()
    sys.settrace(None)
    
if cmd == 'Test2':
    TargetFunc = 'Test2'
    sys.settrace(Debug) 
    Test2()
    sys.settrace(None)

if cmd == 'Test3':
    TargetFunc = 'Test3'
    sys.settrace(Debug) 
    Test3()
    sys.settrace(None)
