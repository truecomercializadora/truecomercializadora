
"""
A module designed to keep functions regarding all sorts of files, from a -
 general perspective. Therefore, no business knowledge should be required
 in order to understand any of the functions defined here.
"""
import base64
import io
import os
import re
import zipfile as zp


def build_zipfile_from_bytesarray(bytes_array):
    """
    Return a zipfile.Zipfile class from a zipfile bytes array. Common when
    getting zipfiles from the requests
    """
    return zp.ZipFile(io.BytesIO(bytes_array), "r")

def update_zipfile(original_zip, update_path, content_bytes):
    """
    Returns an updated zipfile archive represented by its bytes array. The 
     function actually rebuilds the entire zip archive, leaving untouched every
     file except the one explicitly said to be edited.
    The function should receive a zipfile.ZipFile object, the path within the
     zipfile to be updated, and the bytes content of the the desired update.
    """

    if type(original_zip) != zp.ZipFile:
        raise Exception("'update_zipfile' should receive a zipfile.Zipfile as\
            primary input. {} is not a valid input type.".format(original_zip))

    if update_path not in original_zip.namelist():
        raise Exception("{} could not be found inside the zipfile.".format(update_path))

    if type(content_bytes) != bytes:
        raise Exception("'update_zipfile' should receive a bytes input do up-\
            date the desired file. {} is not a valid input type.".format(type(content_bytes)))

    # Initialize a buffer for the new zipfile
    buff = io.BytesIO()
    with zp.ZipFile(buff, mode="w",compression=zp.ZIP_DEFLATED) as zipwrite:
        
        # Iterate over all files within the original zipfile
        for file_name in original_zip.namelist():
            file_bytes = original_zip.read(file_name)

            # Update only the desired file
            if file_name == update_path:
                zipwrite.writestr(file_name, content_bytes)
            else:
                zipwrite.writestr(file_name, file_bytes)

    # Return a bytes array (which could be )
    return buff.getvalue()


def save_bytes2zipfile(output_path, zipfile_bytes):
    """
    Saves a zipfile content (bytes array) into a zipfile archive. The
     function must receive a valid zip path as well as a valid bytes content.
    """
    if (os.path.isdir(os.path.split(output_path)[0]) == False) or \
        (os.path.split(output_path)[1].split('.')[-1] != 'zip'):
            raise Exception("'save_bytes2zipfile' should receive a valid output \
                path. {} is not valid zipfile path.".format(type(output_path)))
            
    if type(zp.ZipFile(io.BytesIO(zipfile_bytes), "r")) != zp.ZipFile:
        raise Exception("'save_bytes2zipfile' should be able to construct a \
            valid zipfile.ZipFile object from zipfile_bytes. zipfile_bytes  \
            does not contain a valid zipfile.")

    # Saving the contents into an output file     
    with open(output_path, 'wb') as f:
        f.write(zipfile_bytes)
    
    return output_path


def find_all_occurences_of_substring(document, substring):
    """
    Return a list of all indexes where a substring occur in a document
    This function can be usefull when slicing a big document based on two sub-
    strings.
    """
    if type(document) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive \
            strings. {} is not a valid string to be search.".format(document))

    if type(substring) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive \
            strings. {} is not a valid substring to be found.".format(substring))

    if substring not in document:
        raise Exception("{}... not found in string".format(substring))


    return [m.start() for m in re.finditer(substring, document)]


def select_document_part(document, substring_begin, substring_end):
    """
    Return the string sliced based on two substrings contained within the
     document.
    This function can be usefull when slicing a big document based on two
     substrings
    """
    if type(document) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid string to be search.".format(document))

    if type(substring_begin) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid substring to be the starting index of the search.".format(substring_begin))

    if type(substring_end) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid substring to be the ending index of the search.".format(substring_end))

    if substring_begin not in document:
        raise Exception("The begin reference {} could not found in the document".format(substring_begin))

    if substring_end not in document:
        raise Exception("The ending reference {} could not found in the document".format(substring_end))


    match_begin = find_all_occurences_of_substring(document, substring_begin)[0]
    match_stop = [ocurrence for ocurrence in find_all_occurences_of_substring(document, substring_end) if ocurrence > match_begin][0]

    return document[match_begin:match_stop]

