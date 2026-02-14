import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN Y CONEXIÓN (Sin librerías conflictivas)
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. BUSCADOR INTERNO DE NOMBRES
def buscar_nombre_proximo(lat_clic, lon_clic, tabla):
    if tabla.empty: return ""
    # Si pinchas a menos de 40 metros de un bar existente, sugiere ese nombre
    margen = 0.0004 
    cerca = tabla[(abs(tabla['LAT'] - lat_clic) < margen) & (abs(tabla['LON'] - lon_clic) < margen)]
    return cerca.iloc[0]['Nombre'] if not cerca.empty else ""

# 3. ICONOS MEJORADOS
def obtener_icono(formato):
    formato = str(formato)
    if "Botella" in formato and "Vasos" not in formato:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        # Icono de copa/vaso sólido que no falla nunca
        return folium.Icon(color="blue", icon="glass-martini", prefix="fa", icon_color="white")

# 4. MAPA
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google',
    max_zoom = 20,
    control = False
).add_to(m)

# 5. DIBUJAR MARCADORES (CON FECHA VISIBLE)
for i, row in df_mapa.iterrows():
    fecha = row.get('Fecha_registro', '---')
    texto = f"<b>{row['Nombre']}</b><br>Sidra: {row['Marca']}<br><small>Fecha: {fecha}</small>"
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(texto, max_width=200),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. LÓGICA DE CLIC
if 'nombre_sugerido' not in st.session_state:
    st.session_state.nombre_sugerido = ""

salida_mapa = st_folium(m, width="100%", height=500)

lat_clic, lon_clic = None, None
if salida_mapa and salida_mapa["last_clicked"]:
    lat_clic = salida_mapa["last_clicked"]["lat"]
    lon_clic = salida_mapa["last_clicked"]["lng"]
    # Si pinchas cerca de un bar que ya está en el Excel, rellena el nombre
    st.session_state.nombre_sugerido = buscar_nombre_proximo(lat_clic, lon_clic, df_mapa)

# 7. FORMULARIO
st.divider()
with st.form("nuevo_pote", clear_on_submit=True):
    st.subheader("➕ Registrar Bar")
    c1, c2 = st.columns(2)
    with c1:
        nombre_form = st.text_input("Nombre del Bar", value=st.session_state.nombre_sugerido)
        marca_form = st.text_input("Marca de Sidra")
    with c2:
        formato_form = st.radio("¿Qué sirven?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    obs_form = st.text_area("Observaciones")
    
    if st.form_submit_button("Guardar Datos"):
        if nombre_form and lat_clic:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre_form, "LAT": lat_clic, "LON": lon_clic,
                "Marca": marca_form, "Formato": formato_form,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": obs_form
            }])
            df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.session_state.nombre_sugerido = ""
            st.success("¡Información guardada!")
            st.rerun()

# 8. TABLA DE HISTORIAL
st.write("### 📜 Listado de la Ruta")
st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], use_container_width=True)
