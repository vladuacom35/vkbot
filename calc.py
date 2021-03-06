rep1 = {"ноль": "0", "нуль": '0', "один": "1", "два": "2", "дважды": "2*", "три": "3", "трижды": "3*", "четыре": "4", "четырежды":"4*", "пять": "5", "пятью": "5*", 
        "шесть": "6", "шестью": "6*", "семь": "7", "семью": "7*", "восемь": "8", "восемью": "8*", "девять": "9", "девятью": "9*"}
rep2 = {"десять": "10", "одиннадцать": "11", "одинадцать": "11", "двенацать": "12", "тринадцать": "13", "четырнадцать": "14", "пятнадцать": "15", 
       "шестнадцать": "16", "семнадцать": "17", "восемнадцать": "18", "девятнадцать": "19"}
rep3 = {"двадцать": "20", "тридцать": "30", "сорок": "40", "пятьдесят": "50", 
       "шестьдесят": "60", "семьдесят": "70", "восемьдесят": "80", "восемдесят": "80", "девяносто": "90", "девяноста": "90"}
#rep4 = {i + ' ' + j: str(int(rep3[i]) + int(rep1[j])) for i in rep3 for j in rep1}
op = {"плюс":"+", "минус":"-", "прибавить": "+", "отнять": "-", "умножить": "", "на": "*"}
allowed = set('йцукенгшщзхъфывапролджэячсмитьбю.1234567890()+-* ')

def isnum(s):
    return s and (s.isdigit() or s[0] == '-' and len(s) > 1 and s[1:].isdigit())


def evalExpression(s):
    s = s.replace('(', ' ( ').replace(')', ' ) ').replace('+', ' + ').replace('-', ' - ').replace('*', ' * ')
    s = ''.join(i if i in allowed else ' ' for i in s.lower()).split()
    ans = []
    for i in s:
        if set(i) <= set('0123456789+-*() '):
            ans.append(i)
        elif i in op:
            ans.append(op[i])
        elif i in rep1:
            ans.append(rep1[i])
        elif i in rep2:
            ans.append(rep2[i])
        elif i in rep3:
            ans.append(rep3[i])
    for i in range(1, len(ans)):
        if ans[i].isdigit() and ans[i-1].isdigit():
            a = int(ans[i])
            b = int(ans[i - 1])
            if a > 0 and a < 10 and b > 10 and b < 100 and b % 10 == 0:
                ans[i] = str(int(ans[i]) + int(ans[i-1]))
                ans[i-1] = ''
            else:
                return None
    s = ''.join(ans).strip()
    if not s:
        return None
    if s[0] == '+' or isnum(s) or isnum(s.replace('(', '').replace(')', '').strip('+')):
        return None
    if '**' in s or '--' in s or '++' in s:
        return None
    if set(s) <= set('0123456789()-') and s[0] == '8':
        return None
    try:
        res = str(eval(s, {'__builtins__':{}}))
    except Exception:
        s = s.replace('(', '').replace(')', '')
        if not s or s[0] == '+' or isnum(s) or isnum(s.replace('(', '').replace(')', '').strip('+')):
            return None
        if '**' in s or '--' in s or '++' in s:
            return None
        try:
            res = str(eval(s, {'__builtins__':{}}))
        except Exception:
            return None
    if isnum(res):
        return res
    else:
        return None

if __name__=="__main__":
    while 1:
        s = input()
        print(evalExpression(s))