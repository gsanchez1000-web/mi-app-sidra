import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la interfaz
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")

# 1. CONEXIÓN Y LIMPIEZA DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
# Aseguramos que las coordenadas sean números
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA SATÉLITE
centro = [43.2960, -2.9975] 
m = folium.Map(location=centro, zoom_start=18, tiles=None)

folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    name = 'Google Satellite',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. FUNCIÓN DE ICONOS
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    else:
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. COLOCAR MARCADORES (Con Fecha de registro)
for i, row in df_mapa.iterrows():
    fecha_reg = row.get('Fecha_registro', '---')
    popup_info = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <p style='margin:5px 0;'><b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}</p>
        <p style='margin:5px 0; font-size: 0.9em; color: #666;'><i>{row['Observaciones']}</i></p>
        <hr style='margin:5px 0;'>
        <div style='font-size: 0.8em; color: #999;'>Registrado: {fecha_reg}</div>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_info, max_width=300),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. VISUALIZACIÓN DEL MAPA
# Usamos un key para mantener la estabilidad del Punto de Control 1
salida = st_folium(m, width="100%", height=550, key="mapa_sidra_control1")

# 6. LÓGICA DE FORMULARIO CONDICIONAL
if salida and salida["last_clicked"]:
    lat_sel = salida["last_clicked"]["lat"]
    lon_sel = salida["last_clicked"]["lng"]
    
    # Buscamos si el clic está sobre un bar que ya existe
    margen = 0.00015
    punto_existente = df_mapa[
        (abs(df_mapa['LAT'] - lat_sel) < margen) & 
        (abs(df_mapa['LON'] - lon_sel) < margen)
    ]
    
    # EL FORMULARIO SOLO APARECE SI EL PUNTO ESTÁ VACÍO
    if punto_existente.empty:
        st.divider()
        st.info("📍 ¡Sitio nuevo detectado! Rellena los datos para guardarlo en la ruta.")
        with st.form("nuevo_bar_control1", clear_on_submit=True):
            st.subheader("➕ Registrar nueva parada")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del establecimiento")
                marca = st.text_input("Marca de Sidra")
            with col2:
                formato = st.radio("¿Cómo la sirven?", ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"])
            
            observaciones = st.text_area("Notas sobre la sidra o el sitio")
            
            if st.form_submit_button("Guardar en mi Excel"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre,
                        "LAT": float(lat_sel),
                        "LON": float(lon_sel),
                        "Marca": marca,
                        "Formato": formato,
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": observaciones
                    }])
                    df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(data=df_act)
                    st.balloons()
                    st.rerun()
                else:
                    st.error("⚠️ El nombre es obligatorio para guardar.")
    else:
        # Si ya existe, simplemente mostramos el nombre arriba como confirmación
        st.write(f"🔎 Estás consultando: **{punto_existente.iloc[0]['Nombre']}**")

# 7. TABLA DE DATOS (Expandible para no molestar)
st.divider()
with st.expander("📜 Ver listado completo y fechas"):
    st.dataframe(
        df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], 
        use_container_width=True
    )
