"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo outgnl
"""
import pandas as pd

from . import utils_files


def get_registro_tg(outgnl_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO TG (Bloco 1 - Termicas a GNL)
     de um outgnl dado na forma de uma string.
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
    Retorna a substring correspondente ao REGISTRO GS (Bloco 2 - Numero de Usinas) 
     de um outgnl dado na forma de uma string.
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
    Retorna a substring correspondente ao REGISTRO NL (Bloco 3 - Lag de antecipacao
     de Despacho) de um outgnl dado na forma de uma string.
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
    Retorna a substring correspondente ao REGISTRO GL (Bloco 4 - Geracoes de Termicas
     GNL ja Comandadas) de um outgnl dado na forma de uma string.
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

def get_df_from_registro_tg(registro_tg_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro TG informado.
     A funcao devera receber o Registro TG ja no formato string
    """
    if type(registro_tg_str) != str:
        raise Exception("'get_df_from_registro_tg' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_tg_str)))

    if 'Usina           Est           Pat 1               Pat 2               Pat3' not in registro_tg_str:
        raise Exception("Input string does not seem to represent a Registro TG"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_tg_str.splitlines()[4:]:
        L.append({
            "bloco": line [:3].strip(),
            "cod_usina": int(line[4:8].strip()),
            "nome_usina": line[14:25].strip(),
            "ip": int(line[25:27].strip()),
            "inflex_1": float(line[30:34].strip()),
            "disp_1":float(line[34:40].strip()),
            "cvu_1": float(line[40:50].strip()),
            "inflex_2": float(line[50:54].strip()),
            "disp_2":float(line[54:60].strip()),
            "cvu_2": float(line[60:70].strip()),
            "inflex_3": float(line[70:74].strip()),
            "disp_3":float(line[74:80].strip()),
            "cvu_3": float(line[80:].strip()),
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)