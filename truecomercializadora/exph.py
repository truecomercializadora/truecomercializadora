import pandas as pd
import io

def addColumn(df, tipo):
    '''
    Adiciona a coluna tipoUsina no dataframe. Tem como entrada o df e o tipo de usina(Hidrelétrica,termica,...).
    '''
    coluna = []
    for i in range(len(df)):
        coluna.append(tipo)
    new = df
    new['tipoUsina'] = coluna
    return new



def exphDF(exph_str):
    '''
    Faz um tratamento na string do arquivo 'exph.dat' e retorna uma string.
    '''
    newlines=[]
    cod = None
    nome = None
    for line in exph_str.splitlines():
        if line[0] == '9':
            pass
        elif (line[0:4].strip()).isdigit():
            if line[24] == ' ':
                cod = line[0:4]
                nome = line[5:17]
                line = line.replace('/', ' ')
                newlines.append(cod + ' ' + nome + line[17:])
                newlines.append(cod + ' ' + nome + line[17:])
            else:
                cod = line[0:4]
                nome = line[5:17]
                line = line.replace('/', ' ')
                newlines.append(cod + ' ' + nome + line[17:])  
        elif cod == None:
            line = line.replace('/', ' ')
            newlines.append(line)
        else:
            line = line.replace('/', ' ')
            newlines.append(cod + ' ' +  nome + line[17:])
    return '\r\n'.join(newlines)

def comparaExph(exph_strA, exph_strB):
    '''
    Realiza a comparação entre dois arquivos 'exph.dat'. Tem como entrada a string do exph e como saída 3 dataframes df_A,df_B,df_Diff.
    '''
    
    exph_strA = exphDF(exph_strA)
    df1 = pd.read_fwf(io.StringIO(exph_strA), skiprows=2)
    df1 = df1.fillna(' ')
    df1 = df1.rename(columns={'XXXX': 'COD', 'XXXXXXXXXXXX': 'NOME', 'XX': 'MES ENCHIMENTO', 'XXXX.1':'ANO ENCHIMENTO', 
    'XX.1':'DURACAO','XX.X':'VOLUME %', 'XX.2':'MES ENTRADA', 'XXXX.2':'ANO ENTRADA', 
    'XXXX.X': 'POT', 'Unnamed: 9': 'MQ', 'Unnamed: 10': 'CJ'})
    df1 = df1.set_index('COD')
    
    exph_strB = exphDF(exph_strB)
    df2 = pd.read_fwf(io.StringIO(exph_strB), skiprows=2)
    df2 = df2.fillna(' ')
    df2 = df2.rename(columns={'XXXX': 'COD', 'XXXXXXXXXXXX': 'NOME', 'XX': 'MES ENCHIMENTO', 'XXXX.1':'ANO ENCHIMENTO', 
    'XX.1':'DURACAO','XX.X':'VOLUME %', 'XX.2':'MES ENTRADA', 'XXXX.2':'ANO ENTRADA', 
    'XXXX.X': 'POT', 'Unnamed: 9': 'MQ', 'Unnamed: 10': 'CJ'})
    df2 = df2.set_index('COD')

    df3 = df1.compare(df2)
    df3 = df3.fillna(' ').rename(columns={'self': 'A', 'other': 'B'})
    df3.columns = df3.columns.get_level_values(0) + ' ' +  df3.columns.get_level_values(1)

    values = [x for x in list((df3.index))]
    dct={}
    for i in set(values):
        dct.update({
            i:(list(df2.loc[i]['NOME'])[0])
        })
    nomes = [dct[x] for x in list((df3.index))]
    df3['NOME']=nomes

    df3=df3.loc[:, ["NOME","MES ENCHIMENTO A","ANO ENCHIMENTO A","MES ENCHIMENTO B","ANO ENCHIMENTO B","MES ENTRADA A","ANO ENTRADA A","MES ENTRADA B","ANO ENTRADA B"]]

    return df1, df2, df3
