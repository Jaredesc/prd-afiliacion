# Backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Afiliacion(db.Model):
    __tablename__ = 'afiliaciones'
    
    # ID único
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    folio = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Responsable de afiliación
    afiliador = db.Column(db.String(100), nullable=False)
    
    # Datos personales
    nombres = db.Column(db.String(100), nullable=False)
    primer_apellido = db.Column(db.String(50), nullable=False)
    segundo_apellido = db.Column(db.String(50), nullable=True)
    lugar_nacimiento = db.Column(db.String(100), nullable=False)
    curp = db.Column(db.String(18), nullable=False, unique=True, index=True)
    clave_elector = db.Column(db.String(18), nullable=False, unique=True, index=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    telefono = db.Column(db.String(10), nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    llegada_prd = db.Column(db.String(50), nullable=False)
    
    # Domicilio
    estado = db.Column(db.String(50), nullable=False, default='Zacatecas')
    municipio = db.Column(db.String(100), nullable=False, index=True)
    colonia = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(5), nullable=False)
    calle = db.Column(db.String(100), nullable=False)
    numero_exterior = db.Column(db.String(10), nullable=True)
    numero_interior = db.Column(db.String(10), nullable=True)
    
    # Acuerdos
    declaracion_veracidad = db.Column(db.Boolean, nullable=False, default=True)
    declaracion_principios = db.Column(db.Boolean, nullable=False, default=True)
    terminos_condiciones = db.Column(db.Boolean, nullable=False, default=True)
    
    # Metadatos
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    metodo_captura = db.Column(db.String(50), nullable=True)  # 'manual' o 'ine_scan'
    ip_registro = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Estado de la afiliación
    estado_afiliacion = db.Column(db.String(20), nullable=False, default='activa', index=True)  # activa, suspendida, cancelada
    
    def __repr__(self):
        return f'<Afiliacion {self.folio}: {self.nombres} {self.primer_apellido}>'
    
    def to_dict(self):
        """Convertir a diccionario para JSON"""
        return {
            'id': self.id,
            'folio': self.folio,
            'afiliador': self.afiliador,
            'nombres': self.nombres,
            'primer_apellido': self.primer_apellido,
            'segundo_apellido': self.segundo_apellido,
            'lugar_nacimiento': self.lugar_nacimiento,
            'curp': self.curp,
            'clave_elector': self.clave_elector,
            'email': self.email,
            'telefono': self.telefono,
            'genero': self.genero,
            'llegada_prd': self.llegada_prd,
            'estado': self.estado,
            'municipio': self.municipio,
            'colonia': self.colonia,
            'codigo_postal': self.codigo_postal,
            'calle': self.calle,
            'numero_exterior': self.numero_exterior,
            'numero_interior': self.numero_interior,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'metodo_captura': self.metodo_captura,
            'estado_afiliacion': self.estado_afiliacion
        }
    
    @staticmethod
    def generar_folio():
        """Generar folio único"""
        from datetime import datetime
        
        # Formato: PRD-YYYY-NNNNN
        year = datetime.now().year
        
        # Buscar el último número usado este año
        last_afiliacion = Afiliacion.query.filter(
            Afiliacion.folio.like(f'PRD-{year}-%')
        ).order_by(Afiliacion.folio.desc()).first()
        
        if last_afiliacion:
            try:
                last_number = int(last_afiliacion.folio.split('-')[-1])
                next_number = last_number + 1
            except:
                next_number = 1
        else:
            next_number = 1
        
        return f"PRD-{year}-{next_number:05d}"

class LogEscaneo(db.Model):
    __tablename__ = 'logs_escaneo'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    afiliacion_id = db.Column(db.String(36), db.ForeignKey('afiliaciones.id'), nullable=True, index=True)
    
    # Detalles del escaneo
    campos_detectados = db.Column(db.JSON, nullable=True)
    texto_extraido = db.Column(db.Text, nullable=True)
    confianza = db.Column(db.Float, nullable=True)
    tiempo_procesamiento = db.Column(db.Float, nullable=True)  # segundos
    
    # Metadatos
    fecha_escaneo = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_usuario = db.Column(db.String(45), nullable=True)
    exito = db.Column(db.Boolean, nullable=False, default=False, index=True)
    error_mensaje = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<LogEscaneo {self.id}: {"Exitoso" if self.exito else "Error"}>'