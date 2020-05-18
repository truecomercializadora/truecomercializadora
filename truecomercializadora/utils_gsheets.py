from oauth2client.service_account import ServiceAccountCredentials
import datetime
import gspread

def _get_spreadsheets_client():
  """
  Returns an authenticated Google Spreadsheets client using the credentials stored in data
  """
  scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
  creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
  return gspread.authorize(creds)


def _get_worksheet(worksheet_name, worksheet_tab):
  """
  Returns an authenticated Spreadsheet Tab. Capable of reading or updating cells and ranges.
  """
  client = _get_spreadsheets_client()
  return client.open(worksheet_name).worksheet(worksheet_tab)


def _get_initial_timestamp():
  return datetime.datetime(1899,12,29,23,53,32,1).timestamp()

def clear_range(worksheet_name, worksheet_tab, worksheet_range):
  """
  Clear an especific range. The range notation should respect the "A#:C#' notation.
  E.g "A1:C10".
  """
  
  worksheet = _get_worksheet(worksheet_name, worksheet_tab)
  cell_list = worksheet.range(worksheet_range)
  
  for i,cell in enumerate(cell_list):
    cell.value = ''

  # Update in batch
  return worksheet.update_cells(cell_list)


def get_timestamp(datetime_value):
  initial_timestamp = _get_initial_timestamp()
  input_timestamp = datetime_value.timestamp()
  return round((input_timestamp - initial_timestamp)/86400,10)


def update_cell(worksheet_name, worksheet_tab, worksheet_cell, value):
  """
  Updates an especific cell. The cell notation should respect the "LETTER#' notation. E.g "A2"
  """
  worksheet = _get_worksheet(worksheet_name, worksheet_tab)
  return worksheet.update_acell(worksheet_cell, value)


def update_range(worksheet_name, worksheet_tab, worksheet_range, values_df):
  """
  Update an especific range. The range notation should respect the "A#:C#' notation.
  E.g "A1:C10".
  Values should be a pandas DataFrame matching the dimension of the input range.
  The range will be updated in a single batch operation.
  """
  values = values_df.values.flatten().tolist()
  
  worksheet = _get_worksheet(worksheet_name, worksheet_tab)
  cell_list = worksheet.range(worksheet_range)
  
  if len(cell_list) != len(values):
    raise Exception(''''update_cells' should receive a dataframe matching the dimension of selected range {}.
    {} has {} values while the values DataFrame has {}.
    '''.format(worksheet_range, worksheet_range, len(cell_list), len(values)))
  
  for i,cell in enumerate(cell_list):
    cell.value = values[i]

  # Update in batch
  return worksheet.update_cells(cell_list)


def get_workheet_records(worksheet_name, worksheet_tab):
  """
  Returns the content within a Google Spreadsheets available within Google Drive, with allowed
  access given to the library's authenticated client email
  """
  client = _get_spreadsheets_client()
  return client.open(worksheet_name).worksheet(worksheet_tab).get_all_records()
