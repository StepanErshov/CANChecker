import streamlit as st
import cantools
import tempfile
import os
import test_libs as tl
import pandas as pd
from pyvis.network import Network
from itertools import combinations


st.set_page_config(layout="wide", page_title="CAN Network Visualizer")

def read_dbc(uploaded_files):
    """Загрузка DBC-файлов из UploadedFile."""
    dbs = {}
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dbc") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        db = cantools.database.load_file(tmp_path)
        os.unlink(tmp_path)
        dbs[uploaded_file.name] = db
    return dbs

def create_graph(dbc_data: dict, highlight_common: bool):
    """Создание интерактивного графа для всех DBC."""
    net = Network(height="1000px", width="100%")
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

    # Collect message names per dbc
    dbc_msg_names = {}
    for name, db in dbc_data.items():
        dbc_msg_names[name] = set(msg.name for msg in db.messages)
    # Identify common messages present in all DBCs
    if dbc_msg_names:
        common_msgs = set.intersection(*dbc_msg_names.values())
    else:
        common_msgs = set()

    message_nodes = {}  # {(dbc_name, msg_name): node_id}

    for name, db in dbc_data.items():
        net.add_node(
            name,
            label=name.split(".")[0],
            level=0,
            color="#862633",
            title="Root node of CAN bus messages",
            size=25,
        )

        message_counter = 0
        signal_counter = 10000

        for message in db.messages:
            message_counter += 1
            message_id = f"msg_{message_counter}_{name}"
            message_nodes[(name, message.name)] = message_id

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

            net.add_edge(name, message_id)

            def format_choices(choices):
                if not choices:
                    return "None"
                return "".join([f"0x{int(k):X}: {v} " for k, v in choices.items()])

            for signal in message.signals:
                signal_counter += 1
                signal_id = f"sig_{signal_counter}_{name}"
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
                    color="#2DAC4F",
                    size=10,
                )

                net.add_edge(message_id, signal_id)

    if highlight_common:
        # Add distinct edges for common messages across all DBCs


        for common_msg in common_msgs:
            # collect node ids of this message in all DBCs
            nodes = [message_nodes[(dbc_name, common_msg)] for dbc_name in dbc_data.keys()]
            # create edges between message nodes of different DBCs with special color
            for node1, node2 in combinations(nodes, 2):
                net.add_edge(node1, node2, color='red', width=3, title='Common message across DBCs')

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

    net.save_graph("temp_graph.html")
    return open("temp_graph.html", "r", encoding="utf-8").read()

