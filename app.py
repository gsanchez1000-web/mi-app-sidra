import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la página
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Haz clic en el mapa para situar un bar y rellena los datos abajo.")

# 1. CONEXIÓN CON GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza de datos (coordenadas)
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. MAPA SATÉLITE DE GOOGLE
centro_barakaldo = [43.2960, -2.9975]
m = folium.Map(location=centro_barakaldo, zoom_start=18, tiles=None)

folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    name = 'Google Satellite',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. ICONOS (VASO DE SIDRA Y BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    # Verde para botella, Azul para vasos
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Este icono es el vaso ancho y limpio que buscábamos
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. DIBUJAR MARCADORES (Con Fecha visible)
for i, row in df_mapa.iterrows():
    fecha_reg = row.get('Fecha_registro', '---')
    popup_info = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <p style='margin:5px 0;'><b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}</p>
        <p style='font-size: 0.85em; color: #666;'><i>{row['Observaciones']}</i></p>
        <hr style='margin:5px 0;'>
        <span style='font-size: 0.75em; color: #999;'>Registrado el: {fecha_reg}</span>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_info, max_width=300),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA Y CAPTURAR POSICIÓN
salida_mapa = st_folium(m, width="100%", height=550)

lat_clic = None
lon_clic = None

if salida_mapa and salida_mapa["last_clicked"]:
    lat_clic = salida_mapa["last_clicked"]["lat"]
    lon_clic = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Ubicación capturada. ¡Ponle nombre al bar abajo!")

# 6. FORMULARIO MANUAL
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Añadir nueva parada a la ruta")
    
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre del bar")
        marca = st.text_input("Marca de sidra")
    
    with c2:
        formato = st.radio(
            "¿Cómo sirven la sidra?",
            ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"]
        )
    
    observaciones = st.text_area("Observaciones (Pinchos, ambiente...)")
    
    if st.form_submit_button("Guardar en 'Temas Varios'"):
        if nombre and lat_clic:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre,
                "LAT": float(lat_clic),
                "LON": float(lon_clic),
                "Marca": marca,
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            
            df_actualizado = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_actualizado)
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ Recuerda tocar primero el mapa para situar el bar y escribir su nombre.")

# 7. TABLA DE DATOS
with st.expander("Ver lista completa de bares registrados"):
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
