import cantools
import os
import logging
import cantools.database
import pandas as pd
from typing import Union, List
from pyvis.network import Network

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

logger = logging.getLogger(__name__)


def read_files(file_pathX: Union[str, List[str]]) -> List[List]:
    if os.path.splitext(file_pathX)[1] == ".dbc":
        db = cantools.database.load_file(file_pathX)
        return db
    elif os.path.splitext(file_pathX)[1] == ".xlsx":
        df = pd.read_excel(file_pathX, sheet_name="Matrix", keep_default_na=True)
        return df


def checkSignalsMessages(
    dfx: pd.DataFrame, dfdbc: cantools.database.can.database.Database
):
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
    net = Network(height="1000px", width="100%", heading="CAN Network Visualization")

    net.set_options(
        """
    {
        "configure": {
            "enabled": true
        },
        "nodes": {
            "font": {
                "size": 12
            }
        }
    }
    """
    )

    net.add_node(
        "CAN_Network",
        label="CAN Network",
        level=0,
        color="#862633",
        title="Root node of CAN bus messages",
        size=25,
    )

    message_counter = 0
    signal_counter = 10000

    for message in dfdbc.messages:
        message_counter += 1
        message_id = f"msg_{message_counter}"
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

        net.add_node(
            message_id,
            label=message.name,
            level=1,
            title=info,
            color="#4285F4",
            size=15,
        )

        net.add_edge("CAN_Network", message_id)

        def format_choices(choices):
            if not choices:
                return "None"
            return "".join([f"0x{int(k):X}: {v} " for k, v in choices.items()])

        for signal in message.signals:
            signal_counter += 1
            signal_id = f"sig_{signal_counter}"
            choices_str = format_choices(
                signal.choices if hasattr(signal, "choices") else None
            )
            info = f"""
                Name signal: {signal.name}
                Recievers: {signal.receivers}
                Byte order: {signal.byte_order}
                Cycle type: {message.cycle_time}
                Start bit: {signal.start}
                Min value: {signal.minimum}
                Max value: {signal.maximum}
                Signal Value Description: {choices_str}
                Initianal value: {signal.raw_initial if signal.raw_initial != None else 0}
                Invalid value: {signal.raw_invalid}
                Scale: {signal.scale}
                Offset: {signal.offset}
                Description: {signal.comment}
                Lenght: {signal.length} bit
                Unit: {signal.unit}
                """

            net.add_node(
                signal_id,
                label=signal.name,
                level=2,
                title=info,
                color="#34A853",
                size=10,
            )

            net.add_edge(message_id, signal_id)

    html = net.generate_html()

    js_code = """
    <div style="position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 5px; border-radius: 5px;">
        <button onclick="changeLayout('UD')">Vertical (Top-Down)</button>
        <button onclick="changeLayout('LR')">Horizontal (Left-Right)</button>
        <button onclick="changeLayout('DU')">Vertical (Down-Up)</button>
        <button onclick="changeLayout('RL')">Horizontal (Right-Left)</button>
    </div>
    
    <script>
    function changeLayout(direction) {
        network.setOptions({
            layout: {
                hierarchical: {
                    direction: direction
                }
            }
        });
    }
    </script>
    """

    html = html.replace("</body>", js_code + "</body>")

    with open("graph.html", "w", encoding="utf-8") as f:
        f.write(html)

    return net


if __name__ == "__main__":
    pathX = "C:\\Users\\79245\\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.xlsx"
    pathDBC = "C:\\Users\\79245\\Desktop\\Files ATOM\\CAN Matrix\\1. Body Domain\\Domain Matrix\\7.0.0\\ATOM_CAN_Matrix_BD_V7.0.0_20250208.dbc"
    dfX = read_files(pathX)
    dfDBC = read_files(pathDBC)
    net = createGraph(dfDBC)
    net.show(name="graph.html", notebook=False)
    checkSignalsMessages(dfX, dfDBC)
