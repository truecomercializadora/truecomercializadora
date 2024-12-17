from . import (
    utils_s3,
    utils_http
)
import pandas as pd
import json
import io 
import os

"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo modif.dat
"""

def _get_modif_line_type(cod):
    '''
    Retorna a lista de colunas referente ao codigo de entrada
    '''
    switcher = {
    "VOLMIN": ['valor','unidade'],
    "VOLMAX": ['valor', 'unidade'],
    "NUMCNJ": ['valor'],
    "NUMMAQ": ['valor','nConjunto'],
    "POTEFE": ['valor','nConjunto'],
    "PRODESP": ['valor'],
    "TEIF": ['valor'],
    "IP": ['valor'],
    "PERDHIDR": ['valor'],
    "VAZMIN": ['valor'],
    "COEFEVAP": ['valor','mes'],
    "COTAREA": ['valor1','valor2','valor3','valor4','valor5'],
    "VOLCOTA": ['valor1','valor2','valor3','valor4','valor5'],
    "CFUGA": ['mes','ano','valor'],
    "VMAXT": ['mes', 'ano', 'valor', 'unidade'],
    "VMINT": ['mes', 'ano', 'valor', 'unidade'],
    "NUMBAS": ['valor'],
    "VMINP": ['mes', 'ano', 'valor', 'unidade'],
    "VAZMINT": ['mes', 'ano', 'valor'],
    "CMONT": ['mes', 'ano', 'valor'],
    "TURBMAXT":['mes','ano','valor'],
    "TURBMINT": ['mes','ano','valor'],
    }
    return switcher.get(cod, 'Codigo Invalido')



def _reset_modif_list(listaAlteracoes):
    '''
    Reseta colunas de listaAlteracoes, adicionando colunas faltantes
    '''
    lista = []
    for alteracao in listaAlteracoes:
      if 'mes' not in alteracao.keys():
        alteracao.update({'mes': ''})
      if 'ano' not in alteracao.keys():
        alteracao.update({'ano': ''})
      if 'nConjunto' not in alteracao.keys():
        alteracao.update({'nConjunto': ''})
      if 'unidade' not in alteracao.keys():
        alteracao.update({'unidade': ''})
      if 'valor' not in alteracao.keys():
        alteracao.update({'valor': ''})
      lista.append(alteracao)
    df = pd.DataFrame(lista, columns = ['idUsina', 'pChave', 'mes', 'ano', 'valor', 'unidade', 'nConjunto']).set_index('idUsina')
    return json.loads(df.reset_index().to_json(orient='records'))

def transcribe_modif(modif_str):
    '''
    Transcreve a string do arquivo modif para uma carga json
    '''
    lista = []
    for line in modif_str.splitlines():
        if 'P.CHAVE' in line or 'XXX' in line: continue
        if 'USINA' in line:
            id_usina = line.split()[1]
            continue
        p_chave = line.split()[0]
        values = line.split()[1:]
        keys = _get_modif_line_type(p_chave)
        linha = {'idUsina': int(id_usina), 'pChave': p_chave}
        modificacoes = dict(zip(keys, values))
        if p_chave.upper() == 'COTAREA' or p_chave.upper() == 'VOLCOTA':
          novo_modificacoes = {'valor':'{valor1} {valor2} {valor3} {valor4} {valor5}'.format(valor1=modificacoes['valor1'],valor2=modificacoes['valor2'],valor3=modificacoes['valor3'],valor4=modificacoes['valor4'],valor5=modificacoes['valor5'])}
          linha.update(novo_modificacoes)
        else:
          linha.update(modificacoes)
        lista.append(linha)
    return _reset_modif_list(lista)


def get_modif_df(modif_lines):
    '''
    Retorna uma dataframe a partir dos dados de modif_lines
    '''
    return pd.DataFrame(
    modif_lines,
    columns = [
      'idUsina',
      'pChave',
      'mes',
      'ano',
      'valor',
      'unidade',
      'nConjunto'
    ]).set_index([
      'idUsina',
      'pChave',
      'mes',
      'ano',
      'valor',
      'unidade',
      'nConjunto',
    ])


def getFilesModif(modif_A,modif_B):
    '''
    Retorna as dataframes referentes às strings A e B apenas com valores inteiros
    '''
    modif_A_lines = transcribe_modif(modif_A)
    modif_B_lines = transcribe_modif(modif_B)

    df_modif_A = get_modif_df(modif_A_lines).astype(float).round().astype(int)
    df_modif_B = get_modif_df(modif_B_lines).astype(float).round().astype(int)

    return df_modif_A,df_modif_B


def getVmintComp(vmint_B,vmint_A):
    '''
    Retorna as dataframes de Vmint A e B com apenas as posições
    que contém diferenças
    '''
    df_B_diff = pd.DataFrame()
    df_A_diff = pd.DataFrame()

    for row in vmint_A.itertuples():
        usina = row[1]
        mes = row[3]
        ano = row[4]
        row_B = vmint_B.loc[vmint_B['idUsina'] == usina]
        row_B = row_B.loc[row_B['mes']==mes]
        row_B = row_B.loc[row_B['ano']==ano]
        row_A = vmint_A.loc[vmint_A['idUsina'] == usina]
        row_A = row_A.loc[row_A['mes']==mes]
        row_A = row_A.loc[row_A['ano']==ano]
        
        if(row_B.empty):
            element = {
                'idUsina': int(row[1]),
                'pChave':str(row[2]),
                'mes':int(row[3]),
                'ano':int(row[4]),
                'valor': 0,
                'unidade': str(row[6]),
                'nConjunto':str(row[7])
            }
            row_B_new=pd.DataFrame.from_dict(element, orient='index').T
        else:
            row_B_new=row_B
        row_B_new.set_index('idUsina',inplace=True)    
        row_A.set_index('idUsina',inplace=True) 
        comparasion_df = row_B_new.compare(row_A, keep_equal=False)
        if(not(comparasion_df.empty)):
            if(df_B_diff.empty == True):    
                df_B_diff = df_B_diff.append(row_B_new)
            else:
                if not usina in (list(df_B_diff.index)):
                    df_B_diff = df_B_diff.append(row_B_new)
                else:
                    if any(df_B_diff['ano']==ano):
                        if not any(df_B_diff['mes']==mes):
                            df_B_diff = df_B_diff.append(row_B_new)
                    else:
                        df_B_diff = df_B_diff.append(row_B_new)
            if(df_A_diff.empty == True):    
                df_A_diff = df_A_diff.append(row_A)
            else:
                if not usina in (list(df_A_diff.index)):
                    df_A_diff = df_A_diff.append(row_A)
                else:
                    if any(df_A_diff['ano']==ano):
                        if not any(df_A_diff['mes']==mes):
                            df_A_diff = df_A_diff.append(row_A)
                    else:
                        df_A_diff = df_A_diff.append(row_A)

    for row in vmint_B.itertuples():
        usina = row[1]
        mes = row[3]
        ano=row[4]
        row_B = vmint_B.loc[vmint_B['idUsina'] == usina]
        row_B = row_B.loc[row_B['mes']==mes]
        row_B = row_B.loc[row_B['ano']==ano]
        row_A = vmint_A.loc[vmint_A['idUsina'] == usina]
        row_A = row_A.loc[row_A['mes']==mes]
        row_A = row_A.loc[row_A['ano']==ano]

        if(row_A.empty):
            element = {
                'idUsina': int(row[1]),
                'pChave':str(row[2]),
                'mes':int(row[3]),
                'ano':int(row[4]),
                'valor': 0,
                'unidade': str(row[6]),
                'nConjunto':str(row[7])
            }
            row_A_new=pd.DataFrame.from_dict(element, orient='index').T

        else:
            row_A_new=row_A
        row_A_new.set_index('idUsina',inplace=True)    
        row_B.set_index('idUsina',inplace=True) 
        
        
        comparasion_df = row_A_new.compare(row_B, keep_equal=False)
        if(not(comparasion_df.empty)):
            if(df_B_diff.empty == True):    
                df_B_diff = df_B_diff.append(row_B)
            else:
                if not usina in (list(df_B_diff.index)):
                    df_B_diff = df_B_diff.append(row_B)
                else:
                    if any(df_B_diff['ano']==ano):
                        if not any(df_B_diff['mes']==mes):
                            df_B_diff = df_B_diff.append(row_B)
                    else:
                        df_B_diff = df_B_diff.append(row_B)
            if(df_A_diff.empty == True):    
                df_A_diff = df_A_diff.append(row_A_new)
            else:
                if not usina in (list(df_A_diff.index)):
                    df_A_diff = df_A_diff.append(row_A_new)
                else:
                    if any(df_A_diff['ano']==ano):
                        if not any(df_A_diff['mes']==mes):
                            df_A_diff = df_A_diff.append(row_A_new)
                    else:
                        df_A_diff = df_A_diff.append(row_A_new)
            
    df_A_diff.reset_index(inplace=True)
    df_B_diff.reset_index(inplace=True)

    return df_A_diff,df_B_diff


def expanded_vazmin_modif(df_vazmin,anos,meses):
    '''
    Retorna a df vazmin completa no horizonte definido por 'anos' e 'meses'
    '''
    df_expanded_vazmin = pd.DataFrame(columns=['idUsina','pChave','mes','ano','valor'])
    df_total_expanded =  pd.DataFrame(columns=['idUsina','pChave','mes','ano','valor'])
    df_expanded_vazmin['mes'] = meses
    df_expanded_vazmin['ano'] = anos

    for row in df_vazmin.itertuples():
        usina = [int(row[1])]*len(anos)
        pChave = [str(row[2])]*len(anos)
        valor = [int(round(float(row[5])))]*len(anos)
        df_expanded_vazmin['idUsina'] = usina
        df_expanded_vazmin['pChave'] = pChave
        df_expanded_vazmin['mes'] = meses
        df_expanded_vazmin['ano'] = anos
        df_expanded_vazmin['valor'] = valor

        df_total_expanded = df_total_expanded.append(df_expanded_vazmin)
    return df_total_expanded


def expand_vazmint_modif(df_vazmint,datas):
    '''
    Retorna a df vazmint completa no horizonte definido por 'datas'
    '''
    usinas = sorted(set(df_vazmint['idUsina']))
    df_expandido = pd.DataFrame()
    for usina in usinas:
        data_usinas = datas
        df_filtered = df_vazmint[(df_vazmint['idUsina']==usina)]
        df_mes = [str(x[:4]).zfill(4) + str(x[4:]).zfill(2) for x in list(df_filtered['ano']+df_filtered['mes'])]
        for element in df_mes:
            if element in data_usinas:
                data_usinas.remove(element)
        dct_filtered = pd.DataFrame.to_dict(df_filtered,orient='records')
        for data in data_usinas:
            if(data[4:]=='01'):
                ehVirada=True
            else: ehVirada=False
            for t in dct_filtered:
                if((int(data)-int((t['ano'].zfill(4))+t['mes'].zfill(2)))==1 or (ehVirada==True and (int(data)-int((t['ano'].zfill(4))+t['mes'].zfill(2)))==89)): # 89 é a diferenca entre jan e dez
                    new_dict={
                    'idUsina': t['idUsina'],
                        'pChave': 'VAZMIN',
                        'mes': data[4:],
                        'ano': data[:4],
                        'valor': t['valor']
                    }
                    dct_filtered.append(new_dict)
        df_expandido= df_expandido.append(pd.DataFrame.from_dict(dct_filtered))
    df_expandido.sort_values(by= ['idUsina','mes','ano'],axis=0,ascending=True,inplace=True)
    return df_expandido


def get_differences(mdf_vmint_diff_A,df_vmint_diff_B,vazmin_A,vazmin_B,vmaxt_A,vmaxt_B):
    '''
    Compara 1 a 1 cada aspecto definido no arquivo modif, ou seja,
    compara as dataframes de entrada e retorna um payload pronto para upload apenas com as diferenças
    '''
    if(mdf_vmint_diff_A.equals(df_vmint_diff_B)):
        message = 'Não há diferença VMINT no modif'
        lista_vmint=[]
    else:
        message = 'Há diferença VMINT no modif'
        df_differences = df_vmint_diff_B.copy()
        df_differences['valor'] = (mdf_vmint_diff_A['valor']).astype(float).round().astype(int).subtract(df_vmint_diff_B['valor'].astype(float).round().astype(int))
        df_differences = df_differences.loc[df_differences['valor']!=int(0)]
        
        df_filter_A  = mdf_vmint_diff_A[mdf_vmint_diff_A.index.isin(df_differences.index)]
        df_filter_B  = df_vmint_diff_B[df_vmint_diff_B.index.isin(df_differences.index)]

        dictHD=eval(open("dictHD.txt","r").read())
        listaNomes=[]
        for item in df_filter_A["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_A.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_filter_B["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_B.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_differences["idUsina"]:
            listaNomes.append(dictHD[item])
        df_differences.insert(0, 'Nomes', listaNomes)
        df_filter_A.insert(len(df_filter_A.columns)-2, 'Tipo','Hidrelétrica' )
        df_filter_B.insert(len(df_filter_B.columns)-2, 'Tipo','Hidrelétrica' )
        df_differences.insert(len(df_differences.columns)-2, 'Tipo','Hidrelétrica' )

        lista_vmint=[df_filter_B.to_dict(orient='records'),df_filter_A.to_dict(orient='records'),df_differences.to_dict(orient='records')]
    print(message)
    if(vazmin_A.equals(vazmin_B)):
        message = 'Não há diferença VAZMIN/VAZMINT no modif'
        lista_vazmin=[]
    else:
        message = 'Há diferença VAZMIN/VAZMINT no modif'
        df_differences = vazmin_B.copy()
        df_differences_vazmin = vazmin_B.copy().drop(columns='valor')

        df_differences_vazmin['valor']=((vazmin_A['valor']).astype(float).round().astype(int).subtract(vazmin_B['valor'].astype(float).round().astype(int)))
        df_differences = df_differences_vazmin.loc[df_differences_vazmin['valor']!=int(0)]
        df_filter_A  = vazmin_A[vazmin_A.index.isin(df_differences.index)]
        df_filter_B  = vazmin_B[vazmin_B.index.isin(df_differences.index)]

        dictHD=eval(open("dictHD.txt","r").read())
        listaNomes=[]
        for item in df_filter_A["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_A.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_filter_B["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_B.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_differences["idUsina"]:
            listaNomes.append(dictHD[item])
        df_differences.insert(0, 'Nomes', listaNomes)
        df_filter_A.insert(len(df_filter_A.columns)-2, 'Tipo','Hidrelétrica' )
        df_filter_B.insert(len(df_filter_B.columns)-2, 'Tipo','Hidrelétrica' )
        df_differences.insert(len(df_differences.columns)-2, 'Tipo','Hidrelétrica' )


        lista_vazmin=[df_filter_B.to_dict(orient='records'),df_filter_A.to_dict(orient='records'),df_differences.to_dict(orient='records')]
    print(message)
    if(vmaxt_A.equals(vmaxt_B)):
        message = 'Não há diferença VMAXT no modif'
        lista_vmaxt=[]
    else:
        message = 'Há diferença VMAXT no modif'
        df_differences = vmaxt_B.copy()
        df_differences['valor'] = (vmaxt_A['valor']).astype(float).round().astype(int).subtract(vmaxt_B['valor'].astype(float).round().astype(int))
        df_differences = df_differences.loc[df_differences['valor']!=int(0)]
        df_filter_A  = vmaxt_A[vmaxt_A.index.isin(df_differences.index)]
        df_filter_B  = vmaxt_B[vmaxt_B.index.isin(df_differences.index)]
        dictHD=eval(open("dictHD.txt","r").read())
        listaNomes=[]
        for item in df_filter_A["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_A.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_filter_B["idUsina"]:
            listaNomes.append(dictHD[item])
        df_filter_B.insert(0, 'Nomes', listaNomes)
        listaNomes=[]
        for item in df_differences["idUsina"]:
            listaNomes.append(dictHD[item])
        df_differences.insert(0, 'Nomes', listaNomes)
        df_filter_A.insert(len(df_filter_A.columns)-2, 'Tipo','Hidrelétrica' )
        df_filter_B.insert(len(df_filter_B.columns)-2, 'Tipo','Hidrelétrica' )
        df_differences.insert(len(df_differences.columns)-2, 'Tipo','Hidrelétrica' )
        lista_vmaxt=[df_filter_B.to_dict(orient='records'),df_filter_A.to_dict(orient='records'),df_differences.to_dict(orient='records')]
    print(message)

    dct_modif = {}
    if(len(lista_vmint)!=0):
        dct_modif.update({
            'VMINT':lista_vmint
        })
    if(len(lista_vazmin)!=0):
        dct_modif.update({
            'VAZMIN':lista_vazmin
        })
    if(len(lista_vmaxt)!=0):
         dct_modif.update({
            'VMAXT':lista_vmaxt
        })
    if(len(dct_modif)!=0):
        payload_body = io.BytesIO(json.dumps(dct_modif).encode())
    else: 
        payload_body=None

    return payload_body

def ComparacaoModif(df_modif_A,df_modif_B,anos,meses,datas):
    '''
    Formata as entradas para utilizar as funções disponiveis de comparação e
    efetuar a comparacao entre A e B, retorna um payload com os dados
    '''
    vmint_A = df_modif_A.loc[(df_modif_A.index.get_level_values('pChave')=='VMINT')] # A ons
    vmint_B = df_modif_B.loc[(df_modif_B.index.get_level_values('pChave')=='VMINT')] # B true
    vmint_B.reset_index(inplace=True)
    vmint_A.reset_index(inplace=True)
    vmint_A = vmint_A.sort_index()
    vmint_B = vmint_B.sort_index()
  
    df_vmint_diff_A, df_vmint_diff_B = getVmintComp(vmint_B,vmint_A)

    vazmin_A = df_modif_A.loc[(df_modif_A.index.get_level_values('pChave')=='VAZMIN')].reset_index() # A ons
    vazmin_B = df_modif_B.loc[(df_modif_B.index.get_level_values('pChave')=='VAZMIN')].reset_index() # B true

    vazmin_expandido_A= expanded_vazmin_modif(vazmin_A,anos,meses)
    vazmin_expandido_B = expanded_vazmin_modif(vazmin_B,anos,meses)

    vazmint_A = df_modif_A.loc[(df_modif_A.index.get_level_values('pChave')=='VAZMINT')].reset_index()
    vazmint_B = df_modif_B.loc[(df_modif_B.index.get_level_values('pChave')=='VAZMINT')].reset_index()

    vazmint_A['mes'] = vazmint_A['mes'].apply(lambda x: x.zfill(2))
    vazmint_A['ano'] = vazmint_A['ano'].apply(lambda x: x.zfill(4))

    vazmint_B['mes'] = vazmint_B['mes'].apply(lambda x: x.zfill(2))
    vazmint_B['ano'] = vazmint_B['ano'].apply(lambda x: x.zfill(4))

    vazmint_B.drop(columns=['unidade','nConjunto'],inplace=True)

    vazmint_A.drop(columns=['unidade','nConjunto'],inplace=True)

    vazmint_B['pChave'] = vazmint_A['pChave'] = 'VAZMIN'

    vazmint_expandido_A = expand_vazmint_modif(vazmint_A,datas).set_index(['idUsina','mes','ano'],inplace=True)
    vazmint_expandido_B = expand_vazmint_modif(vazmint_B,datas).set_index(['idUsina','mes','ano'],inplace=True)


    vazmin_B = pd.concat([vazmin_expandido_B,vazmint_expandido_B],ignore_index=True)
    vazmin_B.sort_values(by= ['idUsina','mes','ano'],axis=0,ascending=True,inplace=True)
    vazmin_B.sort_index(inplace=True)

    vazmin_A = pd.concat([vazmin_expandido_A,vazmint_expandido_A],ignore_index=True)
    vazmin_A.sort_values(by= ['idUsina','mes','ano'],axis=0,ascending=True,inplace=True)
    vazmin_A.sort_index(inplace=True)


    vmaxt_A = df_modif_A.loc[(df_modif_A.index.get_level_values('pChave')=='VMAXT')].reset_index()
    vmaxt_B = df_modif_B.loc[(df_modif_B.index.get_level_values('pChave')=='VMAXT')].reset_index()
    return vmint_A, vmint_B,vazmin_A,vazmin_B,vmaxt_A,vmaxt_B

    # payload_body = get_differences(df_vmint_diff_A, df_vmint_diff_B,vazmin_A,vazmin_B,vmaxt_A,vmaxt_B)

    # return payload_body