def select_document_parts(document, substring_begin, substring_end):
    """
    Return a list of strings sliced based on two substrings contained within the document.
    This function can be usefull when performing multiple slices of a big document based on
    a substring selection.
    """
    if type(document) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid string to be search.".format(document))

    if type(substring_begin) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid substring to be the starting index of the search.".format(substring_begin))

    if type(substring_end) != str:
        raise Exception("'find_all_occurences_of_substring' can only receive strings. {} is not a valid substring to be the ending index of the search.".format(substring_end))

    if substring_begin not in document:
        raise Exception("The begin reference {} could not found in the document".format(substring_begin))

    if substring_end not in document:
        raise Exception("The ending reference {} could not found in the document".format(substring_end))

    beginnings  = find_all_occurences_of_substring(document, substring_begin)
    ends = find_all_occurences_of_substring(document, substring_end)

    L = []
    for beginning_idx in beginnings:
        ending_idx = [end for end in ends if end > beginning_idx][0]
        L.append(document[beginning_idx:ending_idx])
    return L


def replace_ocurrences_in_string(pattern_dict, string):
    """
    Return a string after the replacement of occurences specified in
    the pattern dictionary.
    The input dictionary should contain only strings:
    {
        'first_pattern': 'first_replace',
        ...
        'n_pattern': 'n_replace'
    }
    """
    if type(pattern_dict) != dict:
        raise Exception("'replace_ocurrences_in_string' should receive a dict of patterns. {} is not a valid input.".format(pattern_dict))
        
    if type(string) != str:
        raise Exception("'replace_ocurrences_in_string' should receive a string. {} is not a valid input.".format(string))
        
    rep = dict((re.escape(k), v) for k, v in pattern_dict.items())
    pattern = re.compile("|".join(rep.keys()))
    return pattern.sub(lambda m: rep[re.escape(m.group(0))], string)

def encode_fileReader_zip(zipfile_path):
    """
    When performing a file read using JavaScript it is common to build the
     read file into a buffer and then to a specifig string format. So that it
     could be sent through an API request. 
    This functions allows a zipfile to be encoded just as it would be done by
     JavaScript FileReader Class. Use it in order to test and prototype. And
     remember it only works if receving a zipfile.ZipFile object
    """
    if not os.path.isfile(zipfile_path):
        raise Exception("'encode_fileReader_zip' should receive a valid input \
            path. {} is not valid.".format(type(zipfile_path)))

    if type(zp.ZipFile(zipfile_path)) != zp.ZipFile:
        raise Exception("'encode_fileReader_zip' should be able to construct a \
            valid zipfile.ZipFile object from input. {} does not seem to be a \
            valid zipfile.".format(type(zipfile_path)))

    # Open local zipfile and encode to b64
    with open(zipfile_path, "rb") as f:
        b64zip_bytes = base64.b64encode(f.read())
    # Decode b64bytes to a string
    b64zip_str = b64zip_bytes.decode('latin-1')
    # Concatenate fileReader zipfile message to string
    return 'data:application/zip;base64,' + b64zip_str

def decode_fileReader_zip(fileReader_str):
    """
    When performing a file read using JavaScript it is common to build the
     read file into a buffer and then to a specifig string format. So that it
     could be sent through an API request. 
    This function allows a zipfile in string format to be decoded. Which could 
     be later used to build a zipfile.ZipFile. Use it in order to test and keep
     in mind that fileReader_str should be complient with JavaScript FileReader
     format. I.e:
     'data:application/zip;base64...'
    """

    if ('data:application/zip;base64' not in fileReader_str):
        raise Exception("'decode_fileReader_zip' should receive an encoded file \
            complient to JavaScript FileReader format.")

    # Remove fileReader zipfile message from string
    b64zip_str = fileReader_str.replace('data:application/zip;base64,','')
    # Decode b64string back to a b64bytes
    b64zip_bytes = b64zip_str.encode('latin-1')
    # b64decode bytes back to zipfile bytes
    return base64.b64decode(b64zip_bytes)