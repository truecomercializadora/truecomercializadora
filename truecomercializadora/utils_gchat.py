from apiclient.discovery import build
from googleapiclient.http import MediaFileUpload,MediaIoBaseUpload
from google.oauth2 import service_account
import mimetypes

def mandarMsgGChat(space,msg,cards=[],cardsOld=[],NomeArquivo="",BytesIOArquivo=""):
    '''
    "space":str - É o espaço onde a mensagem será enviada. Consegue a partir do robo TrueChat no Google Chat
    "msg":str - É a mensagem a ser enviada
    "cards":list - Serve para criar cartões conforme documentação: https://developers.google.com/chat/api/reference/rest/v1/cards?hl=pt-br
    "cardsOld":list - Serve para criar cartões da forma antiga, conforme documentacao: https://developers.google.com/chat/api/reference/rest/v1/cards-v1?hl=pt-br
    "NomeArquivo":str - É o nome do arquivo que será enviado. Não é obrigatório
    "BytesIOArquivo":BytesIO - É o BytesIO do arquivo que será enviado. Só é necessário para enviar arquivos em memória.
    *** Para arquivos locais, passar apenas o "NomeArquivo". O "BytesIOArquivo" não é necessário para arquivos locais, apenas em memória
    *** Para enviar apenas texto ou cards, adicionar o app 'TrueChat' na conversa ou espaço.
    *** Para enviar arquivos é necessário adicionar o 'auto.true@truecomercializadora.com' e o app 'TrueChat' na conversa ou espaço.
    '''
    SCOPES = ["https://www.googleapis.com/auth/chat.messages.create"]
    credenciais = {'type': 'service_account', 'project_id': 'truechat-393120', 'private_key_id': '22006fba8a46210ba86eac0231eec6ef1f33bed1', 'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC+7z3R989GZThC\npJMHosPDyNsccLjEzDXRcXEKCCW87C6OKdfgRVmC216GXZdfPBKadccU20xloVf/\nkh3AgBknec/H4RluRzMKlbq1U+hXHJaDIevSi0XwxeEZsu/C+QsZRzdKYZaxQndS\n1a9Jc5DNiQGMJVaUB0pSF/7b0BXI5nsAuIZrAqWr+3P7aDhK99l1yFVmhaHohtMi\nNSzeH3GfCAsr346JvuyFSBsPDT2CKTbPFdATkn3vevb8mHyMkDhASt01bL6sN5hJ\nuLx3Szsilhe6qtRdscR9sdcV0c2XATQRkGZYOkzwGYdlte+n3xAH4J0DCHdpO/B5\nKgFIO+knAgMBAAECggEADSuol1K7CzwqzaIKyFr1ND/aXKBdhnaFrqbFT6+9lqx+\nDtPN4dkDmMMaec9It7EhOvyT2OYo427/og/8s5oo4gm4VPo7v4xZ9eMOx+viGekA\nn7DX0qRFYbUf1wUT6xGalX0aacWVWDEUodo+mj6TOjJQsOk+CyQwZfBLMsBF65+O\nCOuMpWRAvA/wH7AGpSYSnzOqEbjLqfaej2S0zy/qpPDeDqHm/e0HqZMNLFYjBpER\nvt3nJFigJFu81glTufqfoccOlK4BbNqJF6msF5z9dHytkhBOfo+h9n9/dRffhX/Y\nhjv7jjxCRnOMYcezU65SIe44mMB4cM0qRKicuYiKkQKBgQD922KnaTYxKJUSAyPa\nQAAFG/yZrZ0IZrkAWVIiWC/XcWfE2Bk3oE9eFjP+ViFmbwev2bXdNH5oPzX+LJ4Q\nTTUJSIGyrFPOQcSZbi8BuE0R8ZWvmu2rXMbB3HcKKwEeVBMxIT4VF0AwYJcbKgtw\n/9gctJEFAVcJmQWYs/O2yy9aEQKBgQDAi9+U/FhsC+YJBDZ8YsIRctZy8y5jp+BP\nrBlRu9g/NniEGmmZCQWYD3u+wP1/v3UGamftWl8kAsLbb2C/Le84htdR6D1UCHv6\n17wNURbkbzv85U+e3bjQQdGX1CDLxQ1kwoDMbk6lVaahDHv1BxqA5jDMNsAFxBIh\ndl6VQJsXtwKBgQChFjzlBOOJkDoAIxP2I5SfqWHCVyQFt8F/ki6HcrRxHxp9E6/0\n13pltuspYphxOtWC5kD8bJomJq5pawCmUYftKyB6M9Y+VQefYQbdLYlicI3O0B4v\nFoFddTvorN9Z0noXPAP8ODPYPwLEDwsRmpgVpxM7PN1xTrP5cX+eqBKVMQKBgCCh\n1AOo/MdbAOJ4T0+nYSKZ5tRWeH81PWPjU+sxPcYA0k35N/pSuBr8TMmYZZ4X8Zpj\nwDdOwJ8WxLVx2+CqxUc8OxPLm1E5muF5XIqZOpr+axlCN8tB4oeREBd+QQyn2cxA\n1plO/I8yw+m5duyhBpHf8Vc61DJl93iqWf9Lkr1jAoGATK+Ip0GPjLcHdFmHpFd8\nGdmpyXtgbz3PUMbkHHzbR/mIFG+5ixX4B5ompIWHT7TsSX47OZYGSDSh16nL/owO\nIamrTunjzeyOZDDsg3vzLTem4tASk9WYkGkhzOgU4pE7yByW8ihW4z4bs51Z2W67\njQp9+SIVsfssqSGoj+9nOKM=\n-----END PRIVATE KEY-----\n', 'client_email': 'truechat@truechat-393120.iam.gserviceaccount.com', 'client_id': '109534329513894370616', 'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token', 'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs', 'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/truechat%40truechat-393120.iam.gserviceaccount.com', 'universe_domain': 'googleapis.com'}
    space = "spaces/"+space if "spaces/" not in space else space
    credentials = service_account.Credentials.from_service_account_info(credenciais, scopes=SCOPES)
    try:
        if(NomeArquivo!=""):
            delegated_credentials = credentials.with_subject('auto.true@truecomercializadora.com')
            chat = build('chat', 'v1', credentials=delegated_credentials)
            if BytesIOArquivo!="":
                media = MediaIoBaseUpload(BytesIOArquivo,mimetype=mimetypes.guess_type(NomeArquivo)[0])
            else:
                media = MediaFileUpload(NomeArquivo)
            attachment_uploaded = [chat.media().upload(parent=space,body={'filename': NomeArquivo},media_body=media).execute()]
        else:
            chat = build('chat', 'v1', credentials=credentials)
            attachment_uploaded=[]
        chat.spaces().messages().create(parent=space,body={'text': msg,'cardsV2':cards,'cards':cardsOld,'attachment': attachment_uploaded}).execute()
    except:
        print("Sem permissão necessária")
    return