"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo sistema
"""

from . import utils_files

def get_mercado_energia_total(sistema_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO DP (Bloco 6) de um dadger dado
     na forma de uma string
    """
    if type(sistema_str) != str:
        raise Exception("'get_mercado_energia_total' can only receive a string."
                        "{} is not a valid input type".format(type(sistema_str)))

    if 'MERCADO DE ENERGIA TOTAL' not in sistema_str:
        raise Exception("Input string does not seem to represent a sistema.dat "
                        "string. Check the input")

    begin = ' MERCADO DE ENERGIA TOTAL'
    end = ' GERACAO DE USINAS NAO SIMULADAS'
    mercado_energia_total = utils_files.select_document_part(sistema_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    mercado_energia_total = '\r\n'.join(mercado_energia_total.splitlines()[:-1])

    return mercado_energia_total