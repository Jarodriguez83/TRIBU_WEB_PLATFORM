from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

# Cliente público (para operaciones del cliente)
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_key
)

# Cliente de servicio (para operaciones de admin, bypasea RLS)
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)
