import streamlit as st
import mysql.connector
from mysql.connector import errorcode
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Configuración de la página
st.set_page_config(
    page_title="Explorador Avanzado MySQL",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
<style>
    :root {
        --primary-color: #4bff71;
        --secondary-color: #5d8aa8;
        --accent-color: #FFA500;
        --dark-text: #2c3e50;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--secondary-color) !important;
    }
    .st-b7, .st-c0, .st-cj {
        color: var(--dark-text) !important;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: var(--dark-text);
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: var(--dark-text);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        padding: 0 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 0.5rem 0.5rem 0 0;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    .form-container {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #dee2e6;
    }
    .form-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--dark-text);
    }
    .column-item {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .success-msg {
        color: var(--accent-color) !important;
        font-weight: bold;
    }
    .data-type-select {
        width: 150px !important;
    }
    .query-box {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()
clave_sql = os.getenv("CLAVE_SQL")

st.markdown('<div class="main-header">Explorador Avanzado MySQL</div>', unsafe_allow_html=True)

# ---------------------------
# Funciones de conexión y consulta
# ---------------------------

# Conexión al servidor (cliente)
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=clave_sql  # Usando la contraseña segura
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            st.error("Error: Usuario o contraseña incorrectos")
        else:
            st.error(f"Error de conexión: {err}")
        return None

# Conexión a una base de datos específica
def get_db_connection(db_name):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=clave_sql,  # Usando la misma variable de entorno
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error al conectar a {db_name}: {err}")
        return None

# Obtener lista de bases de datos disponibles (excluyendo las de sistema)
def get_databases(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        return [db[0] for db in cursor.fetchall() if db[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
    except mysql.connector.Error as err:
        st.error(f"Error al obtener bases de datos: {err}")
        return []

# Crear nueva base de datos
def create_database(conn, db_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {db_name}")
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error al crear base de datos: {err}")
        return False

# Obtener las tablas de una base de datos
def get_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]
    except mysql.connector.Error as err:
        st.error(f"Error al obtener tablas: {err}")
        return []

# Tipos de datos y atributos para la creación de tablas
DATA_TYPES = [
    "INT", "VARCHAR(255)", "TEXT", "DATE", "DATETIME", 
    "DECIMAL(10,2)", "BOOLEAN", "FLOAT", "DOUBLE"
]
COLUMN_ATTRIBUTES = [
    "PRIMARY KEY", "AUTO_INCREMENT", "NOT NULL", 
    "UNIQUE", "DEFAULT NULL"
]

# Crear una nueva tabla en la base de datos seleccionada
def create_table(conn, table_name, columns):
    try:
        cursor = conn.cursor()
        columns_sql = ", ".join(columns)
        cursor.execute(f"CREATE TABLE {table_name} ({columns_sql})")
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error al crear tabla: {err}")
        return False

# Ejecutar una consulta SQL personalizada
def execute_custom_query(conn, query):
    try:
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute(query)
        # Si es SELECT, retorna los resultados
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            execution_time = time.time() - start_time
            return pd.DataFrame(data, columns=columns), execution_time, None
        else:
            conn.commit()
            execution_time = time.time() - start_time
            return None, execution_time, f"Consulta ejecutada correctamente. Filas afectadas: {cursor.rowcount}"
    except mysql.connector.Error as err:
        return None, 0, f"Error en la consulta: {err}"

# ---------------------------
# Conexión principal y selección de base de datos
# ---------------------------

# Conexión al servidor sin especificar BD
conn = get_connection()
if not conn:
    st.stop()

# Obtener bases de datos disponibles
database_options = get_databases(conn)
if not database_options:
    st.warning("No se encontraron bases de datos disponibles")

# Selección de base de datos desde el sidebar
selected_db = st.sidebar.selectbox(
    "Seleccione una base de datos", 
    database_options,
    key="db_selector"
)

# Conexión a la base de datos seleccionada
db_conn = None
if selected_db:
    db_conn = get_db_connection(selected_db)
    if db_conn:
        st.sidebar.markdown(f'<div class="success-msg">Conectado a: {selected_db}</div>', unsafe_allow_html=True)

# Obtener tablas de la base de datos seleccionada
tables = []
selected_table = None
if db_conn:
    tables = get_tables(db_conn)
    if tables:
        selected_table = st.sidebar.selectbox("Seleccione una tabla", tables)

# ---------------------------
# Pestañas principales
# ---------------------------
tab2, tab3, tab4, tab5, tab6 = st.tabs([ 
    "📋 Estructura", 
    "📊 Datos", 
    "🔍 Consultas SQL",
    "🛠 Crear BD", 
    "🛠 Crear Tabla"
])

# Tab Estructura
with tab2:
    if selected_table:
        st.markdown(f'<div class="sub-header">Estructura de: {selected_table}</div>', unsafe_allow_html=True)
        # Mostrar estructura con DESCRIBE
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
        
        structure_df = get_table_structure(db_conn, selected_table)
        st.dataframe(structure_df, use_container_width=True)
        
        # Mostrar SQL de creación
        st.markdown('<div class="sub-header">SQL de Creación</div>', unsafe_allow_html=True)
        def get_table_info(conn, table):
            try:
                cursor = conn.cursor()
                cursor.execute(f"SHOW CREATE TABLE {table}")
                return cursor.fetchone()[1]
            except mysql.connector.Error as err:
                st.error(f"Error al obtener información: {err}")
                return ""
        create_statement = get_table_info(db_conn, selected_table)
        st.code(create_statement, language="sql")
    else:
        st.warning("Selecciona una base de datos y tabla para ver su estructura")

# Tab Datos
with tab3:
    if selected_table:
        st.markdown(f'<div class="sub-header">Datos en: {selected_table}</div>', unsafe_allow_html=True)
        # Control para limitar resultados
        limit = st.slider("Número de registros a mostrar", 5, 1000, 50)
        
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
        
        data_df = get_table_data(db_conn, selected_table, limit)
        st.dataframe(data_df, use_container_width=True)
        
        # Estadísticas básicas
        if st.checkbox("Mostrar estadísticas"):
            numeric_cols = data_df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                st.markdown('<div class="sub-header">Estadísticas</div>', unsafe_allow_html=True)
                st.dataframe(data_df[numeric_cols].describe(), use_container_width=True)
            else:
                st.info("No hay columnas numéricas para mostrar estadísticas")
    else:
        st.warning("Selecciona una base de datos y tabla para ver los datos")

# Tab Consultas SQL
with tab4:
    st.markdown('<div class="sub-header">Consulta SQL Personalizada</div>', unsafe_allow_html=True)
    if not db_conn:
        st.warning("Primero selecciona una base de datos en el panel izquierdo")
    else:
        query = st.text_area(
            "Escribe tu consulta SQL aquí (Solo SELECT):",
            value=f"SELECT * FROM {selected_table} LIMIT 10" if selected_table else "SELECT * FROM tabla LIMIT 10",
            height=200,
            key="sql_editor"
        )
        col1, col2 = st.columns([1, 4])
        with col1:
            execute_btn = st.button("Ejecutar Consulta", type="primary")
        if execute_btn and query:
            with st.spinner("Ejecutando consulta..."):
                result_df, exec_time, message = execute_custom_query(db_conn, query)
                if result_df is not None:
                    st.success(f"Consulta ejecutada en {exec_time:.2f} segundos")
                    st.dataframe(result_df, use_container_width=True)
                    if not result_df.empty:
                        csv = result_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Descargar resultados como CSV",
                            csv,
                            f"query_result_{selected_db}.csv",
                            "text/csv",
                            key='download-csv'
                        )
                elif message:
                    st.success(f"{message} (Tiempo: {exec_time:.2f} segundos)")

# Tab Crear Base de Datos
with tab5:
    st.markdown('<div class="sub-header">Crear Nueva Base de Datos</div>', unsafe_allow_html=True)
    with st.form("create_db_form"):
        st.markdown('<div class="form-title">Configuración de la Base de Datos</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            db_name = st.text_input("Nombre de la base de datos", help="Usa solo caracteres alfanuméricos y guiones bajos")
        with col2:
            charset = st.selectbox("Juego de caracteres", ["utf8mb4", "latin1", "utf8"])
        submitted = st.form_submit_button("Crear Base de Datos")
        if submitted:
            if db_name:
                if create_database(conn, db_name):
                    st.success(f"Base de datos '{db_name}' creada exitosamente!")
                    database_options = get_databases(conn)
                    st.rerun()
                else:
                    st.error("Error al crear la base de datos")
            else:
                st.warning("Debes ingresar un nombre para la base de datos")

# Tab Crear Tabla
with tab6:
    if not selected_db:
        st.warning("Primero selecciona una base de datos en el panel izquierdo")
    else:
        st.markdown(f'<div class="sub-header">Crear Nueva Tabla en {selected_db}</div>', unsafe_allow_html=True)
        table_name = st.text_input("Nombre de la tabla", help="Usa solo caracteres alfanuméricos y guiones bajos", key="table_name_input")
        if 'columns' not in st.session_state:
            st.session_state.columns = []
        st.markdown('<div class="form-title">Agregar Nueva Columna</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            new_col_name = st.text_input("Nombre columna", key="new_col_name")
        with col2:
            new_col_type = st.selectbox("Tipo de dato", DATA_TYPES, key="new_col_type")
        with col3:
            new_col_attrs = st.multiselect("Atributos", COLUMN_ATTRIBUTES, key="new_col_attrs")
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("➕ Agregar Columna"):
                if new_col_name:
                    attrs_str = " ".join(new_col_attrs)
                    col_def = f"{new_col_name} {new_col_type} {attrs_str}".strip()
                    st.session_state.columns.append(col_def)
                    st.rerun()
                else:
                    st.warning("Ingresa un nombre para la columna")
        with col1:
            if st.button("🗑 Limpiar Columnas"):
                st.session_state.columns = []
                st.rerun()
        if st.session_state.columns:
            st.markdown('<div class="form-title">Columnas Definidas</div>', unsafe_allow_html=True)
            for i, col in enumerate(st.session_state.columns, 1):
                st.markdown(f'<div class="column-item">{i}. {col}</div>', unsafe_allow_html=True)
        st.markdown('<div class="form-title">Opciones Avanzadas</div>', unsafe_allow_html=True)
        engine = st.selectbox("Motor de almacenamiento", ["InnoDB"])
        charset = st.selectbox("Juego de caracteres", ["utf8"])
        with st.form("create_table_final_form"):
            submitted = st.form_submit_button("🚀 Crear Tabla")
            if submitted:
                if table_name and st.session_state.columns:
                    full_columns = st.session_state.columns.copy()
                    table_sql = f"CREATE TABLE {table_name} (\n    "
                    table_sql += ",\n    ".join(full_columns)
                    table_sql += f"\n) ENGINE={engine} DEFAULT CHARSET={charset};"
                    st.code(table_sql, language="sql")
                    if create_table(db_conn, table_name, full_columns):
                        st.success(f"Tabla '{table_name}' creada exitosamente!")
                        tables = get_tables(db_conn)
                        st.session_state.columns = []
                        st.rerun()
                    else:
                        st.error("Error al crear la tabla")
                else:
                    st.warning("Debes ingresar un nombre para la tabla y al menos una columna")

with st.sidebar:
    st.markdown("---")
    st.markdown("### Información del Sistema")
    if selected_db:
        def get_db_size(conn, db_name):
            try:
                cursor = conn.cursor()
                query = f"""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables
                WHERE table_schema = '{db_name}'
                GROUP BY table_schema
                """
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
            except mysql.connector.Error as err:
                st.error(f"Error al obtener tamaño: {err}")
                return 0
        db_size = get_db_size(conn, selected_db)
        if db_size is not None:
            st.metric("Tamaño de la BD", f"{db_size} MB")

if conn:
    conn.close()
if db_conn:
    db_conn.close()
