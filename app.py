import streamlit as st
import openai
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import os
from streamlit_option_menu import option_menu
from streamlit_chat import message

# Nombre del secreto en Azure Key Vault
azure_key_gpt = 'dammgpt'  # Asegúrate de que este nombre coincide con el secreto en Key Vault

# Función para obtener el secreto desde Azure Key Vault
def get_secret(secret_name):
    try:
        # Acceder al nombre del Key Vault desde los secretos de Streamlit
        key_vault_name = st.secrets["KEY_VAULT_NAME"]
        KVUri = f"https://{key_vault_name}.vault.azure.net"

        # Autenticación usando ClientSecretCredential con los secretos de Streamlit
        credential = ClientSecretCredential(
            client_id=st.secrets["AZURE_CLIENT_ID"],
            client_secret=st.secrets["AZURE_CLIENT_SECRET"],
            tenant_id=st.secrets["AZURE_TENANT_ID"]
        )
        client = SecretClient(vault_url=KVUri, credential=credential)

        # Obtener el secreto
        retrieved_secret = client.get_secret(secret_name)
        return retrieved_secret.value
    except KeyError as e:
        st.error(f"Clave faltante en los secretos: {e}")
        return None
    except Exception as e:
        st.error(f"Error al obtener el secreto: {e}")
        return None

# Obtener la clave de API de Azure OpenAI desde Key Vault
api_key = get_secret(azure_key_gpt)

if not api_key:
    st.stop()

# Configuración de la API de Azure OpenAI
openai.api_type = "azure"
openai.api_base = "https://ai-gptdamm235320528959.openai.azure.com/"  # Reemplaza con tu endpoint real
openai.api_version = "2023-12-01-preview"  # Verifica la versión actual de tu API
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
        <h1 style="color:#ffffff;">🏅 Aplicación Deportiva con Chatbot 🏅</h1>
    </div>
    """, unsafe_allow_html=True)

# Barra lateral para la navegación con íconos usando streamlit-option-menu
with st.sidebar:
    selected = option_menu(
        menu_title="Menú Principal",
        options=["🏖 OCIO", "🛒 CONSUMO", "🤖 Chatbot"],
        icons=["sun", "cart", "robot"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#2c3e50"},
            "icon": {"color": "#ffffff", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#1abc9c"},
            "nav-link-selected": {"background-color": "#1abc9c"},
        }
    )

choice = selected

# Función para obtener la respuesta del modelo
def obtener_respuesta(prompt):
    try:
        response = openai.Completion.create(
            engine="gpt4onennisi",  # Reemplaza con el nombre de tu deployment en Azure
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        respuesta = response.choices[0].text.strip()
        return respuesta
    except Exception as e:
        return f"Error: {e}"

# Secciones de la aplicación
if choice == "🏖 OCIO":
    st.header("🏖 OCIO")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("ociosoporte.jpg", use_column_width=True)  # Asegúrate de tener esta imagen en tu repositorio
    with col2:
        st.write("""
            ### Actividades de Ocio
            - Deportes al aire libre
            - Gimnasio y fitness
            - Eventos deportivos
            - Reuniones sociales
        """)

elif choice == "🛒 CONSUMO":
    st.header("🛒 CONSUMO")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
            ### Tendencias de Consumo
            - Equipamiento deportivo
            - Ropa y accesorios
            - Suplementos nutricionales
            - Tecnología wearable
        """)
    with col2:
        st.image("consumodeporte.jpg", use_column_width=True)  # Asegúrate de tener esta imagen en tu repositorio

elif choice == "🤖 Chatbot":
    st.header("🤖 Chatbot")

    # Crear una sesión para almacenar el historial del chat
    if 'historial' not in st.session_state:
        st.session_state['historial'] = []

    # Mostrar el historial del chat usando streamlit-chat
    for chat in st.session_state['historial']:
        message(chat['input'], is_user=True)
        message(chat['response'], is_user=False)

    # Entrada del usuario
    usuario_input = st.text_input("Escribe tu mensaje:")

    if st.button("Enviar"):
        if usuario_input:
            respuesta = obtener_respuesta(usuario_input)
            st.session_state['historial'].append({"input": usuario_input, "response": respuesta})
            st.experimental_rerun()
        else:
            st.warning("Por favor, escribe un mensaje.")

# Footer
st.markdown("""
    <div style="position: fixed; bottom: 0; width: 100%; background-color: #2c3e50; color: #ecf0f1; text-align: center; padding: 10px;">
        <p>© 2024 Tu Nombre. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)
