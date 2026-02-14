import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la página
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")

st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Haz clic en el mapa para situar un nuevo bar y completa los datos abajo.")

# 1. CONEXIÓN CON GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza profunda de coordenadas para evitar el ValueError
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA (GOOGLE SATELLITE)
centro_barakaldo = [43.2960, -2.9975]
m = folium.Map(location=centro_barakaldo, zoom_start=17, tiles=None)

# Capa Satélite Google de alta resolución
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps Satellite',
    name = 'Google Satellite',
    max_zoom = 20,
    overlay = False,
    control = False
).add_to(m)

# 3. LÓGICA DE ICONOS (VASO Y BOTELLA DIBUJADOS EN BLANCO)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    # SI ES SOLO BOTELLA: Fondo Verde, Icono Blanco
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    # SI ES POTE/VASO: Fondo Azul, Icono Blanco
    else:
        return folium.Icon(color="blue", icon="glass-half-full", prefix="fa", icon_color="white")

# 4. DIBUJAR LOS BARES EXISTENTES
for i, row in df_mapa.iterrows():
    popup_html = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <p style='margin:5px 0;'><b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}</p>
        <i style='color: #666;'>{row['Observaciones']}</i>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA Y CAPTURAR CLIC
salida_mapa = st_folium(m, width="100%", height=550)

lat_seleccionada = None
lon_seleccionada = None

if salida_mapa and salida_mapa["last_clicked"]:
    lat_seleccionada = salida_mapa["last_clicked"]["lat"]
    lon_seleccionada = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Ubicación marcada. Ahora rellena el formulario abajo.")

# 6. FORMULARIO
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Añadir Bar a la Ruta")
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Marca de Sidra")
    with c2:
        formato = st.radio("¿Qué sirven?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar en el Excel"):
        if nombre and lat_seleccionada:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": float(lat_seleccionada), "LON": float(lon_seleccionada),
                "Marca": marca, "Formato": formato, "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ Selecciona el punto en el mapa y escribe el nombre.")

# 7. TABLA
with st.expander("Ver tabla completa"):
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Observaciones']], use_container_width=True)
