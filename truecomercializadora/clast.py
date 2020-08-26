"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo clast.dat
"""

def get_clast_conjuntural(clast_str: str) -> str:
    '''
    Retorna a string correspondente ao bloco conjuntural da 
     classe de termicas.
    '''
    
    if type(clast_str) != str:
        raise Exception("'get_clast_conjuntural' can only receive a string")
        
    if 'NUM  NOME CLASSE  TIPO COMB.  CUSTO   CUSTO   CUSTO   CUSTO   CUSTO' not in clast_str:
        raise Exception("input does not seem to be a clast.dat file. Check its content.")
    
    str_begin = ' 9999'
    idx_begin = clast_str.find(str_begin)

    return '\n'.join(clast_str[idx_begin:].splitlines()[1:])