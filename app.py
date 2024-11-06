import streamlit as st
import openai
from openai import AzureOpenAI
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from streamlit_option_menu import option_menu
from streamlit_chat import message
import plotly.express as px  # Importar Plotly Express
import pandas as pd
import numpy as np
from databricks.connect import DatabricksSession
import os
import json
from datetime import datetime
from datetime import timedelta
from pyspark.sql import functions as F

os.environ["DATABRICKS_HOST"] = st.secrets.azure_credentials.databricks_host
os.environ["DATABRICKS_TOKEN"] = st.secrets.azure_credentials.databricks_token
os.environ["DATABRICKS_CLUSTER_ID"] = st.secrets.azure_credentials.databricks_cluster_id
prompt = "Eres un asistente para consultar datos de unas tablas de forma amigable para el usuario. Presentate como un asistente comercial. Puedes usar la funcion consultar_tablas para filtrar unos dataframe de sparks. Limita siempre las consultas a unos 20 valores y solo haz consultas de las columnas que yo te indicaré aquí. El usuario es un comercial y necesita acceder a información del tipo: 'Clientes cercanos no visitados en [tanto tiempo], y censo [caja/barril] de la competencia?'El usuario puede preguntar información de visitas y de censo de estas visitas a la vez, deberas marcar indicar True en los dos campos de visitas y censos si se da este caso.Si te pregunta por canal propio y competencia a la vez, dejalo vacío. La latitud actual es 41.40338 y la longitud 2.17403. Si no se especifica la distancia maxima dejala en 4 Km.Devuelve los establecimientos encontrados con su nombre real siempre. A parte de esto el usuario tambien te puede preguntar por datos de ventas de determinado establecimiento La fecha de hoy es 16/04/2024"



# Inicializar DatabricksSession
def init_databricks_session():
    spark = DatabricksSession.builder.getOrCreate()
    return spark

spark = init_databricks_session()
censo_df = spark.read.table("SF_CENSOS_DEV")
visitas_df = spark.read.table("SF_VISITAS_GPT")
ventas_df = spark.read.table("gold_ventas_material_notcutoffdatefilled_spain")

