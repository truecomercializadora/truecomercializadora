import telebot
from io import BytesIO

class BotTelegram:
	def __init__(self,CHAVE="",ID=""):
		self.CHAVE = '7201629989:AAGEPJcLDYocfayQYR3694TTNF00F1Q5fZI' if CHAVE=='' else CHAVE
		self.bot = telebot.TeleBot(self.CHAVE)
		self.GRUPO_ID = "-1002244454770" if ID=='' else ID

	def sendFile(self,dados,msgArquivo="",nomeArquivo=""):
		'''
		Envia arquivos locais ou em memoria para o chat do telegram
		dados: bytes or string - Caminho do arquivo ou Bytes do arquivo que se deseja enviar.
		msgArquivo: string - Texto que ficará vinculado ao arquivo enviado. Não é obrigatório.
		nomeArquivo: string - Nome do arquivo que será enviado. É obrigatório caso passe os bytes do arquivo, caso mande arquivo local, é enviado o nome do arquivo original. É necessário colocar a extensão do arquivo.
		'''
		if type(dados)!=bytes:
			if nomeArquivo=="":
				nomeArquivo = dados.rsplit("/",1)[-1]
			dados = open(dados,'rb').read()
		return self.bot.send_document(self.GRUPO_ID,dados,caption=msgArquivo,visible_file_name=nomeArquivo)
	def getID(self):
		'''Pega o ID do grupo/chat para enviar as mensagens'''
		print("DIGITE '/id' NA CONVERSA COM O BOT NO TELEGRAM QUE SE DESEJA OBTER O ID")
		print("DIGITE '/exit' NA CONVERSA COM O BOT NO TELEGRAM PARA FINALIZAR")

		@self.bot.message_handler(commands=['id'])
		def getID2(message):
			print('DADOS DA MENSAGEM: ')
			print(message)
			print("ID DO GRUPO:")
			print(message.chat.id)
			print("ID DO USUARIO:")
			print(message.from_user.id)
		
		@self.bot.message_handler(commands=['exit'])
		def EXIT(message):
			self.bot.stop_polling()
			self.bot.stop_bot()
		self.bot.polling()      

	def sendMessage(self,msg):
		'''Mandar msg para o grupo do telegram'''
		return self.bot.send_message(chat_id=self.GRUPO_ID,text=msg)
	
	def sendDF(self,df,nome,LarguraColunas = 2.8,AlturaLinhas = 0.8):
		'''
		***Necessário importar o matplotlib==3.5.1
		Envia diretamente um df do pandas para o chat do telegram no formato jpg
		df: pd.DataFrame - Dataframe do pandas que se quer enviar
		nome: string - Nome do arquivo que será enviado
		LarguraColunas: flaot - Largura da coluna do dataframe na imagem
		AlturaLinhas: flaot - Altura da linha do dataframe na imagem
		'''
		return self.sendFile(dados=dfToImage(df,LarguraColunas=LarguraColunas,AlturaLinhas=AlturaLinhas),msgArquivo=nome,nomeArquivo=f'{nome.replace("/","").replace(" ","")}.jpg')

def dfToImage(df,LarguraColunas = 2.8,AlturaLinhas = 0.8):
    import matplotlib.pyplot as plt
    from matplotlib.table import Table
    _ , ax = plt.subplots(figsize=(len(df.columns)*LarguraColunas, len(df.index)*AlturaLinhas))
    
    ax.axis('tight')
    ax.axis('off')
    tabela = Table(ax, bbox=[0, 0, 1, 1])

    for level in range(df.columns.nlevels):
        for i, col in enumerate(df.columns.get_level_values(level)):
            cell = tabela.add_cell(level, i, width=0.2, height=0.1, text=col, loc='center', facecolor='#002f4a')
            cell.set_text_props(color='white', weight='bold', fontsize=12)

    for i, linha in enumerate(df.values):
        for j, valor in enumerate(linha):
            cell = tabela.add_cell(i + df.columns.nlevels, j, width=0.2, height=0.1, text=valor, loc='center', facecolor='white')
            cell.set_fontsize(12)
            cell.set_text_props(color='black', weight='bold', fontsize=8)

    for (i, j), cell in tabela.get_celld().items():
        cell.set_edgecolor('black')

    tabela.auto_set_font_size(False)
    tabela.set_fontsize(12)
    tabela.scale(1.2, 1.2)

    ax.add_table(tabela)
    Bytes = BytesIO()
    plt.savefig(Bytes, bbox_inches='tight', pad_inches=0)
    return Bytes.getvalue()