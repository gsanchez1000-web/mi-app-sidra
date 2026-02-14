import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración visual de la app
st.set_page_config(page_title="Ruta Sidrera", layout="wide")
st.title("🍎 Nuestra Ruta de la Sidra")

# 1. Conexión con tu Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Leer los datos que ya existan en la hoja
df = conn.read(ttl="0")

# 3. Mostrar el Mapa
st.subheader("📍 Mapa de Bares")
if not df.empty:
    # Eliminamos filas que no tengan coordenadas para que el mapa no falle
    df_mapa = df.dropna(subset=['LAT', 'LON'])
    st.map(df_mapa, latitude='LAT', longitude='LON')

# 4. Formulario para añadir nuevos bares
st.divider()
with st.form("nuevo_bar"):
    st.write("### ➕ Añade un rincón sidrero")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Marca de Sidra")
    with col2:
        # Usamos 0.0000 como valor inicial para las coordenadas
        lat = st.number_input("Latitud (ej: 43.3600)", format="%.4f", value=0.0)
        lon = st.number_input("Longitud (ej: -5.8400)", format="%.4f", value=0.0)
    
    formato = st.selectbox("¿Cómo la sirven?", ["Pote/Vaso", "Botella entera", "Ambos"])
    observaciones = st.text_area("Observaciones (comentarios, tapas, recomendaciones...)")
    
    # Botón para guardar
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat != 0:
            # Creamos la fila con todas tus columnas (de la A a la G)
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, 
                "LAT": lat, 
                "LON": lon, 
                "Marca": marca, 
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            
            # Unimos los datos nuevos con los viejos y actualizamos el Excel
            df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df_actualizado)
            
            st.success(f"¡{nombre} se ha guardado con éxito!")
            st.rerun() # Refresca la app para que aparezca el nuevo punto
        else:
            st.error("Por favor, rellena el Nombre y asegúrate de que la Latitud no sea 0.")

# 5. Tabla con el listado completo para leer las observaciones
st.write("### 📜 Listado detallado")
st.dataframe(df, use_container_width=True)
