import boto3
import pandas as pd

def gerarTabelaBalanco(PDO_SIST,UC,TempoExecucao,dataZIP,inviabilidades,horario=False,tipo='SIN',media=False,horarioDiscretizado=False, df_inflex=None):
    ''' Funcao que processa o retorno do lambda dessem-analise-carregarDecks-prod para retornar a tabela com dados de balanco. 
    '''
    PLD_TABELA =  boto3.resource('dynamodb', region_name='sa-east-1').Table('pld-valor')

    df1 = PDO_SIST.loc[['SE','S','NE','N']]
    if not horario:
        df1=df1[df1['IPER']<49]
    else:
        df1=df1[(df1['IPER']==(horario*2+1))|(df1['IPER']==(horario*2+2))]
    df1['Cmo($/MWH)'] = df1.apply(lambda x:x['Cmo($/MWH)'] if x['Cmo($/MWH)']!="**********" else 999999999,axis=1)
    df1=df1.astype(float,errors='ignore')
    df1['Cmo($/MWH)'] = pd.to_numeric(df1['Cmo($/MWH)'], errors='ignore').fillna(999999999)

    #PLD
    PLD = PLD_TABELA.get_item(**{'Key': {'ano': dataZIP.year}})['Item']
    dfPLD=df1.reset_index()[['HORAFIXA','Sist','Cmo($/MWH)']].groupby(['HORAFIXA','Sist']).mean(numeric_only=True)
    dfPLD=dfPLD.clip(PLD['min'],PLD['max_horario'])
    ####

    if tipo=='SIN':
        df_agrupado = df1.groupby("IPER").sum(numeric_only=True)
        indice = df_agrupado['Carga Liquida(MW)'].idxmax()-1
        MAX_CARGA_LIQ = max(df_agrupado['Carga Liquida(MW)'])
    else:
        df_max = df1.reset_index()
        df_max = df_max.loc[df_max['Sist']==tipo]
        indice = df_max['Carga Liquida(MW)'].idxmax()
        MAX_CARGA_LIQ = max(df_max['Carga Liquida(MW)'])

    horas = int( indice // 2)
    minutos = int((indice % 2) * 30)
    HORARIO_PICO = f"{str(horas).zfill(2)}:{str(minutos).zfill(2)}"


    dfGraficos=df1.copy()
    if horarioDiscretizado or media:
        df1 = df1.reset_index().groupby(['HORAFIXA','Sist']).mean(numeric_only=True).reset_index().set_index("Sist")
        df1['HORA'] = df1.apply(lambda x:f"{x['HORAFIXA']}:00",axis=1)

    df1['PLD($/MWH)'] = df1.apply(lambda x:float(dfPLD.loc[x['HORAFIXA']].loc[x.name]),axis=1)
    dfGraficos['PLD($/MWH)'] = dfGraficos.apply(lambda x:float(dfPLD.loc[x['HORAFIXA']].loc[x.name]),axis=1)

    if tipo=="SIN":
        CMOSEGRAFICOS = list(dfGraficos["Cmo($/MWH)"].loc['SE'].copy())
        CMOSE = list(df1["Cmo($/MWH)"].loc['SE'].copy())
        
        PLDDE = list(df1["PLD($/MWH)"].loc['SE'].copy())
        PLDEGRAFICOS = list(dfGraficos["PLD($/MWH)"].loc['SE'].copy())
        df1 = df1.groupby('HORA').sum(numeric_only=True)
        dfGraficos = dfGraficos.groupby('HORA').sum(numeric_only=True)
        df1['Cmo($/MWH)'] = CMOSE
        dfGraficos['Cmo($/MWH)'] = CMOSEGRAFICOS
        df1['PLD($/MWH)'] = PLDDE
        dfGraficos['PLD($/MWH)'] = PLDEGRAFICOS
    else:
        df1 = (df1.loc[tipo]).set_index("HORA")
        dfGraficos = (dfGraficos.loc[tipo]).set_index("HORA")

    df1=df1.rename(columns={'Demanda(MW)':"DEMANDA(MW)",'Grenova(MW)':'Renovaveis(MW)','SomaGTMin(MW)':"GTMin(MW)","Carga Liquida(MW)":"Carga Liq(MW)",'SomatGH(MW)':"Geração Hidraulica(MW)"})
    dfGraficos=dfGraficos.rename(columns={'Demanda':"DEMANDA(MW)",'Grenova':'Renovaveis(MW)','SomaGTMin':"GTMin(MW)","Carga Liquida(MW)":"Carga Liq(MW)",'SomatGH(MW)':"Geração Hidraulica(MW)"})
    if media:
        TABELA1 = df1.copy()[['DEMANDA+ANDE+BOMB(MW)','Renovaveis(MW)','GTMin(MW)','Carga Liq(MW)','GT Ordem de Merito(MW)','Geração Hidraulica(MW)','PLD($/MWH)','Cmo($/MWH)']].mean(numeric_only=True)
        TABELA1 = round(TABELA1,0).astype(int,errors='ignore')
        TABELA1['UC'] = "LIGADO" if UC else "DESLIGADO"
        TABELA1['Tempo Execução'] = TempoExecucao
        if (TABELA1['PLD($/MWH)'])>PLD['max_estrutural']:
            TABELA1['PLD($/MWH)'] = PLD['max_estrutural']
        TABELA1['INV'] = inviabilidades
        if 'INF' in list(df1.apply(lambda x:int(x['Cmo($/MWH)']) if x['Cmo($/MWH)']< 99999999 else 'INF',axis=1)): TABELA1['Cmo($/MWH)']='INF'
        TABELA1['PICO CARGA LIQ(MW)'] = round(MAX_CARGA_LIQ,0)
        TABELA1['HORÁRIO DE PICO'] = HORARIO_PICO
        colunas = ['DEMANDA+ANDE+BOMB(MW)', 'Renovaveis(MW)', 'GTMin(MW)', 'Carga Liq(MW)','PICO CARGA LIQ(MW)','HORÁRIO DE PICO',
       'GT Ordem de Merito(MW)', 'Geração Hidraulica(MW)', 'PLD($/MWH)',
       'Cmo($/MWH)', 'UC', 'Tempo Execução', 'INV']
        df=pd.DataFrame(TABELA1).T[colunas]
        try:
            if tipo == 'SIN':
                if df_inflex is not None:
                    df_inflex.columns = ['Geração Inicial (MW)', 'Inflexibilidade Inicial (MW)']
                    posicao = 6
                    parte_a = df.iloc[:, :posicao]
                    parte_b = df.iloc[:, posicao:]
                    df = pd.concat([parte_a, df_inflex, parte_b], axis=1)
        except:
            pass
        
    else: 
        TABELA1 = df1.copy()[['DEMANDA+ANDE+BOMB(MW)','Renovaveis(MW)','GTMin(MW)','Carga Liq(MW)','GT Ordem de Merito(MW)','Geração Hidraulica(MW)','PLD($/MWH)','Cmo($/MWH)']]
        TABELA1 = round(TABELA1,0).astype(int,errors='ignore')
        df=pd.DataFrame(TABELA1).reset_index()
    if tipo=="SIN": df=df.rename(columns={'Cmo($/MWH)':'Cmo SE($/MWH)','PLD($/MWH)':'PLD SE($/MWH)'})
    return df,dfGraficos