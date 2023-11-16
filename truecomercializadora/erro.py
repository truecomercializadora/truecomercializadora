import traceback
from datetime import datetime,timedelta
import urllib
import os
import sys
import utils_ses

def EnviarEmailERRO(informacoes=None,emails = ["tecnologia@truecomercializadora.com"],EnviarVariaveis = True, tiposVariaveis = [int,str,dict,float,list,bool,tuple,set]):
    ERRO = traceback.format_exc()
    try:
        awslambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME").upper()
        CLOUDWATCH = f'https://sa-east-1.console.aws.amazon.com/cloudwatch/home?region={urllib.parse.quote(os.environ.get("AWS_REGION"), safe="")}#logsV2:log-groups/log-group/{urllib.parse.quote(os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME"), safe="")}/log-events/{urllib.parse.quote(os.environ.get("AWS_LAMBDA_LOG_STREAM_NAME"), safe="")}'
        data = datetime.today()-timedelta(hours=3)
        MENSAGEM = f'<B><H3> Ocorreu um erro no lambda {awslambda} em {data}<br>\
                <br> LINK DO CLOUDWATCH {CLOUDWATCH}<BR>\
                <br> ERRO:<br> {ERRO}'
        
        if EnviarVariaveis:
            tb = sys.exc_info()[2]
            variaveis = tb.tb_frame.f_locals
            variaveis = {x:variaveis[x] for x in variaveis.keys() if type(variaveis[x]) in tiposVariaveis}
            if variaveis!={}:
                MENSAGEM += "<br> VARIÁVEIS:<br>"
                for item in variaveis.keys():
                    MENSAGEM+= f'{item}:{variaveis[item]}<br><br>'
        
        MENSAGEM += f'<br> INFORMAÇÕES COMPLEMENTARES:<br> {informacoes}' if informacoes!=None else ''
        
        print('ENVIANDO EMAIL DE ERRO')
        utils_ses.send_email("Tecnologia True <tecnologia@truecomercializadora.com>",
            {'ToAddresses': emails,'CcAddresses': [''],'BccAddresses': []},
            {'subject': f"[ERRO] LAMBDA {awslambda}",
            'body_text': '',
            'body_html': MENSAGEM.replace("\n",'<br>')
            }
        )
    except:
        print("MODO DESENVOLVEDOR")
        print(ERRO)
    return