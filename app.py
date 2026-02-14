import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# CSS para fijar la chincheta exactamente en el centro del visor del mapa
st.markdown("""
    <style>
    .map-wrapper {
        position: relative;
        width: 100%;
        height: 450px;
        margin-top: 10px;
    }
    .floating-pin {
        position: absolute;
        top: 50%;
        left: 50%;
        /* El secreto: -50% horizontal y -100% vertical para que la PUNTA sea el centro */
        transform: translate(-50%, -100%); 
        z-index: 9999;
        pointer-events: none;
        font-size: 50px;
        filter: drop-shadow(2px 4px 3px rgba(0,0,0,0.5));
    }
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 12px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
        box-shadow: 0 4px 15px rgba(211, 84, 0, 0.3);
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")
df_mapa = df_raw.copy()
df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. NAVEGACIÓN
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Menú Principal", ["🗺️ Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Mapa":
    st.subheader("Nuestros Bares")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']],
            popup=f"<b>{row['Nombre']}</b>",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_ver")

elif menu == "📜 Listado":
    st.subheader("Resumen de la Ruta")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], 
                 use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.markdown("#### 📍 Sitúa el bar bajo la chincheta")
        
        # Envoltorio visual para que la chincheta no flote en el aire
        st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)
        st.markdown('<div class="floating-pin">📍</div>', unsafe_allow_html=True)
        
        # Mapa centrado en San Vicente
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        # Captura del centro del mapa en tiempo real
        salida_sel = st_folium(m_sel, width="100%", height=450, key="mapa_chincheta_ajustada")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if salida_sel and salida_sel.get("center"):
            c_lat = salida_sel["center"]["lat"]
            c_lng = salida_sel["center"]["lng"]
            
            # Botón naranja destacado
            if st.button("🎯 Seleccionar este Bar", type="primary"):
                st.session_state.temp_coords = (c_lat, c_lng)
                st.rerun()
    else:
        # PANTALLA DE FORMULARIO INDEPENDIENTE
        st.subheader("📝 Registro del Nuevo Bar")
        with st.form("registro_final"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("¿Cómo se sirve?", ["Vaso (Pote)", "Solo Botella entera"])
            obs = st.text_area("Notas / Observaciones")
            
            c_f1, c_f2 = st.columns(2)
            if c_f1.form_submit_button("✅ Registrar Bar"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre,
                        "LAT": st.session_state.temp_coords[0],
                        "LON": st.session_state.temp_coords[1],
                        "Marca": marca, "Formato": formato,
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": obs
                    }])
                    df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Por favor, introduce el nombre del bar.")
            
            if c_f2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
