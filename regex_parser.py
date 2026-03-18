from typing import List, Tuple

Token = Tuple[str, str]
def tokenize_regex(regex:str)->List[Token]:
    tokens=[]
    i=0 
    while i<len(regex):
        c=regex[i]

        #bracket
        if c == '[':
            j = i + 1
            while j < len(regex) and regex[j] != ']':
                j += 1
            bracket_token = regex[i:j+1]
            tokens.append([bracket_token, 'variable'])
            i = j + 1
            continue

        #range [a-z]
        elif c == '-' and len(tokens)!=0:
            start = regex[i - 1]
            end = regex[i + 1]
            tokens[-1] = (f"{start}-{end}", 'variable')
            i += 2
            continue

        #operators
        elif c in '()[]*+?_|':
            tokens.append([c,'operation'])

        #variable
        else:
            tokens.append([c,'variable'])

        i+=1
    return tokens

def expand_ranges(tokens:List[Token])->List[Token]:
    result=[]
    inside_range=False
    for value,type in tokens:
        #starting range
        if value == "[":
            inside_range = True
            continue
        
        #ending range
        if value == "]":
            inside_range = False
            continue
        
        #replace range with ORed variables like a-c -> a|b|c
        if inside_range and result:
            _, prev_type = result[-1]
            if prev_type == "variable":
                result.append(("|", "op"))

        result.append((value, type))

    return result


def insert_concat_operator(tokens:List[Token])->List[Token]:
    result = []

    for i in range(len(tokens) - 1):

        result.append(tokens[i])

        curr_val, curr_type = tokens[i]
        next_val, next_type = tokens[i + 1]

        left = curr_type == "variable" or curr_val in ")*+?"
        right = next_type == "variable" or next_val in "("

        if left and right:
            result.append(("_", "op"))

    result.append(tokens[-1])

    return result
    
def to_postfix(tokens:List[Token]) -> List[str]:

    precedence = {
        "*": 3,
        "+": 3,
        "?": 3,
        "_": 2,
        "|": 1
    }

    output = []
    stack = []

    for value, type in tokens:

        if type == "variable":
            output.append(value)

        elif value == "(":
            stack.append(value)

        elif value == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()

        #operator
        else:  
            while (
                stack
                and stack[-1] != "("
                and precedence.get(stack[-1], 0) >= precedence[value]
            ):
                output.append(stack.pop())

            stack.append(value)

    while stack:
        output.append(stack.pop())

    return output


def parse_regex(regex:str):
    tokens = tokenize_regex(regex)
    tokens = expand_ranges(tokens)
    tokens = insert_concat_operator(tokens)
    postfix = to_postfix(tokens)
    return postfix