def main():
    st.title("📡 CAN Network Visualizer")
    uploaded_files = st.file_uploader("Выберите DBC-файлы", type=".dbc", accept_multiple_files=True)
    cols = st.columns(2)
    with cols[0]:
        check = st.checkbox("Отобразить граф")
    with cols[1]:
        highlight = st.checkbox("Подсвечивать общие сообщения красными связями", value=True)
    
    dbc_data = {}
    
    all_msg = []
    all_ecu = []

    if uploaded_files:
        try:
            dbc_data = read_dbc(uploaded_files)
            if check:
                html = create_graph(dbc_data, highlight)
                st.components.v1.html(html, height=1000, scrolling=True)

            st.subheader("Статистика")
            col1, col2 = st.columns(2)
            
            signals_data = []
            messages_data = []

            for name, db in dbc_data.items():
                for msg in db.messages:
                    messages_data.append({
                        'Message': msg.name,
                        'ID': f"0x{msg.frame_id:X}",
                        'Length': msg.length,
                        'Signals Count': len(msg.signals)
                    })
                    for sig in msg.signals:
                        signals_data.append({
                            'Signal': sig.name,
                            'Message': msg.name,
                            'Start Bit': sig.start,
                            'Length': sig.length
                        })
            
            signals_df = pd.DataFrame(signals_data)
            messages_df = pd.DataFrame(messages_data)
            
            col1.metric("Сообщений", len(messages_df))
            col1.dataframe(messages_df)
            
            col2.metric("Сигналов", signals_df.shape[0])
            col2.dataframe(signals_df)
            
            all_msg = tl.getMessages(dbc_data)
            all_ecu = tl.getEcu(dbc_data)

        except Exception as e:
            st.error(f"Ошибка загрузки файла: {e}")

    with st.form("DBC_form"):
        st.title("Добавление сообщений в файл")
        num_messages = st.number_input("Количество сообщений", min_value=1, max_value=20, value=1)

        messages = []
        for i in range(num_messages):
            st.subheader(f"Сообщение {i+1}")
            
            cols = st.columns(6)
            with cols[0]:
                msg_name = st.text_input(f"Имя сообщения {i+1}", key=f"msg_name_{i}")
                if msg_name:
                    if msg_name in all_msg:
                        st.error(f"Сообщение с именем '{msg_name}' уже существует!")
                        break
            with cols[1]:
                msg_id = st.text_input(f"ID {i+1} (hex)", value="0x", key=f"msg_id_{i}")
            with cols[2]:
                msg_len = st.number_input(f"Длина {i+1} (байт)", min_value=1, max_value=64, value=8, key=f"msg_len_{i}")
            with cols[3]:
                msg_ext = st.checkbox(f"Extended {i+1}", key=f"msg_ext_{i}")
            with cols[4]:
                msg_comment = st.text_input(f"Комментарий {i+1}", key=f"msg_comment_{i}")
            with cols[5]:
                msg_sender = st.selectbox("Выберете Sender", (all_ecu), key=f"msg_send_{i}")
            
            with st.expander(f"Добавить сигналы для сообщения {i+1}"):
                num_signals = st.number_input(f"Количество сигналов для сообщения {i+1}", min_value=0, max_value=50, value=0, key=f"num_sig_{i}")
                
                signals = []
                
                for j in range(num_signals):
                    st.markdown(f"**Сигнал {j+1}**")
                    sig_cols = st.columns(14)
                    with sig_cols[0]:
                        sig_name = st.text_input(f"Name siganl {i+1}-{j+1}", key=f"sig_name_{i}_{j}")
                    with sig_cols[1]:
                        sig_start = st.number_input(f"Start bit {i+1}-{j+1}", min_value=0, value=0, key=f"sig_start_{i}_{j}")
                    with sig_cols[2]:
                        sig_len = st.number_input(f"Length {i+1}-{j+1} (бит)", min_value=1, value=1, key=f"sig_len_{i}_{j}")
                    with sig_cols[3]:
                        sig_scale = st.number_input(f"Scale {i+1}-{j+1}", value=1.0, key=f"sig_scale_{i}_{j}")
                    with sig_cols[4]:
                        sig_offset = st.number_input(f"Offset {i+1}-{j+1}", value=0.0, key=f"sig_offset_{i}_{j}")
                    with sig_cols[5]:
                        sig_unit = st.text_input(f"Unit {i+1}-{j+1}", key=f"sig_unit_{i}_{j}")
                    with sig_cols[6]:
                        sig_is_signed = st.selectbox(f"Is signed? {i+1}-{j+1}", (True, False),  key=f"sig_signed_{i}_{j}")
                    with sig_cols[7]:
                        sig_receivers = st.multiselect(
                            "Receivers", 
                            options=[ecu for ecu in all_ecu if ecu != msg_sender],
                            key=f"sig_receivers_{i}_{j}"
                        )
                        if msg_sender in sig_receivers:
                            st.error("Получатель не может быть тем же ECU, что и отправитель!")

                    with sig_cols[8]:
                        sig_byte_order = st.selectbox(f"Byte order {i+1}-{j+1}", ("little_endian", "big_endian"), key=f"sig_byte_order_{i}_{j}")
                    with sig_cols[9]:
                        sig_max = st.number_input(f"Max value {i+1}-{j+1}", min_value=-100000, value=0, key=f"sig_max_{i}_{j}")
                    with sig_cols[10]:
                        sig_min = st.number_input(f"Min value {i+1}-{j+1}", min_value=-100000, value=0, key=f"sig_min_{i}_{j}")
                    with sig_cols[11]:
                        sig_init = st.number_input(f"Init value {i+1}-{j+1}", min_value=-100000, value=0, key=f"sig_init_{i}_{j}")
                    with sig_cols[12]:
                        sig_invalid = st.number_input(f"Invalid value {i+1}-{j+1}", min_value=-100000, value=0, key=f"sig_invalid_{i}_{j}")
                    with sig_cols[13]:
                        sig_deck = st.text_input(f"Description {i+1}-{j+1}", value="0x0: No request\n0x1: On\n0x2: Off", key=f"sig_deck_label_{i}_{j}")
                    
                    signals.append({
                        'name': sig_name,
                        'start_bit': sig_start,
                        'length': sig_len,
                        'scale': sig_scale,
                        'offset': sig_offset,
                        'unit': sig_unit,
                        'is_signed': sig_is_signed,
                        'recievers': sig_receivers,
                        'byte_order': sig_byte_order,
                        'max': sig_max,
                        'min':  sig_min,
                        'init': sig_init,
                        'invalid': sig_invalid,
                        'description': sig_deck
                    })
            
            messages.append({
                'name': msg_name,
                'id': msg_id,
                'length': msg_len,
                'extended': msg_ext,
                'comment': msg_comment,
                'sender': msg_sender,
                'signals': signals
            })
        
        if st.form_submit_button("Сохранить изменения"):
            st.success(f"Сохранено {num_messages} сообщений!")
            st.json(messages)
        
if __name__ == "__main__":
    main()

