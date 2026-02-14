import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# CSS para que el botón + parezca un botón de acción principal
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #d35400; color: white; border-radius: 20px;
        width: 100%; font-weight: bold; border: None;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar estados de navegación
if 'modo' not in st.session_state:
    st.session_state.modo = "inicio"  # inicio o registro
if 'coords_nuevas' not in st.session_state:
    st.session_state.coords_nuevas = None

# 2. DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")
df_mapa = df_raw.copy()
df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# --- FUNCIONES AUXILIARES ---
def volver_inicio():
    st.session_state.modo = "inicio"
    st.session_state.coords_nuevas = None
    st.rerun()

# --- FLUJO DE PANTALLAS ---

# PANTALLA A: FORMULARIO DE REGISTRO
if st.session_state.modo == "registro":
    st.header("📝 Registrar Nuevo Bar")
    st.write(f"📍 Coordenadas: `{st.session_state.coords_nuevas}`")
    
    with st.form("form_alta"):
        nombre = st.text_input("Nombre del Bar")
        marca = st.text_input("Marca de Sidra")
        formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
        obs = st.text_area("Observaciones")
        
        col_f1, col_f2 = st.columns(2)
        if col_f1.form_submit_button("✅ Registrar Bar"):
            if nombre:
                nueva_fila = pd.DataFrame([{
                    "Nombre": nombre,
                    "LAT": st.session_state.coords_nuevas[0],
                    "LON": st.session_state.coords_nuevas[1],
                    "Marca": marca, "Formato": formato,
                    "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                    "Observaciones": obs
                }])
                df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                conn.update(data=df_final)
                st.success("¡Guardado!")
                volver_inicio()
            else:
                st.error("El nombre es obligatorio")
        
        if col_f2.form_submit_button("❌ Cancelar"):
            volver_inicio()

# PANTALLA B: INICIO (MAPA / LISTADO)
else:
    tab1, tab2 = st.tabs(["🗺️ Mapa", "📜 Listado"])
    
    with tab1:
        # Mapa principal
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
        
        salida = st_folium(m, width="100%", height=500, key="mapa_principal")
        
        # Botón de añadir
        st.write(" ")
        if st.button("➕ AÑADIR NUEVO BAR"):
            st.warning("Pulsa ahora en el mapa donde está el bar y luego dale a 'Confirmar Ubicación'")
            
        if salida and salida["last_clicked"]:
            st.session_state.coords_nuevas = (salida["last_clicked"]["lat"], salida["last_clicked"]["lng"])
            if st.button(f"📍 Confirmar ubicación en {st.session_state.coords_nuevas}"):
                st.session_state.modo = "registro"
                st.rerun()

    with tab2:
        st.subheader("Bares en la zona")
        st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True)
