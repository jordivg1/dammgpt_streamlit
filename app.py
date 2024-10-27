import streamlit as st
import openai
from openai import AzureOpenAI
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from streamlit_option_menu import option_menu
from streamlit_chat import message

# Función para obtener el secreto desde Azure Key Vault
def get_secret(secret_name):
    try:
        key_vault_name = st.secrets["KEY_VAULT_NAME"]
        KVUri = f"https://{key_vault_name}.vault.azure.net"

        credential = ClientSecretCredential(
            client_id=st.secrets["AZURE_CLIENT_ID"],
            client_secret=st.secrets["AZURE_CLIENT_SECRET"],
            tenant_id=st.secrets["AZURE_TENANT_ID"]
        )
        client = SecretClient(vault_url=KVUri, credential=credential)
        retrieved_secret = client.get_secret(secret_name)
        return retrieved_secret.value
    except KeyError as e:
        st.error(f"Clave faltante en los secretos: {e}")
        return None
    except Exception as e:
        st.error(f"Error al obtener el secreto: {e}")
        return None

# Obtener la clave de API de Azure OpenAI desde Key Vault
api_key = get_secret('dammgpt')

if not api_key:
    st.stop()

# Obtener el endpoint de Azure OpenAI desde los secretos
azure_openai_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]

# Configurar la API de OpenAI para Azure
openai.api_type = "azure"
openai.api_base = azure_openai_endpoint  # Asegúrate de que incluye 'https://'
openai.api_version = "2023-12-01-preview"
openai.api_key = api_key

# Aplicar estilos CSS personalizados (si tienes alguno)
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se encontró el archivo de estilos CSS.")

local_css("styles.css")  # Asegúrate de tener este archivo en tu repositorio

# Título con banner deportivo
st.markdown("""
    <div style="text-align: center; padding: 10px; background-color: #2c3e50;">
        <h1 style="color:#ffffff;"> ReFill ReTrain ReJoin </h1>
    </div>
    """, unsafe_allow_html=True)

# Menú de navegación horizontal
selected = option_menu(
    menu_title=None,  # Ocultar el título del menú
    options=["Leisure", "ReFill", "Chatbot"],
    icons=["🏖", "🛒", "🤖"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#2c3e50"},
        "icon": {"color": "#ffffff", "font-size": "25px"},
        "nav-link": {"font-size": "18px", "color": "#ffffff", "margin": "0px", "--hover-color": "#1abc9c"},
        "nav-link-selected": {"background-color": "#1abc9c"},
    }
)

choice = selected

# Puedes agregar esta línea para depurar y ver el valor de 'choice'
# st.write(f"Debug: choice is '{choice}'")

# Función para obtener la respuesta del modelo usando Azure OpenAI
def obtener_respuesta(messages, model='gpt4onennisi'):
    cliente = AzureOpenAI(
        azure_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"], 
        api_key=api_key,  
        api_version="2023-12-01-preview"
    )
    try:
        respuesta = cliente.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=150,
            tool_choice=None,
        )
        respuesta = respuesta.choices[0].message.content  # Extraer el contenido del mensaje
        return respuesta
    except Exception as e:
        st.error(f"Error al obtener la respuesta: {e}")
        print(f"Error detallado: {e}")  # Para registros adicionales
        return "Lo siento, hubo un error al procesar tu solicitud."

# Secciones de la aplicación
if choice == "Leisure":
    st.header("🏖 Leisure")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("estrella-damm.jpg", use_column_width=True)
    with col2:
        st.write("""
            ###
            - Deportes al aire libre
            - Gimnasio y fitness
            - Eventos deportivos
            - Festivales / Música
            - Cultura
            - Barcelona
        """)

elif choice == "ReFill":
    st.header("🛒 ReFill: Consulta los litros que quedan o faltan en tu subscripción")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
            ### Te quedan 10 litros este mes
        """)
    with col2:
        st.image("agua.jpg", use_column_width=True)

elif choice == "Chatbot":
    st.header("🤖 Coach GPT")

    # Crear una sesión para almacenar el historial del chat
    if 'historial' not in st.session_state:
        st.session_state['historial'] = []

    # Mostrar el historial del chat usando streamlit-chat con claves únicas
    for i, chat in enumerate(st.session_state['historial']):
        message(chat['input'], is_user=True, key=f"user_{i}")
        message(chat['response'], is_user=False, key=f"bot_{i}")

    # Entrada del usuario
    usuario_input = st.text_input("Escribe tu mensaje:")

    if st.button("Enviar"):
        if usuario_input:
            messages = [{"role": "user", "content": usuario_input}]
            respuesta = obtener_respuesta(messages)
            st.session_state['historial'].append({"input": usuario_input, "response": respuesta})
            st.rerun()
        else:
            st.warning("Por favor, escribe un mensaje.")

# Footer
st.markdown("""
    <div style="position: fixed; bottom: 0; width: 100%; background-color: #2c3e50; color: #ecf0f1; text-align: center; padding: 10px;">
        <p>© 2024 Tu Nombre. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)
