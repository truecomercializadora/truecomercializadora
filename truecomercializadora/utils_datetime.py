import datetime

def subtract_one_month(dt0):
    """
    # ============================================================================================ #
    #    Subtract one month from a datetime.date input reference                                   #
    # ============================================================================================ #
    """
    if type(dt0) != datetime.date:
        raise Exception("'subtract_one_month' should receive a 'datetime.date' value. {} is not a valid input".format(dt0))
    
    current_day = dt0.day
    dt1 = dt0.replace(day=1)
    dt2 = dt1 - datetime.timedelta(days=1)
    dt3 = dt2.replace(day=current_day)
    return dt3

def add_one_month(dt0):
    """
    # ============================================================================================ #
    #    Add one month from a datetime.date input reference                                        #
    # ============================================================================================ #
    """
    if type(dt0) != datetime.date:
        raise Exception("'add_one_month' should receive a 'datetime.date' value. {} is not a valid input".format(dt0))
    
    current_day = dt0.day
    dt1 = dt0.replace(day=1)
    dt2 = dt1 + datetime.timedelta(days=32)
    dt3 = dt2.replace(day=current_day)
    return dt3

def yield_all_saturdays(year):
    """
    # ============================================================================================ #
    #    Yield a iterable generator of all saturdays in a year                                     #
    # ============================================================================================ #
    """
    d = datetime.date(year, 1, 1)                    # January 1st
    d += datetime.timedelta(days = (5 - d.weekday() + 7) % 7)  # First Saturday
    while d.year == year:
        yield d
        d += datetime.timedelta(days = 7)

def get_list_of_dates_between_days(begin_datetime, final_datetime, deltaIncrement=None):
    """
    # ============================================================================================ #
    # Return a list of dates between two days. Use delta increment do create a list skiping        #
    # a specific number os days between days, exemple: produce a list of every two days between    #
    # the first and last day of the month                                                          #
    # ============================================================================================ #
    """
    if not deltaIncrement:
        delta = final_datetime - begin_datetime         # Delta days
        list_of_dates = []
        
        for i in range(delta.days + 1):
            date_value = begin_datetime + datetime.timedelta(i)
            list_of_dates.append(date_value)

        return list_of_dates

    list_of_dates = []
    aux_date = final_datetime
    while aux_date >= begin_datetime:
        list_of_dates.append(aux_date)
        aux_date -= datetime.timedelta(deltaIncrement)

    list_of_dates.reverse()
    return list_of_dates 


def count_days_in_month(datetime_list, month):
    """
    # ============================================================================================ #
    #  Count de number of days within a list of dates that belong to a certain month               #
    # ============================================================================================ #
    """
    if type(month) != int:
        raise Exception("'count_days_in_month' should receive an integer between 1 and 12")
    
    if type(datetime_list) != list:
        raise Exception("'count_days_in_month' should receive a list")
        
    if not all(isinstance(x, datetime.date) for x in datetime_list):
        raise Exception("'count_days_in_month' should receive a list of 'datetime.date' variables")
    
    return len([day for day in datetime_list if day.month == month])


def get_br_abreviated_month_number(abreviated_month):
    """
    # ============================================================================================ #
    #  Return the integer representing the abreviated month. A common necessity when reading rows  #
    #  out of spreadsheets where months are represented in an abreviated way                       #
    # ============================================================================================ #
    """
    if type(abreviated_month) != str:
        raise Exception("'get_abreviated_month_number' can only receive str variable. {} is not a valid string.".format(abreviated_month))
        
    if len(abreviated_month) != 3:
        raise Exception("'get_abreviated_month_number' can only receive a month with string size equals 3. E.g 'jan', 'fev', 'mar'. '{}' is not a valid format.".format(abreviated_month))
    
    abreviated_month = abreviated_month.lower()
    switcher = {
        'jan': 1,
        'fev': 2,
        'mar': 3,
        'abr': 4,
        'mai': 5,
        'jun': 6,
        'jul': 7,
        'ago': 8,
        'set': 9,
        'out': 10,
        'nov': 11,
        'dez': 12
    }
    return switcher.get(abreviated_month, '{} is not a valid abreviated month'.format(abreviated_month))

def get_br_abreviated_month(month_number):
    """
    # ============================================================================================ #
    #  Return the abreviated month string based on the month number.                               #
    # ============================================================================================ #
    """
    if type(month_number) != int:
        raise Exception("'get_br_abreviated_month' can only receive an int variable. '{}' is not a valid integer.".format(month_number))
        
    if month_number not in list(range(1,13)):
        raise Exception("'get_br_abreviated_month' can only receive an integer within the 1,...,12. '{}' is not number.".format(month_number))
    switcher = {
        1: 'jan',
        2: 'fev',
        3: 'mar',
        4: 'abr',
        5: 'mai',
        6: 'jun',
        7: 'jul',
        8: 'ago',
        9: 'set',
        10: 'out',
        11: 'nov',
        12: 'dez'
    }
    return switcher.get(month_number, '{} is not a valid month'.format(month_number))
