from unittest import TestCase

import datetime

from truecomercializadora import decomp


# ============================================================================================ #
#    get_estagios()                                                                            #
# ============================================================================================ #
def test_get_estagios():
    meses = range(1,13)
    anos = [datetime.datetime.today().year, datetime.datetime.today().year + 1]
    for mes in meses:
        for ano in anos:
            estagios = decomp.get_estagios(ano,mes)
            for estagio in estagios:
                inicio = estagio['inicio']
                fim = estagio['fim']
                delta = fim - inicio
                assert delta.days > 0
