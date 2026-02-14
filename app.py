import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la página
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")

st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Haz clic en el mapa para marcar la ubicación y rellena los datos abajo.")

# 1. CONEXIÓN CON GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

# Limpieza profunda de datos (evita errores de formato en el Excel)
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA (GOOGLE SATELLITE)
centro_barakaldo = [43.2960, -2.9975] # Centrado cerca de San Vicente
m = folium.Map(location=centro_barakaldo, zoom_start=17, tiles=None)

# Añadimos la capa de Google Satélite (Zoom hasta 20 para ver portales)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps Satellite',
    name = 'Google Satellite',
    max_zoom = 20,
    overlay = False,
    control = False
).add_to(m)

# 3. LÓGICA DE ICONOS (MÁXIMO CONTRASTE)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    # SI ES SOLO BOTELLA: Fondo Verde, Icono Blanco
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    # SI ES POTE/VASO: Fondo Azul Oscuro, Icono Blanco
    else:
        return folium.Icon(color="cadetblue", icon="glass-half-full", prefix="fa", icon_color="white")

# 4. DIBUJAR LOS BARES EXISTENTES
for i, row in df_mapa.iterrows():
    popup_info = f"""
    <div style='font-family: sans-serif;'>
        <b>{row['Nombre']}</b><br>
        <b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}<br>
        <hr>
        <i>{row['Observaciones']}</i>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_info, max_width=250),
        tooltip=row['Nombre'], # Al pasar el ratón se ve el nombre
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA Y CAPTURAR CLIC
salida_mapa = st_folium(m, width="100%", height=550)

lat_seleccionada = None
lon_seleccionada = None

if salida_mapa and salida_mapa["last_clicked"]:
    lat_seleccionada = salida_mapa["last_clicked"]["lat"]
    lon_seleccionada = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Punto seleccionado: {lat_seleccionada:.5f}, {lon_seleccionada:.5f}")

# 6. FORMULARIO PARA REGISTRAR
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Añadir nuevo bar a la ruta")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Establecimiento")
        marca = st.text_input("Marca de Sidra")
    
    with col2:
        formato = st.radio(
            "¿Qué ofrecen?",
            ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"]
        )
    
    observaciones = st.text_area("Observaciones (Pinchos, ambiente, etc.)")
    
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat_seleccionada:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre,
                "LAT": float(lat_seleccionada),
                "LON": float(lon_seleccionada),
                "Marca": marca,
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.balloons()
            st.success("✅ ¡Guardado! El mapa se está actualizando...")
            st.rerun()
        else:
            st.warning("⚠️ Recuerda marcar el punto en el mapa y poner el nombre.")

# 7. LISTADO INFERIOR
with st.expander("Ver lista de todos los bares"):
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Observaciones']], use_container_width=True)
