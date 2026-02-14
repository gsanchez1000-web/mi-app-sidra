import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Haz clic en el mapa para situar un bar y rellena los datos abajo manualmente.")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza de coordenadas
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. MAPA SATÉLITE
centro_barakaldo = [43.2960, -2.9975]
m = folium.Map(location=centro_barakaldo, zoom_start=18, tiles=None)

folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. ICONOS (VASO LIMPIO VS BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Icono de vaso ancho sin marcas internas
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. MARCADORES CON FECHA
for i, row in df_mapa.iterrows():
    fecha_reg = row.get('Fecha_registro', '---')
    popup_html = f"""
    <div style='font-family: sans-serif; min-width: 140px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}<br>
        <hr style='margin:5px 0;'>
        <small style='color: #666;'>Registrado: {fecha_reg}</small>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. VISUALIZACIÓN Y CAPTURA
salida_mapa = st_folium(m, width="100%", height=500)

lat_c, lon_c = None, None
if salida_mapa and salida_mapa["last_clicked"]:
    lat_c = salida_mapa["last_clicked"]["lat"]
    lon_c = salida_mapa["last_clicked"]["lng"]
    st.info("📍 Punto seleccionado. Escribe el nombre del bar abajo.")

# 6. FORMULARIO MANUAL
st.divider()
with st.form("registro_bar", clear_on_submit=True):
    st.subheader("➕ Añadir Bar")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Sidra")
    with col2:
        formato = st.radio("¿Qué tienen?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    observaciones = st.text_area("Notas")
    
    if st.form_submit_button("Guardar"):
        if nombre and lat_c:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": lat_c, "LON": lon_c,
                "Marca": marca, "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.success("¡Guardado!")
            st.rerun()

# 7. TABLA DE HISTORIAL
st.write("### 📜 Listado de Bares")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
