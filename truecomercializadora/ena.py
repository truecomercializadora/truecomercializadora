import pandas as pd
import io
from . import decomp,utils_s3,utils_datetime

def bacias_index(): 
    return [
        'GRANDE',
        'PARANAÍBA',
        'ALTO TIETÊ',
        'TIETÊ',
        'PARANAPANEMA (SE)',
        'ALTO PARANÁ',
        'BAIXO PARANÁ',
        'SÃO FRANCISCO (SE)',
        'TOCANTINS (SE)',
        'AMAZONAS (SE)',
        'ITABAPOANA',
        'MUCURI',
        'PARAÍBA DO SUL*',
        'DOCE',
        'PARAGUAI',
        'JEQUITINHONHA (SE)',
        'ITAIPU',
        'STA. MARIA DA VITÓRIA',
        'PARANAPANEMA (S)',
        'IGUAÇU',
        'URUGUAI',
        'JACUÍ',
        'ITAJAÍ-AÇU',
        'CAPIVARI',
        'SÃO FRANCISCO (NE)',
        'JEQUITINHONHA (NE)',
        'PARNAÍBA',
        'PARAGUAÇU',
        'ARAGUARI',
        'AMAZONAS (N)',
        'XINGU',
        'TOCANTINS (N)'
    ]

def bacias_index_correto(): 
    '''
    Funcao para deixar na ordem da plataforma
    '''
    return [
        'GRANDE',
        'PARANAÍBA',
        'ALTO PARANÁ',
        'TIETÊ',
        'BAIXO PARANÁ',
        'PARANAPANEMA (SE)',
        'ALTO TIETÊ',
        'PARAÍBA DO SUL*',
        'DOCE',
        'AMAZONAS (SE)',
        'SÃO FRANCISCO (SE)',
        'TOCANTINS (SE)',
        'ITABAPOANA',
        'PARAGUAI',
        'JEQUITINHONHA (SE)',
        'MUCURI',
        'ITAIPU',
        'STA. MARIA DA VITÓRIA',
        'PARANAPANEMA (S)',
        'IGUAÇU',
        'URUGUAI',
        'JACUÍ',
        'ITAJAÍ-AÇU',
        'CAPIVARI',
        'SÃO FRANCISCO (NE)',
        'JEQUITINHONHA (NE)',
        'PARNAÍBA',
        'PARAGUAÇU',
        'ARAGUARI',
        'AMAZONAS (N)',
        'TOCANTINS (N)',
        'XINGU'
    ]
def submercado_index():
    return [
        'SE',
        'S',
        'NE',
        'N'
    ]


def calc_media_mes(df: pd.DataFrame, ano: int, mes: int) -> list:
    '''
    Calculado a media mes para o dataframe passado
    '''
    estagios_decomp = decomp.get_estagios(ano, mes)
    dias_por_estagio = decomp.get_dias_do_mes_por_estagio(estagios_decomp)
    L = []
    for i, row in enumerate(df.iterrows()):
        soma = 0
        for j, coluna in enumerate(row[1]):
            if i == 16: soma = '' #condicao para itaipu
            else: 
                if len(dias_por_estagio)<j+1: continue
                soma += (coluna*dias_por_estagio[j])/sum(dias_por_estagio)
                soma = round(soma, 1)
        L.append(soma)
    print(L)
    return L

def calc_porcentagem_mlt(df: pd.DataFrame, mes: int,BUCKET_DATALAKE:str) -> list:
    '''
    Calcula a porcentagem da MLT para um df que contenha o valor de media mes
    '''
    f = utils_s3.get_obj_from_s3(BUCKET_DATALAKE, 'consume/ena/info/POSTOS - MLT_BACIA.csv')
    mlt_bacia = pd.read_csv(io.BytesIO(f)).to_dict('records')

    mlt_bacia = [mlt[utils_datetime.get_br_abreviated_month(mes)] for mlt in mlt_bacia]

    f = utils_s3.get_obj_from_s3(BUCKET_DATALAKE, 'consume/ena/info/POSTOS - MLT.csv')
    mlt_submercado = pd.read_csv(io.BytesIO(f)).to_dict('records')
        
    mlt_submercado = [mlt[utils_datetime.get_br_abreviated_month(mes)] for mlt in mlt_submercado]
    L = []

    for i, row in enumerate(df.iterrows()):
        soma = 0
        media = row[1][6]
        if len(df) > 4: soma = '' if i == 16 else round(media/float(mlt_bacia[i])*100, 1) #ternaria para itaipu
        else: soma = round(media/float(mlt_submercado[i])*100, 1)
        L.append(soma)
    return L

def build_submercado_table(df_submercado: pd.DataFrame, postos_table: list, vazoes_obj: dict, ano: int, mes: int,bucket:str):
    submercado = [posto['submercado'] for posto in postos_table if posto['idPosto'] in vazoes_obj.keys()]
    df_submercado.insert(0, 'Submercado', submercado)
    df_submercado = df_submercado.groupby(['Submercado']).sum().round()
    df_submercado = df_submercado.reindex(submercado_index())
    print('Calculando medias submercado')
    df_submercado['Media Mes'] = calc_media_mes(df_submercado, ano, mes)
    df_submercado['% MLT'] = calc_porcentagem_mlt(df_submercado, mes,bucket)
    return df_submercado

def build_bacia_table(df_bacia: pd.DataFrame, postos_table: list, vazoes_obj: dict, ano: int, mes: int,tipo_index:bool,bucket:str) -> pd.DataFrame:
    bacias = [posto['bacia'] for posto in postos_table if posto['idPosto'] in vazoes_obj.keys()]
    df_bacia.insert(0, 'Bacia', bacias)
    print('Adicionando Itaipu para tabela de bacias')
    itaipu = ['ITAIPU']
    for i in range(6):
        itaipu.append(vazoes_obj[266][i]-vazoes_obj[246][i]-vazoes_obj[63][i])
    df_bacia.loc[-0] = itaipu
    df_bacia = df_bacia.groupby(['Bacia']).sum().round(decimals=1)
    df_bacia = df_bacia.reindex(bacias_index())
    print('Calculando medias bacias')
    df_bacia['Media Mes'] = calc_media_mes(df_bacia, ano, mes)
    df_bacia['% MLT'] = calc_porcentagem_mlt(df_bacia, mes,bucket)
    if tipo_index:
        df_bacia = df_bacia.reindex(bacias_index_correto())
    return df_bacia

