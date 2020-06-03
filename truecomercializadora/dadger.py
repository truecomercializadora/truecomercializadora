"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo dadger
"""

from . import utils_files

def get_registro_dp(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO DP (Bloco 6) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_dp' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 6 *** CARGA DOS SUBSISTEMAS ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 6"
    end = "BLOCO 7"
    registro_dp = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_dp = '\r\n'.join(registro_dp.splitlines()[2:-2])

    return registro_dp