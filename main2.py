import streamlit as st
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

# Selección de base de datos
database_options = ["mundo", "sakila", "pets", "test", "delitos_terr"]
selected_db = st.sidebar.selectbox("Seleccione una base de datos", database_options)

# Crear conexión a la base de datos seleccionada
@st.cache_resource(ttl=3600)
def get_connection(db_name):
    return st.connection(
        f"{db_name}_db",
        type="sql",
        dialect="mysql",
        host="localhost",
        database=db_name,
        username="root",
        password="Zyzser-resbih-kezqu0"
    )

try:
    conn = get_connection(selected_db)
    st.sidebar.success(f"Conectado a la base de datos: {selected_db}")
except Exception as e:
    st.sidebar.error(f"Error de conexión: {e}")
    st.stop()

# Función para obtener las tablas de la base de datos
# Nota: Usamos _conn para que Streamlit no intente hacer hash de la conexión
@st.cache_data(ttl=600)
def get_tables(db_name):
    conn = get_connection(db_name)
    query = "SHOW TABLES"
    tables_df = conn.query(query)
    # Extraer los nombres de las tablas de la primera columna
    table_names = tables_df.iloc[:, 0].tolist()
    return table_names

# Obtener las tablas
try:
    tables = get_tables(selected_db)
    if not tables:
        st.warning(f"No se encontraron tablas en la base de datos {selected_db}")
        st.stop()
except Exception as e:
    st.error(f"Error al obtener las tablas: {e}")
    st.stop()

# Selección de tabla
selected_table = st.sidebar.selectbox("Seleccione una tabla", tables)

# Pestañas para diferentes operaciones
tab1, tab2= st.tabs(["🔍 Consulta Personalizada", "📋 Estructura de la Tabla"])

with tab2:
    st.markdown(f'<div class="sub-header">Estructura de la tabla (DESCRIBE): {selected_table}</div>', unsafe_allow_html=True)
    
    # Obtener la estructura de la tabla (DESCRIBRE)
    @st.cache_data(ttl=600)
    def get_table_structure(db_name, table):
        conn = get_connection(db_name)
        query = f"DESCRIBE {table}"
        return conn.query(query)
    
    try:
        with st.spinner("Cargando estructura de la tabla..."):
            structure_df = get_table_structure(selected_db, selected_table)
            st.dataframe(structure_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error al obtener la estructura de la tabla: {e}")
    
    # Mostrar información adicional sobre la tabla
    st.markdown('<div class="sub-header">Información de la tabla</div>', unsafe_allow_html=True)
    
    @st.cache_data(ttl=600)
    def get_table_info(db_name, table):
        conn = get_connection(db_name)
        query = f"SHOW CREATE TABLE {table}"
        return conn.query(query)
    
    try:
        with st.spinner("Cargando información de la tabla..."):
            table_info = get_table_info(selected_db, selected_table)
            create_statement = table_info.iloc[0, 1]
            st.code(create_statement, language="sql")
    except Exception as e:
        st.error(f"Error al obtener información de la tabla: {e}")
    

with tab1:
    st.markdown('<div class="sub-header">Consulta personalizada (SELECT)</div>', unsafe_allow_html=True)
    
    st.markdown("**Escriba su consulta SQL. Por seguridad, solo se permiten consultas SELECT.**", unsafe_allow_html=True)
    
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
                    result = conn.query(custom_query)
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
    
    @st.cache_data(ttl=600)
    def get_db_size(db_name):
        conn = get_connection(db_name)
        query = f"""
        SELECT 
            table_schema as 'Base de Datos',
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as 'Tamaño (MB)'
        FROM information_schema.tables
        WHERE table_schema = '{db_name}'
        GROUP BY table_schema
        """
        return conn.query(query) 
    
    try:
        db_size = get_db_size(selected_db)
        st.markdown(f"**Base de Datos:** {selected_db}  |  **Tamaño:** {db_size['Tamaño (MB)'].values[0]} MB")
    except Exception as e:
        st.error(f"Error al obtener el tamaño de la base de datos: {e}")
    
    st.markdown('<div class="sub-header">Tablas disponibles</div>', unsafe_allow_html=True)
    
    @st.cache_data(ttl=600)
    def get_tables_info(db_name):
        conn = get_connection(db_name)
        query = f"""
        SELECT 
            table_name as 'Tabla', 
            table_rows as 'Filas',
            ROUND((data_length + index_length) / 1024 / 1024, 2) as 'Tamaño (MB)'
        FROM information_schema.tables
        WHERE table_schema = '{db_name}'
        ORDER BY (data_length + index_length) DESC
        """
        return conn.query(query)
    
    try:
        tables_info = get_tables_info(selected_db)
        st.dataframe(tables_info, use_container_width=True)
    except Exception as e:
        st.error(f"Error al obtener información de las tablas: {e}")

