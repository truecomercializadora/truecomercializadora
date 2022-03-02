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
	Retorna a soma dos valores de potef para cada sistema
	'''
    df_sum = pd.DataFrame(columns = ['data', 'valor'])

    for date in dates:
        year=date[:4]
        month = date[4:6]
        sum = ((df_potef.loc[(df_potef['mesInicio']==int(month))]).loc[(df_potef['anoInicio']==int(year))])['novoValor'].sum()
        dct_sum = {
            'data':f'{int(month)}/{int(year)}',
            'valor':int(sum.round(3))
        }
        df_sum = df_sum.append(dct_sum,ignore_index=True)
    return df_sum 


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


def uploadComparacaoExpt(df_expt_A,df_expt_B,S3_path,dates):
    '''
    Formata as entradas para utilizar as funções disponiveis de comparação e
    efetuar o upload de todas as diferenças entre A e B para datawarehouse-true
    '''

    modific_A_potef = df_expt_A.loc[(df_expt_A.index.get_level_values('tipoModificacao')=='POTEF')].reset_index()

    modific_A_potef=modific_A_potef.sort_values(by=['numeroUsina','mesInicio','anoInicio','mesFim','anoFim'])
    modific_A_potef.set_index(['numeroUsina'],inplace=True)
    modific_A_potef=modific_A_potef.reset_index()

    modific_B_potef = df_expt_B.loc[(df_expt_B.index.get_level_values('tipoModificacao')=='POTEF')].reset_index()

    modific_B_potef.set_index(['numeroUsina'],inplace=True)
    modific_B_potef=modific_B_potef.sort_values(by=['numeroUsina','mesInicio','anoInicio','mesFim','anoFim'])
    modific_B_potef=modific_B_potef.reset_index()


    df_sum_A_sis = getPOTEFporSIS(dates,modific_A_potef)
    df_sum_B_sis = getPOTEFporSIS(dates,modific_B_potef)
    

    modific_A_gtmin = df_expt_A.loc[(df_expt_A.index.get_level_values('tipoModificacao')=='GTMIN')].reset_index()
    modific_B_gtmin = df_expt_B.loc[(df_expt_B.index.get_level_values('tipoModificacao')=='GTMIN')].reset_index()
        
    payload_body = get_differences(modific_A_potef,modific_B_potef,df_sum_A_sis,df_sum_B_sis,modific_A_gtmin,modific_B_gtmin)

    if(payload_body!=None):
        try:
            utils_s3.upload_io_object(payload_body,'datawarehouse-true',S3_path)
            return utils_http.success_response(200, "Upload feito com sucesso para o s3")
        except Exception as error:
            print(error.args)
            return utils_http.server_error_response(500, "Erro no upload para s3")
    else:
        print('Não há diferença entre os arquivos expt')