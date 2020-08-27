def safe_replace(input_str:str, match_str:str , replace_str: str) -> str:
    '''
    Safely replaces all ocurrences of a certain criteria. In case no
     criteria is matched, thus no replace happens, the functions raises an exception.
    '''
    
    output_str = input_str.replace(match_str, replace_str)
    
    if input_str == output_str:
        raise Exception('Input string was not changed by replace. No match_str found.')
        
    return output_str