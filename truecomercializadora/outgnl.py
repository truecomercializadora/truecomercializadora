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

def get_registro_gs(outgnl_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO GS (Bloco 2) de um outgnl dado
     na forma de uma string
    """
    if type(outgnl_str) != str:
        raise Exception("'get_registro_gs' can only receive a string."
                        "{} is not a valid input type".format(type(outgnl_str)))

    if 'BLOCO 2 *** NUMERO DE SEMANAS ***' not in outgnl_str:
        raise Exception("Input string does not seem to represent a outgnl.rv# "
                        "string. Check the input")

    begin = "BLOCO 2"
    end = "BLOCO 3"
    registro_gs = utils_files.select_document_part(outgnl_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_gs = '\r\n'.join(registro_gs.splitlines()[2:-2])

    return registro_gs

def get_registro_nl(outgnl_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO NL (Bloco 3) de um outgnl dado
     na forma de uma string
    """
    if type(outgnl_str) != str:
        raise Exception("'get_registro_nl' can only receive a string."
                        "{} is not a valid input type".format(type(outgnl_str)))

    if 'BLOCO 3 *** LAG DE ANTECIPACAO DE DESPACHO ***' not in outgnl_str:
        raise Exception("Input string does not seem to represent a outgnl.rv# "
                        "string. Check the input")

    begin = "BLOCO 3"
    end = "BLOCO 4"
    registro_nl = utils_files.select_document_part(outgnl_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_nl = '\r\n'.join(registro_nl.splitlines()[2:-2])

    return registro_nl

def get_registro_gl(outgnl_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO NL (Bloco 3) de um outgnl dado
     na forma de uma string
    """
    if type(outgnl_str) != str:
        raise Exception("'get_registro_gl' can only receive a string."
                        "{} is not a valid input type".format(type(outgnl_str)))

    if 'BLOCO 4 *** GERACOES DE TERMICAS GNL JA COMANDADAS ***' not in outgnl_str:
        raise Exception("Input string does not seem to represent a outgnl.rv# "
                        "string. Check the input")

    begin = utils_files.find_all_occurences_of_substring(outgnl_str, "BLOCO 4")[0]
    registro_gl = outgnl_str[begin:]
    
    # eliminando as linhas antes e depois dos dados     
    registro_gl = '\r\n'.join(registro_gl.splitlines()[2:])

    return registro_gl