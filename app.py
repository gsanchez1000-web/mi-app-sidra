import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Configuración de la interfaz
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# 1. CONEXIÓN Y DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. FUNCIÓN PARA OBTENER DIRECCIÓN AUTOMÁTICA
def obtener_nombre_calle(lat, lon):
    try:
        geolocator = Nominatim(user_agent="sidra_app")
        location = geolocator.reverse((lat, lon), timeout=3)
        # Intentamos sacar el nombre del local si Google/OSM lo tiene
        address = location.raw.get('address', {})
        return address.get('amenity') or address.get('shop') or address.get('road', "Nuevo punto")
    except:
        return ""

# 3. MAPA SATÉLITE
centro = [43.2960, -2.9975]
m = folium.Map(location=centro, zoom_start=18, tiles=None)
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    max_zoom = 20,
    control = False
).add_to(m)

# 4. ICONOS
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 5. MARCADORES (Con Fecha visible)
for i, row in df_mapa.iterrows():
    fecha_str = row['Fecha_registro'] if 'Fecha_registro' in row else "Sin fecha"
    popup_html = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <p style='margin:5px 0;'><b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}</p>
        <p style='font-size: 0.85em; color: #666;'><i>{row['Observaciones']}</i></p>
        <hr style='margin:5px 0;'>
        <span style='font-size: 0.75em; color: #999;'>Registrado el: {fecha_str}</span>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 6. CAPTURA DE CLIC Y AUTOCOMPLETADO
salida = st_folium(m, width="100%", height=500)

# Inicializamos variables en el estado de la sesión para el formulario
if 'nombre_auto' not in st.session_state:
    st.session_state.nombre_auto = ""

lat_sel, lon_sel = None, None
if salida and salida["last_clicked"]:
    lat_sel = salida["last_clicked"]["lat"]
    lon_sel = salida["last_clicked"]["lng"]
    # Buscamos el nombre de la calle/local automáticamente
    st.session_state.nombre_auto = obtener_nombre_calle(lat_sel, lon_sel)
    st.success(f"📍 Seleccionado: {st.session_state.nombre_auto}")

# 7. FORMULARIO
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Registrar Parada")
    
    col1, col2 = st.columns(2)
    with col1:
        # El nombre se rellena solo si hemos pinchado en el mapa
        nombre = st.text_input("Nombre del establecimiento", value=st.session_state.nombre_auto)
        marca = st.text_input("Marca de Sidra")
    
    with col2:
        formato = st.radio("¿Cómo la sirven?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
    
    observaciones = st.text_area("Notas")
    
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat_sel:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "LAT": float(lat_sel), "LON": float(lon_sel),
                "Marca": marca, "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            st.balloons()
            st.session_state.nombre_auto = "" # Limpiamos para el siguiente
            st.rerun()

# 8. TABLA (Donde también se ve la fecha)
with st.expander("Ver historial completo de registros"):
    columnas_ver = ['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']
    st.dataframe(df_mapa[columnas_ver], use_container_width=True)
