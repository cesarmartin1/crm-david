"""
Panel de Administración para CRM Autocares David
Gestión de usuarios, invitaciones y permisos
"""
import streamlit as st
from supabase_client import get_supabase, get_admin_client
from datetime import datetime, timedelta


# Secciones disponibles en el CRM
SECCIONES = [
    'Dashboard',
    'Tiempo Anticipacion',
    'Seguimiento Presupuestos',
    'Clientes',
    'Campanas Segmentadas',
    'Analisis Conversion',
    'Incentivos',
    'Calculadora',
    'Tarifas',
    'Configuracion'
]


def panel_admin():
    """Panel principal de administración"""
    st.title("⚙️ Panel de Administración")

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Usuarios",
        "📧 Invitaciones",
        "🔐 Permisos",
        "📊 Log de Accesos"
    ])

    with tab1:
        gestionar_usuarios()

    with tab2:
        gestionar_invitaciones()

    with tab3:
        gestionar_permisos()

    with tab4:
        ver_log_accesos()


def gestionar_usuarios():
    """Lista y gestiona usuarios activos"""
    st.subheader("Gestión de Usuarios")

    admin_client = get_admin_client()
    usuarios = admin_client.table('usuarios').select('*').order('fecha_registro', desc=True).execute()

    if not usuarios.data:
        st.info("No hay usuarios registrados.")
        return

    # Mostrar usuarios en tabla
    for user in usuarios.data:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                nombre = user['nombre'] or user['email'].split('@')[0]
                estado = "🟢" if user['activo'] else "🔴"
                st.write(f"{estado} **{nombre}**")
                st.caption(user['email'])

            with col2:
                rol_badge = "🔑 Admin" if user['rol'] == 'admin' else "👤 Usuario"
                st.write(rol_badge)

            with col3:
                if user['ultimo_acceso']:
                    ultimo = datetime.fromisoformat(user['ultimo_acceso'].replace('Z', '+00:00'))
                    st.caption(f"Último acceso: {ultimo.strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.caption("Nunca ha accedido")

            with col4:
                # No permitir desactivar al propio usuario
                if user['id'] != st.session_state.user['id']:
                    if user['activo']:
                        if st.button("Desactivar", key=f"deact_{user['id']}", type="secondary"):
                            admin_client.table('usuarios').update({'activo': False}).eq('id', user['id']).execute()
                            st.rerun()
                    else:
                        if st.button("Activar", key=f"act_{user['id']}", type="primary"):
                            admin_client.table('usuarios').update({'activo': True}).eq('id', user['id']).execute()
                            st.rerun()

            st.divider()


def gestionar_invitaciones():
    """Crear y gestionar invitaciones"""
    st.subheader("Nueva Invitación")

    admin_client = get_admin_client()

    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email del empleado (Microsoft 365)")
    with col2:
        rol = st.selectbox("Rol", ["usuario", "admin"])

    col3, col4 = st.columns(2)
    with col3:
        dias_validez = st.number_input("Días de validez", min_value=1, max_value=30, value=7)

    # Selector de permisos
    st.write("**Permisos de acceso:**")

    if rol == 'admin':
        st.info("ℹ️ Los administradores tienen acceso completo a todas las secciones.")
        permisos_seleccionados = {s: {'ver': True, 'editar': True} for s in SECCIONES}
    else:
        # Mostrar checkboxes para cada sección
        permisos_seleccionados = {}

        # Crear grid de permisos
        col_header = st.columns([4, 2, 2])
        with col_header[0]:
            st.caption("**Sección**")
        with col_header[1]:
            st.caption("**Ver**")
        with col_header[2]:
            st.caption("**Editar**")

        for seccion in SECCIONES:
            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                st.write(seccion)

            with col2:
                ver = st.checkbox(
                    "Ver",
                    value=True,  # Por defecto puede ver
                    key=f"inv_ver_{seccion}",
                    label_visibility="collapsed"
                )

            with col3:
                editar = st.checkbox(
                    "Editar",
                    value=False,  # Por defecto no puede editar
                    key=f"inv_edit_{seccion}",
                    label_visibility="collapsed",
                    disabled=not ver
                )

            permisos_seleccionados[seccion] = {
                'ver': ver,
                'editar': editar if ver else False
            }

    st.write("")
    if st.button("📤 Enviar Invitación", type="primary"):
        if email:
            # Verificar si ya existe una invitación o usuario
            existe_usuario = admin_client.table('usuarios').select('id').eq('email', email).execute()
            if existe_usuario.data:
                st.error("Este email ya tiene una cuenta registrada.")
            else:
                existe_inv = admin_client.table('invitaciones').select('id')\
                    .eq('email', email).eq('usado', False).execute()
                if existe_inv.data:
                    st.warning("Ya existe una invitación pendiente para este email.")
                else:
                    import json
                    # Crear invitación con permisos
                    datos_invitacion = {
                        'email': email,
                        'rol': rol,
                        'invitado_por': st.session_state.user['id'],
                        'fecha_expiracion': (datetime.now() + timedelta(days=dias_validez)).isoformat()
                    }

                    # Intentar agregar permisos (puede fallar si la columna no existe)
                    try:
                        datos_invitacion['permisos'] = json.dumps(permisos_seleccionados)
                        admin_client.table('invitaciones').insert(datos_invitacion).execute()
                    except Exception:
                        # Si falla por la columna permisos, crear sin ella
                        del datos_invitacion['permisos']
                        admin_client.table('invitaciones').insert(datos_invitacion).execute()
                        st.warning("⚠️ Los permisos personalizados no se guardaron. Agrega la columna 'permisos' en Supabase.")

                    st.success(f"✅ Invitación creada para {email}")
                    st.info(f"El usuario puede iniciar sesión con su cuenta Microsoft 365. La invitación expira en {dias_validez} días.")
        else:
            st.error("Por favor, introduce un email válido.")

    # Mostrar invitaciones pendientes
    st.subheader("Invitaciones Pendientes")

    invitaciones = admin_client.table('invitaciones').select('*')\
        .eq('usado', False)\
        .order('fecha_creacion', desc=True).execute()

    if not invitaciones.data:
        st.info("No hay invitaciones pendientes.")
    else:
        for inv in invitaciones.data:
            with st.container():
                col1, col2, col3 = st.columns([4, 2, 2])

                with col1:
                    st.write(f"📧 **{inv['email']}**")
                    rol_text = "🔑 Admin" if inv['rol'] == 'admin' else "👤 Usuario"
                    st.caption(f"Rol: {rol_text}")

                with col2:
                    expira = datetime.fromisoformat(inv['fecha_expiracion'].replace('Z', '+00:00'))
                    dias_restantes = (expira - datetime.now(expira.tzinfo)).days
                    if dias_restantes > 0:
                        st.caption(f"Expira en {dias_restantes} días")
                    else:
                        st.caption("⚠️ Expirada")

                with col3:
                    if st.button("🗑️ Cancelar", key=f"cancel_{inv['id']}"):
                        admin_client.table('invitaciones').delete().eq('id', inv['id']).execute()
                        st.rerun()

                st.divider()

    # Mostrar invitaciones usadas (historial)
    with st.expander("📜 Historial de Invitaciones"):
        usadas = admin_client.table('invitaciones').select('*')\
            .eq('usado', True)\
            .order('fecha_creacion', desc=True)\
            .limit(20).execute()

        if usadas.data:
            for inv in usadas.data:
                st.caption(f"✅ {inv['email']} - {inv['rol']} - Usada")
        else:
            st.caption("No hay invitaciones usadas.")


def gestionar_permisos():
    """Configura permisos por usuario y sección"""
    st.subheader("Gestión de Permisos")

    admin_client = get_admin_client()

    # Obtener usuarios activos
    usuarios = admin_client.table('usuarios').select('*').eq('activo', True).execute()

    if not usuarios.data:
        st.info("No hay usuarios activos para configurar permisos.")
        return

    # Selector de usuario
    opciones_usuarios = {u['email']: u for u in usuarios.data}
    usuario_sel = st.selectbox(
        "Seleccionar Usuario",
        options=list(opciones_usuarios.keys()),
        format_func=lambda x: f"{opciones_usuarios[x]['nombre'] or x.split('@')[0]} ({x})"
    )

    if usuario_sel:
        user = opciones_usuarios[usuario_sel]

        st.write(f"**Permisos para:** {user['nombre'] or user['email']}")

        if user['rol'] == 'admin':
            st.info("ℹ️ Los administradores tienen acceso completo a todas las secciones.")

        # Obtener permisos actuales
        permisos = admin_client.table('permisos_seccion').select('*').eq('usuario_id', user['id']).execute()
        permisos_dict = {p['seccion']: p for p in permisos.data}

        # Crear formulario de permisos
        st.write("")
        cambios = []

        # Header
        col_header = st.columns([4, 2, 2])
        with col_header[0]:
            st.write("**Sección**")
        with col_header[1]:
            st.write("**Ver**")
        with col_header[2]:
            st.write("**Editar**")

        st.divider()

        for seccion in SECCIONES:
            col1, col2, col3 = st.columns([4, 2, 2])

            permiso_actual = permisos_dict.get(seccion, {'puede_ver': True, 'puede_editar': False})

            with col1:
                st.write(seccion)

            with col2:
                ver = st.checkbox(
                    "Ver",
                    value=permiso_actual.get('puede_ver', True),
                    key=f"ver_{user['id']}_{seccion}",
                    label_visibility="collapsed"
                )

            with col3:
                editar = st.checkbox(
                    "Editar",
                    value=permiso_actual.get('puede_editar', False),
                    key=f"edit_{user['id']}_{seccion}",
                    label_visibility="collapsed",
                    disabled=not ver  # No puede editar si no puede ver
                )

            cambios.append({
                'seccion': seccion,
                'ver': ver,
                'editar': editar if ver else False
            })

        st.write("")
        if st.button("💾 Guardar Permisos", type="primary"):
            for c in cambios:
                admin_client.table('permisos_seccion').upsert({
                    'usuario_id': user['id'],
                    'seccion': c['seccion'],
                    'puede_ver': c['ver'],
                    'puede_editar': c['editar']
                }, on_conflict='usuario_id,seccion').execute()

            st.success("✅ Permisos guardados correctamente")
            st.rerun()


def ver_log_accesos():
    """Muestra el log de accesos recientes"""
    st.subheader("Log de Accesos")

    admin_client = get_admin_client()

    # Obtener últimos 100 accesos
    logs = admin_client.table('log_accesos').select('*, usuarios(email, nombre)')\
        .order('timestamp', desc=True)\
        .limit(100).execute()

    if not logs.data:
        st.info("No hay registros de acceso.")
        return

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_accion = st.selectbox("Filtrar por acción", ["Todas", "login", "logout", "view", "edit"])
    with col2:
        filtro_seccion = st.selectbox("Filtrar por sección", ["Todas"] + SECCIONES)

    # Mostrar logs
    for log in logs.data:
        # Aplicar filtros
        if filtro_accion != "Todas" and log['accion'] != filtro_accion:
            continue
        if filtro_seccion != "Todas" and log.get('seccion') != filtro_seccion:
            continue

        usuario_info = log.get('usuarios', {})
        nombre = usuario_info.get('nombre') or usuario_info.get('email', 'Desconocido')

        timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))

        icono = {
            'login': '🔓',
            'logout': '🔒',
            'view': '👁️',
            'edit': '✏️'
        }.get(log['accion'], '📝')

        seccion_texto = f"en {log['seccion']}" if log.get('seccion') else ''
        st.caption(
            f"{icono} **{nombre}** - {log['accion']} {seccion_texto} - "
            f"{timestamp.strftime('%d/%m/%Y %H:%M')}"
        )


def registrar_accion(usuario_id: str, accion: str, seccion: str = None):
    """Registra una acción en el log de accesos"""
    admin_client = get_admin_client()

    try:
        admin_client.table('log_accesos').insert({
            'usuario_id': usuario_id,
            'accion': accion,
            'seccion': seccion
        }).execute()
    except Exception:
        pass  # No fallar si no se puede registrar el log
