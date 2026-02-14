import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN E INTERFAZ INCLUSIVA
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilos para que los botones sean cómodos y el cursor sea claro
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 12px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
    }
    /* Indicador visual para que el mapa se sienta interactivo */
    .leaflet-container {
        cursor: crosshair !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN Y CARGA DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargamos los datos actuales
# Nota: "Ruta de sidreria colaborativa" es el nombre de la hoja (pestaña)
df_raw = conn.read(worksheet="Ruta de sidreria colaborativa", ttl="0")
df_mapa = df_raw.copy()

# Limpieza de coordenadas para que el mapa no falle
if not df_mapa.empty:
    df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
    df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. CONTROL DE ESTADO
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

# Menú superior
menu = st.radio("Menú", ["🗺️ Ver Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- LÓGICA DE PANTALLAS ---

if menu == "🗺️ Ver Mapa":
    st.subheader("Lugares registrados por nuestra comunidad")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=17, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']], 
            popup=f"<b>{row['Nombre']}</b><br>{row['Marca']}",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width="100%", height=550, key="mapa_lectura")

elif menu == "📜 Listado":
    st.subheader("Historial de la ruta")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro', 'Observaciones']], 
                 use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.info("📍 **Paso 1:** Busca el bar en el mapa y **pulsa sobre él** para seleccionarlo.")
        
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        # Captura el toque en el móvil o clic en PC
        salida_sel = st_folium(m_sel, width="100%", height=500, key="mapa_interactivo")
        
        if salida_sel and salida_sel.get("last_clicked"):
            st.session_state.temp_coords = (
                salida_sel["last_clicked"]["lat"], 
                salida_sel["last_clicked"]["lng"]
            )
            st.rerun()
            
    else:
        # PANTALLA DE FORMULARIO
        st.subheader("📝 Paso 2: Datos del bar seleccionado")
        
        with st.form("formulario_registro", clear_on_submit=True):
            nombre = st.text_input("¿Cómo se llama el establecimiento?")
            marca = st.text_input("¿Qué marca de sidra ofrecen?")
            formato = st.radio("¿En qué formato?", ["Vaso (Pote)", "Botella entera"])
            observaciones = st.text_area("¿Alguna nota extra para el grupo?")
            
            col1, col2 = st.columns(2)
            
            if col1.form_submit_button("✅ Guardar"):
                if nombre:
                    try:
                        # Creamos la fila asegurando formatos correctos
                        nueva_fila = pd.DataFrame([{
                            "Nombre": str(nombre),
                            "LAT": float(st.session_state.temp_coords[0]),
                            "LON": float(st.session_state.temp_coords[1]),
                            "Marca": str(marca),
                            "Formato": str(formato),
                            "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                            "Observaciones": str(observaciones)
                        }])
                        
                        # Combinamos con los datos existentes
                        df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                        
                        # ACTUALIZACIÓN: Apuntamos al nombre exacto de tu hoja
                        conn.update(worksheet="Ruta de sidreria colaborativa", data=df_final)
                        
                        st.session_state.temp_coords = None
                        st.balloons()
                        st.success("¡Información guardada con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al intentar guardar en la hoja: {e}")
                else:
                    st.warning("El nombre es necesario para el registro.")
            
            if col2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
