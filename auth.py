"""
Sistema de autenticación para CRM Autocares David
Usa Azure AD (Microsoft 365) a través de Supabase
Con persistencia de sesión mediante cookies seguras
"""
import streamlit as st
from supabase_client import get_supabase, get_admin_client
from datetime import datetime, timedelta
import time
import extra_streamlit_components as stx

COOKIE_EXPIRY_DAYS = 7  # Días de validez de la cookie

def get_cookie_manager():
    """Obtiene el cookie manager (sin cache porque usa widgets)"""
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="crm_cookies")
    return st.session_state.cookie_manager


def login_page():
    """Muestra página de login con botón Microsoft 365"""
    query_params = st.query_params

    # 1. Manejar callback con código de autorización
    if "code" in query_params:
        _handle_auth_code(query_params.get("code"))
        return

    # 2. Mostrar error si hay
    if "auth_error" in query_params:
        st.error(f"Error de autenticación: {query_params.get('auth_error')}")
        st.query_params.clear()
        time.sleep(2)
        st.rerun()

    # 3. Mostrar página de login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://img.icons8.com/color/96/bus.png", width=96)
        st.title("CRM Autocares David")
        st.caption("Sistema de Gestión de Presupuestos")

        st.divider()

        # Obtener URL de OAuth al cargar la página
        oauth_url = _get_oauth_url()

        if oauth_url:
            # Usar link_button para redirección directa (más confiable)
            st.link_button(
                "🔐 Iniciar sesión con Microsoft 365",
                oauth_url,
                type="primary",
                use_container_width=True
            )
        else:
            st.error("Error al configurar autenticación")


def _get_oauth_url() -> str:
    """Obtiene la URL de OAuth de Azure AD via Supabase"""
    supabase = get_supabase()

    try:
        redirect_url = st.secrets.get("REDIRECT_URL", "http://localhost:8501")

        response = supabase.auth.sign_in_with_oauth({
            "provider": "azure",
            "options": {
                "redirect_to": redirect_url,
                "scopes": "openid profile email"
            }
        })

        return response.url if response.url else None

    except Exception as e:
        st.error(f"Error al obtener URL de autenticación: {str(e)}")
        return None


def _handle_auth_code(code: str):
    """Intercambia el código de autorización por tokens"""
    st.info("🔄 Completando autenticación...")

    supabase = get_supabase()
    cookie_manager = get_cookie_manager()

    try:
        # Intercambiar código por sesión
        response = supabase.auth.exchange_code_for_session({"auth_code": code})

        if response.session:
            # Guardar tokens en session_state
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token

            # Guardar tokens en cookies seguras (persisten al refrescar)
            cookie_manager.set(
                "crm_access_token",
                response.session.access_token,
                expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)
            )
            cookie_manager.set(
                "crm_refresh_token",
                response.session.refresh_token,
                expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)
            )

            # Registrar usuario si es nuevo
            registrar_usuario_si_nuevo(response.user)

            # Limpiar URL y recargar
            st.query_params.clear()
            time.sleep(0.5)  # Dar tiempo a que se guarden las cookies
            st.rerun()
        else:
            st.error("No se pudo obtener la sesión")
            st.query_params.clear()

    except Exception as e:
        error_msg = str(e).lower()
        # Manejar errores comunes de OAuth sin mostrar error al usuario
        if "code" in error_msg and ("invalid" in error_msg or "expired" in error_msg):
            pass  # Código expirado - silencioso
        elif "flow state" in error_msg or "flow_state" in error_msg:
            pass  # Estado de flujo inválido - silencioso
        elif "pkce" in error_msg:
            pass  # Error PKCE - silencioso
        else:
            st.error(f"Error en autenticación: {str(e)}")

        st.query_params.clear()
        time.sleep(0.5)
        st.rerun()


def registrar_usuario_si_nuevo(user):
    """Registra un nuevo usuario en la tabla usuarios si no existe"""
    if not user:
        return

    admin_client = get_admin_client()

    # Verificar si el usuario ya existe
    result = admin_client.table('usuarios').select('*').eq('id', user.id).execute()

    if not result.data:
        # Verificar si hay una invitación válida para este email
        email = user.email
        invitacion = admin_client.table('invitaciones').select('*')\
            .eq('email', email)\
            .eq('usado', False)\
            .gte('fecha_expiracion', datetime.now().isoformat())\
            .execute()

        if invitacion.data:
            # Crear usuario con rol de la invitación
            inv = invitacion.data[0]
            admin_client.table('usuarios').insert({
                'id': user.id,
                'email': email,
                'nombre': user.user_metadata.get('full_name', user.user_metadata.get('name', '')),
                'rol': inv['rol'],
                'activo': True,
                'invitado_por': inv['invitado_por']
            }).execute()

            # Marcar invitación como usada
            admin_client.table('invitaciones').update({'usado': True})\
                .eq('id', inv['id']).execute()

            # Crear permisos - usar los de la invitación si existen
            permisos_invitacion = inv.get('permisos')
            crear_permisos_usuario(user.id, inv['rol'], permisos_invitacion)
        else:
            # Usuario no invitado - crear como inactivo
            admin_client.table('usuarios').insert({
                'id': user.id,
                'email': email,
                'nombre': user.user_metadata.get('full_name', user.user_metadata.get('name', '')),
                'rol': 'usuario',
                'activo': False  # Necesita aprobación de admin
            }).execute()


