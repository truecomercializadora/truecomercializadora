import pandas as pd

def transcribe_re(re_str):
    '''
    Tranforma a string do 're.dat' em uma lista de dicionarios com infomações das usinas por conjunto
    '''
    dictio = []
    for line in re_str.splitlines():
        if 'RES' in line or 'XXX' in line: continue
        if '999' in line: break
        id_restricao = line.split()[0]
        line_size = len(line.split())
        usinas_restricao = []
        while(line_size-1 > 0):
            usinas_restricao.append(line.split()[line_size-1])
            line_size-=1
        linha = {'idRestricao': int(id_restricao),'usinasRestricao':usinas_restricao}
        dictio.append(linha)
    return dictio

def transcribe_re_value(re_str):
    '''
    Obtem as informções de cada restrição com as usinas correspondentes da string de um arquivo 're.dat'. Retorna uma lista de dicionarios.
    '''
    dictio2 = []
    skip_lines = len(transcribe_re(re_str))
    for line in re_str.splitlines()[skip_lines+3:]:
        if 'RESTRICAO' in line or 'XXXXXXXXXXXXXXX' in line: continue
        if '999' in line : break
        
        for line_tr in transcribe_re(re_str):
            if(int(line_tr['idRestricao'])==int(line.split()[0])):
                mes_inicio = line.split()[1]
                ano_inicio = line.split()[2]
                mes_fim = line.split()[3]
                ano_fim = line.split()[4]
                id_p = line.split()[5]
                valor_restricao = int(round(float(line.split()[6])))
                linha2 = {'idRestricao':line_tr['idRestricao'],
                'usinasRestricao:':line_tr['usinasRestricao'],
                'mesInicio':mes_inicio,
                'anoInicio':ano_inicio,
                'mesFim':mes_fim,
                'anoFim':ano_fim,
                'idP':id_p,
                'valorRestricao':valor_restricao}
                dictio2.append(linha2)
    return dictio2

def get_re_df(re_lines):
    '''
    Converte os dicionários resultantes da função 'transcribe_re_value' em dataframe.
    '''
    return pd.DataFrame(
    re_lines,
    columns = [
      'idRestricao',
      'usinasRestricao',
      'mesInicio',
      'anoInicio',
      'mesFim',
      'anoFim',
      'idP',
      'valorRestricao'
    ]).set_index([
      'idRestricao',
      'mesInicio',
      'anoInicio',
      'mesFim',
      'anoFim',
      'idP',
      'valorRestricao'
      ])
def expand_re(re_lines):
    new_re_lines = []
    dct_re = {}
    for linha in re_lines:
        idRestricao = int(linha['idRestricao'])
        usinasRestricao = list(linha['usinasRestricao:'])
        mesInicio = str(linha['mesInicio']).zfill(2)
        anoInicio = str(linha['anoInicio']).zfill(4)
        mesFim = str(linha['mesFim']).zfill(2)
        anoFim = str(linha['anoFim']).zfill(4)
        idP = int(linha['idP'])
        valorRestricao = int(round(float((linha['valorRestricao']))))
        if(anoInicio != anoFim or mesInicio != mesFim):
            data_inicial = f'{anoInicio}-{mesInicio}-01'
            data_final = f'{anoFim}-{mesFim}-01'
            datas = pd.date_range(data_inicial,data_final, freq='MS').strftime("%Y-%m").tolist()
            for data in datas:
                # print(new_mesInicio,new_anoInicio)
                new_mesInicio = data.split('-')[1]
                new_anoInicio = data.split('-')[0]
                dct_re.update({
                    'idRestricao':idRestricao,
                    'usinasRestricao:':usinasRestricao,
                    'mesInicio': int(new_mesInicio),
                    'anoInicio':int(new_anoInicio),
                    'mesFim': int(new_mesInicio),
                    'anoFim':int(new_anoInicio),
                    'idP':idP,
                    'valorRestricao':valorRestricao
                })
                new_re_lines.append(dct_re.copy())
        else:
            new_re_lines.append(linha)
    return new_re_lines

def getFileRE(re_A,re_B):
    '''
    Converte a string de 2 arquivos "re.dat" em dois dataframes.
    '''
    re_A_lines = transcribe_re_value(re_A)
    re_B_lines = transcribe_re_value(re_B)
    new_re_A_lines = expand_re(re_A_lines)
    new_re_B_lines = expand_re(re_B_lines)

    df_A = pd.DataFrame().from_dict(new_re_A_lines).drop(columns='idRestricao')
    df_A=df_A.astype({'mesInicio':'int32','anoInicio':'int32','mesFim':'int32','anoFim':'int32','idP':'int32'})

    df_B = pd.DataFrame().from_dict(new_re_B_lines).drop(columns='idRestricao')
    df_B=df_B.astype({'mesInicio':'int32','anoInicio':'int32','mesFim':'int32','anoFim':'int32','idP':'int32'})
    return df_A,df_B

