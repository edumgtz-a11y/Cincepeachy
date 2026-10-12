import streamlit as st
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DATA_FILE = "data.json"

MESES_ESPANOL = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def limitar_a_ultimos_10_pedidos(datos):
    semanas = datos.get("semanas", {})
    if len(semanas) > 10:
        llaves = list(semanas.keys())
        llaves_a_mantener = llaves[-10:]
        datos["semanas"] = {k: semanas[k] for k in llaves_a_mantener}
    return datos

def obtener_nombre_semana_auto(datos):
    ahora = datetime.now()
    mes_nombre = MESES_ESPANOL[ahora.month].lower()
    semanas_existentes = list(datos.get("semanas", {}).keys())
    semanas_este_mes = [s for s in semanas_existentes if mes_nombre in s.lower()]
    siguiente_numero = len(semanas_este_mes) + 1
    return f"Pedido {siguiente_numero} {mes_nombre.capitalize()}"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
            return limitar_a_ultimos_10_pedidos(datos)
    
    ahora = datetime.now()
    mes_nombre = MESES_ESPANOL[ahora.month].lower()
    semana_inicial = f"Pedido 1 {mes_nombre.capitalize()}"
    
    datos_iniciales = {
        "clientes": ["Chusita", "Esme", "Juanita", "Ana"],
        "semanas": {
            semana_inicial: {
                "Papel": {
                    "tipo": "normal",
                    "precio": 40.0,
                    "costo_inversion": 100.0,
                    "fecha_llegada": "Por definir",
                    "clientes": {"Chusita": 1, "Esme": 2, "Juanita": 3}
                },
                "Pistaches": {
                    "tipo": "normal",
                    "precio": 90.0,
                    "costo_inversion": 500.0,
                    "fecha_llegada": "Por definir",
                    "clientes": {"Chusita": 1, "Juanita": 1, "Ana": 1}
                }
            }
        }
    }
    return limitar_a_ultimos_10_pedidos(datos_iniciales)

