import datetime
import pandas as pd
import json
from truecomercializadora import utils_http,utils_s3
import io


def intercambio_df(agrint):
  '''
  Retorna dois dataframes, sendo o primeiro as informações do bloco intercambio e depois do bloco limites. Tem como entrada a string do arquivo 'agrint.dat'.
  '''
  agrupamentosIntercambio = []
  limitesGrupo = []
  aux = 0

  agrint=agrint.splitlines()
  for line in agrint:
    if '999' in line: aux += 1
    if aux == 0 and '999' not in line and 'AGRUPAMENTOS DE INTERC' not in line and '#AG' not in line and 'XXX' not in line:
      values = line.split()
      keys = ['agrupamento', 'subsistemaOrigem', 'subsistemaDestino', 'coeficiente', ]
      agrupamentosIntercambio.append(dict(zip(keys, values)))
    elif aux == 1 and '999' not in line and 'LIMITES POR GRUPO' not in line and '#AG' not in line and 'XXX' not in line:
      values = {
        'agrupamento': line[:5].strip().replace('.',''), 
        'mesInicial': line[5:8].strip().replace('.',''), 
        'anoInicial': line[9:13].strip().replace('.',''), 
        'mesFinal': line[13:17].strip().replace('.',''), 
        'anoFinal': line[17:21].strip().replace('.',''), 
        'limP1': line[23:29].strip().replace('.',''), 
        'limP2': line[31:37].strip().replace('.',''), 
        'limP3': line[39:45].strip().replace('.','')        
      }
      limitesGrupo.append(values)
    elif aux >1: break
    else: continue

  lista = []
  proxMes = None
  for alteracao in limitesGrupo:
    # if alteracao['mesFinal'] == '' and alteracao['anoFinal'] == '':
    #   continue
    if proxMes == None:
      anoBase = int(alteracao['anoInicial'])
    mesIni = int(alteracao['mesInicial'])
    anoIni = int(alteracao['anoInicial'])
    if alteracao['mesFinal'].isdigit():
      mesFim = int(alteracao['mesFinal'])
    else:
      mesFim = 12
    if alteracao['mesFinal'].isdigit():
      anoFim = int(alteracao['anoFinal'])
    else:
      anoFim = anoBase + 4
      
    dataInicio = datetime.datetime(anoIni, mesIni,1)
    dataFim = datetime.datetime(anoFim, mesFim,1)

    proxMes = mesIni
    proxAno = anoIni
    diferenca_horizonte = (dataFim.year - dataInicio.year) * 12 + dataFim.month - dataInicio.month
    
    if diferenca_horizonte == 0:
      lista.append({
        'agrupamento': alteracao['agrupamento'],
        'mesInicial': proxMes,
        'anoInicial': proxAno,
        'mesFinal':  proxMes,
        'anoFinal': proxAno,
        'limP1': int(alteracao['limP1']),
        'limP2': int(alteracao['limP2']),
        'limP3': int(alteracao['limP3'])
      })
    else:
      for i in range(diferenca_horizonte + 1):
        if proxMes % 12 == 0:
          lista.append({
            'agrupamento': alteracao['agrupamento'],
            'mesInicial': proxMes,
            'anoInicial': proxAno,
            'mesFinal':  proxMes,
            'anoFinal': proxAno,
            'limP1': int(alteracao['limP1']),
            'limP2': int(alteracao['limP2']),
            'limP3': int(alteracao['limP3'])
          })
          proxMes = 1
          proxAno += 1
        else:
          lista.append({
            'agrupamento': alteracao['agrupamento'],
            'mesInicial': proxMes,
            'anoInicial': proxAno,
            'mesFinal':  proxMes,
            'anoFinal': proxAno,
            'limP1': int(alteracao['limP1']),
            'limP2': int(alteracao['limP2']),
            'limP3': int(alteracao['limP3'])
          })
          proxMes += 1
  intercambio = pd.DataFrame(agrupamentosIntercambio)
  limites = pd.DataFrame(lista)
  limites=limites.set_index(["agrupamento","mesInicial","anoInicial","mesFinal","anoFinal"])
  intercambio=intercambio.set_index(["agrupamento","subsistemaOrigem","subsistemaDestino"])
  intercambio=intercambio.astype({i:float for i in intercambio.columns})
  limites=limites.astype({i:float for i in limites.columns})

  return intercambio.astype(int),limites.astype(int)
    
def tabela_diferencas(df1,df2):
  '''
  Retorna um dataframe com a diferença entre dois blocos iguais resultantes da função 'intercambio_df'.
  '''
  df_diff=df1.subtract(df2, fill_value=0)

  index=list(df_diff.index)
  teste2=[]
  df1_dif=[]
  df2_dif=[]
  for item in index:
      teste=0
      for item2 in df_diff.loc[item]:
          if item2==0 or pd.isna(item2):
              teste=teste+1
          if pd.isna(item2):
              try:
                df1.loc[item]
                df1_dif.append(item)
              except:
                df2.loc[item]
                df2_dif.append(item)
      if teste==len(df_diff.columns):
          continue
      teste2.append(item)
  df_diff=df_diff.loc[teste2]
  df_diff=df_diff.append(df2.loc[df2_dif])
  df_diff=df_diff.append(df1.loc[df1_dif])
  for item in teste2:
    df2_dif.append(item)
    df1_dif.append(item)
  
  df1_new = df1.subtract(df2)
  df1_new = df1_new[(df1_new != 0).all(1)]
  df1_new = df1_new.fillna(0)

  df2_new = df2.subtract(df1)
  df2_new = df2_new[(df2_new != 0).all(1)]
  df2_new = df2_new.fillna(0)

  if len(df2) > len(df1):
    df2_new = df2.add(df2_new).dropna()
  else:
    df1_new = df1.add(df1_new).dropna()

  return df_diff.round().astype(int), df2_new.round().astype(int), df1_new.round().astype(int)