def comparaRE(df_A,df_B):
    '''
    Realiza a comparação entre 2 dataframes e retorna 2 dataframes com as diferenças entre eles.
    '''
    df_B_diff = pd.DataFrame()
    df_A_diff = pd.DataFrame()
    for row in df_A.itertuples():
        usinas = list(map(str, row[1]))
        mesInicio = row[2]
        anoInicio = row[3]
        mesFim = row[4]
        anoFim = row[5]
        value_list = [usinas]
        boolean_series = (df_B['usinasRestricao:']).isin(value_list)
        filtered_df_B = df_B[boolean_series]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['mesInicio']==mesInicio]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['anoInicio']==anoInicio]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['mesFim']==mesFim]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['anoFim']==anoFim]

        boolean_series = (df_A['usinasRestricao:']).isin(value_list)
        filtered_df_A = df_A[boolean_series]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['mesInicio']==mesInicio]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['anoInicio']==anoInicio]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['mesFim']==mesFim]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['anoFim']==anoFim]

        if(filtered_df_B.empty):
            element = {
                'usinasRestricao:':[usinas],
                'mesInicio':int(row[2]),
                'anoInicio':int(row[3]),
                'mesFim': int(row[4]),
                'anoFim': int(row[5]),
                'idP':str(row[6]),
                'valorRestricao':0
            }
            row_B_new=pd.DataFrame.from_dict(element)
            
        else:
            row_B_new=filtered_df_B

        filtered_df_A.set_index('usinasRestricao:',inplace=True)
        row_B_new.set_index('usinasRestricao:',inplace=True)

        comparasion_df = row_B_new.compare(filtered_df_A, keep_equal=False)
        if(not(comparasion_df.empty)):
            if(df_B_diff.empty == True):    
                df_B_diff = df_B_diff.append(row_B_new)
            else:
                if not [usinas] in (list(df_B_diff.index)):
                    df_B_diff = df_B_diff.append(row_B_new)
                else:
                    if any(df_B_diff['anoInicio']==anoInicio):
                        if not any(df_B_diff['mesInicio']==mesInicio):
                            df_B_diff = df_B_diff.append(row_B_new)
                    else:
                        df_B_diff = df_B_diff.append(row_B_new)
            if(df_A_diff.empty == True):    
                df_A_diff = df_A_diff.append(filtered_df_A)
            else:
                if not [usinas] in (list(df_A_diff.index)):
                    df_A_diff = df_A_diff.append(filtered_df_A)
                else:
                    if any(df_A_diff['anoInicio']==anoInicio):
                        if not any(df_A_diff['mesInicio']==mesInicio):
                            df_A_diff = df_A_diff.append(filtered_df_A)
                    else:
                        df_A_diff = df_A_diff.append(filtered_df_A)
        
    for row in df_B.itertuples():
        usinas = list(map(str, row[1]))
        mesInicio = row[2]
        anoInicio = row[3]
        mesFim = row[4]
        anoFim = row[5]
        value_list = [usinas]

        boolean_series = df_B['usinasRestricao:'].isin(value_list)
        filtered_df_B = df_B[boolean_series]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['mesInicio']==mesInicio]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['anoInicio']==anoInicio]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['mesFim']==mesFim]
        filtered_df_B = filtered_df_B.loc[filtered_df_B['anoFim']==anoFim]

        boolean_series = df_A['usinasRestricao:'].isin(value_list)
        filtered_df_A = df_A[boolean_series]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['mesInicio']==mesInicio]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['anoInicio']==anoInicio]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['mesFim']==mesFim]
        filtered_df_A = filtered_df_A.loc[filtered_df_A['anoFim']==anoFim]

        if(filtered_df_A.empty):
            element = {
                'usinasRestricao:':[usinas],
                'mesInicio':int(row[2]),
                'anoInicio':int(row[3]),
                'mesFim': int(row[4]),
                'anoFim': int(row[5]),
                'idP':str(row[6]),
                'valorRestricao':0
            }
            row_A_new=pd.DataFrame.from_dict(element)
            
        else:
            row_A_new=filtered_df_A

        filtered_df_B.set_index('usinasRestricao:',inplace=True)
        row_A_new.set_index('usinasRestricao:',inplace=True)

        comparasion_df = row_A_new.compare(filtered_df_B, keep_equal=False)
        if(not(comparasion_df.empty)):
            if(df_B_diff.empty == True):
                df_B_diff = df_B_diff.append(filtered_df_B)
            else:
                if not [usinas] in (list(df_B_diff.index)):
                    df_B_diff = df_B_diff.append(filtered_df_B)
                else:
                    if any(df_B_diff['anoInicio']==anoInicio):
                        if not any(df_B_diff['mesInicio']==mesInicio):
                            df_B_diff = df_B_diff.append(filtered_df_B)     
                    else:
                        df_B_diff = df_B_diff.append(filtered_df_B)  
            if(df_A_diff.empty == True):    
                df_A_diff = df_A_diff.append(row_A_new)
            else:
                if not [usinas] in (list(df_A_diff.index)):
                    df_A_diff = df_A_diff.append(row_A_new)
                else:
                    if any(df_A_diff['anoInicio']==anoInicio):
                        if not any(df_A_diff['mesInicio']==mesInicio):
                            df_A_diff = df_A_diff.append(row_A_new)
                    else:
                        df_A_diff = df_A_diff.append(row_A_new)
    


    df_B_diff=(df_B_diff.reset_index()).round().astype({'usinasRestricao:':'str'})
    df_B_diff=df_B_diff.drop_duplicates(keep='first')
    usinasRestr=list(df_B_diff['usinasRestricao:'])
    lista_converted= []
    for i in range(len(usinasRestr)):
        word = usinasRestr[i]
        partial = [int(x) for x in word[2:len(word)-2].replace('\'',"").split(",")]
        lista_converted.append(partial)
    df_B_diff['usinasRestricao:']=lista_converted   


    df_A_diff=(df_A_diff.reset_index()).round().astype({'usinasRestricao:':'str'})
    df_A_diff=df_A_diff.drop_duplicates(keep='first')
    usinasRestr=list(df_A_diff['usinasRestricao:'])
    lista_converted= []
    for i in range(len(usinasRestr)):
        word = usinasRestr[i]
        partial = [int(x) for x in word[2:len(word)-2].replace('\'',"").split(",")]
        lista_converted.append(partial)
    df_A_diff['usinasRestricao:']=lista_converted   


   
    return (df_A_diff.reset_index()).round(),(df_B_diff.reset_index()).round()