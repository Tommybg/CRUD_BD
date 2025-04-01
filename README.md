# Explorador Avanzado MySQL

Este proyecto es una herramienta interactiva desarrollada con Streamlit que te permite explorar bases de datos MySQL de manera eficiente. A continuación, se detallan las funcionalidades que ofrece esta aplicación:

1. **Conexión Segura**: Puedes conectarte a un servidor MySQL utilizando credenciales seguras que se almacenan en un archivo `.env`. Asegúrate de que este archivo contenga las variables necesarias para la conexión.

2. **Visualización de Datos**: La aplicación te permite visualizar tanto la estructura como los datos de las tablas en la base de datos seleccionada, facilitando la comprensión de la información almacenada.

3. **Ejecutar Consultas SQL**: Puedes ejecutar consultas SQL personalizadas, limitadas a consultas de tipo SELECT, para obtener información específica de las tablas.

4. **Gestión de Bases de Datos**: La herramienta también te permite crear nuevas bases de datos y tablas. 

## Requisitos

- **Python 3.7** o superior.
- **MySQL Server** en ejecución (local o remoto).
- Credenciales de acceso a MySQL (usuario: root y contraseña).

## Estructura del Proyecto

```plaintext
explorador_mysql/
├── main.py
├── requirements.txt
└── README.md
```

- **main.py:** Contiene el código de la aplicación Streamlit para conectarse a MySQL, explorar bases de datos, tablas y ejecutar consultas.
- **requirements.txt:** Lista las dependencias necesarias para instalar y ejecutar la aplicación.
- **README.md:** Proporciona instrucciones para la instalación, configuración (incluyendo la creación del archivo `.env`) y ejecución del proyecto.

---

## Instalación

1. **Clonar el repositorio o descargar los archivos**

   ```bash
   git clone https://tu-repositorio-url.git
   cd explorador_mysql
   ```

2. **Crear un entorno virtual (opcional, pero recomendado):**

   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual:**

   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuración

1. **Crear el archivo `.env` en la raíz del proyecto.**

2. **Agregar la variable de entorno para la contraseña de MySQL:**

   ```
   CLAVE_SQL=tu_contraseña_segura
   ```

   *Asegúrate de reemplazar `tu_contraseña_segura` con la contraseña real de tu usuario MySQL.*

## Ejecución

Para iniciar la aplicación, ejecuta el siguiente comando:

```bash
streamlit run main.py
```

La aplicación se abrirá en tu navegador, normalmente en `http://localhost:8501`.

