import json
import os

LOOKUP_TABLES_DIR = "qrg_to_mode_tables"

def get_mode_from_qrg(qrg_lookup_table_name: str, qrg: int):
    """
    Resolve mode for given QRG and selected lookup table.
    If no range for qrg is found, return None.
    """
    lookup_table_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        LOOKUP_TABLES_DIR,
        f"{qrg_lookup_table_name}.json",
    )
    
    if not os.path.exists(lookup_table_file_path):
        raise QRGLookupTableDoesNotExist(
            f"requested QRG lookup table '{qrg_lookup_table_name}' does not exist"
        )
    
    resolved_mode = None
    with open(lookup_table_file_path) as f:
        ranges = json.load(f)
        
        if type(ranges) is not list:
            raise QRGLookupTableInvalid(
                "lookup table should be a json array"
            )
        
        for range_item in ranges:
            freq_from = range_item.get("freq_from")
            freq_to = range_item.get("freq_to")
            mode = range_item.get("mode")
            
            if not freq_from or not freq_to or not mode:
                raise QRGLookupTableInvalid(
                    "some of the lookup table ranges is not valid"
                )
            
            if freq_from > freq_to:
                raise QRGLookupTableInvalid(
                    "some of the lookup table ranges has start freq greater than end freq"
                )
            
            if freq_from <= qrg < freq_to:
                resolved_mode = mode
                break
        
    return resolved_mode
    
class QRGLookupTableDoesNotExist(BaseException):
    pass

class QRGLookupTableInvalid(BaseException):
    pass