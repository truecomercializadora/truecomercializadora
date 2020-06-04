"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo sistema
"""
import io
import pandas as pd

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

def _get_mercado_energia_formated_line(
    df_submercado: pd.DataFrame,
    format_type: str,
    begin_idx: int,
    submercado_number: int=None) -> str:

    """
    Retorna uma string correspondente a linha desejada do bloco Mercado de Energia
     Total, baseado no dataframe do submercado, o tipo de formato da linha o indice
     inicial da linha do bloco e, se necessario, qual o submercado
    """

    if type(df_submercado) != pd.DataFrame:
        raise Exception("'_get_mercado_energia_formated_line' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_submercado)))
    if format_type not in ['A', 'B', 'C']:
        raise Exception("'_get_mercado_energia_formated_line' can only receive 'A', 'B' or 'C' as format_type."
                        "{} is not a valid input type".format(type(format_type)))
    if type(begin_idx) != int:
        raise Exception("'_get_mercado_energia_formated_line' can only receive line index as integer."
                        "{} is not a valid input type".format(type(begin_idx)))

    if format_type == 'A':
        line_format = "   {}\n{}    {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \r\n"
        return line_format.format(submercado_number,
            df_submercado.iloc[begin_idx]['data'].year,
            df_submercado.iloc[begin_idx]['valor'],
            df_submercado.iloc[begin_idx+1]['valor'],
            df_submercado.iloc[begin_idx+2]['valor'],
            df_submercado.iloc[begin_idx+3]['valor'],
            df_submercado.iloc[begin_idx+4]['valor'],
            df_submercado.iloc[begin_idx+5]['valor'],
            df_submercado.iloc[begin_idx+6]['valor'],
            df_submercado.iloc[begin_idx+7]['valor'],
            df_submercado.iloc[begin_idx+8]['valor'],
            df_submercado.iloc[begin_idx+9]['valor'],
            df_submercado.iloc[begin_idx+10]['valor'],
            df_submercado.iloc[begin_idx+11]['valor']        
        )
    if format_type == 'B':
        line_format = "{}    {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \r\n"
        return line_format.format(
            df_submercado.iloc[begin_idx]['data'].year,
            df_submercado.iloc[begin_idx]['valor'],
            df_submercado.iloc[begin_idx+1]['valor'],
            df_submercado.iloc[begin_idx+2]['valor'],
            df_submercado.iloc[begin_idx+3]['valor'],
            df_submercado.iloc[begin_idx+4]['valor'],
            df_submercado.iloc[begin_idx+5]['valor'],
            df_submercado.iloc[begin_idx+6]['valor'],
            df_submercado.iloc[begin_idx+7]['valor'],
            df_submercado.iloc[begin_idx+8]['valor'],
            df_submercado.iloc[begin_idx+9]['valor'],
            df_submercado.iloc[begin_idx+10]['valor'],
            df_submercado.iloc[begin_idx+11]['valor']        
        )    
    elif format_type == 'C':
        line_format = "POS     {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}.  {:>5.0f}. \r\n"
        return line_format.format(
        df_submercado.iloc[begin_idx]['valor'],
        df_submercado.iloc[begin_idx+1]['valor'],
        df_submercado.iloc[begin_idx+2]['valor'],
        df_submercado.iloc[begin_idx+3]['valor'],
        df_submercado.iloc[begin_idx+4]['valor'],
        df_submercado.iloc[begin_idx+5]['valor'],
        df_submercado.iloc[begin_idx+6]['valor'],
        df_submercado.iloc[begin_idx+7]['valor'],
        df_submercado.iloc[begin_idx+8]['valor'],
        df_submercado.iloc[begin_idx+9]['valor'],
        df_submercado.iloc[begin_idx+10]['valor'],
        df_submercado.iloc[begin_idx+11]['valor']        
    )

def _write_bloco_submercado(df_submercado: pd.DataFrame, submercado_number: int) -> bytes:

    """
    Retorna uma string correspondente a sessao do submercado dentro do bloco de Mercado
     de Energia Total.
    """

    if type(df_submercado) != pd.DataFrame:
        raise Exception("'_write_bloco_submercado' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_submercado)))
    if submercado_number not in [1,2,3,4]:
        raise Exception("'_write_bloco_submercado' can only integers between [1,4] for submercado_number."
                        "{} is not a valid input type".format(type(submercado_number)))

    master_io = io.BytesIO()
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='A',begin_idx=0, submercado_number=submercado_number).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=12).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=24).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=36).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='B',begin_idx=48).encode('latin-1'))
    master_io.write(_get_mercado_energia_formated_line(df_submercado=df_submercado,format_type='C',begin_idx=48).encode('latin-1'))
    return master_io.getvalue().decode()


def write_mercado_energia(
        df_sudeste: pd.DataFrame,
        df_sul: pd.DataFrame,
        df_nordeste: pd.DataFrame,
        df_norte: pd.DataFrame) -> str:
    '''
    Escreve o bloco Mercado de Energia Total de um arquivo sistema.dat a partir
    dos dataframes de carga dos 4 submercados.
    '''

    if type(df_sudeste) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_sudeste)))
    if type(df_sul) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_sul)))
    if type(df_nordeste) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_nordeste)))
    if type(df_norte) != pd.DataFrame:
        raise Exception("'write_mercado_energia' can only receive pandas.DataFrame."
                        "{} is not a valid input type".format(type(df_norte)))

    master_io = io.BytesIO()
    master_io.write(" MERCADO DE ENERGIA TOTAL\r\n".encode("latin-1"))
    master_io.write(" XXX\r\n".encode("latin-1"))
    master_io.write("       XXXJAN. XXXFEV. XXXMAR. XXXABR. XXXMAI. XXXJUN. XXXJUL. XXXAGO. XXXSET. XXXOUT. XXXNOV. XXXDEZ.\r\n".encode('latin-1'))

    bloco_sudeste = _write_bloco_submercado(df_sudeste, 1)
    bloco_sul = _write_bloco_submercado(df_sul, 2)
    bloco_nordeste = _write_bloco_submercado(df_nordeste, 3)
    bloco_norte = _write_bloco_submercado(df_norte, 4)

    output_str = master_io.getvalue().decode() + bloco_sudeste + bloco_sul + bloco_nordeste + bloco_norte
    return output_str.strip()