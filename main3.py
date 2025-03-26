import streamlit as st
import mysql.connector
from mysql.connector import errorcode
import pandas as pd
import time

# Configuración de la página
st.set_page_config(
    page_title="Explorador de Bases de Datos MySQL",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        font-size: 1rem;
    }
    .stDataFrame {
        margin-top: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Explorador de Bases de Datos MySQL</div>', unsafe_allow_html=True)

# Función para establecer conexión con MySQL
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            auth_plugin='mysql_native_password'  # Soluciona el error de autenticación
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            st.error("Error: Usuario o contraseña incorrectos")
        else:
            st.error(f"Error de conexión: {err}")
        return None

# Conexión principal
conn = get_connection()
if not conn:
    st.stop()

# Obtener lista de bases de datos
def get_databases(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        return [db[0] for db in cursor.fetchall() if db[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
    except mysql.connector.Error as err:
        st.error(f"Error al obtener bases de datos: {err}")
        return []

database_options = get_databases(conn)
if not database_options:
    st.error("No se encontraron bases de datos disponibles")
    st.stop()

# Selección de base de datos
selected_db = st.sidebar.selectbox("Seleccione una base de datos", database_options)

# Función para obtener conexión a una base de datos específica
def get_db_connection(db_name):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Noseasapo11+2",
            database=db_name,
            auth_plugin='mysql_native_password'
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error al conectar a {db_name}: {err}")
        return None

db_conn = get_db_connection(selected_db)
if not db_conn:
    st.stop()

st.sidebar.success(f"Conectado a la base de datos: {selected_db}")

# Función para obtener las tablas de la base de datos
def get_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]
    except mysql.connector.Error as err:
        st.error(f"Error al obtener tablas: {err}")
        return []

tables = get_tables(db_conn)
if not tables:
    st.warning(f"No se encontraron tablas en la base de datos {selected_db}")
    st.stop()

# Selección de tabla
selected_table = st.sidebar.selectbox("Seleccione una tabla", tables)

# Pestañas para diferentes operaciones
tab1, tab2, tab3 = st.tabs(["📋 Estructura de la Tabla", "📊 Datos de la Tabla", "🔍 Consulta Personalizada"])

with tab1:
    st.markdown(f'<div class="sub-header">Estructura de la tabla: {selected_table}</div>', unsafe_allow_html=True)
    
    # Obtener la estructura de la tabla (DESCRIBE)
    def get_table_structure(conn, table):
        try:
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE {table}")
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except mysql.connector.Error as err:
            st.error(f"Error al obtener estructura: {err}")
            return pd.DataFrame()
    
    try:
        with st.spinner("Cargando estructura de la tabla..."):
            structure_df = get_table_structure(db_conn, selected_table)
            st.dataframe(structure_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Mostrar información adicional sobre la tabla
    st.markdown('<div class="sub-header">Información de la tabla</div>', unsafe_allow_html=True)
    
    def get_table_info(conn, table):
        try:
            cursor = conn.cursor()
            cursor.execute(f"SHOW CREATE TABLE {table}")
            return cursor.fetchone()[1]
        except mysql.connector.Error as err:
            st.error(f"Error al obtener información: {err}")
            return ""
    
    try:
        with st.spinner("Cargando información de la tabla..."):
            create_statement = get_table_info(db_conn, selected_table)
            st.code(create_statement, language="sql")
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Mostrar índices de la tabla
    st.markdown('<div class="sub-header">Índices de la tabla</div>', unsafe_allow_html=True)
    
    def get_table_indexes(conn, table):
        try:
            cursor = conn.cursor()
            cursor.execute(f"SHOW INDEX FROM {table}")
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except mysql.connector.Error as err:
            st.error(f"Error al obtener índices: {err}")
            return pd.DataFrame()
    
    try:
        with st.spinner("Cargando índices de la tabla..."):
            indexes_df = get_table_indexes(db_conn, selected_table)
            st.dataframe(indexes_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

with tab2:
    st.markdown(f'<div class="sub-header">Datos de la tabla: {selected_table}</div>', unsafe_allow_html=True)
    
    # Opciones para limitar los resultados
    col1, col2 = st.columns([1, 3])
    with col1:
        limit = st.slider("Número de registros", 5, 1000, 10)
    with col2:
        st.markdown('<div class="info-box">Ajuste el número de registros a mostrar. Para consultas más complejas, use la pestaña "Consulta Personalizada".</div>', unsafe_allow_html=True)
    
    # Obtener datos de la tabla
    def get_table_data(conn, table, limit):
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except mysql.connector.Error as err:
            st.error(f"Error al obtener datos: {err}")
            return pd.DataFrame()
    
    try:
        with st.spinner(f"Cargando datos de {selected_table}..."):
            data_df = get_table_data(db_conn, selected_table, limit)
            
            # Mostrar estadísticas básicas
            st.markdown('<div class="sub-header">Vista previa de datos</div>', unsafe_allow_html=True)
            st.dataframe(data_df, use_container_width=True)
            
            # Mostrar estadísticas básicas
            if not data_df.empty and st.checkbox("Mostrar estadísticas básicas"):
                st.markdown('<div class="sub-header">Estadísticas básicas</div>', unsafe_allow_html=True)
                
                # Identificar columnas numéricas
                numeric_cols = data_df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    stats_df = data_df[numeric_cols].describe().T
                    st.dataframe(stats_df, use_container_width=True)
                else:
                    st.info("No hay columnas numéricas para mostrar estadísticas.")
    except Exception as e:
        st.error(f"Error: {e}")

with tab3:
    st.markdown('<div class="sub-header">Consulta personalizada</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">Escriba su consulta SQL. Por seguridad, solo se permiten consultas SELECT.</div>', unsafe_allow_html=True)
    
    custom_query = st.text_area(
        "Consulta SQL:",
        value=f"SELECT * FROM {selected_table} LIMIT 10",
        height=150
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("Ejecutar consulta", type="primary")
    
    if execute_button:
        if "SELECT" in custom_query.upper() and not any(keyword in custom_query.upper() for keyword in ["UPDATE", "DELETE", "DROP", "INSERT", "CREATE", "ALTER", "TRUNCATE"]):
            try:
                with st.spinner("Ejecutando consulta..."):
                    start_time = time.time()
                    cursor = db_conn.cursor()
                    cursor.execute(custom_query)
                    columns = [column[0] for column in cursor.description]
                    data = cursor.fetchall()
                    result = pd.DataFrame(data, columns=columns)
                    execution_time = time.time() - start_time
                    
                    st.success(f"Consulta ejecutada en {execution_time:.2f} segundos")
                    st.dataframe(result, use_container_width=True)
                    
                    # Opción para descargar resultados
                    if not result.empty:
                        csv = result.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Descargar resultados como CSV",
                            csv,
                            f"query_result_{selected_table}.csv",
                            "text/csv",
                            key='download-csv'
                        )
            except Exception as e:
                st.error(f"Error en la consulta: {e}")
        else:
            st.warning("Por favor, ingrese solo consultas SELECT para garantizar la seguridad.")

# Información adicional en la barra lateral
with st.sidebar:
    st.markdown('<div class="sub-header">Información de la base de datos</div>', unsafe_allow_html=True)
    
    def get_db_size(conn, db_name):
        try:
            cursor = conn.cursor()
            query = f"""
            SELECT 
                table_schema as 'Base de Datos',
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as 'Tamaño (MB)'
            FROM information_schema.tables
            WHERE table_schema = '{db_name}'
            GROUP BY table_schema
            """
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except mysql.connector.Error as err:
            st.error(f"Error al obtener tamaño: {err}")
            return pd.DataFrame()
    
    try:
        db_size = get_db_size(conn, selected_db)
        st.dataframe(db_size, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown('<div class="sub-header">Tablas disponibles</div>', unsafe_allow_html=True)
    
    def get_tables_info(conn, db_name):
        try:
            cursor = conn.cursor()
            query = f"""
            SELECT 
                table_name as 'Tabla', 
                table_rows as 'Filas',
                ROUND((data_length + index_length) / 1024 / 1024, 2) as 'Tamaño (MB)'
            FROM information_schema.tables
            WHERE table_schema = '{db_name}'
            ORDER BY (data_length + index_length) DESC
            """
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
        except mysql.connector.Error as err:
            st.error(f"Error al obtener información: {err}")
            return pd.DataFrame()
    
    try:
        tables_info = get_tables_info(conn, selected_db)
        st.dataframe(tables_info, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Información sobre la aplicación
    st.markdown("---")
    st.markdown("### Acerca de")
    st.markdown("""
    Esta aplicación permite explorar bases de datos MySQL de forma interactiva.
    
    Características:
    - Explorar estructura de tablas
    - Visualizar datos
    - Ejecutar consultas personalizadas
    - Ver estadísticas básicas
    
    Desarrollado con Streamlit y MySQL Connector.
    """)

# Cerrar conexiones al final
conn.close()
if 'db_conn' in locals():
    db_conn.close()