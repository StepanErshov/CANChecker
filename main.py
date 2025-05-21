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

    net = Network()

    for i, message_name in enumerate(messagesDBC):
        net.add_node(i + 1, label=message_name)

    for i in range(1, len(messagesDBC)):
        net.add_edge(i, i + 1)

    return net





if __name__ == "__main__":
    pathX = "C:\\Users\\79245\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.xlsx"
    pathDBC =  "C:\\Users\\79245\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.dbc"
    dfX = read_files(pathX)
    dfDBC = read_files(pathDBC)
    net = createGraph(dfDBC)
    net.show("graph.html", notebook=False)
    checkSignalsMessages(dfX, dfDBC)
