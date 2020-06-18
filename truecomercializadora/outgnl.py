"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo outgnl
"""

from . import utils_files


def get_registro_tg(outgnl_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO TG (Bloco 1) de um outgnl dado
     na forma de uma string
    """
    if type(outgnl_str) != str:
        raise Exception("'get_registro_tg' can only receive a string."
                        "{} is not a valid input type".format(type(outgnl_str)))

    if 'BLOCO 1 *** TERMICAS A GNL ***' not in outgnl_str:
        raise Exception("Input string does not seem to represent a outgnl.rv# "
                        "string. Check the input")

    begin = "BLOCO 1"
    end = "BLOCO 2"
    registro_tg = utils_files.select_document_part(outgnl_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_tg = '\r\n'.join(registro_tg.splitlines()[2:-2])

    return registro_tg