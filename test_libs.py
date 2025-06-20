import cantools
from typing import Union, List, Dict
import cantools.database
import os
from datetime import datetime
import pprint

def read_dbc(file_path: Union[str, List]) -> Union[cantools.database.can.database.Database, Dict]:
    try:
        if isinstance(file_path, str):
            return cantools.database.load_file(file_path)
        else:
            result = {}
            for file in file_path:
                try:
                    key = os.path.basename(file)
                    db = cantools.database.load_file(file)
                    result[key] = db
                except Exception as e:
                    print(f"Error loading {file}: {e}")
                    continue
            return result
    except Exception as e:
        return f"Error: {e}"

def getEcu(df_dbc: Union[cantools.database.can.database.Database, Dict]) -> List:
    try:
        if isinstance(df_dbc, cantools.database.can.database.Database):
            return [node.name for node in df_dbc.nodes]
        else:
            lst = []
            for value in df_dbc.values():
                lst.extend([node.name for node in value.nodes])
            return lst
    except Exception as e:    
        return f"Error: {e}"

def getBus(df_dbc: Union[cantools.database.can.database.Database, Dict]) -> List:
    try:
        if isinstance(df_dbc, cantools.database.can.database.Database):
            return df_dbc.buses
        else:
            lst = []
            for _, value in df_dbc.items():
                lst.append(value.buses)
            return lst
    except Exception as e:    
        return f"Error: {e}"

def getMessages(df_dbc: Union[cantools.database.can.database.Database, Dict]) -> List:
    try:
        lst = []
        if isinstance(df_dbc, cantools.database.can.database.Database):
            for message in df_dbc.messages:
                lst.append(message.name)
            return lst
        else:
            for _, value in df_dbc.items():
                for message in value.messages:
                    lst.append(message.name)
            return lst
    except Exception as e:
        return f"Error: {e}"
    
def getSignalsDetailed(df_dbc: Union[cantools.database.can.database.Database, Dict]) -> Dict:
    try:
        def signal_to_dict(signal):
            return {
                'name': signal.name,
                'start_bit': signal.start,
                'length': f"{signal.length} bit",
                'scale': signal.scale,
                'offset': signal.offset,
                'unit': signal.unit,
                'is_signed': signal.is_signed,
                'recievers': signal.receivers,
                'byte order': signal.byte_order,
                'max': signal.maximum,
                'min': signal.minimum,
                'init': signal.raw_initial if signal.raw_initial != None else 0,
                'invalid': signal.raw_invalid,
                'description': signal.comment
            }

        if isinstance(df_dbc, cantools.database.can.database.Database):
            result = {}
            for message in df_dbc.messages:
                result[message.name] = [signal_to_dict(signal) for signal in message.signals]
            return result
        else:
            result = {}
            for filename, dbc_data in df_dbc.items():
                result[filename] = {}
                for message in dbc_data.messages:
                    result[filename][message.name] = [signal_to_dict(signal) for signal in message.signals]
            return result
            
    except Exception as e:
        return f"Error: {e}"

def addMessage(df_dbc: cantools.database.can.database.Database, 
               name: str, 
               message_id: int, 
               length: int, 
               signals: list = None,
               is_extended_frame: bool = False,
               comment: str = None,
               file_path: str = 'New_file'):
    try:
        if isinstance(message_id, str):
            if message_id.startswith('0x'):
                message_id_int = int(message_id, 16)
            else:
                message_id_int = int(message_id)
        else:
            message_id_int = message_id
        
        message = cantools.database.can.Message(
            frame_id=message_id_int,
            name=name,
            length=length,
            signals=signals if signals else [],
            is_extended_frame=is_extended_frame,
            comment=comment
        )
        if isinstance(df_dbc, cantools.database.can.database.Database):
            df_dbc.messages.append(message)
        
        if isinstance(df_dbc, Dict):
            for key in  df_dbc.keys():
                df_dbc[key].messages.append(message)
        
        cantools.database.dump_file(df_dbc, f"{file_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dbc")
        return df_dbc
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    path1 = "C:\\Users\\StepanErshov\\Downloads\\ATOM_CANFD_Matrix_SGW-CGW_V5.0.0_20250123.dbc"
    path = ["C:\\Users\\StepanErshov\\Downloads\\ATOM_CANFD_Matrix_SGW-CGW_V5.0.0_20250123.dbc", "C:\\Users\\StepanErshov\\Downloads\\ATOM_CANFD_Matrix_ET_V5.0.0_20250318.dbc"]
    dbc_data = read_dbc(path)
    dbc_nodes = getEcu(dbc_data)
    dbc_buses = getBus(dbc_data)
    messages = getMessages(dbc_data)
    signals = getSignalsDetailed(dbc_data)
    y = addMessage(dbc_data, "Hui", 0x1, 8,)
    return y


if __name__ == "__main__":
    x = main()
    print(x)