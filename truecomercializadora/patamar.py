"""
Modulo desenhado para conter as classes e funcoes relacionadas ao arquivo patamar
"""

def get_numero_patamares(patamar_str: str) -> int:
    """
    Retorna o inteiro correspondente ao numero de patamares definido
     no arquivo 
    """
    if type(patamar_str) != str:
        raise Exception("'get_numero_patamares' can only receive a string."
                        "{} is not a valid input type".format(type(patamar_str)))

    if ' NUMERO DE PATAMARES' not in patamar_str:
        raise Exception("Input string does not seem to represent a sistema.dat "
                        "string. Check the input")

   
    # Obtendo os patamares com o pressuposto dele estar na terceira linha
    #  do documento
    return int(patamar_str.splitlines()[2].strip())