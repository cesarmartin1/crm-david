"""
Cliente Supabase para CRM Autocares David
"""
from supabase import create_client, Client
import streamlit as st


@st.cache_resource
def get_supabase() -> Client:
    """
    Obtiene el cliente Supabase con la clave anónima (para usuarios autenticados).
    """
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )


def get_admin_client() -> Client:
    """
    Obtiene el cliente Supabase con la clave de servicio (para operaciones admin).
    USAR CON CUIDADO - tiene acceso completo a la base de datos.
    """
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    )
