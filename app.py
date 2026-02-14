import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# Conexión con el Excel
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. MAPA SATÉLITE
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)

folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. ICONOS (Vaso y Botella)
def obtener_icono(formato):
    formato = str(formato)
    if "Botella" in formato and "Vasos" not in formato:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. MARCADORES EXISTENTES
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    popup_text = f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br><small>Registrado: {fecha}</small>"
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_text, max_width=200),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA
salida = st_folium(m, width="100%", height=550, key="mapa_sidra")

# 6. LÓGICA DEL FORMULARIO CONDICIONAL
# Solo mostramos el formulario si se ha pinchado en el mapa
if salida and salida["last_clicked"]:
    lat_clic = salida["last_clicked"]["lat"]
    lon_clic = salida["last_clicked"]["lng"]
    
    # Comprobamos si el punto pinchado ya existe (con un pequeño margen de error)
    margen = 0.0001
    existe = df_mapa[
        (abs(df_mapa['LAT'] - lat_clic) < margen) & 
        (abs(df_mapa['LON'] - lon_clic) < margen)
    ]
    
    if existe.empty:
        # SI NO EXISTE: Mostramos el formulario para registrarlo
        st.success("📍 Has seleccionado un punto nuevo. ¡Regístralo aquí!")
        with st.form("nuevo_registro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del bar")
                marca = st.text_input("Marca de sidra")
            with col2:
                formato = st.radio("¿Cómo la sirven?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
            
            notas = st.text_area("Observaciones")
            
            if st.form_submit_button("Guardar en la Ruta"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre, "LAT": lat_clic, "LON": lon_clic,
                        "Marca": marca, "Formato": formato,
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": notas
                    }])
                    df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Por favor, escribe al menos el nombre del bar.")
    else:
        # SI YA EXISTE: Solo mostramos la info (o nada, para que el mapa mande)
        st.info(f"Vas a ver la info de: **{existe.iloc[0]['Nombre']}** en el mapa.")

# 7. TABLA (Solo visible si quieres expandirla)
with st.expander("📜 Ver listado completo"):
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True)
