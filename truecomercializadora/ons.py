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
    j=0
    semana_operativa = None

    #Bloco do first saturday é necessario para pegar o caso de quando o primeiro sabado do ano esta no ano anterior
    first_saturday = [d-datetime.timedelta(7) for i, d in enumerate(utils_datetime.yield_all_saturdays(ano)) if i == 0 and d.day > 1]
    if first_saturday == []:
        lista_sabados = list(utils_datetime.yield_all_saturdays(ano))
    else:
        lista_sabados = list(utils_datetime.yield_all_saturdays(ano))
        lista_sabados.insert(0, first_saturday[0])

    #Bloco para construir corretamente a primeira semana operativa do ano
    for i, d in enumerate(lista_sabados):
        if d.month == 1:
            while (d - datetime.timedelta(j)).year == ano and j <=6 and (d-datetime.timedelta(7)).year != ano:
                j=j+1
                semana_operativa = 1
        if i > 0: semana_operativa = None
        
        if semana_operativa == None:
            semana_operativa = i+1

        #Verificar se todos os dias de sabado até sexta estao dentro do mesmo mês, caso contrário a semana já pertence ao proximo mês
        d_1 = d+datetime.timedelta(1)
        d_2 = d+datetime.timedelta(2)
        d_3 = d+datetime.timedelta(3)
        d_4 = d+datetime.timedelta(4)
        d_5 = d+datetime.timedelta(5)
        d_6 = d+datetime.timedelta(6)

        if (d.month == mes and d.year == ano) or \
             (d_1.month == mes and d_1.year == ano) or \
                 (d_2.month == mes and d_2.year == ano) or \
                     (d_3.month == mes and d_3.year == ano) or \
                         (d_4.month == mes and d_4.year == ano) or \
                             (d_5.month == mes and d_5.year == ano) or \
                                 (d_6.month == mes and d_6.year == ano):
            inicio = d
            fim = d+datetime.timedelta(6)
            if fim.month != mes: continue
            lista.append({
                'inicio': inicio,
                'fim': fim,
                'semana': semana_operativa,
                'rev': count
            })
            count = count+1
            semana_operativa = None
    return lista