# Función para obtener el secreto desde Azure Key Vault
def get_secret(secret_name):
    try:
        print(st.secrets.dammgpt.key_vault_name)
        key_vault_name = st.secrets.dammgpt.key_vault_name
        KVUri = f"https://{key_vault_name}.vault.azure.net"

        credential = ClientSecretCredential(
            client_id=st.secrets.dammgpt.azure_client_id,
            client_secret=st.secrets.dammgpt.azure_client_secret,
            tenant_id=st.secrets.dammgpt.azure_tenant_id
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
azure_openai_endpoint = st.secrets.dammgpt.azure_openai_endpoint

# Configurar la API de OpenAI para Azure
openai.api_type = "azure"
openai.api_base = azure_openai_endpoint  # Asegúrate de que incluye 'https://'
openai.api_version = "2023-12-01-preview"
openai.api_key = api_key

# Aplicar estilos CSS personalizados
def local_css():
    st.markdown("""
        <style>
            /* Importar fuente desde Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

            /* Aplicar fuente a toda la aplicación */
            html, body, [class*="css"]  {
                font-family: 'Roboto', sans-serif;
                background-color: #f5f5f5;
            }

            /* Estilos del título principal */
            .main-title {
                text-align: center;
                padding: 20px 0;
                background-color: #ffffff;
                margin-bottom: 20px;
                border-bottom: 1px solid #e0e0e0;
            }
            .main-title h1 {
                color: #333333;
                font-weight: 700;
            }

            /* Estilos del menú de navegación */
            .css-1n543e5 {
                background-color: #ffffff !important;
                padding: 0;
                margin-bottom: 20px;
            }
            .nav-link {
                font-size: 16px !important;
                color: #333333 !important;
                padding: 10px 20px !important;
                margin: 0 5px !important;
                border-radius: 5px;
            }
            .nav-link:hover {
                background-color: #e0e0e0 !important;
                color: #333333 !important;
            }
            .nav-link-selected {
                background-color: #1abc9c !important;
                color: #ffffff !important;
            }

            /* Estilos de los encabezados de sección */
            .stMarkdown h2 {
                color: #333333;
                font-weight: 500;
                margin-top: 0;
            }

            /* Estilos del contenido */
            .stContainer {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            /* Estilos de imágenes */
            img {
                border-radius: 8px;
            }

            /* Estilos del chat */
            .streamlit-chat-message {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
            .streamlit-chat-message-user {
                background-color: #1abc9c;
                color: #ffffff;
            }

            /* Estilos de botones */
            .stButton > button {
                background-color: #1abc9c;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 16px;
            }
            .stButton > button:hover {
                background-color: #17a085;
                color: #ffffff;
            }

            /* Estilos del footer */
            .footer {
                text-align: center;
                padding: 10px 0;
                color: #999999;
                font-size: 14px;
                margin-top: 40px;
            }
        </style>
        """, unsafe_allow_html=True)

local_css()

# Título con estilo actualizado
st.markdown("""
    <div class="main-title">
        <h1>ReFill ReTrain ReJoin</h1>
    </div>
    """, unsafe_allow_html=True)

# Menú de navegación horizontal
selected = option_menu(
    menu_title=None,
    options=["Leisure", "ReFill", "Chatbot", "Análisis"],  # Mantén "Análisis" si lo deseas
    icons=["sun", "droplet", "robot", "bar-chart"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important"},
        "nav-link": {"--hover-color": "#e0e0e0"},
        "nav-link-selected": {"background-color": "#1abc9c"},
    }
)

choice = selected

def consultar_tablas(visitas=False, censo=False, ventas=False, 
                     correo_usuario=None, fecha_limite=None, latitud_actual=41.40338, longitud_actual=2.17403, 
                     distancia_max_km=4, canal=None, establecimientos_censo=None, establecimientos_ventas=None, 
                     envase=None, start_date_ventas=None, end_date_ventas=None, material_filter_ventas=None):
    
    resultados = []
    establecimientos_visitas = []

    print(visitas, censo, correo_usuario, fecha_limite, latitud_actual, longitud_actual, distancia_max_km, establecimientos_censo, envase, canal, ventas, establecimientos_ventas, start_date_ventas, end_date_ventas, material_filter_ventas)
    if visitas:
        # Convertimos la fecha límite en datetime
        fecha_limite_dt = datetime.strptime(fecha_limite, "%Y-%m-%d") if fecha_limite else datetime.now() - timedelta(days=7)
        
        # Filtramos por visitas según criterios
        visitas_filtradas = visitas_df.filter(
            (F.col("`CREATEDBY.USERNAME`") == correo_usuario) &
            (F.col("`UPDATE_DATE`") <= fecha_limite_dt) &
            (
                6371 * F.acos(
                    F.cos(F.radians(F.lit(latitud_actual))) * F.cos(F.radians(F.col("`BILLINGLATITUDE`").cast("float"))) *
                    F.cos(F.radians(F.col("`BILLINGLONGITUDE`").cast("float")) - F.radians(F.lit(longitud_actual))) +
                    F.sin(F.radians(F.lit(latitud_actual))) * F.sin(F.radians(F.col("`BILLINGLATITUDE`").cast("float")))
                ) <= distancia_max_km
            )
        ).select("ESTABLECIMIENTO", "EVENT_SUBJECT").limit(10)

        establecimientos_visitas = [row["ESTABLECIMIENTO"] for row in visitas_filtradas.collect()]
        print("lista:" )
        print(establecimientos_visitas)
        # Convertir resultados de visitas a texto
        visitas_resultado = "\n".join([f"Establecimiento: {row['ESTABLECIMIENTO']}, Nombre: {row['EVENT_SUBJECT']}" for row in visitas_filtradas.collect()])
        resultados.append("Visitas:\n" + visitas_resultado)
        print("Visitas:\n" )
        print(visitas_resultado)

    # Combinamos los establecimientos de visitas con los proporcionados para el censo
    establecimientos_combined = list(set(establecimientos_visitas + (establecimientos_censo or [])))

    if censo and establecimientos_combined:
        # Filtramos censo para los establecimientos combinados y por envase si se especifica
        censo_filtrado = censo_df.filter(
            (F.col("ESTABLECIMIENTO").isin(establecimientos_combined)) &  # Filtrar solo establecimientos combinados
            ((F.col("ENVASE") == envase) if envase else True) &  # Solo filtra por envase si se especifica
            ((F.col("CANAL") == canal) if envase else True)  # Solo establecimientos del canal especificado
        ).select("VOLUMENANUAL", "MARCANAME", "ENVASE", "ESTABLECIMIENTO", "CANAL")

        # Recoger los resultados del censo
        censo_coleccion = censo_filtrado.collect()

        # Verificar si hay resultados
        if censo_coleccion:
            # Convertir resultados de censo a texto
            censo_resultado = "\n".join([
                f"Establecimiento: {row['ESTABLECIMIENTO']}, Marca: {row['MARCANAME']}, Envase: {row['ENVASE']}, Volumen Anual: {row['VOLUMENANUAL']}"
                for row in censo_coleccion
            ])
        else:
            # Mensaje en caso de que no se encuentren resultados
            censo_resultado = "No se ha encontrado censo."

        resultados.append("Censo:\n" + censo_resultado)
        print("Censo:\n" + censo_resultado)

    # Filtrado de ventas con el parámetro `establecimientos_venta`
    if ventas and (establecimientos_ventas or establecimientos_combined):
        establecimientos_combined_ventas = list(set(establecimientos_ventas or []) | set(establecimientos_combined))

        # Filtramos las ventas para los establecimientos combinados y el rango de fechas
        ventas_filtradas = ventas_df.filter(
            (F.col("establecimiento").isin(establecimientos_combined_ventas)) &
            (F.col("week-month-year").between(datetime.strptime(start_date_ventas, "%Y-%m-%d"), datetime.strptime(end_date_ventas, "%Y-%m-%d"))) &
            (F.col("material").like(material_filter_ventas) if material_filter_ventas else True)
        )

        print(ventas_filtradas.show())
        
        # Calcular la suma total de ventas
        total_ventas = ventas_filtradas.agg(F.sum(F.coalesce(F.col("ventas"), F.lit(0))).alias("total_ventas")).collect()[0]["total_ventas"]
        
        # Añadir el resultado de ventas a la lista de resultados
        resultados.append(f"Ventas:\nTotal ventas: {total_ventas}")
        print(f"Ventas:\nTotal ventas: {total_ventas}")

    # Unir resultados y retornar como cadena de texto
    return "\n\n".join(resultados) if resultados else "No se encontraron resultados."

# Función para obtener la respuesta del modelo usando Azure OpenAI
def obtener_respuesta(messages, model='gpt4onennisi'):

    
    cliente = AzureOpenAI(
        azure_endpoint=st.secrets.dammgpt.azure_openai_endpoint,
        api_key=api_key,
        api_version="2023-12-01-preview"
    )
    
    try:
        tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "consultar_tablas",
                        "description": "Consulta información de visitas, censo de competencia y/o ventas según los parámetros establecidos por el usuario.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "visitas": {
                                    "type": "boolean",
                                    "description": "Indica si se necesita información de visitas."
                                },
                                "censo": {
                                    "type": "boolean",
                                    "description": "Indica si se necesita información de censo."
                                },
                                "ventas": {
                                    "type": "boolean",
                                    "description": "Indica si se necesita información de ventas."
                                },
                                "correo_usuario": {
                                    "type": "string",
                                    "description": "Correo electrónico del comercial que solicita la consulta."
                                },
                                "fecha_limite": {
                                    "type": "string",
                                    "description": "Fecha límite para las visitas, en formato 'YYYY-MM-DD'. Este campo es opcional y solo se usa si 'visitas' es true."
                                },
                                "latitud_actual": {
                                    "type": "number",
                                    "description": "Latitud actual del comercial para calcular la distancia a los establecimientos."
                                },
                                "longitud_actual": {
                                    "type": "number",
                                    "description": "Longitud actual del comercial para calcular la distancia a los establecimientos."
                                },
                                "distancia_max_km": {
                                    "type": "number",
                                    "description": "Distancia máxima en kilómetros para filtrar clientes cercanos."
                                },
                                "canal": {
                                    "type": "string",
                                    "description": "Canal por el que se pregunta en la visitas (Propio o Competencia)."
                                },
                                "establecimientos_censo": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "Lista de IDs de establecimientos específica, utilizada en la consulta de censo."
                                },
                                "establecimientos_ventas": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "Lista de IDs de establecimientos específica para ventas."
                                },
                                "envase": {
                                    "type": "string",
                                    "description": "Tipo de envase del censo ('Caja' o 'Barril'). Este campo es opcional y solo se usa si 'censo' es true.",
                                    "enum": ["Caja", "Barril", None]
                                },
                                "start_date_ventas": {
                                    "type": "string",
                                    "description": "Fecha de inicio para la consulta de ventas, en formato 'YYYY-MM-DD'."
                                },
                                "end_date_ventas": {
                                    "type": "string",
                                    "description": "Fecha de fin para la consulta de ventas, en formato 'YYYY-MM-DD'."
                                },
                                "material_filter_ventas": {
                                    "type": "string",
                                    "description": "Filtro de material para la consulta de ventas. Es opcional y se usa solo si 'ventas' es true."
                                }
                            },
                            "required": ["correo_usuario"],
                        }
                    }
                }
                
        ]


        print("Model's request:")
        response = cliente.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
            tools=tools,
            tool_choice="auto",
        )

        # Process the model's response
        response_message = response.choices[0].message
        messages.append(response_message)

        print("Model's response:")  
        print(response_message)  

        # Handle function calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "consultar_tablas":
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"Function arguments: {function_args}")  
                    response_string = consultar_tablas(
                        visitas=function_args.get("visitas", False),
                        censo=function_args.get("censo", False),
                        correo_usuario=function_args.get("correo_usuario"),
                        fecha_limite=function_args.get("fecha_limite"),
                        latitud_actual=function_args.get("latitud_actual"),
                        longitud_actual=function_args.get("longitud_actual"),
                        distancia_max_km=function_args.get("distancia_max_km"),
                        establecimientos_censo=function_args.get("establecimientos_censo"),
                        envase=function_args.get("envase"),
                        canal=function_args.get("canal"),
                        ventas=function_args.get("ventas", False),
                        establecimientos_ventas=function_args.get("establecimientos_ventas"),
                        start_date_ventas=function_args.get("start_date_ventas"),
                        end_date_ventas=function_args.get("end_date_ventas"),
                        material_filter_ventas=function_args.get("material_filter_ventas")

                    )
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "consultar_tablas",
                        "content": response_string,
                    })
        else:
            print("No tool calls were made by the model.")  

        # Second API call: Get the final response from the model
        final_response = cliente.chat.completions.create(
            model=model,
            messages=messages,
        )

        print(messages)

        return final_response.choices[0].message.content

    except Exception as e:
        st.error(f"Error al obtener la respuesta: {e}")
        print(f"Error detallado: {e}")  # Para registros adicionales
        return "Lo siento, hubo un error al procesar tu solicitud."

