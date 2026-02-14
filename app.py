import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN Y DATOS
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. FUNCIÓN PARA BUSCAR SI EL BAR YA EXISTE CERCA
def buscar_nombre_cercano(lat_clic, lon_clic, df_puntos):
    if df_puntos.empty: return ""
    # Buscamos si hay algún bar a menos de unos metros
    umbral = 0.0005 
    cercanos = df_puntos[
        (abs(df_puntos['LAT'] - lat_clic) < umbral) & 
        (abs(df_puntos['LON'] - lon_clic) < umbral)
    ]
    if not cercanos.empty:
        return cercanos.iloc[0]['Nombre']
    return ""

# 3. ICONOS (VASO DE SIDRA LIMPIO)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # 'glass-martini' es el más fiable para que salga un vaso blanco sin fallos
        return folium.Icon(color="blue", icon="glass-martini", prefix="fa", icon_color="white")

# 4. MAPA SATÉLITE
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    max_zoom = 20,
    control = False
).add_to(m)

# 5. DIBUJAR MARCADORES (CON FECHA)
for i, row in df_mapa.iterrows():
    fecha_reg = row.get('Fecha_registro', '---')
    popup_text = f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br><small>Fecha: {fecha_reg}</small>"
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_text, max_width=200),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. CAPTURA DE CLIC
if 'nombre_sugerido' not in st.session_state:
    st.session_state.nombre_sugerido = ""

mapa_render = st_folium(m, width="100%", height=500)

lat_c, lon_c = None, None
if mapa_render and mapa_render["last_clicked"]:
    lat_c = mapa_render["last_clicked"]["lat"]
    lon_c = mapa_render["last_clicked"]["lng"]
    # Autocompletado: Si pinchas en uno existente, pilla el nombre
    st.session_state.nombre_sugerido = buscar_nombre_cercano(lat_c, lon_c, df_mapa)

# 7. FORMULARIO
st.divider()
with st.form("registro", clear_on_submit=True):
    st.subheader("➕ Registrar Parada")
    col1, col2 = st.columns(2)
    with col1:
        nombre_form = st.text_input("Nombre del Bar", value=st.session_state.nombre_sugerido)
        marca_form = st.text_input("Marca de Sidra")
    with col2:
        formato_form = st.radio("¿Qué tienen?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs_form = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar"):
        if nombre_form and lat_c:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre_form, "LAT": lat_c, "LON": lon_c,
                "Marca": marca_form, "Formato": formato_form,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs_form
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.session_state.nombre_sugerido = "" 
            st.success("¡Guardado!")
            st.rerun()

# 8. TABLA
st.write("### 📜 Historial")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
