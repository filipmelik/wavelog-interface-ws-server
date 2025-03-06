import logging
import requests

QRG_TABLE_URL_TEMPLATE = "https://raw.githubusercontent.com/filipmelik/wavelog-interface-ws-server/refs/heads/main/qrg_to_mode_tables/##TABLE_NAME##.json"

def get_mode_from_qrg(
    logger: logging.Logger,
    qrg_table_cache: dict,
    qrg_lookup_table_name: str,
    qrg: int
):
    """
    Resolve mode for given QRG and selected lookup table.
    If no range for qrg or the mapping table is found, return None.
    """
    cached_lookup_table = qrg_table_cache.get(qrg_lookup_table_name)
    if not cached_lookup_table:
        logger.debug(
            f"QRG mapping table with name {qrg_lookup_table_name} not found in cache."
        )
        fetched_table = fetch_qrg_lookup_table(logger=logger, table_name=qrg_lookup_table_name)
        qrg_table_cache[qrg_lookup_table_name] = fetched_table
        qrg_table = fetched_table
        logger.debug(
            f"QRG mapping table with name {qrg_lookup_table_name} saved into cache."
        )
    else:
        logger.debug(
            f"Using cached QRG mapping table with name {qrg_lookup_table_name}."
        )
        qrg_table = cached_lookup_table
    
    resolved_mode = None
    for range_item in qrg_table:
        freq_from = range_item.get("freq_from")
        freq_to = range_item.get("freq_to")
        mode = range_item.get("mode")
        
        if freq_from <= qrg < freq_to:
            resolved_mode = mode
            break
        
    return resolved_mode

def fetch_qrg_lookup_table(
    logger: logging.Logger,
    table_name: str,
):
    """
    Fetch the QRG lookup table with given name from the remote storage
    """
    logger.info(f"Fetching QRG mapping table with name {table_name}.")
    url = QRG_TABLE_URL_TEMPLATE.replace("##TABLE_NAME##", table_name)
    r = requests.get(url)
    
    if r.status_code == 200:
        ranges = r.json()
        
        # validate the table contents
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
            
        return ranges
        
    elif r.status_code == 404:
        raise QRGLookupTableDoesNotExist(
            f"requested QRG lookup table '{table_name}' does not exist"
        )
    else:
        raise Exception(
            f"unexpected status code '{r.status_code}' while fetching qrg lookup table"
        )
    
class QRGLookupTableDoesNotExist(BaseException):
    pass

class QRGLookupTableInvalid(BaseException):
    pass

class QRGLookupTableFetchFailed(BaseException):
    pass