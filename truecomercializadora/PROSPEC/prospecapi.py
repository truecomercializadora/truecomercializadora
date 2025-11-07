# -*- coding: utf-8 -*-
'''
Created on Wed Nov 27 12:12:02 2024

@author: Norus

'''

import os
import re
import json
import requests
from datetime import datetime, timedelta
from types import SimpleNamespace
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, parse_qs, unquote

__VERSION__ = '1.1'

class ProspecAPI():
    def __init__(self, username=None, password=None,
                 proxy_url=None, proxy_user=None, proxy_pass=None,
                 logs=True, bypass_ssl=False, autenticar_com_token=False):

        # Se não forem fornecidos username e password, tenta ler do arquivo credentials
        if (username is None or password is None) and os.path.isfile('credentials'):
            with open('credentials', 'r') as cred_file:
                print('Carregando usuário e senha do arquivo credentials')
                for line in cred_file.read().splitlines():
                    if '=' not in line:
                        continue

                    key, val = line.split('=', 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key in ('user', 'username', 'client_id'):
                        username = val
                    elif key in ('pass', 'password', 'client_secret'):
                        password = val

        self.username = username
        self.password = password

        if not username or not password:
            print('É necessário informar credenciais (via argumentos ou arquivo credentials)')
            raise

        # Se não forem fornecidos informações de proxy, tenta ler do arquivo credentials_proxy
        proxy_file = 'credentials_proxy'
        if (proxy_url is None or proxy_user is None or proxy_pass is None) and os.path.isfile(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f.read().splitlines():
                    if '=' not in line:
                        continue

                    key, val = line.split('=', 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'proxy_url':
                        proxy_url = val if val != '' else None
                    elif key == 'proxy_user':
                        proxy_user = val if val != '' else None
                    elif key == 'proxy_pass':
                        proxy_pass = val if val != '' else None

        self.proxy_url = proxy_url
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass

        # Dicionário de proxies para o requests
        if self.proxy_url:
            # Limpa proxy_url
            if not re.match(r'^https?://', self.proxy_url):
                self.proxy_url = 'http://' + self.proxy_url
            # Adiciona credenciais se existirem
            if self.proxy_user and self.proxy_pass:
                creds = f"{self.proxy_user}:{self.proxy_pass}@"
                self.proxy_url = re.sub(r'^(https?://)', r'\1' + creds, self.proxy_url)
            self.proxies = {'http': self.proxy_url,
                            'https': self.proxy_url}
        else:
            self.proxies = None

        # Defaults
        self.logs = logs
        self.bypass_ssl = bypass_ssl
        self.autenticar_com_token = autenticar_com_token

        # Controle de Bearer Token
        self.access_token = None
        self.token_expires_at = None
        self.token_type = None
        self.token_endpoint = '/auth/token'

        # Tenta ler as configurações do arquivo prospecapi.cfg
        yes_strings = ['true', '1', 't', 'yes', 'y', 'on', 'ligado', 'sim', 's']

        config_file = 'prospecapi.cfg'
        if os.path.isfile(config_file):
            print('Lendo configurações do arquivo prospecapi.cfg')
            try:
                with open(config_file, 'r') as file:
                    for line in file:
                        if '=' not in line:
                            continue

                        key, value = line.lower().strip().split('=', 1)
                        if key == 'url_jsonapi':
                            self.url_jsonapi = value
                        elif key == 'url_base':
                            self.url_base = value
                        elif key == 'token_endpoint':
                            self.token_endpoint = value
                        elif key == 'logs':
                            self.logs = value.lower() in yes_strings
                        elif key == 'bypass_ssl':
                            self.bypass_ssl = value.lower() in yes_strings
                        elif key == 'autenticar_com_token':
                            self.autenticar_com_token = value.lower() in yes_strings
            except Exception as e:
                print(f'Não foi possível ler arquivo prospecapi.cfg {e.args}')
        else:
            print('Não foi possível encontrar o arquivo prospecapi.cfg, utilizando valores padrão')

        # Configura a autenticação
        self.auth = None
        if self.username and self.password:
            self.auth = requests.auth.HTTPBasicAuth(self.username, self.password)

        # Inicializa funções dinâmicas de endpoints
        try:
            self._initialize_endpoints(self.list_endpoints())
        except Exception as e:
            print('[Aviso]: Não foi possível inicializar funções dinâmicas. As requisições ainda podem ser feitas utilizando os métodos tradicionais.')
            if self.logs:
                print(f'Exception: {e.args}')

    # Ligar/desligar logs
    def logs_on(self):
        self.logs = True

    def logs_off(self):
        self.logs = False

    def _timestamp(self):
        return f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}]'

    def _log_filename(self):
        return f'prospecapi_{datetime.now().strftime("%Y%m%d")}.log'

    # Métodos de gerenciamento de Bearer Token
    def get_access_token(self):
        '''
        Obtém um novo access token do servidor

        :return: True se sucesso, False caso contrário
        '''
        if self.logs:
            print(f'{self._timestamp()} Solicitando novo access token...')

        url = self.url_base + self.token_endpoint

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.username,
            "client_secret": self.password
        }

        try:
            response = requests.post(url, json=payload,
                                    proxies=self.proxies,
                                    verify=not self.bypass_ssl)

            if response.status_code == 200:
                data = response.json()

                self.access_token = data.get('access_token')
                self.token_type = data.get('token_type', 'jwt')
                expires_in = data.get('expires_in', 3600)

                # Calcula quando o token expira (com margem de segurança de 10s)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 10)

                if self.logs:
                    print(f'{self._timestamp()} Token obtido com sucesso! Expira em {expires_in}s')

                return True
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_description', 'Unknown error')
                except:
                    error_msg = f'Status code {response.status_code}'

                if self.logs:
                    print(f'{self._timestamp()} Erro ao obter token: {error_msg}')
                return False

        except Exception as e:
            if self.logs:
                print(f'{self._timestamp()} Exceção ao obter token: {str(e)}')
            return False

    def is_token_valid(self):
        '''
        Verifica se o token atual ainda é válido

        :return: True se o token é válido, False caso contrário
        '''
        if not self.access_token:
            return False

        if not self.token_expires_at:
            return False

        # Verifica se o token ainda não expirou
        is_valid = datetime.now() < self.token_expires_at

        if not is_valid and self.logs:
            print(f'{self._timestamp()} Token expirado, será renovado')

        return is_valid

    def ensure_token(self):
        '''
        Garante que existe um token válido, renovando se necessário

        :return: True se token válido está disponível, False caso contrário
        '''
        if not self.autenticar_com_token:
            return True

        if self.is_token_valid():
            return True

        return self.get_access_token()

    def _make_request_with_retry(self, method, endpoint, **kwargs):
        '''
        Faz uma requisição HTTP com retry automático em caso de 401 (token expirado)

        :param method: Método HTTP (get, post, put, patch, delete)
        :param endpoint: Endpoint da requisição
        :param kwargs: Argumentos para a requisição (params, data, json, headers, etc.)
        :return: Response object
        '''
        # Preparar argumentos base para requests
        request_kwargs = {
            'proxies': self.proxies,
            'verify': not self.bypass_ssl
        }

        # Adicionar todos os kwargs passados (params, data, json, files, stream, etc.)
        request_kwargs.update(kwargs)

        if self.autenticar_com_token:
            # Garantir que o token é válido antes da primeira tentativa
            if not self.ensure_token():
                raise Exception("Não foi possível obter token válido")

            # Preparar headers
            headers = request_kwargs.get('headers', {})
            if headers is None:
                headers = {}
                request_kwargs['headers'] = headers

            # Adicionar token
            headers['Authorization'] = f'Bearer {self.access_token}'

            # Primeira tentativa
            response = getattr(requests, method)(endpoint, **request_kwargs)

            # Se receber 401, tentar renovar token e refazer requisição
            if response.status_code == 401:
                if self.logs:
                    print(f'{self._timestamp()} Recebido 401 - Token pode ter expirado no servidor, renovando...')

                # Forçar renovação do token
                self.access_token = None  # Invalidar token atual

                if self.get_access_token():
                    # Atualizar header com novo token
                    headers['Authorization'] = f'Bearer {self.access_token}'

                    if self.logs:
                        print(f'{self._timestamp()} Tentando novamente com novo token...')

                    # Segunda tentativa com novo token
                    response = getattr(requests, method)(endpoint, **request_kwargs)
                else:
                    if self.logs:
                        print(f'{self._timestamp()} Falha ao renovar token')
        else:
            # Modo autenticação básica (HTTPBasicAuth)
            request_kwargs['auth'] = self.auth
            response = getattr(requests, method)(endpoint, **request_kwargs)

        return response

    def _prepare_request(self, endpoint, json_param=None):
        '''
        Prepara o endpoint e processa parâmetros JSON comuns

        :param endpoint: Endpoint relativo ou absoluto
        :param json_param: Parâmetro JSON que pode ser um dict ou caminho para arquivo .json
        :return: Tupla (endpoint_completo, json_processado)
        '''
        # Adicionar base URL se necessário
        if self.url_base not in endpoint:
            endpoint = self.url_base + endpoint

        # Processar JSON se for caminho de arquivo
        if json_param is not None and isinstance(json_param, str) and json_param.endswith('.json'):
            json_param = self.read_json(json_param)

        return endpoint, json_param

    def _initialize_endpoints(self, endpoints):
        '''
        Cria métodos dinamicamente para cada (path, method_http) que vier
        do dicionário `endpoints`. Exemplo de `endpoints`:
        {
          "/api/Estudos": {
            "GET": {
              "descricao": "Busca estudos",
              "params": [...],
              "requestBody": {...}
            },
            "POST": {...},
            "PUT": {...}
          },
          "/api/Tags": {
            "GET": {...},
            "POST": {...}
          }
        }

        Cada método (GET, POST, PUT, etc.) vira um sub-namespace
        dentro de `self.endpoints`. Por exemplo:
          self.endpoints.get.Estudos(...)
          self.endpoints.post.Estudos(...)
          self.endpoints.put.Estudos(...)
        '''

        # Gera self.endpoints
        if not hasattr(self, 'endpoints'):
            self.endpoints = SimpleNamespace()

        # Mapeia texto -> método de requisição
        method_map = {'GET': self.get, 'POST': self.post, 'PUT': self.put,
                      'PATCH': self.patch, 'DELETE': self.delete}

        # Função auxiliar para gerar nomes de função seguros
        def clean_endpoint_name(path):
            '''
            Converte nomes de endpoint como '/api/Estudos' em 'Estudos',
            removendo caracteres inválidos para funções Python
            '''
            # Tira a barra inicial
            name = path.strip('/')
            # Substitui / por _
            name = name.replace('/', '_')
            # Remove chaves de path param
            name = name.replace('{', '').replace('}', '')
            # Remover prefixo api_
            name = name.replace('api_', '')
            # Tira qualquer caracter estranho por precaução (regex)
            name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            if not name:
                name = 'root'  # se sobrar vazio
            return name

        # Percorre cada path e seus métodos
        for path, methods_dict in endpoints.items():
            # methods_dict = { 'GET': {...}, 'POST': {...}, ... }
            for method_http, details in methods_dict.items():
                # Se não implementado, pular
                if method_http not in method_map:
                    continue

                # Pega o "sub-namespace" para esse método dentro de self.endpoints
                if not hasattr(self.endpoints, method_http.lower()):
                    setattr(self.endpoints, method_http.lower(), SimpleNamespace())
                method_namespace = getattr(self.endpoints, method_http.lower())

                # Nome base
                method_name = clean_endpoint_name(path)

                # Lista de parâmetros obrigatórios, se existir
                params = details.get('params', [])
                required_params = [p['nome'] for p in params if p.get('obrigatorio')]

                # Função factory
                def make_endpoint_function(_path, _details, _method_http):
                    '''Retorna a função que chama self.get/post/put com os parâmetros corretos.'''
                    request_func = method_map[_method_http]

                    # Função endpoint
                    def endpoint_method(this, **kwargs):
                        # Valida obrigatórios
                        missing = [p for p in required_params if p not in kwargs]
                        if missing:
                            raise ValueError(f"Parâmetros obrigatórios ausentes: {', '.join(missing)}")

                        # Substitui parâmetros entre {}
                        path_params = {}
                        for k in list(kwargs.keys()):
                            if f'{{{k}}}' in _path:
                                path_params[k] = kwargs[k]

                        url = self.url_base + _path.format(**path_params)

                        # Remove do kwargs os que foram pro path
                        for k in path_params:
                            del kwargs[k]

                        # Get -> params = kwargs
                        # Se tiver files -> files = kwargs[files]
                        # Resto -> json = kwargs**
                        if _method_http == 'GET':
                            # GET → querystring
                            return request_func(url, params=kwargs)
                        else:
                            # POST, PUT, PATCH → verifica se precisamos enviar arquivos
                            if 'files' in kwargs:
                                files = kwargs.pop('files')

                                return request_func(url, files=files, data=kwargs)
                            else:
                                return request_func(url, json=kwargs)

                    # Monta docstring
                    docstring = f"Descrição: {_details.get('descricao', 'Sem descrição disponível.')}\n"
                    docstring += f'Endpoint: {_path}\n'
                    docstring += f'Método HTTP: {_method_http}\n'
                    # Parametros
                    if len(params) > 0:
                        docstring += "\nParâmetros:\n\n"
                        for param in params:
                            param_desc = f"- {param['nome']} ({param['tipo']}"
                            if param.get('formato'):
                                param_desc += f"/{param['formato']}"
                            param_desc += ")"
                            if param.get('obrigatorio'):
                                param_desc += " [obrigatório]"
                            docstring += f"\n    {param_desc}"
                    # Request body
                    if len(_details['requestBody']) > 0:
                        docstring += "\nRequest Body:\n\n"
                        for rb in _details['requestBody']:
                            docstring += f'{rb}: {_details["requestBody"][rb]}\n'

                    endpoint_method.__doc__ = docstring
                    return endpoint_method

                # Atribuir no namespace
                func = make_endpoint_function(path, details, method_http)
                setattr(method_namespace, method_name, func.__get__(self))

    # Listagens de endpoints
    def list_endpoints(self, verbose=False):
        '''Listar todos os endpoints do SWAGGER'''
        resposta = requests.get(self.url_jsonapi, auth=self.auth)
        endpoints = {}

        if resposta.status_code == 200:
            dados = resposta.json()
            paths = dados.get('paths', {})

            for path, path_item in paths.items():
                # path = "/api/Estudos"
                # path_item = {
                #   "get": {...},
                #   "post": {...},
                #   "put": {...},
                #   ...
                # }

                # Inicializar dict
                if path not in endpoints:
                    endpoints[path] = {}

                # Iterar métodos
                for method_http, method_data in path_item.items():
                    # method_http = "get" | "post" | "put" etc.
                    # method_data é um dict com summary, parameters, responses, etc.

                    summary = method_data.get('summary', 'Sem descrição disponível.')
                    if verbose:
                        print(f"\n{method_http.upper()} {path}")
                        print(f"  Resumo: {summary}")

                    # Coletar parâmetros
                    parameters = method_data.get('parameters', [])
                    params_list = []

                    if verbose and parameters:
                        print("  Parâmetros:")

                    for param in parameters:
                        # Resolve referências $ref, se existirem
                        while '$ref' in param:
                            ref_path = param['$ref']
                            partes = ref_path.lstrip('#/').split('/')
                            ref_obj = dados
                            for parte in partes:
                                ref_obj = ref_obj.get(parte, {})
                            param = ref_obj

                        nome = param.get('name')
                        schema = param.get('schema', {})
                        tipo = schema.get('type')
                        formato = schema.get('format')
                        obrigatorio = param.get('required', False)

                        params_list.append({'nome': nome,
                                            'tipo': tipo,
                                            'formato': formato,
                                            'obrigatorio': obrigatorio})

                        if verbose:
                            info_tipo = f"{tipo}/{formato}" if formato else tipo
                            req_flag = " [obrigatório]" if obrigatorio else ""
                            print(f"    - {nome} ({info_tipo}){req_flag}")

                    # Coletar requestBody, se existir
                    request_body = method_data.get('requestBody', {})

                    # Salvar endpoint
                    endpoints[path][method_http.upper()] = {'descricao': summary,
                                                            'params': params_list,
                                                            'requestBody': request_body}

        else:
            print(f'Não foi possível acessar a URL: {self.url_jsonapi} ({resposta.status_code})')

        return endpoints

    def read_json(self, path):
        ''' Ler arquivo JSON para params '''
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f'Não foi possível ler o arquivo JSON {path} {e.args}')

    # Requests
    def get(self, endpoint, params=None, headers=None, stream=False):
        '''
        Realiza um GET request.
        :param endpoint: URL completa ou relativa (caso relativa, deve ter um base_url pré-definido)
        :param params: Dicionário de parâmetros para a URL.
        :param headers: Dicionário de headers, se necessário.
        :param stream: Se True, retorna o response do requests sem carregá-lo na memória (útil para grandes arquivos).
        :return: Resposta da requisição
        '''
        endpoint, _ = self._prepare_request(endpoint)

        response = self._make_request_with_retry('get', endpoint,
                                                  params=params,
                                                  headers=headers,
                                                  stream=stream)

        return self._handle_response(response, stream=stream)

    def post(self, endpoint, data=None, json=None, files=None, headers=None, stream=False):
        '''
        Realiza um POST request.
        :param endpoint: URL completa ou relativa (caso relativa, deve ter um base_url).
        :param data: Dados form-urlencoded ou multipart a serem enviados.
        :param json: Dicionário a ser enviado como JSON no corpo da requisição.
        :param files: Arquivos a serem enviados no formato {'file': (filename, fileobj, 'content_type')}
        :param headers: Dicionário de headers, se necessário.
        :param stream: Se True, retorna o response do requests sem carregá-lo na memória.
        :return: Resposta da requisição
        '''
        endpoint, json = self._prepare_request(endpoint, json)

        response = self._make_request_with_retry('post', endpoint,
                                                  data=data,
                                                  json=json,
                                                  files=files,
                                                  headers=headers,
                                                  stream=stream)

        return self._handle_response(response, stream=stream)

    def put(self, endpoint, data=None, json=None, files=None, headers=None, stream=False):
        '''
        Realiza um PUT request.
        :param endpoint: URL completa ou relativa.
        :param data: Dados form-urlencoded ou multipart a serem enviados.
        :param json: Dicionário a ser enviado como JSON no corpo da requisição.
        :param files: Arquivos a serem enviados no formato {'file': (filename, fileobj, 'content_type')}
        :param headers: Dicionário de headers, se necessário.
        :param stream: Se True, retorna o response do requests sem carregá-lo na memória.
        :return: Resposta da requisição
        '''
        endpoint, json = self._prepare_request(endpoint, json)

        response = self._make_request_with_retry('put', endpoint,
                                                  data=data,
                                                  json=json,
                                                  files=files,
                                                  headers=headers,
                                                  stream=stream)

        return self._handle_response(response, stream=stream)

    def patch(self, endpoint, data=None, json=None, headers=None, stream=False):
        '''
        Realiza um PATCH request.
        :param endpoint: URL completa ou relativa (caso relativa, deve ter um base_url).
        :param data: Dados form-urlencoded ou multipart a serem enviados.
        :param json: Dicionário a ser enviado como JSON no corpo da requisição.
        :param headers: Dicionário de headers, se necessário.
        :param stream: Se True, retorna o response do requests sem carregá-lo na memória.
        :return: Resposta da requisição
        '''
        endpoint, json = self._prepare_request(endpoint, json)

        response = self._make_request_with_retry('patch', endpoint,
                                                  data=data,
                                                  json=json,
                                                  headers=headers,
                                                  stream=stream)

        return self._handle_response(response, stream=stream)

    def delete(self, endpoint, json=None, headers=None, stream=False):
        '''
        Realiza um DELETE request.
        :param endpoint: URL completa ou relativa (caso relativa, deve ter um base_url).
        :param json: Dicionário a ser enviado como JSON no corpo da requisição.
        :param headers: Dicionário de headers, se necessário.
        :param stream: Se True, retorna o response do requests sem carregá-lo na memória.
        :return: Resposta da requisição
        '''
        endpoint, json = self._prepare_request(endpoint, json)

        response = self._make_request_with_retry('delete', endpoint,
                                                  json=json,
                                                  headers=headers,
                                                  stream=stream)

        return self._handle_response(response, stream=stream)

    def _handle_response(self, response, stream=False):
        '''
        Trata a resposta para verificar se o retorno é JSON, texto ou binário.
        Se for um arquivo binário, retorna o conteúdo bruto (bytes).
        Caso contrário, tenta retornar JSON ou texto.
        :param stream: Se True, retorna diretamente o objeto response.
        '''
        result = {}
        http_method = response.request.method
        endpoint = response.request.url

        if not stream:
            # Checa status
            if not response.ok:
                result = {'endpoint': endpoint, 'status_code': response.status_code,
                          'response': response.text}

            # Verifica content-type
            content_type = response.headers.get('Content-Type', '').lower()

            binary_content_types = ['application/octet-stream',
                                    'application/zip',
                                    'attachment']

            if 'application/json' in content_type:
                result = {'endpoint': endpoint, 'status_code': response.status_code,
                          'response': response.json()}
            elif content_type in binary_content_types:
                # Retorna um dict com filename e bytes
                filename = response.headers['Content-Disposition'].split(';')[1]
                filename = filename.replace('filename=', '').replace('"', '').strip()

                # Se for um application/zip mas não tiver zip no nome, adicionar
                if content_type == 'application/zip' and not filename.endswith('.zip'):
                    filename += '.zip'

                result = {'endpoint': endpoint, 'status_code': response.status_code,
                          'response': {'file': (filename, response.content)}}
            else:
                # Retorna texto genérico
                result = {'endpoint': endpoint, 'status_code': response.status_code,
                          'response': response.text}
        else:
            # Se stream=True, retornar Response inteira
            result = {'endpoint': endpoint, 'status_code': response.status_code,
                      'response': response}

        # Registrar logs
        if self.logs:
            try:
                log_filename = self._log_filename()
                log_entry = f'{self._timestamp()} {http_method.upper()} para endpoint {endpoint} - Status code {result["status_code"]}\n'

                if response.request.body:
                    body_string = response.request.body.decode("utf-8")
                    if 'filename' in body_string:
                        filenames = re.findall(r'filename="([^"]+)"', body_string)
                        log_entry += f'{self._timestamp()} Arquivos enviados: {", ".join(filenames)}\n'
                    else:
                        log_entry += f'{self._timestamp()} Request Body: {body_string}\n'

                if 'file' in result['response']:
                    log_entry += f'{self._timestamp()} Response: {result["response"]["file"][0]}\n\n'
                else:
                    log_entry += f'{self._timestamp()} Response: {result["response"]}\n\n'
                with open(log_filename, 'a') as log_file:
                    log_file.write(log_entry)
            except Exception as e:
                print(f'Não foi possível registrar logs {e.args}')

        return result

    # Auxiliares
    def save_file(self, retorno, file_path):
        '''
        Salva o conteúdo em bytes da resposta no caminho especificado.

        :param response: Resposta em bytes obtida do _handle_response.
        :param file_path: Caminho onde o arquivo será salvo.
        '''
        try:
            # Separar filename e binário caso seja dicionário
            if isinstance(retorno, dict):
                try:
                    filename, contents = retorno['response']['file'][0], retorno['response']['file'][1]
                except KeyError:
                    filename, contents = retorno['file'][0], retorno['file'][1]

            # Se path fornecido for um diretório, utilizar filename
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, filename)

            if isinstance(contents, bytes):
                directory = os.path.dirname(file_path)
                if directory:  # Apenas cria diretórios se o caminho não estiver vazio
                    os.makedirs(directory, exist_ok=True)
                with open(file_path, 'wb') as file:
                    file.write(contents)
                print(f"Resposta salva em: {file_path}")
            else:
                raise ValueError("A resposta fornecida não está em formato de bytes.")
        except Exception as e:
            print(f'Não foi possível salvar arquivo {e.args}')

    def download_url(self, url, file_path=''):
        '''
        Faz o download do conteúdo de uma URL pré-assinada e salva no caminho especificado.

        :param url: URL pré-assinada.
        :param save_path: Caminho onde o arquivo será salvo.
        '''
        if isinstance(url, dict):
            try:
                url = url['response']['urlPreAssinada']
            except KeyError:
                url = url['urlPreAssinada']

        # Se um diretório tiver sido passado em save_path
        if os.path.isdir(file_path) or file_path == '':
            # Parseia a URL e extrai os parâmetros da query
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # Recupera o parâmetro "response-content-disposition"
            disposition_list = query_params.get('response-content-disposition')
            if disposition_list:
                # Pega o primeiro valor (normalmente é único)
                disposition = unquote(disposition_list[0])
                # Utiliza regex para capturar o valor do filename
                match = re.search(r'filename="?([^";]+)"?', disposition)
                if match:
                    filename = match.group(1)
                    filename = filename.replace('/', '_').replace(r'\\', '_')
                    file_path = os.path.join(file_path, filename)
                else:
                    raise Exception('Filename não encontrado no content-disposition.')
            else:
                raise Exception('Parâmetro "response-content-disposition" não encontrado na URL.')

        chunk_size = 1024 * 1024 * 50  # 50 MB

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Levanta uma exceção para erros HTTP

            # Salva o conteúdo no arquivo especificado
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
            print(f"Resposta salva em: {file_path}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o conteúdo: {e}")

    def prepare_file_list(self, file_list):
        try:
            # Se for folder
            if not isinstance(file_list, (list, tuple)) and os.path.isdir(file_list):
                file_list = [os.path.normpath(file_list + '/' + x) for x in os.listdir(file_list)]

            return [("files", (os.path.basename(p), open(p, "rb"), "application/octet-stream")) for p in file_list]
        except Exception as e:
            print(f'Não foi possível preparar lista de arquivos {file_list} {e.args}')

    def prepare_month_list(self, mes_inicial, ano_inicial, quantidade_meses,
                           meses_estagio_mensal=[],
                           meses_unica_revisao=[]):
        '''
        Gera uma lista de dicionários a partir do mês inicial, ano inicial, quantidade_meses de meses,
        e dos vetores de meses_estagio_mensal e meses_unica_revisao.

        Regras:
        1. Todos os valores de meses_estagio_mensal devem estar em meses_unica_revisao;
           caso contrário, lança Exception.
        2. Para cada mês, a posição (começando em 1) é utilizada para definir os flags:
           - Se a posição estiver em meses_estagio_mensal, então 'multiplosEstagios' é False;
             caso contrário, True.
           - Se a posição estiver em meses_unica_revisao, então 'multiplasRevisoes' é False;
             caso contrário, True.

        O mês inicial e ano inicial são fornecidos separadamente.

        Exemplo:
            mes_inicial = 1
            ano_inicial = 2025
            quantidade_meses = 6
            meses_estagio_mensal = [4, 5]
            meses_unica_revisao = [2, 3, 4, 5, 6]

            Resultado:
                [{'ano': 2025, 'mes': '01', 'multiplosEstagios': True,  'multiplasRevisoes': True},
                 {'ano': 2025, 'mes': '02', 'multiplosEstagios': True,  'multiplasRevisoes': False},
                 {'ano': 2025, 'mes': '03', 'multiplosEstagios': True,  'multiplasRevisoes': False},
                 {'ano': 2025, 'mes': '04', 'multiplosEstagios': False, 'multiplasRevisoes': False},
                 {'ano': 2025, 'mes': '05', 'multiplosEstagios': False, 'multiplasRevisoes': False},
                 {'ano': 2025, 'mes': '06', 'multiplosEstagios': True,  'multiplasRevisoes': False}]
        '''
        # Validação: todos os meses de estagio mensal devem constar em unica revisao
        if not set(meses_estagio_mensal).issubset(set(meses_unica_revisao)):
            raise Exception("Todos os meses de 'meses_estagio_mensal' devem estar em 'meses_unica_revisao'")

        # Cria um objeto de data inicial
        data_inicial = datetime(ano_inicial, mes_inicial, 1)

        resultado = []
        for i in range(quantidade_meses):
            # Calcula a data corrente adicionando i meses à data inicial
            data_atual = data_inicial + relativedelta(months=i)

            # Define os flags de acordo com as regras:
            multiplos_estagios = False if (i + 1) in meses_estagio_mensal else True
            multiplas_revisoes = False if (i + 1) in meses_unica_revisao else True

            # Append resultado
            resultado.append({'ano': data_atual.year,
                              'mes': f"{data_atual.month:02}",
                              'multiplosEstagios': multiplos_estagios,
                              'multiplasRevisoes': multiplas_revisoes})

        return resultado

    # Requests pré-feitas
    def get_deck_id(self, id_estudo, nome_deck):
        ''' Obter id do deck baseado no id do estudo e nome do deck '''
        decks_do_estudo = self.get(endpoint=f'/api/Estudos/Info/Deck/{id_estudo}')['response']
        for deck in decks_do_estudo:
            if deck['nome'] == nome_deck:
                return deck['id']

        print(f'Não foi possível encontrar o deck com nome "{nome_deck}" no estudo com ID {id_estudo}')
        return None


if __name__ == '__main__':
    api = ProspecAPI()