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

# Limpieza de coordenadas
df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA
centro_barakaldo = [43.2960, -2.9975]
m = folium.Map(location=centro_barakaldo, zoom_start=17, tiles=None)

# Satélite Google
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    name = 'Google Satellite',
    max_zoom = 20,
    overlay = False,
    control = False
).add_to(m)

# 3. LÓGICA DE ICONOS (ESTÁNDAR Y FIABLES)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    # SI ES SOLO BOTELLA: Fondo Verde, Icono Gota blanca (tint)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="tint", prefix="glyphicon", icon_color="white")
    # SI ES POTE/VASO: Fondo Azul, Icono Vaso blanco (glass)
    else:
        return folium.Icon(color="blue", icon="glass", prefix="glyphicon", icon_color="white")

# 4. DIBUJAR LOS BARES
for i, row in df_mapa.iterrows():
    popup_html = f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}"
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_html, max_width=200),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. MOSTRAR MAPA Y CAPTURAR CLIC
salida_mapa = st_folium(m, width="100%", height=550)

lat_sel, lon_sel = None, None
if salida_mapa and salida_mapa["last_clicked"]:
    lat_sel = salida_mapa["last_clicked"]["lat"]
    lon_sel = salida_mapa["last_clicked"]["lng"]
    st.success(f"📍 Ubicación marcada correctamente.")

# 6. FORMULARIO
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Añadir Bar")
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Sidra")
    with c2:
        formato = st.radio("¿Qué tienen?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    if st.form_submit_button("Guardar"):
        if nombre and lat_sel:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": float(lat_sel), "LON": float(lon_sel),
                "Marca": marca, "Formato": formato, "Fecha_registro": datetime.now().strftime("%d/%m/%Y")
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.rerun()

st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato']])
