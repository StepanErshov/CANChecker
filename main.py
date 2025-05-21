import cantools 
import os
import logging
import cantools.database
import pandas as pd
from typing import Union, List
from pyvis.network import Network

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

logger = logging.getLogger(__name__)

def read_files(file_pathX: Union[str, List[str]]) -> List[List]:   
    if os.path.splitext(file_pathX)[1] == ".dbc":
        db = cantools.database.load_file(file_pathX)
        return db
    elif os.path.splitext(file_pathX)[1] == ".xlsx":
        df = pd.read_excel(file_pathX, sheet_name="Matrix", keep_default_na=True, )
        return df

    

def checkSignalsMessages(dfx: pd.DataFrame, dfdbc: cantools.database.can.database.Database):
    messagesX = set(dfx["Msg Name\n报文名称"].tolist()) - {"nan"}
    messagesDBC = set([message.name for message in dfdbc.messages]) - {"nan"}

    different_messagesX = messagesX - messagesDBC
    different_messagesDBC = messagesDBC - messagesX
    
    logger.info("===CHECKING MESSAGES===")
    logger.info(f"xlsx - dbc (сообщения только в Excel) = {different_messagesX}")
    logger.info(f"dbc - xlsx (сообщения только в DBC) = {different_messagesDBC}")

    signalsX = set(dfx["Signal Name\n信号名称"].tolist()) - {"nan"}
    signalsDBC = set()
    for message in dfdbc.messages:
        signalsDBC.update(signal.name for signal in message.signals)

    different_signalsX = signalsX - signalsDBC
    different_signalsDBC = signalsDBC - signalsX

    logger.info("===CHECKING SIGNALS===")
    logger.info(f"xlsx - dbc (сигналы только в Excel) = {different_signalsX}")
    logger.info(f"dbc - xlsx (сигналы только в DBC) = {different_signalsDBC}")
    
def createGraph(dfdbc: cantools.database.can.database.Database):
    messagesDBC = set([message.name for message in dfdbc.messages])
    signalsDBC = set()
    for message in dfdbc.messages:
        signalsDBC.update(signal.name for signal in message.signals)

    net = Network(height="1000px", width="100%", heading="CAN Network Visualization")
    
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "UD",
                "sortMethod": "directed",
                "nodeSpacing": 400,
                "levelSeparation": 400
            }
        },
        "physics": {
            "hierarchicalRepulsion": {
                "centralGravity": 0,
                "nodeDistance": 400,
                "springLength": 400
            },
            "minVelocity": 0.75,
            "solver": "hierarchicalRepulsion"
        },
        "nodes": {
            "margin": 20,
            "font": {
                "size": 14,
                "face": "arial"
            }
        },
        "edges": {
            "length": 500
        }
    }
    """)
    
    net.add_node(0, label="CAN Network", level=0, color="#862633", 
                title="Root node of CAN bus messages", size=30)
    
    for i, message in enumerate(dfdbc.messages, start=1):
        info = f"""
        Name message: {message.name}
        Sender: {message.senders}
        Recievers: {message.receivers}
        Send type: {message.send_type}
        Cycle type: {message.cycle_time}
        ID: 0x{message.frame_id:X}
        Length: {message.length} bytes
        Signals: {len(message.signals)}
        """
        net.add_node(i, 
                    label=message.name,
                    level=1,
                    title=info,
                    color="#4285F4",
                    size=10)

    for i in range(1, len(dfdbc.messages)+1):
        net.add_edge(0, i, length=500)
    
    return net




if __name__ == "__main__":
    pathX = "C:\\Users\\79245\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.xlsx"
    pathDBC =  "C:\\Users\\79245\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.dbc"
    dfX = read_files(pathX)
    dfDBC = read_files(pathDBC)
    net = createGraph(dfDBC)
    net.show("graph.html", notebook=False)
    checkSignalsMessages(dfX, dfDBC)
