import datetime

from unittest import TestCase

from truecomercializadora import utils_datetime

# ============================================================================================ #
#    count_days_in_month                                                                       #
# ============================================================================================ #
def test_count_days_in_month():
    lista_datas = [datetime.date(2020,3,1), datetime.date(2020,3,2)]
    count = utils_datetime.count_days_in_month(lista_datas, 3)
    assert isinstance(count, int)

def test_count_days_in_monthA():
    lista_datas = [datetime.date(2020,3,1), datetime.date(2020,3,2)]
    count = utils_datetime.count_days_in_month(lista_datas, 3)
    assert count == 2

def test_count_days_in_monthB():
    lista_datas = [datetime.date(2020,2,29), datetime.date(2020,3,1), datetime.date(2020,3,2)]
    count = utils_datetime.count_days_in_month(lista_datas, 3)
    assert count == 2


# ============================================================================================ #
#    subtract_one_month                                                                        #
# ============================================================================================ #
def test_subtract_one_month():
    dt0 = datetime.date(2020,3,1)
    dt_teste = utils_datetime.subtract_one_month(dt0)

    assert isinstance(dt_teste, datetime.date)

def test_subtract_one_monthA():
    dt0 = datetime.date(2020,3,1)
    dt1 = datetime.date(2020,2,1)

    dt_teste = utils_datetime.subtract_one_month(dt0)

    assert dt1 == dt_teste

def test_subtract_one_monthB():
    dt0 = datetime.date(2020,3,10)
    dt1 = datetime.date(2020,2,10)

    dt_teste = utils_datetime.subtract_one_month(dt0)

    assert dt1 == dt_teste

# ============================================================================================ #
#    add_one_month                                                                             #
# ============================================================================================ #
def test_add_one_month():
    dt0 = datetime.date(2020,3,1)
    dt_teste = utils_datetime.add_one_month(dt0)

    assert isinstance(dt_teste, datetime.date)

def test_add_one_monthA():
    dt0 = datetime.date(2020,3,1)
    dt1 = datetime.date(2020,4,1)

    dt_teste = utils_datetime.add_one_month(dt0)

    assert dt1 == dt_teste

def test_add_one_monthB():
    dt0 = datetime.date(2020,3,13)
    dt1 = datetime.date(2020,4,13)

    dt_teste = utils_datetime.add_one_month(dt0)

    assert dt1 == dt_teste

# ============================================================================================ #
#    get_br_abreviated_month                                                                   #
# ============================================================================================ #
def test_get_br_abreviated_month():
    abreviated_month = utils_datetime.get_br_abreviated_month(3)

    assert abreviated_month == 'mar'

# ============================================================================================ #
#    get_br_abreviated_month_number                                                            #
# ============================================================================================ #
def test_get_br_abreviated_month_number():
    abreviated_month_number = utils_datetime.get_br_abreviated_month_number('abr')

    assert abreviated_month_number == 4