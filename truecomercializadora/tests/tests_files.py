from unittest import TestCase

from truecomercializadora import utils_files

def test_select_document_part():
    document = 'Esse é um documento padrão\nEstou procurando o que APARTIR DAQUI\nO que pode ser bastante coisa, ou quase nada depende bastante do documento\nATE AQUI'
    s = utils_files.select_document_part(document,'APARTIR DAQUI', 'ATE AQUI')
    assert isinstance(s, str)