def guardar_datos(datos):
    datos = limitar_a_ultimos_10_pedidos(datos)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def generar_pdf_resumen_semana(datos, semana_nombre):
    pdf_filename = "temp_resumen.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=14, alignment=1, spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=15, textColor=colors.gray)
    cliente_style = ParagraphStyle('ClienteTitle', parent=styles['Heading2'], fontSize=11, spaceBefore=10, spaceAfter=4, textColor=colors.black)
    
    story.append(Paragraph(f"RESUMEN DE CUENTAS - {semana_nombre.upper()}", titulo_style))
    story.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))
    
    prods_en_sem = datos.get("semanas", {}).get(semana_nombre, {})
    
    cuentas_clientes = {}
    for p_nombre, p_info in prods_en_sem.items():
        tipo = p_info.get("tipo", "normal")
        clientes_dict = p_info.get("clientes", {})
        
        if tipo == "normal":
            precio = p_info.get("precio", 0.0)
            for cli, cant in clientes_dict.items():
                if cli not in cuentas_clientes:
                    cuentas_clientes[cli] = []
                subtotal = cant * precio
                cuentas_clientes[cli].append((p_nombre, cant, precio, subtotal))
        else:
            for cli, info_cli in clientes_dict.items():
                if cli not in cuentas_clientes:
                    cuentas_clientes[cli] = []
                if isinstance(info_cli, dict):
                    detalle = info_cli.get("detalle", "")
                    cant = info_cli.get("cantidad", 1)
                    precio = info_cli.get("precio", 0.0)
                    subtotal = cant * precio
                    nombre_prod_completo = f"{p_nombre} ({detalle})" if detalle else p_nombre
                    cuentas_clientes[cli].append((nombre_prod_completo, cant, precio, subtotal))
                else:
                    subtotal = info_cli * 0
                    cuentas_clientes[cli].append((p_nombre, info_cli, 0.0, subtotal))
            
    if not cuentas_clientes:
        story.append(Paragraph("No hay pedidos registrados en este ciclo.", styles['Italic']))
    else:
        gran_total = 0
        for cli in sorted(cuentas_clientes.keys()):
            items = cuentas_clientes[cli]
            total_cli = sum(item[3] for item in items)
            gran_total += total_cli
            
            story.append(Paragraph(f"CLIENTE: {cli.upper()}", cliente_style))
            
            table_data = [["Producto / Detalle", "Cantidad", "Precio U.", "Subtotal"]]
            for prod, cant, precio, subtotal in items:
                table_data.append([prod, str(cant), f"${precio:,.2f}", f"${subtotal:,.2f}"])
            
            table_data.append(["", "", "Total Cliente:", f"${total_cli:,.2f}"])
            
            t = Table(table_data, colWidths=[250, 70, 80, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('ALIGN', (3,1), (3,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
                ('LINEBELOW', (0,-1), (-1,-1), 1, colors.black),
                ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            
        story.append(Spacer(1, 10))
        t_total = Table([[f"GRAN TOTAL DEL PEDIDO: ${gran_total:,.2f}"]], colWidths=[500])
        t_total.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(t_total)
        
    doc.build(story)
    with open(pdf_filename, "rb") as f:
        pdf_bytes = f.read()
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    return pdf_bytes

st.set_page_config(page_title="Control de Pedidos", page_icon="📦", layout="wide")

if "data" not in st.session_state:
    st.session_state.data = cargar_datos()

datos = st.session_state.data

st.title("📦 Control de Pedidos Semanales")

if "semanas" not in datos or not datos["semanas"]:
    semana_inicial = f"Pedido 1 {MESES_ESPANOL[datetime.now().month].capitalize()}"
    datos["semanas"] = {semana_inicial: {}}

lista_semanas = list(datos["semanas"].keys())

st.sidebar.header("📅 Selección de Pedido / Semana")
semana_seleccionada = st.sidebar.selectbox(
    "Pedido Activo", 
    lista_semanas, 
    index=len(lista_semanas)-1
)

st.sidebar.markdown("#### ➕ Nuevo Ciclo de Pedido")
nombre_sugerido = obtener_nombre_semana_auto(datos)

with st.sidebar.form("form_nueva_semana"):
    nueva_semana_nombre = st.text_input("Nombre del pedido:", value=nombre_sugerido)
    submit_semana = st.form_submit_button("➕ Aperturar Pedido")
    if submit_semana:
        if nueva_semana_nombre and nueva_semana_nombre not in datos["semanas"]:
            datos["semanas"][nueva_semana_nombre] = {}
            guardar_datos(datos)
            st.success(f"¡'{nueva_semana_nombre}' aperturado y guardado!")
            st.rerun()
        elif nueva_semana_nombre:
            st.warning("Ese ciclo de pedido ya existe.")

st.sidebar.divider()

st.sidebar.markdown("### 💾 Control y Exportación")
if st.sidebar.button("💾 Guardar Todos los Cambios Ahora", type="primary"):
    guardar_datos(datos)
    st.sidebar.success("¡Cambios guardados correctamente!")

pdf_bytes = generar_pdf_resumen_semana(datos, semana_seleccionada)
st.sidebar.download_button(
    label=f"📄 Descargar PDF Resumen ({semana_seleccionada})",
    data=pdf_bytes,
    file_name=f"Resumen_{semana_seleccionada.replace(' ', '_')}.pdf",
    mime="application/pdf"
)

tab_gestion, tab_buscador, tab_clientes = st.tabs([
    "📋 Gestión de Productos y Pedidos", 
    "🔍 Buscador y Cobros por Cliente",
    "👥 Registro Global de Clientes"
])

with tab_gestion:
    st.subheader(f"Trabajando en: {semana_seleccionada}")
    
    with st.expander("➕ Agregar Nuevo Producto a este Pedido", expanded=False):
        with st.form("form_nuevo_producto"):
            st.markdown("### Nuevo Producto / Categoría")
            nuevo_prod = st.text_input("Nombre del Producto o Catálogo (ej. Pistaches o Zapatos Andrea)")
            
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                costo_inv = st.number_input("Costo Total de Inversión / Proveedor ($)", min_value=0.0, step=10.0, value=0.0)
            with col_inf2:
                fecha_llegada = st.text_input("Fecha Estimada de Llegada (ej. 20 Octubre)", value="Por definir")
            
            es_catalogo = st.checkbox("¿Es producto de catálogo con precios individuales por cliente (ej. Zapatos Andrea)?")
            
            precio_base = 0.0
            if not es_catalogo:
                precio_base = st.number_input("Precio Estándar de Venta ($)", min_value=0.0, step=1.0, value=50.0)
            
            submit_prod = st.form_submit_button("Guardar Producto")
            
            if submit_prod:
                if nuevo_prod:
                    if nuevo_prod not in datos["semanas"][semana_seleccionada]:
                        datos["semanas"][semana_seleccionada][nuevo_prod] = {
                            "tipo": "catalogo" if es_catalogo else "normal",
                            "precio": precio_base if not es_catalogo else 0.0,
                            "costo_inversion": costo_inv,
                            "fecha_llegada": fecha_llegada,
                            "clientes": {}
                        }
                        guardar_datos(datos)
                        st.success(f"Producto '{nuevo_prod}' agregado y guardado.")
                        st.rerun()
                    else:
                        st.warning("El producto ya existe en este pedido.")
                else:
                    st.error("Escribe un nombre de producto válido.")

    productos_semana = datos["semanas"][semana_seleccionada]

    if not productos_semana:
        st.info("No hay productos registrados en este pedido todavía. Agrega uno arriba.")
    else:
        nombres_productos = list(productos_semana.keys())
        tabs_productos = st.tabs([f"🛍️ {p}" for p in nombres_productos])
        
        for idx, prod_nombre in enumerate(nombres_productos):
            with tabs_productos[idx]:
                prod_info = productos_semana[prod_nombre]
                tipo_prod = prod_info.get("tipo", "normal")
                costo_inversion = prod_info.get("costo_inversion", 0.0)
                fecha_llegada = prod_info.get("fecha_llegada", "Por definir")
                
                col_p_title, col_p_del = st.columns([3, 1])
                with col_p_title:
                    st.markdown(f"### Producto: **{prod_nombre}**")
                with col_p_del:
                    with st.form(f"form_eliminar_prod_{prod_nombre}"):
                        submit_del_prod = st.form_submit_button("🗑️ Eliminar Producto")
                        if submit_del_prod:
                            del datos["semanas"][semana_seleccionada][prod_nombre]
                            guardar_datos(datos)
                            st.success(f"Producto '{prod_nombre}' eliminado del pedido.")
                            st.rerun()

                st.info(f"📅 **Fecha de llegada:** {fecha_llegada}  |  💰 **Costo de Inversión al Proveedor:** ${costo_inversion:,.2f}")

                if tipo_prod == "normal":
                    with st.form(f"form_precio_{semana_seleccionada}_{prod_nombre}"):
                        cp1, cp2, cp3 = st.columns([2, 2, 1])
                        with cp1:
                            precio_actual = prod_info.get("precio", 0.0)
                            nuevo_precio_edit = st.number_input("Precio Estándar ($)", value=float(precio_actual), key=f"inp_precio_{prod_nombre}")
                        with cp2:
                            nuevo_costo_edit = st.number_input("Costo Inversión ($)", value=float(costo_inversion), key=f"inp_costo_{prod_nombre}")
                        with cp3:
                            nueva_fecha_edit = st.text_input("F. Llegada", value=fecha_llegada, key=f"inp_fecha_{prod_nombre}")
                        
                        submit_precio = st.form_submit_button("💾 Actualizar Datos")
                        if submit_precio:
                            datos["semanas"][semana_seleccionada][prod_nombre]["precio"] = nuevo_precio_edit
                            datos["semanas"][semana_seleccionada][prod_nombre]["costo_inversion"] = nuevo_costo_edit
                            datos["semanas"][semana_seleccionada][prod_nombre]["fecha_llegada"] = nueva_fecha_edit
                            guardar_datos(datos)
                            st.success(f"Datos de {prod_nombre} actualizados y guardados.")
                            st.rerun()
                else:
                    with st.form(f"form_info_cat_{prod_nombre}"):
                        cp1, cp2 = st.columns([2, 1])
                        with cp1:
                            nuevo_costo_edit = st.number_input("Costo Inversión al Proveedor ($)", value=float(costo_inversion), key=f"inp_costo_cat_{prod_nombre}")
                        with cp2:
                            nueva_fecha_edit = st.text_input("Fecha Llegada", value=fecha_llegada, key=f"inp_fecha_cat_{prod_nombre}")
                        
                        submit_info_cat = st.form_submit_button("💾 Actualizar Inversión y Fecha")
                        if submit_info_cat:
                            datos["semanas"][semana_seleccionada][prod_nombre]["costo_inversion"] = nuevo_costo_edit
                            datos["semanas"][semana_seleccionada][prod_nombre]["fecha_llegada"] = nueva_fecha_edit
                            guardar_datos(datos)
                            st.success(f"Información actualizada y guardada.")
                            st.rerun()

                st.divider()
                
                st.markdown("#### Registrar Cliente para este Producto")
                
                if tipo_prod == "normal":
                    with st.form(f"form_cliente_{prod_nombre}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        lista_clientes_global = datos.get("clientes", [])
                        
                        with c1:
                            cliente_elegido = st.selectbox("Seleccionar de Lista Guardada", options=["-- Seleccionar --"] + lista_clientes_global, key=f"sel_c_{prod_nombre}")
                            cliente_nuevo_input = st.text_input("O escribe un NUEVO cliente:", key=f"new_c_{prod_nombre}")
                        with c2:
                            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, key=f"cant_{prod_nombre}")
                        with c3:
                            st.write("")
                            st.write("")
                            submit_pedido = st.form_submit_button("➕ Anotar Pedido")
                        
                        if submit_pedido:
                            cliente_final = cliente_nuevo_input.strip() if cliente_nuevo_input.strip() else cliente_elegido
                            if cliente_final == "-- Seleccionar --" or not cliente_final:
                                st.error("Por favor selecciona o escribe un nombre de cliente válido.")
                            else:
                                if cliente_final not in datos["clientes"]:
                                    datos["clientes"].append(cliente_final)
                                
                                datos["semanas"][semana_seleccionada][prod_nombre]["clientes"][cliente_final] = cantidad
                                guardar_datos(datos)
                                st.success(f"¡Registrado {cantidad}x {prod_nombre} para {cliente_final}!")
                                st.rerun()
                else:
                    with st.form(f"form_cliente_cat_{prod_nombre}"):
                        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                        lista_clientes_global = datos.get("clientes", [])
                        
                        with c1:
                            cliente_elegido = st.selectbox("Cliente", options=["-- Seleccionar --"] + lista_clientes_global, key=f"sel_cc_{prod_nombre}")
                            cliente_nuevo_input = st.text_input("O nuevo cliente:", key=f"new_cc_{prod_nombre}")
                        with c2:
                            detalle_articulo = st.text_input("Detalle / Modelo (ej. Adidas 200)", key=f"det_{prod_nombre}")
                        with c3:
                            precio_articulo = st.number_input("Precio ($)", min_value=0.0, step=10.0, value=200.0, key=f"p_art_{prod_nombre}")
                        with c4:
                            cant_articulo = st.number_input("Cant.", min_value=1, value=1, step=1, key=f"cant_art_{prod_nombre}")
                        
                        submit_pedido_cat = st.form_submit_button("➕ Anotar Artículo de Catálogo")
                        
                        if submit_pedido_cat:
                            cliente_final = cliente_nuevo_input.strip() if cliente_nuevo_input.strip() else cliente_elegido
                            if cliente_final == "-- Seleccionar --" or not cliente_final:
                                st.error("Por favor selecciona o escribe un nombre de cliente válido.")
                            else:
                                if cliente_final not in datos["clientes"]:
                                    datos["clientes"].append(cliente_final)
                                
                                datos["semanas"][semana_seleccionada][prod_nombre]["clientes"][cliente_final] = {
                                    "detalle": detalle_articulo,
                                    "precio": precio_articulo,
                                    "cantidad": cant_articulo
                                }
                                guardar_datos(datos)
                                st.success(f"¡Registrado {detalle_articulo} para {cliente_final} ($ {precio_articulo:,.2f})!")
                                st.rerun()

                st.markdown("#### Clientes registrados en este producto:")
                pedidos_prod = prod_info["clientes"]
                
                if not pedidos_prod:
                    st.info("Aún no hay clientes anotados para este producto.")
                else:
                    data_tabla = []
                    if tipo_prod == "normal":
                        precio_unit = prod_info.get("precio", 0.0)
                        for cli, cant in pedidos_prod.items():
                            subtotal = cant * precio_unit
                            data_tabla.append({"Cliente": cli, "Cantidad": cant, "Precio U.": f"${precio_unit:,.2f}", "Subtotal ($)": f"${subtotal:,.2f}"})
                    else:
                        for cli, info in pedidos_prod.items():
                            if isinstance(info, dict):
                                det = info.get("detalle", "")
                                cant = info.get("cantidad", 1)
                                prec = info.get("precio", 0.0)
                                sub = cant * prec
                                data_tabla.append({"Cliente": cli, "Detalle": det, "Cantidad": cant, "Precio U.": f"${prec:,.2f}", "Subtotal ($)": f"${sub:,.2f}"})
                            else:
                                data_tabla.append({"Cliente": cli, "Detalle": "-", "Cantidad": info, "Precio U.": "$0.00", "Subtotal ($)": "$0.00"})
                    
                    st.dataframe(data_tabla, use_container_width=True)
                    
                    with st.form(f"form_del_cli_{prod_nombre}"):
                        cliente_a_borrar = st.selectbox("Eliminar cliente de este producto", options=["-- Seleccionar para borrar --"] + list(pedidos_prod.keys()), key=f"del_{prod_nombre}")
                        submit_del = st.form_submit_button("🗑️ Quitar Cliente Seleccionado")
                        if submit_del:
                            if cliente_a_borrar != "-- Seleccionar para borrar --":
                                del datos["semanas"][semana_seleccionada][prod_nombre]["clientes"][cliente_a_borrar]
                                guardar_datos(datos)
                                st.success(f"Se eliminó a {cliente_a_borrar} del producto {prod_nombre}.")
                                st.rerun()
                            else:
                                st.warning("Selecciona un cliente válido para borrar.")

with tab_buscador:
    st.subheader("🔍 Buscador General por Cliente")
    
    with st.form("form_buscador"):
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            semana_busqueda = st.selectbox("Seleccionar Pedido / Semana a Consultar", lista_semanas, index=len(lista_semanas)-1, key="busq_sem")
        with col_b2:
            clientes_disponibles = datos.get("clientes", [])
            cliente_busqueda = st.selectbox("Seleccionar Cliente", options=["-- Selecciona un cliente --"] + clientes_disponibles, key="busq_cli")
            cliente_texto_libre = st.text_input("O escribe el nombre exacto:", key="busq_cli_txt")

        submit_busqueda = st.form_submit_button("🔎 Buscar Cuenta")

    cliente_final_busq = cliente_texto_libre.strip() if cliente_texto_libre.strip() else cliente_busqueda

    if submit_busqueda:
        if cliente_final_busq == "-- Selecciona un cliente --" or not cliente_final_busq:
            st.warning("Selecciona o escribe un cliente válido.")
        else:
            st.markdown(f"### 📋 Resumen para: **{cliente_final_busq}** ({semana_busqueda})")
            
            prods_en_sem = datos["semanas"].get(semana_busqueda, {})
            total_cobrar = 0
            resultados = []
            
            for p_nombre, p_info in prods_en_sem.items():
                tipo = p_info.get("tipo", "normal")
                clientes_dict = p_info.get("clientes", {})
                
                if tipo == "normal":
                    if cliente_final_busq in clientes_dict:
                        cant = clientes_dict[cliente_final_busq]
                        precio = p_info.get("precio", 0.0)
                        subtotal = cant * precio
                        total_cobrar += subtotal
                        resultados.append({
                            "Producto": p_nombre,
                            "Detalle": "-",
                            "Cantidad": cant,
                            "Precio Unitario": f"${precio:,.2f}",
                            "Subtotal": f"${subtotal:,.2f}"
                        })
                else:
                    if cliente_final_busq in clientes_dict:
                        info = clientes_dict[cliente_final_busq]
                        if isinstance(info, dict):
                            det = info.get("detalle", "")
                            cant = info.get("cantidad", 1)
                            precio = info.get("precio", 0.0)
                            subtotal = cant * precio
                            total_cobrar += subtotal
                            resultados.append({
                                "Producto": p_nombre,
                                "Detalle": det,
                                "Cantidad": cant,
                                "Precio Unitario": f"${precio:,.2f}",
                                "Subtotal": f"${subtotal:,.2f}"
                            })
            
            if not resultados:
                st.info(f"El cliente '{cliente_final_busq}' no tiene ningún pedido registrado en '{semana_busqueda}'.")
            else:
                st.dataframe(resultados, use_container_width=True)
                st.markdown(f"### 💵 **Total a Cobrar: ${total_cobrar:,.2f}**")

with tab_clientes:
    st.subheader("👥 Administración General de Clientes")
    st.write("Registra nuevos clientes aquí para que estén siempre disponibles en la lista desplegable de cualquier pedido.")
    
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        with st.form("form_alta_cliente_global"):
            st.markdown("#### ➕ Registrar Nuevo Cliente")
            nuevo_cli_nombre = st.text_input("Nombre completo del cliente:")
            submit_alta_cli = st.form_submit_button("💾 Guardar Cliente en el Sistema")
            
            if submit_alta_cli:
                nombre_limpio = nuevo_cli_nombre.strip()
                if nombre_limpio:
                    if nombre_limpio not in datos["clientes"]:
                        datos["clientes"].append(nombre_limpio)
                        datos["clientes"].sort()
                        guardar_datos(datos)
                        st.success(f"¡Cliente '{nombre_limpio}' registrado con éxito!")
                        st.rerun()
                    else:
                        st.warning("Este cliente ya se encuentra en la lista registrada.")
                else:
                    st.error("Por favor escribe un nombre válido.")

    with col_c2:
        st.markdown("#### 📜 Lista de Clientes Registrados")
        lista_cli_actual = datos.get("clientes", [])
        if not lista_cli_actual:
            st.info("No hay clientes registrados aún.")
        else:
            tabla_clientes = [{"#": i+1, "Nombre del Cliente": c} for i, c in enumerate(sorted(lista_cli_actual))]
            st.dataframe(tabla_clientes, use_container_width=True, height=350)
            
            with st.form("form_baja_cliente_global"):
                cli_borrar_global = st.selectbox("Eliminar cliente del catálogo global", options=["-- Seleccionar para eliminar --"] + sorted(lista_cli_actual))
                submit_baja_cli = st.form_submit_button("🗑️ Eliminar de la Lista Global")
                if submit_baja_cli:
                    if cli_borrar_global != "-- Seleccionar para eliminar --":
                        datos["clientes"].remove(cli_borrar_global)
                        guardar_datos(datos)
                        st.success(f"Se eliminó a '{cli_borrar_global}' del catálogo global.")
                        st.rerun()
                    else:
                        st.warning("Selecciona un cliente para eliminar.")
