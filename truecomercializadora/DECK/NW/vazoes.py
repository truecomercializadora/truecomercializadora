from DECK.utils import UTILS
from datetime import datetime

class vazoes_block(UTILS):
    def __init__(self):
        self.cabecalho = ""
        self.campos = [
            (  0, 0, "I*", "Ano"),
            (0 ,0 ,"I*","Mes"),
            (0, 0,"I*","Usina"),
            (1,4,"I4","Valor"),
                    ]
        self.valores = []
        self.size = 4
        self.meses = 12
        self.postos = 320
        self.ano_inicial = 1931

class VAZOES(UTILS):
    def __init__(self,caminho):
        self.blocos = {'vazoes':vazoes_block()}
        self.caminho = caminho
        self.vazoes = self.blocos['vazoes']
        self.nome = "VAZOES"
        self.ERROS = []
        self.load()
        self.hash = super().gerarHash()

    def load(self):
        if type(self.caminho) == bytes:
            dados = self.caminho
        else:
            with open(self.caminho, 'rb') as f:
                dados = f.read()

        tamanho_valor = self.vazoes.size
        total_valores = len(dados) // tamanho_valor
        total_meses = total_valores // self.vazoes.postos

        for i in range(total_meses):
            ano = self.vazoes.ano_inicial + (i // self.vazoes.meses)
            mes = (i % self.vazoes.meses) + 1

            for p in range(self.vazoes.postos):
                offset = (i * self.vazoes.postos + p) * tamanho_valor
                bloco = dados[offset:offset + tamanho_valor]

                vaz = super()._interpretarLinhaBinaria(
                    self.vazoes.campos,
                    bloco,
                    {"Ano": ano, "Mes": mes, "Usina": p + 1}
                )

                self.vazoes.valores.append(vaz)

        for item in self.vazoes.valores:
            item['DATA'] = datetime(item['Ano'], item['Mes'], 1)

    def save(self):
        return super()._saveToFileBytes(self.blocos.values())
    