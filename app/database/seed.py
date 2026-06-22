import uuid
from sqlmodel import Session, SQLModel
from app.database.database import engine
from app.models.models import Usuario, Producto
from app.services.auth import hash_password

def seed_database():
    """Genera tablas y siembra datos iniciales de prueba (Admin y Productos)."""
    print("Iniciando siembra de base de datos de TRIBU...")
    
    # Asegurar que las tablas existan
    SQLModel.metadata.create_all(engine)
    print("Tablas verificadas/creadas con éxito.")
    
    with Session(engine) as session:
        # 1. Crear usuario administrador si no existe
        admin_email = "admin@tribu.com"
        existing_admin = session.query(Usuario).filter(Usuario.email == admin_email).first()
        
        if not existing_admin:
            print("Creando usuario administrador de prueba...")
            admin_user = Usuario(
                nombre="Admin TRIBU Store",
                email=admin_email,
                hashed_password=hash_password("admin123_tribu_2023"),
                rol="admin",
                telefono="3001234567",
                direccion="Sede Principal TRIBU",
                ciudad="Medellin",
                departamento="Antioquia"
            )
            session.add(admin_user)
            print(f" -> Admin creado: {admin_email} / pass: admin123_tribu_2023")
        else:
            print(f" -> El administrador ya existe: {admin_email}")

        # 2. Crear productos si la tabla está vacía
        existing_products_count = session.query(Producto).count()
        if existing_products_count == 0:
            print("Sembrando catálogo inicial de productos streetwear...")
            
            productos_data = [
                {
                    "nombre": "Hoodie Oversized Tribu Classic",
                    "descripcion": "Saco con capota de corte oversized, confeccionado en algodón de alto gramaje (400g) perchado. Bordado frontal TRIBU en relieve de alta densidad y hombros caídos. Acabado lavado vintage. Color Negro Lavado.",
                    "precio": 145000.0,
                    "stock": 25,
                    "categoria": "hoodies",
                    "imagen_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["S", "M", "L", "XL"]
                },
                {
                    "nombre": "Chaqueta Bomber Apocalypse",
                    "descripcion": "Chaqueta tipo bomber acolchada impermeable de alta resistencia con forro satinado estampado con ilustraciones de marca. Cremalleras termoselladas y bolsillo cargo utilitario en la manga izquierda. Color Gris Grafito.",
                    "precio": 220000.0,
                    "stock": 15,
                    "categoria": "chaquetas",
                    "imagen_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["M", "L", "XL"]
                },
                {
                    "nombre": "Camiseta Distortion Boxy Tee",
                    "descripcion": "Camiseta manga corta de corte rectangular (boxy fit) y hombros caídos. Fabricada en algodón premium de 240 gramos. Estampado en serigrafía digital en la espalda con diseño abstracto conceptual de distorsión. Color Blanco Crudo.",
                    "precio": 75000.0,
                    "stock": 40,
                    "categoria": "camisetas",
                    "imagen_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["S", "M", "L", "XL"]
                },
                {
                    "nombre": "Gorra Trucker T-23",
                    "descripcion": "Gorra tipo camionera con frente rígido de lona estructurada y malla transpirable posterior. Parche frontal de silicona cosido con las siglas TRIBU 2023. Broche plástico ajustable en la nuca. Talla única unisex.",
                    "precio": 55000.0,
                    "stock": 30,
                    "categoria": "gorras",
                    "imagen_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["U"]
                },
                {
                    "nombre": "Chaleco Tactical Cargo Vest",
                    "descripcion": "Chaleco utilitario de estilo militar táctico con hebillas frontales de liberación rápida. Múltiples bolsillos modulares de carga con cierres de cremallera y solapas con velcro. Correas laterales de ajuste. Color Negro mate.",
                    "precio": 180000.0,
                    "stock": 12,
                    "categoria": "chalecos",
                    "imagen_url": "https://images.unsplash.com/photo-1622434641406-a158123450f9?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["S", "M", "L"]
                },
                {
                    "nombre": "Buzo Nightstalker Sweater",
                    "descripcion": "Buzo cuello redondo sin capota de fit regular, tejido de punto suave de mezcla de algodón y poliéster reciclado. Mangas raglán con aberturas para pulgares en los puños y costuras planas decorativas. Color Negro Profundo.",
                    "precio": 125000.0,
                    "stock": 20,
                    "categoria": "buzos",
                    "imagen_url": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?q=80&w=600&auto=format&fit=crop",
                    "tallas": ["S", "M", "L"]
                }
            ]
            
            for prod_dict in productos_data:
                nuevo_prod = Producto(
                    nombre=prod_dict["nombre"],
                    descripcion=prod_dict["descripcion"],
                    precio=prod_dict["precio"],
                    stock=prod_dict["stock"],
                    categoria=prod_dict["categoria"],
                    imagen_url=prod_dict["imagen_url"],
                    tallas=prod_dict["tallas"],
                    activo=True
                )
                session.add(nuevo_prod)
            print(f" -> Se sembraron {len(productos_data)} productos con éxito.")
        else:
            print(f" -> El catálogo ya cuenta con {existing_products_count} productos. Saltando siembra.")
            
        session.commit()
    print("Siembra de base de datos finalizada correctamente.")

if __name__ == "__main__":
    seed_database()
