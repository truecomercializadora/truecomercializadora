"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo dadger
"""
import datetime
import io
import pandas as pd

from . import utils_datetime
from . import utils_files
from . import decomp
from . import ons

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
    registro_dp_str = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados
    registro_dp = '\n'.join(registro_dp_str.splitlines()[2:-2])

    return registro_dp

def get_registro_ct(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO CT (Bloco 4) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_ct' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 4  ***  CADASTRO UTE  ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 4"
    end = "BLOCO 5"
    registro_ct = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_ct = '\n'.join(registro_ct.splitlines()[2:-2])

    return registro_ct

def write_registro_dp(
    ano_deck: int,
    mes_deck: int,
    cargas_mes_atual: list,
    cargas_mes_seguinte: list,
    patamares_table: dict) -> str:

    """
    Retorna o Registro DP a partir da tabela de cargas do mes atual e do mes se
    guinte, juntamente com a lista de patamares oficiais de carga.
    """

    if type(ano_deck) != int:
        raise Exception("'write_registro_dp' can only receive ano_deck as an integer."
                        "{} is not a valid input type".format(type(ano_deck)))
    if type(mes_deck) != int:
        raise Exception("'write_registro_dp' can only receive mes_deck as an integer."
                        "{} is not a valid input type".format(type(mes_deck)))
    if type(cargas_mes_atual) != list:
        raise Exception("'write_registro_dp' can only receive cargas_mes_atual as list."
                        "{} is not a valid input type".format(type(cargas_mes_atual)))
    if type(cargas_mes_seguinte) != list:
        raise Exception("'write_registro_dp' can only receive cargas_mes_seguinte as list."
                        "{} is not a valid input type".format(type(cargas_mes_seguinte)))
    if type(patamares_table) != dict:
        raise Exception("'write_registro_dp' can only receive patamares_table as dict."
                        "{} is not a valid input type".format(type(patamares_table)))

    # Obtendo os estagios do DECOMP
    estagios_decomp = decomp.get_estagios(ano=ano_deck,mes=mes_deck)

    master_io = io.BytesIO()
    master_io.write("&----------------------------------------------------------------------------------------------\n".encode("latin-1"))
    master_io.write("&                   PESADA              MEDIA               LEVE\n".encode('latin-1'))
    master_io.write("&   5     10  15   20        30        40        50        60        70\n".encode('latin-1'))
    master_io.write("&   ++    +   +    +--------++--------++--------++--------++--------++--------+\n".encode('latin-1'))
    master_io.write("&   IP    S  PAT     MWmed    Pat_1(h)   MWmed    Pat_2(h)   MWmed    Pat_3(h)\n".encode('latin-1'))
    master_io.write("&   ++    +   +    +--------++--------++--------++--------++--------++--------+\n".encode('latin-1'))
    master_io.write("&DP\n".encode('latin-1'))
    for i, semana in enumerate(estagios_decomp):
        horas_por_patamar = decomp.get_horas_por_patamar(semana, patamares_table)
        for j, subsistema in enumerate(cargas_mes_atual):
            indice = subsistema['indice']
            if i == (len(estagios_decomp)-1):
                patamar_alto = cargas_mes_seguinte[j]['cargas']['pesada']
                patamar_medio = cargas_mes_seguinte[j]['cargas']['media']
                patamar_baixo = cargas_mes_seguinte[j]['cargas']['leve']
            else:
                patamar_alto = subsistema['cargas']['pesada']
                patamar_medio = subsistema['cargas']['media']
                patamar_baixo = subsistema['cargas']['leve']
            master_io.write(
                "DP  {:>2d}   {:>2d}   3    {:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}{:>10.1f}\n".format(
                i+1,
                indice,
                patamar_alto,
                horas_por_patamar['pesada'],    
                patamar_medio,
                horas_por_patamar['media'],
                patamar_baixo,
                horas_por_patamar['leve'],
            ).encode('latin-1'))
            if (j+1) % 4 == 0:
                master_io.write("DP  {:>2d}   11   3              {:>10.1f}          {:>10.1f}          {:>10.1f}\n".format(
                    i+1,
                    horas_por_patamar['pesada'],
                    horas_por_patamar['media'],
                    horas_por_patamar['leve']
                ).encode('latin-1'))
                master_io.write("&\n".encode('latin-1'))

    # Retornando o buffer decoded e eliminando as linhas vazias
    return "\n".join(master_io.getvalue().decode('latin-1').strip().splitlines())

def get_df_from_registro_ct(registro_ct_str: str) -> pd.DataFrame:
    """
    Retorna o pd.DataFrame correspondente ao Registro CT informado.
     A funcao devera receber o Registro CT ja no formato string
    """
    if type(registro_ct_str) != str:
        raise Exception("'get_df_from_registro_ct' can only receive a string. "
                        "{} is not a valid input type".format(type(registro_ct_str)))

    if 'X  COD  SU   NOMEDAUSINES' not in registro_ct_str:
        raise Exception("Input string does not seem to represent a Registro CT"
                        "string. Check the input")

    # Interando pelas linhas do registro e estruturando elas como dicionarios     
    L = []
    for line in registro_ct_str.splitlines()[6:]:
        L.append({
            'X': line[:2],
            'COD': line[2:7].strip(),
            'SUBM': line[7:12].strip(),
            'NOME': line[12:25].strip(),
            'ESTAGIO': line[25:29].strip(),
            'INFL_P': line[29:34].strip(),
            'DISP_P': line[34:39].strip(),
            'CVU_P': line[39:49].strip(),
            'INFL_M': line[49:54].strip(),
            'DISP_M': line[54:59].strip(),
            'CVU_M': line[59:69].strip(),
            'INFL_L': line[69:74].strip(),
            'DISP_L': line[74:79].strip(),
            'CVU_L': line[79:].strip()
        })
    
    # Retornando a lista de dicionarios como um pd.DataFrame     
    return pd.DataFrame(L)

def write_registro_ct_from_df(
    registro_ct_df: pd.DataFrame) -> str:

    """
    Retorna o Registro DP a partir da tabela de cargas do mes atual e do mes se
    guinte, juntamente com a lista de patamares oficiais de carga.
    """
    if type(registro_ct_df) != pd.DataFrame:
        raise Exception("'write_registro_ct_from_df' can only receive values as a pd.DataFrame"
                        " {} is not a valid input type".format(type(registro_ct_df)))

    # Escrevendo o cabecalho padrao
    master_io = io.BytesIO()
    master_io.write("&----------------------------------------------------------------------------------------\n".encode("latin-1"))
    master_io.write("&___________________________|______________________PATAMAR DE CARGA_____________________|\n".encode("latin-1"))
    master_io.write("&_______USINA_____________| |_____PESADA________|_______MEDIA_______|_______LEVE________|\n".encode("latin-1"))
    master_io.write("&X  COD  SU   NOMEDAUSINES| |INFL|DISP|CVUCVUCVU|INFL|DISP|CVUCVUCVU|INFL|DISP|CVUCVUCVU|\n".encode("latin-1"))
    master_io.write("&|____|___|____________|__| |____|____|_________|____|____|_________|____|____|_________|\n".encode("latin-1"))
    master_io.write("&CT\n".encode("latin-1"))
    
    # Escrevendo as linhas do DataFrame
    line_format = "CT  {:>3}   {:>1d}   {:<10} {:>1d}   {:>5}{:>5}   {:>7}{:>5}{:>5}   {:>7}{:>5}{:>5}   {:>7}\n"
    for _, row in registro_ct_df.iterrows():
        master_io.write(
            line_format.format(
                row['COD'],
                row['SUBM'],
                row['NOME'],
                row['ESTAGIO'],
                row['INFL_P'],    
                row['DISP_P'],
                row['CVU_P'],
                row['INFL_M'],    
                row['DISP_M'],
                row['CVU_M'],
                row['INFL_L'],
                row['DISP_L'],
                row['CVU_L'],
            ).encode('latin-1')
        )

    return "\n".join(master_io.getvalue().decode('latin-1').strip().splitlines())

def get_registro_te(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO TE (Bloco 1) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_te' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 1  *** TITULO ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 1"
    end = "BLOCO 2"
    registro_te = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_te = '\n'.join(registro_te.splitlines()[3:-2])

    return registro_te

def write_registro_te(ano_inicio: int, mes_inicio: int, rev: int) -> str:
    """
    Retorna a substring correspondente ao REGISTRO TE (Bloco 1) de um dadger dado
     considerando os inputs:
     : mes_inicio deck
     : ano_inicio deck
     : rev do deck
    """
    if (type(ano_inicio) != int) or (type(mes_inicio) != int) or (type(rev) != int):
        raise Exception("'write_registro_te' can only receive integers.")
    
    date_ini = datetime.date(ano_inicio, mes_inicio, 1)
    date_fim = utils_datetime.add_one_month(date_ini)

    ref_inicio = '{}/{}'.format(
        utils_datetime.get_br_month(date_ini.month).upper(),
        date_ini.year - 2000)
    ref_fim = '{}/{}'.format(
        utils_datetime.get_br_month(date_fim.month).upper(),
        date_fim.year - 2000)

    return '&TE\n&&   CENARIOS GERADOS COM HISTORICO DE 1931-2018\nTE  PMO - {inicio} - {fim} - REV {rev} - FCF COM CVAR - 12 REE - VALOR ESPERADO      '.format(inicio=ref_inicio, fim=ref_fim, rev=rev)

def get_registro_dt(dadger_str: str) -> str:
    """
    Retorna a substring correspondente ao REGISTRO DT (Bloco 17) de um dadger dado
     na forma de uma string
    """
    if type(dadger_str) != str:
        raise Exception("'get_registro_dt' can only receive a string."
                        "{} is not a valid input type".format(type(dadger_str)))

    if 'BLOCO 17 ***' not in dadger_str:
        raise Exception("Input string does not seem to represent a dadger.rv# "
                        "string. Check the input")

    begin = "BLOCO 17"
    end = "BLOCO 18"
    registro_dt = utils_files.select_document_part(dadger_str, begin, end)
    
    # eliminando as linhas antes e depois dos dados     
    registro_dt = '\n'.join(registro_dt.splitlines()[3:-2])

    return registro_dt

def write_registro_dt(ano_deck: int, mes_deck: int, rev: int) -> str:
    """
    Retorna a substring correspondente ao REGISTRO DT (Bloco 17) de um dadger dado
     considerando os inputs:
     : mes_deck mes do deck desejado
     : ano_deck ano do deck desejado 
     : rev do deck
    """
    if (type(ano_deck) != int) or (type(mes_deck) != int) or (type(rev) != int):
        raise Exception("'write_registro_dt' can only receive integers.")
    
    estagios = ons.get_semanas_operativas(ano=ano_deck, mes=mes_deck)

    ano = estagios[rev]['inicio'].year
    mes = estagios[rev]['inicio'].month
    dia = estagios[rev]['inicio'].day

    str_format = '&DT\nDT  {:02d}   {:02d}   {}'

    return str_format.format(dia, mes, ano)