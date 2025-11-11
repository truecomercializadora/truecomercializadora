import json
import os
from truecomercializadora.PROSPEC import prospecapi
from functools import wraps

api = None

def configurar_credenciais(username, password):
    global api
    api = prospecapi.ProspecAPI(username=username, password=password)

def requer_api_configurada(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if api is None:
            raise RuntimeError(
                f"Não foi configurado as credenciais para realizar o login na api da Prospec. "
                f"Chame 'prospec.configurar_credenciais(usuario, senha)' antes de usar '{func.__name__}()'."
            )
        return func(*args, **kwargs)
    return wrapper

@requer_api_configurada
def upload_zip_prospec(caminho_zip):
    files_list_folder = api.prepare_file_list(os.path.dirname(caminho_zip))
    print(files_list_folder)
    GUID = []
    retorno  = api.post("/api/Repositorio/UploadArquivos", files=files_list_folder)
    
    if retorno['status_code'] != 201:
        print("Erro ao fazer upload para prospec", json.loads(retorno['response']))
        return retorno
    
    response = retorno['response']
    GUID.append(response['fileName'])
    arquivosDeEntrada = { "arquivosEnviados": GUID, "idsDecks": []}
    print(arquivosDeEntrada)
    for _, (_, f, _) in files_list_folder:
        f.close()
    os.remove(caminho_zip)
    return arquivosDeEntrada

@requer_api_configurada
def get_deck_original(idEstudo: int, modelo: str) -> dict:
    """
    identificar o ID dos decks a serem reaproveitados
    idEstudo = id do estudo
    Modelo = NEWAVE, DECOMP ou DESSEM
    """
    lista_decks = api.get(f'/api/Estudos/Info/Deck/{idEstudo}')['response']
    for deck in lista_decks:
        if deck['modelo'] == modelo:
            print(deck)
            return deck
    return None

@requer_api_configurada
def get_id_maquina_dessem():
    return [server['id'] for server in api.get('/api/Servidores')['response'] if server['executaDessem'] == True][0]

@requer_api_configurada
def deletar_estudo(ids_estudo):
    if type(ids_estudo) == int:
        ids_estudo = [ids_estudo]
    response = api.delete('/api/Estudos', json = {"idsEstudos": ids_estudo})
    if response['status_code'] == 204:
        print("Estudo deletado com sucesso", ids_estudo)
    else:
        print(f"Erro ao deletar estudos {ids_estudo}:", json.loads(response['response']))
    return response

@requer_api_configurada
def reaproveitarCortesVolume(idEstudo: int, idCortes: int | None, idVolume: int | None):
    
    print("reaproveitarCortesVolume")
    response = {'status_code': 200}
    
    ## Cortes
    if idCortes:
        reponse_cortes = api.post(endpoint='/api/Reaproveitamentos/Cortes/Estudo/Associar',json={
            "reaproveitamentos": [
            {
                "idFonte": idCortes,
                "idDestino": idEstudo
            }
            ]
        })
        if reponse_cortes['status_code'] == 200:
            print(f"Cortes {idCortes} associado com sucesso ao estudo {idEstudo}")
        else:
            print(f"Erro ao associar cortes {idCortes} ao estudo {idEstudo}:", json.loads(reponse_cortes['response']))
            response = reponse_cortes
        print(reponse_cortes)

    ## Volumes
    if idVolume:
        deck_id_original = get_deck_original(idEstudo, "DECOMP")
        deck_id_volume = get_deck_original(idVolume, "DECOMP")
        if deck_id_original['anoOperativo'] > deck_id_volume['anoOperativo'] or \
        deck_id_original['mesOperativo'] > deck_id_volume['mesOperativo'] or \
        (deck_id_original['mesOperativo'] == deck_id_volume['mesOperativo'] and deck_id_original['revisao'] > deck_id_volume['revisao']):
            previous_stage = True
        else: previous_stage = False
        
        reponse_volume = api.post(endpoint='/api/Reaproveitamentos/Volumes/Estudo/Associar',json={
            "reaproveitamentos": [
                {
                "idFonte": idVolume,
                "idDestino": idEstudo, 
                "considerarEstagioAnterior": previous_stage}
            ]
        })
        if reponse_volume['status_code'] == 200:
            print(f"Volume {idVolume} associado com sucesso ao estudo {idEstudo}, previous_stage == {previous_stage}")
        else:
            print(f"Erro ao associar volume {idVolume} ao estudo {idEstudo}:", json.loads(reponse_volume['response']))
            response = reponse_volume
        print(reponse_volume)

    return response

@requer_api_configurada
def getInfoEstudos(IdEstudo: int | None = None, Titulo: str | None = None, Tags: list | None = None, Mes: int | None = None, Ano: int | None = None, TemDecomp: bool | None = None, TemNewave: bool | None = None, Status: str | None = None, Deslocamento: int | None = None, Limite: int | None = None) -> dict:
    """
    Obtém todos os estudos cadastrados no sistema e filtros podem ser enviados como argumento da função.
    
    IdEstudo: número de identificação do estudo

    Titulo: título do estudo

    Tags: marcadores associados ao estudo

    Mes: mês inicial do estudo

    Ano: ano inicial do estudo

    TemDecomp: se o estudo possui decks DECOMP, podendo ser "true" ou "false"

    TemNewave: se o estudo possui decks NEWAVE, podendo ser "true" ou "false"

    Status: Situação do estudo, podendo ser:
    NotReady (não está pronto)
    Generating (gerando)
    Ready (pronto)
    Executing (em execução)
    Failed (com falha)
    Finished (concluído)
    Aborted (abortado)

    Deslocamento (x): Ignora os primeiros "x" elementos.

    Limite (y): Retorna os próximos "y" elementos.
    
    As informações de retorno são dispostas em um json como apresentado abaixo, e nele existirão todas as informações de cada deck segundo os filtros inseridos pelo usuário.
    """
    
    response = api.get('/api/Estudos', params={"IdEstudo": IdEstudo,
                                            "Titulo": Titulo,
                                            "NomesTags": Tags,
                                            "Mes": Mes,
                                            "Ano": Ano,
                                            "TemDecomp": TemDecomp,
                                            "TemNewave": TemNewave,
                                            "Status": Status,
                                            "Skip": Deslocamento,
                                            "Take": Limite,
                                            })
    
    print(response)
    
    if response['status_code'] != 200:
        print("Erro ao obter informação do(s) estudo(s):", json.loads(response['response']))

    return response

@requer_api_configurada
def geracaoDessem(titulo: str, arquivosDeEntrada:dict, anoInicial: int, mesInicial: int, diaInicial: int, quantidadeDeDias: int = 1, descricao: str | None = None, tags: list | None = None, versaoDessem: str | None = None) -> dict:
    """
    Com essa função é possível gerar estudos compostos por decks do modelos DESSEM. 
    É necessário utilizar a rota /api/Geracoes/Dessem no método POST.
    Para os arquivos enviados, é necessário gerar um código através da função /api/Repositorio/UploadArquivos e junto com os outros parâmetros, gerar o estudo. 
    Caso o usuário deseje usar algum deck de outro estudo como base, é possível através do parâmetro idsDecks.
    
    titulo: título desejado para o estudo criado

    descricao: descrição do estudo criado

    tags: marcadores desejados para o estudo criado

    mesInicial: mês de início do estudo

    anoInicial: ano de início do estudo

    arquivosDeEntrada:
        arquivosEnviados: código gerado para os arquivos usados como base
        idsDecks: número de identificação do deck existente que será usado como base
        
    quantidadeDeDias: quantidade de dias do estudo, Caso se deseje executar apenas um deck de Dessem, esse valor precisa ser igual a 1; Caso desejar geraçao interssemanal, é necesário adicionar decks do NEWAVE e DECOMP junto ao deck do DESSEM

    diaInicial: dia de início do estudo

    versaoDessem: versão do DESSEM usada no estudo
    
    O retorno informa o ID do estudo e possíveis alertas:
    {
    "id": 0,
    "alertas": [
    "string"
    ]
    }
    """
    
    print("geracaoDessem")
    
    response = api.post(endpoint='/api/Geracoes/Dessem',json={
                "titulo":            titulo,
                "descricao":         descricao,
                "tags":              tags,
                "mesInicial":        mesInicial,
                "anoInicial":        anoInicial,
                "arquivosDeEntrada": arquivosDeEntrada,
                "quantidadeDeDias":  quantidadeDeDias,
                "versaoDessem":      versaoDessem,
                "diaInicial":        diaInicial
    })
    
    print(response)
    
    if response['status_code'] == 201:
        print("Estudo gerado com sucesso")
    else:
        print("Erro ao gerar o estudo Dessem:", json.loads(response['response']))

    return response

@requer_api_configurada
def executaDessem(idEstudo: int, idDeckInicial: int | None, idServidor: int, tipoTratamento: int, limiteTratamentos: int) -> dict:
    """
    idEstudo: número de identificação do estudo

    idDeckInicial: número de identificação do deck que se deseja iniciar, caso não seja informado, o Prospec executa a partir do último deck ainda não executado

    idServidor: número de identificação do servidor, caso seja uma instância on demand fixa

    tratamento:
        tipoTratamento: tipo de tratamento em caso de inviabilidade no dessem, podendo ser:
        0 - Parar estudo;
        1 - Tratar inviabilidades;
        2 - Ignorar inviabilidades;
        3 - Tratar + Ignorar inviabilidades;
        4 - Ignorar sem MILPIN
        5 - Tratar + Ignorar sem MILPIN
        limiteTratamentos: número máximo de tratamentos de inviabilidade
        
    configuracaoDecks:
        deckId: número de identificação do deck que se deseja configurar antes da execução
            versaoModelo: versão do deck que se deseja configurar antes da execução
            tratamento:
            tipoTratamento: tipo de tratamento em caso de inviabilidade no dessem, podendo ser:
            0 - Parar estudo;
            1 - Tratar inviabilidades;
            2 - Ignorar inviabilidades;
            3 - Tratar + Ignorar inviabilidades;
            4 - Ignorar sem MILPIN
            5 - Tratar + Ignorar sem MILPIN
            
            limiteTratamentos: número máximo de tratamentos de inviabilidade
        
    O retorno da função segue o json à seguir:
    {
        "chave": "string",
        "alertas": [
        "string"
        ]
    }
    """
    
    print("executaDessem")
    
    tratamento = {"tipoTratamento": tipoTratamento,"limiteTratamentos": limiteTratamentos}
    print(tratamento)
    
    configuracaoDecks = []
    
    infoDeck = get_deck_original(idEstudo, 'DESSEM')
    deckId = infoDeck['id']
    versaoModelo = infoDeck['versao']
    tratamentosDessem_deck = {"tipoTratamento": tipoTratamento, "limiteTratamentos": limiteTratamentos}
    
    configuracaoDecks.append({"deckId": deckId,
                            "versaoModelo": versaoModelo,
                            "tratamento": tratamentosDessem_deck
                            })

    print(configuracaoDecks)
    
    response = api.post(endpoint='/api/Execucoes/Dessem',json={
                                "idEstudo": idEstudo,
                                "idDeckInicial": idDeckInicial,
                                "idServidor": idServidor,
                                "tratamento": tratamento,
                                "configuracaoDecks": configuracaoDecks
    })

    print(response)
    
    if response['status_code'] == 200:
        print("Estudo executado com sucesso")
    else:
        print("Erro ao executar o estudo Dessem:", json.loads(response['response']))

    return response

@requer_api_configurada
def geracaoDecomp(titulo: str, arquivosDeEntrada:dict, anoInicial: int, mesInicial: int, revisaoInicial: int, quantidadeDeRevisoes: int = 1, descricao: str | None = None, tags: list | None = None, versaoDecomp: str | None = None, versaoGevazp: str | None = None) -> dict:
    """
    titulo: título desejado para o estudo criado

    descricao: descrição do estudo criado

    tags: marcadores desejados para o estudo criado

    mesInicial: mês de início do estudo

    anoInicial: ano de início do estudo

    arquivosDeEntrada:
        arquivosEnviados: código gerado para os arquivos usados como base
        idsDecks: número de identificação do deck existente que será usado como base

    quantidadeDeRevisoes: número de meses de duração do estudo

    revisaoInicial: revisão inicial do estudo

    versaoDecomp: versão do DECOMP usada no estudo

    versaoGevazp: versão do GEVAZP usada no estudo
    O retorno informa o ID do estudo e possíveis alertas:

    {
        "id": 0,
        "alertas": [
        "string"
        ]
    }
    """
    print("geracaoDecomp")
    
    response = api.post(endpoint='/api/Geracoes/Decomp',json={
                    "titulo": titulo,
                    "descricao": descricao,
                    "tags":tags,
                    "mesInicial": mesInicial,
                    "mesInicial": mesInicial,
                    "anoInicial": anoInicial,
                    "arquivosDeEntrada": arquivosDeEntrada,
                    "quantidadeDeRevisoes": quantidadeDeRevisoes,
                    "revisaoInicial": revisaoInicial,
                    "versaoDecomp": versaoDecomp,
                    "versaoGevazp": versaoGevazp
    })
    print(response)
    
    if response['status_code'] == 201:
        print("Estudo gerado com sucesso")
    else:
        print("Erro ao gerar o estudo Decomp:", json.loads(response['response']))
            
    return response

@requer_api_configurada
def executaNewaveDecomp(idEstudo: int, idDeckInicial: int | None, idServidor: int | None, modoExecucao: int, tipoInstancia: str | None, opcaoCicloDeVidaServidor: int, tratamentoEmCasoDeQuedaSpot: int, tipoTratamento: int, limiteTratamentos: int, limiteTratamentosNaoConvergencia: int, tipoTratamentoSensibilidade: int, limiteTratamentosSensibilidade: int, limiteTratamentosNaoConvergenciaSensibilidade: int):
    """
    idEstudo: número de identificação do estudo

    idDeckInicial: número de identificação do deck que se deseja iniciar, caso não seja informado, o Prospec executa a partir do último deck ainda não executado

    idServidor: número de identificação do servidor, caso seja uma instância on demand fixa

    modoExecucao: modo de execução do estudo, podendo ser:
        0 - Modo padrão;
        1 - Consistência de Estudo;
        2 - Consistência de Estudo + Padrão;
        3 - Consistência de Decks;
        4 - Consistência de Decks + Padrão;

    tipoInstancia: tipo da instância escolhida para a execução, por exemplo “c5.18xlarge”, se = None, o Prospec seleciona a mesma instância recomendada na interface 

    opcaoCicloDeVidaServidor: tipo de servidor que será solicitado na AWS, podendo ser:
        0 = servidor do tipo spot;
        1 = servidor do tipo OnDemand;

    tratamentoEmCasoDeQuedaSpot: parâmetro que indica o comportamento do Prospec em casos em que a AWS derruba a instância SPOT em que o estudo está sendo executado. Podendo ser:
        0 = Tentar no Spot por X tentativas e depois parar;
        1 = Parar Estudo;
        2 = Solicitar OnDemand imediatamente
        3 = Tentar no Spot por X tentativas e depois usar OnDemand

    configuracaoDecks: É possível alterar a versão do modelo ou o tratamento de inviabilidade dos decks do estudo. É necessário obter o id do deck.
        deckId: número de identificação do deck que se deseja configurar antes da execução
        versaoModelo: versão do deck que se deseja configurar antes da execução
        tratamentosDecomp: (procedimento caso a máquina seja derrubada pela AWS (servidor secundário))
            tipoTratamento: tipo de tratamento em caso de inviabilidade para o deck principal, podendo ser:
                0 = parar o estudo em caso de inviabilidade; 
                1 = tratar as inviabilidades + parar; 
                2 = ignorar as inviabilidades; 
                3 = tratar + ignorar as inviabilidades;
            limiteTratamentos: número máximo de tratamentos de inviabilidade para o deck principal
            limiteTratamentosNaoConvergencia: número máximo de tratamentos em caso de não convergência para o deck principal
            tipoTratamentoSensibilidade: tipo de tratamento de inviabilidades para os decks de sensibilidade, podendo ser
            limiteTratamentosSensibilidade: número máximo de tratamentos de inviabilidade para os decks de sensibilidade
            limiteTratamentosNaoConvergenciaSensibilidade: número máximo de tratamentos em caso de não convergência para os decks de sensibilidade
            
    O retorno da função segue o json à seguir:
    {
        "chave": "string",
        "alertas": [
        "string"
        ]
    }
        
    """
    print("executaNewaveDecomp")
    
    tratamentosDecomp = {
                    "tipoTratamento": tipoTratamento,
                    "limiteTratamentos": limiteTratamentos,
                    "limiteTratamentosNaoConvergencia": limiteTratamentosNaoConvergencia,
                    "tipoTratamentoSensibilidade": tipoTratamentoSensibilidade,
                    "limiteTratamentosSensibilidade": limiteTratamentosSensibilidade,
                    "limiteTratamentosNaoConvergenciaSensibilidade": limiteTratamentosNaoConvergenciaSensibilidade
                    }
    
    print(tratamentosDecomp)
    
    configuracaoDecks=[]
    decks_do_estudo = api.get(endpoint=f'/api/Estudos/Info/Deck/{idEstudo}')['response']
    
    for deck in decks_do_estudo:
        deckId = deck['id']
        versaoModelo = deck['versao']
    
        tratamentosDecomp_deck = {
                        "tipoTratamento": tipoTratamento,
                        "limiteTratamentos": limiteTratamentos,
                        "limiteTratamentosNaoConvergencia": limiteTratamentosNaoConvergencia,
                        "tipoTratamentoSensibilidade": tipoTratamento,
                        "limiteTratamentosSensibilidade": limiteTratamentosSensibilidade,
                        "limiteTratamentosNaoConvergenciaSensibilidade": limiteTratamentosNaoConvergenciaSensibilidade
                        }

        
        configuracaoDecks.append({
                                "deckId": deckId,
                                "versaoModelo": versaoModelo,
                                "tratamentosDecomp": tratamentosDecomp_deck
                                })
        
    print(configuracaoDecks)

    response = api.post(endpoint='/api/Execucoes/NewaveDecomp',json={
    "idEstudo": idEstudo,
    "idServidor": idServidor,
    "idDeckInicial": idDeckInicial,
    "modoExecucao": modoExecucao,
    "tipoInstancia": tipoInstancia,
    "tratamentosDecomp": tratamentosDecomp,
    "opcaoCicloDeVidaServidor": opcaoCicloDeVidaServidor,
    "tratamentoEmCasoDeQuedaSpot": tratamentoEmCasoDeQuedaSpot,
    "configuracaoDecks": configuracaoDecks
    })

    print(response)
    
    if response['status_code'] == 200:
        print("Estudo executado com sucesso")
    else:
        print("Erro ao executar o estudo Newave/Decomp:", json.loads(response['response']))

    return response

@requer_api_configurada
def GeracaoNewaveDecomp(titulo: str, arquivosDeEntrada:dict, anoInicial: int, mesInicial: int, revisaoInicial: int, quantidadeDeMeses: int, configuracoesMeses: list, descricao: str | None = None, tags: list | None = None, versaoNewave: str | None = None, versaoDecomp: str | None = None, versaoGevazp: str | None = None) -> dict:
    """
    titulo: título desejado para o estudo criado

    descricao: descrição do estudo criado

    tags: marcadores desejados para o estudo criado

    mesInicial: mês de início do estudo

    anoInicial: ano de início do estudo

    arquivosDeEntrada:
        arquivosEnviados: código gerado para os arquivos usados como base
        idsDecks: número de identificação do deck existente que será usado como base
        
    quantidadeDeMeses: número de meses de duração do estudo

    versaoNewave: versão do NEWAVE usada no estudo

    versaoDecomp: versão do DECOMP usada no estudo

    versaoGevazp: versão do GEVAZP usada no estudo

    revisaoInicial: revisão inicial do estudo

    configuracoesMeses:
        ano: ano para configurar
        mes: mês para confirgurar
        multiplosEstagios: se o estudo terá múltiplos estágios. Se true, gerará decks de Decomp semanais. Se false, gerará decks de Decomp com dois estágios apenas, ou seja, mensais. Obs.: caso o json seja mantido conforme o exemplo acima, por default somente os dois primeiros meses terão estágio semanal. Os demais meses terão estágios mensais.
        multiplasRevisoes: se o estudo terá múltiplas revisões. Se true, gerará todas as revisões partindo da revisão do deck de Decomp enviado. Se false, permanecerá apenas com a revisão inicial. Obs.: caso o json seja mantido conforme o exemplo acima, por default somente os dois primeiros meses terão todas as revisões geradas. Os demais meses gerarão somente a rev0.
        
    O retorno informa o ID do estudo e possíveis alertas:
    {
        "id": 0,
        "alertas": [
        "string"
        ]
    }
    """
    
    print("GeracaoNewaveDecomp")
    
    response = api.post(endpoint='/api/Geracoes/NewaveDecomp',json={
                "titulo": titulo,
                "descricao": descricao,
                "tags":tags,
                "mesInicial": mesInicial,
                "anoInicial": anoInicial,
                "arquivosDeEntrada": arquivosDeEntrada,
                "quantidadeDeMeses": quantidadeDeMeses,
                "versaoNewave": versaoNewave,
                "versaoDecomp": versaoDecomp,
                "versaoGevazp": versaoGevazp,
                "revisaoInicial": revisaoInicial,
                "configuracoesMeses": configuracoesMeses    
    })
    
    print(response)
    
    if response['status_code'] == 201:
        print("Estudo gerado com sucesso")
        print('ID ESTUDO CRIADO: ', response['response']['id'])
    else:
        print("Erro ao gerar o estudo Newave/Decomp:", json.loads(response['response']))
        
    return response

@requer_api_configurada
def PararExecucaoEstudo(idEstudo: int):
    response = api.post(f'/api/Execucoes/Parar/{idEstudo}')
    
    if response['status_code'] == '202':
        print(f"Estudo {idEstudo} abortado com sucesso")
    else:
        print(f"Erro ao parar estudo {idEstudo}")
        print(json.loads(response['response']))
        
    return response