# Función para mostrar el formulario de login
def mostrar_login():
    st.subheader("Por favor, inicia sesión para acceder al chatbot.")
    username = st.text_input("Nombre de usuario")
    password = st.text_input("Contraseña", type="password")
    user_saved = st.secrets.dammgpt.username
    pass_saved = st.secrets.dammgpt.password
    if st.button("Iniciar sesión"):
        if username == user_saved and password == pass_saved:
            st.session_state['logged_in'] = True
            st.success("¡Has iniciado sesión correctamente!")
            st.rerun()
        else:
            st.error("Nombre de usuario o contraseña incorrectos.")

# Secciones de la aplicación
if choice == "Leisure":
    st.header("Actividades de Ocio")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("estrella-damm.jpg", use_column_width=True)
    with col2:
        st.markdown("""
            - **Deportes al aire libre**
            - **Gimnasio y fitness**
            - **Eventos deportivos**
            - **Festivales / Música**
            - **Cultura**
            - **Barcelona**
        """)

elif choice == "ReFill":
    st.header("Consulta los litros que quedan o faltan en tu suscripción")
    
    # Usar columnas para una mejor disposición
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            ### Te quedan **10 litros** este mes
            ¿Necesitas más? Renueva tu suscripción para disfrutar de más beneficios.
        """)
        
        # Generar datos de muestra para el consumo
        fechas = pd.date_range(start='2023-01-01', periods=10, freq='D')
        consumo_isotonica = np.random.randint(1, 5, size=10)  # Litros consumidos por día
        consumo_proteica = np.random.randint(0, 3, size=10)
        
        df_consumo = pd.DataFrame({
            'Fecha': fechas,
            'Agua Isotónica': consumo_isotonica,
            'Agua Proteica': consumo_proteica
        })
        
        # Gráfico de barras apiladas para mostrar el consumo
        df_consumo_melted = df_consumo.melt(id_vars='Fecha', value_vars=['Agua Isotónica', 'Agua Proteica'], var_name='Producto', value_name='Litros')
        fig_consumo = px.bar(df_consumo_melted, x='Fecha', y='Litros', color='Producto', title='Consumo de Productos por Día')
        st.plotly_chart(fig_consumo, use_container_width=True)
        
        # Gráfico circular para mostrar la distribución total del consumo
        total_consumo = df_consumo[['Agua Isotónica', 'Agua Proteica']].sum().reset_index()
        total_consumo.columns = ['Producto', 'Litros']
        fig_pie = px.pie(total_consumo, values='Litros', names='Producto', title='Distribución Total del Consumo')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.image("fake_qr.jpg", use_column_width=True)

elif choice == "Chatbot":
    st.header("Coach GPT")
    
    # Verificar si el usuario ha iniciado sesión
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        mostrar_login()
    else:
        # Crear una sesión para almacenar el historial del chat
        if 'historial' not in st.session_state:
            st.session_state['historial'] = []

        # Mostrar el historial del chat
        for i, chat in enumerate(st.session_state['historial']):
            message(chat['input'], is_user=True, key=f"user_{i}")
            message(chat['response'], is_user=False, key=f"bot_{i}")

        # Entrada del usuario
        usuario_input = st.text_input("Escribe tu mensaje:", key="input")

        if st.button("Enviar"):
            if usuario_input:
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": usuario_input}]
                respuesta = obtener_respuesta(messages)
                st.session_state['messages'] = messages
                st.session_state['historial'].append({"input": usuario_input, "response": respuesta})
                st.rerun()
            else:
                st.warning("Por favor, escribe un mensaje.")

        # Botón para cerrar sesión
        if st.button("Cerrar sesión"):
            st.session_state['logged_in'] = False
            st.success("Has cerrado sesión.")
            st.rerun()

elif choice == "Análisis":
    st.header("Análisis de Entrenamiento Deportivo")
    
    # Generar datos de muestra
    fechas = pd.date_range(start='2023-01-01', periods=10, freq='D')
    calorias = np.random.randint(400, 800, size=10)
    max_hr = np.random.randint(150, 190, size=10)
    zonas_entrenamiento = np.random.randint(1, 5, size=10)
    
    df = pd.DataFrame({
        'Fecha': fechas,
        'Calorías': calorias,
        'Frecuencia Cardíaca Máxima': max_hr,
        'Zona de Entrenamiento': zonas_entrenamiento
    })
    
    # Gráfico de barras de calorías
    fig_calorias = px.bar(df, x='Fecha', y='Calorías', title='Calorías Quemadas por Día')
    st.plotly_chart(fig_calorias, use_container_width=True)
    
    # Gráfico de líneas de frecuencia cardíaca máxima
    fig_hr = px.line(df, x='Fecha', y='Frecuencia Cardíaca Máxima', markers=True, title='Frecuencia Cardíaca Máxima por Día')
    st.plotly_chart(fig_hr, use_container_width=True)
    
    # Gráfico de pastel de zonas de entrenamiento
    df_zonas = df.groupby('Zona de Entrenamiento').size().reset_index(name='Conteo')
    fig_zonas = px.pie(df_zonas, values='Conteo', names='Zona de Entrenamiento', title='Distribución de Zonas de Entrenamiento')
    st.plotly_chart(fig_zonas, use_container_width=True)
    
    # Puedes agregar más gráficos si lo deseas

# Footer con estilo actualizado
st.markdown("""
    <div class="footer">
        © 2024 Tu Nombre. Todos los derechos reservados.
    </div>
    """, unsafe_allow_html=True)
