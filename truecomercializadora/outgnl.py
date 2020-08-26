"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo outgnl
"""
import datetime
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
    registro_tg = '\n'.join(registro_tg.splitlines()[2:-2])

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
    registro_gs = '\n'.join(registro_gs.splitlines()[2:-2])

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
    registro_nl = '\n'.join(registro_nl.splitlines()[2:-2])

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
    registro_gl = '\n'.join(registro_gl.splitlines()[2:])

    return registro_gl

import pandas as pd

def get_df_from_registro_tg(registro_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro TG informado.
     A funcao devera receber o Registro TG ja no formato string
    """
    if type(registro_str) != str:
        raise Exception("'get_df_from_registro_tg' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_str)))

    if 'cod  ss      nome   ip   infl disp    cvu    infl disp    cvu    infl disp    cvu' not in registro_str:
        raise Exception("Input string does not seem to represent a Registro TG"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_str.splitlines()[4:]:
        L.append({
            "bloco": line [:3].strip(),
            "cod_usina": int(line[4:8].strip()),
            "nome_usina": line[14:25].strip(),
            "ip": int(line[25:27].strip()),
            "infl_1": float(line[27:34].strip()),
            "disp_1":float(line[34:40].strip()),
            "cvu_1": float(line[40:49].strip()),
            "infl_2": float(line[49:54].strip()),
            "disp_2":float(line[54:59].strip()),
            "cvu_2": float(line[60:69].strip()),
            "infl_3": float(line[69:74].strip()),
            "disp_3":float(line[74:80].strip()),
            "cvu_3": float(line[80:].strip()),
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)

def get_df_from_registro_gs(registro_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro GS informado.
     A funcao devera receber o Registro GS ja no formato string.
    """
    if type(registro_str) != str:
        raise Exception("'get_df_from_registro_gs' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_str)))

    if 'mes  semanas' not in registro_str:
        raise Exception("Input string does not seem to represent a Registro TG"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_str.splitlines()[4:]:
        L.append({
            "bloco": line [:3].strip(),
            "mes": int(line [3:7].strip()),
            "semanas": int(line [7:].strip())
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)


def get_df_from_registro_gl(registro_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro GL informado.
     A funcao devera receber o Registro GL ja no formato string
    """
    if type(registro_str) != str:
        raise Exception("'get_df_from_registro_gl' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_str)))

    if 'cod  ss  sem    geracao   dur  geracao   dur  geracao   dur  data inic' not in registro_str:
        raise Exception("Input string does not seem to represent a Registro TG"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_str.splitlines()[4:]:
        date_str = line[65:].strip()
        L.append({
            "bloco": line [:3].strip(),
            "cod": int(line[4:8].strip()),
            "ss": int(line[8:12].strip()),
            "sem": int(line[12:17].strip()),
            "ger_1": float(line[17:30].strip()) if line[17:30].strip() != '' else None,
            "dur_1": float(line[30:35].strip()) if line[30:35].strip() != '' else None,
            "ger_2": float(line[35:45].strip()) if line[35:45].strip() != '' else None,
            "dur_2": float(line[45:50].strip()) if line[45:50].strip() != '' else None,
            "ger_3": float(line[50:60].strip()) if line[50:60].strip() != '' else None,
            "dur_4": float(line[60:65].strip()) if line[60:65].strip() != '' else None,
            "data_ini": datetime.datetime(
                int(date_str[4:]),
                int(date_str[2:4]),
                int(date_str[:2]))
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)


def get_df_from_registro_nl(registro_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro NL informado.
     A funcao devera receber o Registro NL ja no formato string.
    """
    if type(registro_str) != str:
        raise Exception("'get_df_from_registro_nl' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_str)))

    if 'cod  ss  lag' not in registro_str:
        raise Exception("Input string does not seem to represent a Registro NL"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_str.splitlines()[3:]:
        L.append({
            "bloco": line [:3].strip(),
            "cod": int(line[3:8].strip()),
            "ss": int(line[8:12].strip()),
            "lag": int(line [12:16].strip())
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)


def get_nome_usina_from_registro_tg(registro_tg_str: str, id_usina: int) -> str:
    '''
    Retorna a string referente ao nome da usina.
    '''
    if type(registro_tg_str) != str:
        raise Exception("'get_nome_usina_from_registro_tg' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_tg_str)))

    if type(id_usina) != int:
        raise Exception("'get_nome_usina_from_registro_tg' can only receive an int. "
                        "{} is not a valid input type".format(type(id_usina)))

    if 'cod  ss      nome   ip   infl disp    cvu    infl disp    cvu    infl disp    cvu' not in registro_tg_str:
        raise Exception("Input string does not seem to represent a Registro TG"
                        "string. Check the input")

    registro_tg_df = get_df_from_registro_tg(registro_str=registro_tg_str)
    query_usina = registro_tg_df.query('cod_usina == {}'.format(id_usina))
    
    if not query_usina.empty:
        return query_usina.nome_usina.values[0]
    else:
        raise Exception('{id_usina} not found in Registro TG'.format(id_usina=id_usina))

 
def get_lag_usina_from_registro_nl(registro_nl_str: str, id_usina: int) -> str:
    '''
    Retorna a string referente ao nome da usina.
    '''
    if type(registro_nl_str) != str:
        raise Exception("'get_lag_usina_from_registro_nl' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_nl_str)))

    if type(id_usina) != int:
        raise Exception("'get_lag_usina_from_registro_nl' can only receive an int. "
                        "{} is not a valid input type".format(type(id_usina)))

    if 'cod  ss  lag' not in registro_nl_str:
        raise Exception("Input string does not seem to represent a Registro NL"
                        "string. Check the input")

    registro_nl_df = get_df_from_registro_nl(registro_str=registro_nl_str)
    query_usina = registro_nl_df.query('cod == {}'.format(id_usina))

    if not query_usina.empty:
        return query_usina.lag.values[0]
    else:
        raise Exception('{id_usina} not found in Registro NL'.format(id_usina=id_usina))