def crear_permisos_usuario(usuario_id: str, rol: str, permisos_json: str = None):
    """
    Crea permisos para el usuario.
    Si permisos_json está definido, usa esos permisos.
    Si no, usa permisos por defecto según el rol.
    """
    import json

    admin_client = get_admin_client()

    secciones = [
        'Dashboard', 'Tiempo Anticipacion', 'Seguimiento Presupuestos',
        'Clientes', 'Campanas Segmentadas', 'Analisis Conversion',
        'Incentivos', 'Calculadora', 'Tarifas', 'Configuracion'
    ]

    # Parsear permisos de la invitación si existen
    permisos_personalizados = None
    if permisos_json:
        try:
            permisos_personalizados = json.loads(permisos_json) if isinstance(permisos_json, str) else permisos_json
        except (json.JSONDecodeError, TypeError):
            permisos_personalizados = None

    for seccion in secciones:
        if permisos_personalizados and seccion in permisos_personalizados:
            # Usar permisos de la invitación
            puede_ver = permisos_personalizados[seccion].get('ver', True)
            puede_editar = permisos_personalizados[seccion].get('editar', False)
        else:
            # Permisos por defecto: admin todo, usuario solo ver
            puede_ver = True
            puede_editar = rol == 'admin'

        admin_client.table('permisos_seccion').insert({
            'usuario_id': usuario_id,
            'seccion': seccion,
            'puede_ver': puede_ver,
            'puede_editar': puede_editar
        }).execute()


def check_auth():
    """
    Verifica si el usuario está autenticado y autorizado.
    Retorna los datos del usuario si está autenticado, None si no.
    Primero intenta recuperar tokens de cookies si no están en session_state.
    """
    supabase = get_supabase()
    cookie_manager = get_cookie_manager()

    # Si no hay tokens en session_state, intentar recuperar de cookies
    if 'access_token' not in st.session_state:
        access_token = cookie_manager.get("crm_access_token")
        refresh_token = cookie_manager.get("crm_refresh_token")

        if access_token and refresh_token:
            st.session_state.access_token = access_token
            st.session_state.refresh_token = refresh_token
        else:
            return None

    try:
        # Verificar sesión con Supabase
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

        user_response = supabase.auth.get_user()

        if not user_response or not user_response.user:
            _clear_auth_data(cookie_manager)
            return None

        user = user_response.user

        # Verificar si está en lista de usuarios autorizados y activo
        admin_client = get_admin_client()
        result = admin_client.table('usuarios').select('*').eq('id', user.id).single().execute()

        if not result.data:
            return None

        if not result.data['activo']:
            return {'error': 'inactive', 'user': result.data}

        # Actualizar último acceso
        admin_client.table('usuarios').update({
            'ultimo_acceso': datetime.now().isoformat()
        }).eq('id', user.id).execute()

        return result.data

    except Exception as e:
        # Token inválido o expirado - limpiar todo
        _clear_auth_data(cookie_manager)
        return None


def _clear_auth_data(cookie_manager=None):
    """Limpia tokens de session_state y cookies"""
    if 'access_token' in st.session_state:
        del st.session_state.access_token
    if 'refresh_token' in st.session_state:
        del st.session_state.refresh_token

    if cookie_manager:
        try:
            cookie_manager.delete("crm_access_token")
            cookie_manager.delete("crm_refresh_token")
        except:
            pass


def get_user_permissions(user_id: str) -> dict:
    """
    Obtiene permisos del usuario por sección.
    Retorna un diccionario con la estructura:
    {
        'Dashboard': {'ver': True, 'editar': False},
        ...
    }
    """
    admin_client = get_admin_client()
    result = admin_client.table('permisos_seccion').select('*').eq('usuario_id', user_id).execute()

    permisos = {}
    for p in result.data:
        permisos[p['seccion']] = {
            'ver': p['puede_ver'],
            'editar': p['puede_editar']
        }

    return permisos


def logout():
    """Cierra sesión del usuario y limpia cookies"""
    supabase = get_supabase()
    cookie_manager = get_cookie_manager()

    try:
        supabase.auth.sign_out()
    except:
        pass

    # Limpiar session_state y cookies
    _clear_auth_data(cookie_manager)

    if 'user' in st.session_state:
        del st.session_state.user

    st.rerun()


def mostrar_usuario_no_autorizado():
    """Muestra mensaje para usuarios no autorizados"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⚠️ **Acceso Pendiente de Aprobación**")
        st.write("""
        Tu cuenta ha sido registrada pero aún no ha sido activada.

        Por favor, contacta con el administrador para solicitar acceso.
        """)

        if st.button("Cerrar Sesión"):
            logout()
