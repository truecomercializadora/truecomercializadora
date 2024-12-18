from . import (
    utils_s3,
    utils_datetime,
    utils_http
)
import pandas as pd
import json
import datetime
import io 

"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo modif.dat
"""

def _expand_linhas_expt(expt_lines):
	'''
    Retorna uma lista de dicionarios expandindo os valores contidos em expt_lines
    para completar o horizonte inteiro
    '''
	lista = []
	for alteracao in expt_lines:
		if alteracao['mesFim'] == '' and alteracao['anoFim'] == '':
			continue

		mesIni = int(alteracao['mesInicio'])
		anoIni = int(alteracao['anoInicio'])
		mesFim = int(alteracao['mesFim'])
		anoFim = int(alteracao['anoFim'])
		
		dataInicio = datetime.datetime(anoIni, mesIni,1)
		dataFim = datetime.datetime(anoFim, mesFim,1)

		proxMes = mesIni
		proxAno = anoIni
		if alteracao['nomeUsina'] != 'AJUSTE' and alteracao['nomeUsina'] != '':
			cod = alteracao['nomeUsina']
        
        
		diferenca_horizonte = utils_datetime.diff_month(dataFim, dataInicio)
		if diferenca_horizonte == 0:
			lista.append({
				'numeroUsina': int(alteracao['numeroUsina']),
                'nomeUsina': cod,
				'tipoModificacao': alteracao['tipoModificacao'],
				'mesInicio': proxMes,
				'anoInicio': proxAno,
				'mesFim':  proxMes,
				'anoFim': proxAno,
				'novoValor': int(round(float(alteracao['novoValor']))),
			})
		else:
			for _ in range(diferenca_horizonte + 1):
				if proxMes % 12 == 0:
					lista.append({
						'numeroUsina': int(alteracao['numeroUsina']),
                        'nomeUsina': cod,
						'tipoModificacao': alteracao['tipoModificacao'],
						'mesInicio': proxMes,
						'anoInicio': proxAno,
						'mesFim':  proxMes,
						'anoFim': proxAno,
						'novoValor': int(round(float(alteracao['novoValor']))),
					})
					proxMes = 1
					proxAno += 1
				else:
					lista.append({
						'numeroUsina': int(alteracao['numeroUsina']),
                        'nomeUsina': cod,
						'tipoModificacao': alteracao['tipoModificacao'],
						'mesInicio': proxMes,
						'anoInicio': proxAno,
						'mesFim':  proxMes,
						'anoFim': proxAno,
						'novoValor': round(int(alteracao['novoValor']),2),
					})
					proxMes += 1
	return lista

def get_expt_list(expt_str: str, ano_deck: int) -> list:
	'''
	Retorna uma lista de dicionarios representando cada uma das linhas do arquivo
	  expt.dat
	'''
	if type(expt_str) != str:
		raise TypeError("'get_expt_list' can only receive a expt.dat string.")

	if ('NUM   TIPO   MODIF  MI ANOI MF ANOF' not in expt_str):
		raise Exception("'get_expt_list' input str does not seem to represent a "
	                    "expt.dat file. Verify the input content.")

	if type(ano_deck) != int:
		raise TypeError("'get_expt_list' can only receive an integer for 'ano_deck'")

	return [{
		'numeroUsina': line[:5].strip(),
		'tipoModificacao': line[5:10].strip(),
		'novoValor': int(round(float(line[11:19].strip()))),
		'mesInicio': int(line[20:22].strip()),
		'anoInicio': int(line[23:27].strip()),
		'mesFim': int(line[28:30].strip()) if line[28:30].strip() != '' else 12 ,
		'anoFim': int(line[31:35].strip()) if line[31:35].strip() != '' else int(ano_deck) + 4,
        'nomeUsina': line[35:].strip()
	} for line in expt_str.splitlines()[2:]]


def get_expt_df(expt_str, ano_deck):
  '''
  Retorna a dataframe completa a partir da string expt e do ano do deck
  '''
  expt_lines = get_expt_list(expt_str, ano_deck)
  expt_expandido = _expand_linhas_expt(expt_lines)
  return pd.DataFrame(
    expt_expandido,
    columns = [
      'numeroUsina',
      'nomeUsina',
      'tipoModificacao',
      'mesInicio',
      'anoInicio',
      'mesFim',
      'anoFim',
      'novoValor',
    ]).set_index([
      'numeroUsina',
      'nomeUsina',
      'tipoModificacao',
      'mesInicio',
      'anoInicio',
      'mesFim',
      'anoFim',
      ])


def getPOTEFporSIS(dates,df_potef):
    '''
	Retorna a soma acumulada dos valores de potef para cada sistema 
	'''
    df_sum = pd.DataFrame(columns = ['data', 'valor'])
    somas=[]
    
    for i in range(len(dates)):
        year=dates[i][:4]
        month = dates[i][4:6]
        df_data = df_potef.loc[(df_potef['mesInicio']==int(month)) & (df_potef['anoInicio']==int(year))]
        if i == 0:
            if(len(df_data)!=0):
                sum = df_data['degrau'].sum()
            else:
                sum=0
        else:
            newsum = df_data['degrau'].sum()
            sum = newsum + somas[-1]

        somas.append(int(sum))
        dct_sum = {
        'data':f'{int(month)}/{int(year)}',
        'valor':int(sum)
        }
        df_sum = df_sum.append(dct_sum,ignore_index=True)
          
        
    return df_sum 

def get_degrau(df):
    '''
	Retorna um dataframe com o degrau acumulado de cada usina do parâmetro POTEF

	'''
    usinas = list(set(df['numeroUsina']))
    usinas.sort(reverse=False)
    df_degrau = pd.DataFrame(columns=['numeroUsina','tipoModificacao','nomeUsina','mesInicio','anoInicio','mesFim','anoFim','novoValor','degrau'])
    dct={}
    for usina in usinas:
        potef_usina=df.loc[df['numeroUsina']==usina]
        for i in range(len(potef_usina)):
            dct.update({
            'numeroUsina':usina,
            'tipoModificacao':'POTEF',
            'nomeUsina':list(potef_usina['nomeUsina'])[0],
            'mesInicio':int(potef_usina['mesInicio'].iloc[i]),
            'anoInicio':int(potef_usina['anoInicio'].iloc[i]),
            'mesFim':int(potef_usina['mesFim'].iloc[i]),
            'anoFim':int(potef_usina['anoFim'].iloc[i]),
            'novoValor':int(potef_usina['novoValor'].iloc[i]),
            })
            if i == 0:
                dct.update({
                    'degrau':int(potef_usina['novoValor'].iloc[i]),
                })
            else:
                dct.update({
                    'degrau':int(potef_usina['novoValor'].iloc[i]-potef_usina['novoValor'].iloc[i-1]),
                })
            df_degrau=df_degrau.append(dct,ignore_index=True)
    df_degrau = df_degrau.drop_duplicates()
    return df_degrau

def unexpand_potef(df):
    '''
	Retorna um dataframe do parâmetro POTEF do expt sem expansão até o final do horizonte do deck
	'''

    df_unexpanded=pd.DataFrame(columns=list(df.columns))
    usinas = list(set(df['numeroUsina']))
    usinas.sort(reverse=False)
    dct={}
    for usina in usinas:
    
        values=[]
        potef_usina=df.loc[df['numeroUsina']==usina]
        for v in list(potef_usina['novoValor']):
            if v not in values:
                values.append(v)
        
        for value in values:
            df_value = potef_usina.loc[potef_usina['novoValor']==value]
            mesInicio = int(df_value['mesInicio'].iloc[0])
            anoInicio = int(df_value['anoInicio'].iloc[0])
            mesFim = int(df_value['mesFim'].iloc[-1])
            anoFim = int(df_value['anoFim'].iloc[-1])

            dct.update({
                'numeroUsina':usina,
                'tipoModificacao':'POTEF',
                'nomeUsina':list(df_value['nomeUsina'])[0],
                'mesInicio':mesInicio,
                'anoInicio':anoInicio,
                'mesFim':mesFim,
                'anoFim':anoFim,
                'novoValor':int(value)
            })
            df_unexpanded=df_unexpanded.append(dct,ignore_index=True)

    return df_unexpanded
def getFilesExpt(expt_A,expt_B,year):
    '''
	Retorna as dataframes formatadas de expt_A e expt_B com elementos inteiros
	'''
    df_expt_A = get_expt_df(expt_A,year)

    df_expt_B= get_expt_df(expt_B,year)

    return (df_expt_A.round()).astype(float).round().astype(int),(df_expt_B.astype(float).round().astype(int))

def get_differences(modific_A_potef,modific_B_potef,df_sum_A_sis,df_sum_B_sis,modific_A_gtmin,modific_B_gtmin):
    '''
    Compara 1 a 1 cada aspecto definido no arquivo expt, ou seja,
    compara as dataframes de entrada e retorna um payload pronto para upload apenas com as diferenças
    '''
    if(modific_A_potef.equals(modific_B_potef)):
        message = 'Não há diferença entre os POTEF por sistema'
        lista_potef=[]
    else:
        message = 'Há diferença entre os POTEF por sistema'

        df_differences = modific_B_potef.copy()
        df_differences['novoValor'] = (modific_A_potef['novoValor']).astype(float).round().astype(int).subtract(modific_B_potef['novoValor'].astype(float).round().astype(int))
        df_differences = df_differences.loc[df_differences['novoValor']!=int(0)]
        df_filter_A  = modific_A_potef[modific_A_potef.index.isin(df_differences.index)]
        
        df_filter_B  = modific_B_potef[modific_B_potef.index.isin(df_differences.index)]
        
        lista_potef=[df_filter_B.to_dict(orient='records'),df_filter_A.to_dict(orient='records'),df_differences.to_dict(orient='records')]
    print(message)
    
    lista_sum = [df_sum_A_sis.to_dict(orient='records'),df_sum_B_sis.to_dict(orient='records')]

    if(modific_A_gtmin.equals(modific_B_gtmin)):
        message = 'Não há diferença entre os GTMIN'
        lista_gtmin=[]
    else:
        message = 'Há diferença entre os GTMIN'
        df_differences = modific_A_gtmin.copy()
        df_differences['novoValor'] = ((modific_A_gtmin['novoValor']).astype(float).round().astype(int)).subtract(modific_B_gtmin['novoValor'].astype(float).round().astype(int))
        df_differences = df_differences.loc[df_differences['novoValor']!=int(0)]
        df_filter_A  = modific_A_gtmin[modific_A_gtmin.index.isin(df_differences.index)]
        df_filter_B  = modific_B_gtmin[modific_B_gtmin.index.isin(df_differences.index)]
        lista_gtmin=[df_filter_B.to_dict(orient='records'),df_filter_A.to_dict(orient='records'),df_differences.to_dict(orient='records')]
    print(message)
    
    dct_modif = {}
    if(len(lista_potef)!=0):
        dct_modif.update({
            'POTEF':lista_potef
        })
    if(len(lista_sum)!=0):
        dct_modif.update({
            'POTEF-GRAF':lista_sum
        })
    if(len(lista_gtmin)!=0):
         dct_modif.update({
            'GTMIN':lista_gtmin
        })
    if(len(dct_modif)!=0):
        payload_body = io.BytesIO(json.dumps(dct_modif).encode())
    else: 
        payload_body=None

    return payload_body


def ComparacaoExpt(df_expt_A,df_expt_B,dates):
    '''
    Formata as entradas para utilizar as funções disponiveis de comparação e
    efetuar a comparacao entre A e B, retorna um payload com os dados
    '''
    modific_A_potef = df_expt_A.loc[(df_expt_A.index.get_level_values('tipoModificacao')=='POTEF')].reset_index()

    modific_A_potef=modific_A_potef.sort_values(by=['numeroUsina','anoInicio','mesInicio','mesFim','anoFim'])
    modific_A_potef.set_index(['numeroUsina'],inplace=True)
    modific_A_potef=modific_A_potef.reset_index()

    modific_B_potef = df_expt_B.loc[(df_expt_B.index.get_level_values('tipoModificacao')=='POTEF')].reset_index()

    modific_B_potef.set_index(['numeroUsina'],inplace=True)
    modific_B_potef=modific_B_potef.sort_values(by=['numeroUsina','anoInicio','mesInicio','mesFim','anoFim'])
    modific_B_potef=modific_B_potef.reset_index()


    unexpanded_B = unexpand_potef(modific_B_potef)
    unexpanded_A = unexpand_potef(modific_A_potef)

    degrau_B = get_degrau(unexpanded_B)
    degrau_A= get_degrau(unexpanded_A)

    df_sum_A_sis = getPOTEFporSIS(dates,degrau_A)
    df_sum_B_sis = getPOTEFporSIS(dates,degrau_B)

   

    modific_A_gtmin = df_expt_A.loc[(df_expt_A.index.get_level_values('tipoModificacao')=='GTMIN')].reset_index()
    modific_B_gtmin = df_expt_B.loc[(df_expt_B.index.get_level_values('tipoModificacao')=='GTMIN')].reset_index()
    
    return modific_A_potef,modific_B_potef,df_sum_A_sis,df_sum_B_sis,modific_A_gtmin,modific_B_gtmin

    # payload_body = get_differences(modific_A_potef,modific_B_potef,df_sum_A_sis,df_sum_B_sis,modific_A_gtmin,modific_B_gtmin)

    # return payload_body
