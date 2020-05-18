import datetime

from . import utils_datetime
from . import utils_gsheets

def get_mlts():
    """
    # ========================================================================================= #
    #  Retorna um dicionario de medias de longo termo para cada subsistema do SIN.              #
    # ========================================================================================= #
    """
    mlts_table = utils_gsheets.get_workheet_records("POSTOS", "MLT")
    return {
        subsistema['subsistema']: {str(i+1): item[1] for i,item in enumerate(list(subsistema.items())[1:])}
        for subsistema in mlts_table
    }

def get_semanas_operativas(ano,mes):
    """
    # ========================================================================================= #
    #  Retorna a lista de dicionarios representando as informacoes da semana operativa do mes   #
    #  desejado. A funcao baseia-se exclusivamente nos sabados do ano e nao diz respeito a data #
    #  de reunioes ou da disponibilizacao de arquivos oficiais.                                 # 
    # ========================================================================================= #
    """
    lista = []
    count = 0
    for d in utils_datetime.yield_all_saturdays(ano):
        if d.month == mes and d.day != 1:
            prim_sabado = d
            inicio = d - datetime.timedelta(7)
            fim = d - datetime.timedelta(1)
            lista.append({
                'inicio': inicio,
                'fim': fim,
                'semana': d.isocalendar()[1],
                'rev': count
            })
            count += 1
        
        if d.month == mes and ((d + datetime.timedelta(7)).day == 1):
            prim_sabado = (d + datetime.timedelta(7))
            inicio = prim_sabado - datetime.timedelta(7)
            fim = prim_sabado - datetime.timedelta(1)
            lista.append({
                'inicio': inicio,
                'fim': fim,
                'semana': d.isocalendar()[1],
                'rev': count
            })
            count += 1
    return lista

