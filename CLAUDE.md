# Instrucciones del Proyecto

Cuando completes una tarea, ejecuta: afplay /System/Library/Sounds/Glass.aiff

## Estado Actual (8 Enero 2026)

### CRM Autocares David - Streamlit App

**URL producción:** https://crm-david-9bvwvmklthzft66jn4tnza.streamlit.app

**Repositorio:** https://github.com/cesarmartin1/crm-david

### Configuración

- **Supabase:** https://zqqqnpnxbogfzrxvvjab.supabase.co
- **Tenant Azure (acautopullman):** da47f97f-944c-4b0e-9dde-e799eced5c82
- **Solo usuarios del tenant pueden loguearse**

### Completado

1. Login con Microsoft 365 - ARREGLADO (usamos st.link_button en lugar de JavaScript)
2. Sistema de invitaciones con permisos personalizados - IMPLEMENTADO
3. Deploy en Streamlit Cloud - HECHO
4. Supabase configurado para tenant específico

### Pendiente

- Verificar que la app sea pública en Streamlit Cloud (Settings → Sharing → "This app is public")
- Puede que haya que guardar cambios o hacer reboot de la app

### Archivos clave

- `app.py` - App principal de Streamlit
- `auth.py` - Autenticación con Microsoft 365 via Supabase
- `admin_panel.py` - Panel de administración con invitaciones y permisos
- `database.py` - Base de datos SQLite (usa /tmp/ en Streamlit Cloud)
- `.streamlit/secrets.toml` - Secrets locales (NO subir a git)
