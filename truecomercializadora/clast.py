import pandas as pd
import json
import numpy as np
import datetime
import io
from . import utils_datetime, utils_http, utils_s3
"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo clast.dat
"""

BUCKET_TRUE = 'datawarehouse-true'

def get_clast_conjuntural(clast_str: str) -> str:
    '''
    Retorna a string correspondente ao bloco conjuntural da 
     classe de termicas.
    '''
    
    if type(clast_str) != str:
        raise Exception("'get_clast_conjuntural' can only receive a string")
        
    if 'NUM  NOME CLASSE  TIPO COMB.  CUSTO   CUSTO   CUSTO   CUSTO   CUSTO' not in clast_str:
        raise Exception("input does not seem to be a clast.dat file. Check its content.")
    
    str_begin = ' 9999'
    idx_begin = clast_str.find(str_begin)

    return '\n'.join(clast_str[idx_begin:].splitlines()[1:])


def transcribe_clast(clast_str):
    '''
    Transcreve ambos os blocos do arquivo CLAST.dat para o formato de uma lista de dicionarios
    '''
    blocos = clast_str.split(' 9999')
    custo_operacao = [{
    'numUsina': line[:5].strip(),
    'nomeUsina': line[6:18].strip(),
    'tipo': line[19:29].strip(),
    'custo1': int(round(float(line[30:37].strip()))),
    'custo2': int(round(float(line[38:45].strip()))),
    'custo3': int(round(float(line[46:53].strip()))),
    'custo4': int(round(float(line[54:61].strip()))),
    'custo5': int(round(float(line[62:69].strip())))
  } for line in blocos[0].splitlines()[2:]]
    alteracao_custo = [{
    'numUsina': line[:5].strip(),
    'custo':  int(round(float(line[9:15].strip()))),
    'mesInicioModificacao': line[17:19],
    'anoInicioModificacao': line[20:24],
    'mesFimModificacao': line[26:28],
    'anoFimModificacao': line[29:33],
    'nomeUsina': line[35:46]
  } for line in blocos[1].splitlines()[3:]]
    return {'custoOperacao': custo_operacao, 'alteracaoCusto': alteracao_custo}


def _get_custoOperacao_diff(blocoA, blocoB):
    '''
    Calcula a diferença entre os blocos estruturais de entrada tratando valores NaN, retorna um json loads do dataframe de diferenças
    '''
    dfA = pd.DataFrame(blocoA, columns = ['numUsina','tipo', 'custo1', 'custo2', 'custo3','custo4', 'custo5']).set_index(['numUsina', 'tipo']).replace(r'^\s*$', np.nan, regex=True).astype(float)
    dfB = pd.DataFrame(blocoB, columns = ['numUsina','tipo', 'custo1', 'custo2', 'custo3','custo4', 'custo5']).set_index(['numUsina', 'tipo']).replace(r'^\s*$', np.nan, regex=True).astype(float)
    dfDiff = dfA.subtract(dfB)
    dfDiff = dfDiff.fillna(0).reset_index()

    dfDiff.numUsina = pd.to_numeric(dfDiff.numUsina, errors='coerce')



    return json.loads(dfDiff.reset_index().to_json(orient='records'))

def _get_alteracaoCusto_diff(blocoA, blocoB):
    '''
    Calcula a diferença entre os blocos conjunturais de entrada tratando valores NaN, retorna um json loads do dataframe de diferenças
    '''
    dfA = pd.DataFrame(blocoA, columns = ['numUsina', 'mesInicioModificacao', 'anoInicioModificacao','mesFimModificacao', 'anoFimModificacao','custo']).set_index(['numUsina', 'mesInicioModificacao', 'anoInicioModificacao','mesFimModificacao', 'anoFimModificacao'])
    dfB = pd.DataFrame(blocoB, columns = ['numUsina', 'mesInicioModificacao', 'anoInicioModificacao','mesFimModificacao', 'anoFimModificacao','custo']).set_index(['numUsina', 'mesInicioModificacao', 'anoInicioModificacao','mesFimModificacao', 'anoFimModificacao'])

    dfDiff = dfA - dfB
    dfDiff = dfDiff.fillna(0).reset_index()

    dfDiff.numUsina = pd.to_numeric(dfDiff.numUsina, errors='coerce')
    dfDiff.mesInicioModificacao = pd.to_numeric(dfDiff.mesInicioModificacao, errors='coerce')
    dfDiff.anoInicioModificacao = pd.to_numeric(dfDiff.anoInicioModificacao, errors='coerce')
    dfDiff.mesFimModificacao = pd.to_numeric(dfDiff.mesFimModificacao, errors='coerce')
    dfDiff.anoFimModificacao = pd.to_numeric(dfDiff.anoFimModificacao, errors='coerce')

    dfDiff = dfDiff.sort_values(['numUsina', 'anoInicioModificacao', 'mesInicioModificacao']).set_index('numUsina')
    return json.loads(dfDiff.reset_index().to_json(orient='records'))

    
def _expand_linhas_alteracaoCusto(blocoAlteracaoCusto):
    '''
    Retorna a lista expandida do arquivo conjuntural, ou seja,
    garante que todos os meses do horizonte estarão presentes
    '''
    lista = []
    for alteracao in blocoAlteracaoCusto:
        mesInicio = int(alteracao['mesInicioModificacao'])
        anoInicio = int(alteracao['anoInicioModificacao'])
        if alteracao['mesFimModificacao'].isdigit():
            mesFim = int(alteracao['mesFimModificacao'])
            anoFim = int(alteracao['anoFimModificacao'])
        else:
            mesFim = 12
            anoFim = anoInicio

        dataInicio = datetime.datetime(anoInicio, mesInicio,1)
        dataFim = datetime.datetime(anoFim, mesFim,1)
        
        proxMes = mesInicio
        proxAno = anoInicio
        diferenca_horizonte = utils_datetime.diff_month(dataFim, dataInicio)
        
        if diferenca_horizonte == 0:
            lista.append({'numUsina': alteracao['numUsina'],
            'nomeUsina': alteracao['nomeUsina'],
            'custo': alteracao['custo'],
            'mesInicioModificacao': str(proxMes),
            'anoInicioModificacao': str(proxAno),
            'mesFimModificacao':  str(proxMes),
            'anoFimModificacao': str(proxAno)
            })
        else:
            for i in range(diferenca_horizonte + 1):
                if proxMes % 12 == 0:
                    lista.append({'numUsina': alteracao['numUsina'],
                        'nomeUsina': alteracao['nomeUsina'],
                        'custo': alteracao['custo'],
                        'mesInicioModificacao': str(proxMes),
                        'anoInicioModificacao': str(proxAno),
                        'mesFimModificacao':  str(proxMes),
                        'anoFimModificacao': str(proxAno)
                    })
                    proxMes = 1
                    proxAno += 1
                else:
                    lista.append({'numUsina': alteracao['numUsina'],
                        'nomeUsina': alteracao['nomeUsina'],
                        'custo': alteracao['custo'],
                        'mesInicioModificacao': str(proxMes),
                        'anoInicioModificacao': str(proxAno),
                        'mesFimModificacao':  str(proxMes),
                        'anoFimModificacao': str(proxAno)
                    })
                    proxMes += 1
        return lista


def get_diff_clast(dictClastDeckA, dictClastDeckB):
    '''
    Calcula e retorna como dicionario as diferenças entre os blocos A e B
    custoOperacao == Estrutural, alteracaoCusto == Conjuntural
    '''
    blocoCustoOperacaoA = dictClastDeckA['custoOperacao']
    blocoCustoOperacaoB = dictClastDeckB['custoOperacao']
    blocoAlteracaoCustosA = _expand_linhas_alteracaoCusto(dictClastDeckA['alteracaoCusto'])
    blocoAlteracaoCustosB = _expand_linhas_alteracaoCusto(dictClastDeckB['alteracaoCusto'])

    return {
    'custoOperacao': _get_custoOperacao_diff(blocoCustoOperacaoA, blocoCustoOperacaoB),
    'alteracaoCusto': _get_alteracaoCusto_diff(blocoAlteracaoCustosA, blocoAlteracaoCustosB)
    }
def retornaNome(dfA, dfC):
    '''
    Retorna o dataframe dfC adicionando o nome de cada usina presente conforme os nomes de presentes em dfA
    '''
    coluna = []
    dfA = dfA.reset_index()
    
    for i in dfC.reset_index()['numUsina']:
      cont = 0
      for num in dfA.reset_index()['numUsina']:
        if int(i) == int(num):
          coluna.append(dfA['nomeUsina'][cont])
          break
        cont = cont + 1
    
    dfC['nomeUsina'] = coluna
    return dfC


def comparaClast(clast_strA, clast_strB):
    '''
    Compara ambos os arquivos clast já formatados para string
    Retorna dataframes formatadas para o conjuntural e estrutural de A, B e a diferença entre eles
    '''

    blocoA = transcribe_clast(clast_str=clast_strA)

    dfAcusto = pd.DataFrame(blocoA['custoOperacao']).set_index('numUsina')
    dfAalteracoes = pd.DataFrame(blocoA['alteracaoCusto'])
    dfAalteracoes=dfAalteracoes.loc[:, ["nomeUsina","custo","mesInicioModificacao","anoInicioModificacao","mesFimModificacao","anoFimModificacao"]]

    blocoB = transcribe_clast(clast_str=clast_strB)

    dfBcusto = pd.DataFrame(blocoB['custoOperacao']).set_index('numUsina')
    dfBalteracoes = pd.DataFrame(blocoB['alteracaoCusto'])
    dfBalteracoes=dfBalteracoes.loc[:, ["nomeUsina","custo","mesInicioModificacao","anoInicioModificacao","mesFimModificacao","anoFimModificacao"]]

    blocoC = get_diff_clast(blocoA, blocoB)

    dfCcusto = pd.DataFrame(blocoC['custoOperacao']).set_index('numUsina')
    dfCcusto.drop('index',axis = 1, inplace=True)
    dfCcusto = dfCcusto[(dfCcusto != 0).all(1)]

    values = [str(x) for x in list(dfCcusto.index)]
    df_filtered_A  = dfAcusto[dfAcusto.index.isin(values)].sort_index(ascending=True)
    df_filtered_B  = dfBcusto[dfBcusto.index.isin(values)].sort_index(ascending=True)
    dfCcusto['nomeUsina']=list(df_filtered_A['nomeUsina'])
    dfCcusto=dfCcusto.loc[:, ['nomeUsina','tipo','custo1','custo2','custo3','custo4','custo5']]

    dfCalteracoes = pd.DataFrame(blocoC['alteracaoCusto']).set_index('numUsina')
    dfCalteracoes = dfCalteracoes[(dfCalteracoes != 0).all(1)]
    usinas = list((dfCalteracoes.index))
    nomeUsinas = [dfAalteracoes.loc[str(x)]['nomeUsina'] for x in usinas]
    dfCalteracoes['nomeUsina']=nomeUsinas
    dfCalteracoes=dfCalteracoes.loc[:, ["nomeUsina","custo","mesInicioModificacao","anoInicioModificacao","mesFimModificacao","anoFimModificacao"]]
    
    values = [str(x) for x in list(set(dfCalteracoes.index))]
    df_filtered_Aalt  = dfAalteracoes[dfAalteracoes.index.isin(values)].sort_index(ascending=True)
    df_filtered_Balt  = dfBalteracoes[dfBalteracoes.index.isin(values)].sort_index(ascending=True)


    return df_filtered_A.round(2), df_filtered_Aalt.round(2), df_filtered_B.round(2), df_filtered_Balt.round(2), dfCcusto.round(2), dfCalteracoes.round(2)

def PayloadClast(dfAcusto, dfAalteracoes, dfBcusto, dfBalteracoes, dfCcusto, dfCalteracoes):
    '''
    Cria um payload a partir das saidas da função comparacaClast
    '''
    try:
        if(dfAcusto.equals(dfBcusto) and dfAalteracoes.equals(dfBalteracoes)):
            message = 'Não há diferença entre os decks'
            lista_custo=[dfAcusto.to_dict(orient='records')]
            lista_alteracoes = [dfAalteracoes.to_dict(orient='records')]
            dct_clast={
              'ESTRUTURAL':lista_custo,
              'CONJUNTURAL':lista_alteracoes,
            }

            payload_body = io.BytesIO(json.dumps(dct_clast).encode())
            print(message)
            return payload_body
            
        else:
            message = 'Há diferença entre os decks'
            print(message)
            lista_custo=[dfAcusto.to_dict(orient='records'),dfBcusto.to_dict(orient='records'),dfCcusto.to_dict(orient='records')]
            lista_alteracoes = [dfAalteracoes.to_dict(orient='records'), dfBalteracoes.to_dict(orient='records'), dfCalteracoes.to_dict(orient='records')]
            dct_clast={
              'ESTRUTURAL':lista_custo,
              'CONJUNTURAL':lista_alteracoes,
            }
            payload_body = io.BytesIO(json.dumps(dct_clast).encode())
            return payload_body
    except Exception as error:
            print(error.args)
            return utils_http.server_error_response(500, "Erro na comparacao")