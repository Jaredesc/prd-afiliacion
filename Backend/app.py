from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import cv2
import numpy as np
import base64
import re
import requests
from datetime import datetime
import os
import time
from dotenv import load_dotenv
import traceback
import pymysql

# Configurar PyMySQL como driver MySQL
pymysql.install_as_MySQLdb()

# Importar modelos de base de datos
from models import db, Afiliacion, LogEscaneo

# ===============================================
# CONFIGURACIÓN PARA RAILWAY - FRONTEND + BACKEND + MYSQL
# ===============================================

load_dotenv()

# Flask configurado para servir archivos estáticos
app = Flask(__name__, static_folder='..', static_url_path='')

# CORS configurado
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# ===============================================
# CONFIGURACIÓN DE BASE DE DATOS MYSQL
# ===============================================

# Variables de entorno
MYSQL_URL = os.getenv('MYSQL_URL')
DATABASE_URL = os.getenv('DATABASE_URL')
GOOGLE_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key_2025')
PORT = int(os.getenv('PORT', 5001))
HOST = '0.0.0.0'

# Configurar Flask SECRET_KEY
app.config['SECRET_KEY'] = SECRET_KEY

# Configurar SQLAlchemy para MySQL
if MYSQL_URL:
    # Railway MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URL
    print("✅ Configurando MySQL desde MYSQL_URL")
elif DATABASE_URL:
    # Railway MySQL (alternativo)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("✅ Configurando MySQL desde DATABASE_URL")
else:
    # Configuración manual con los datos de Railway
    mysql_config = {
        'host': 'maglev.proxy.rlwy.net',
        'port': 26954,
        'user': 'root',
        'password': 'KdjBgzwzRqIRkMkWKdIpYPOUvTrIpKUD',
        'database': 'railway'
    }
    
    mysql_url = f"mysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url
    print("✅ Configurando MySQL con credenciales manuales")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'max_overflow': 0,
    'echo': False  # Cambiar a True para debug SQL
}

# Inicializar base de datos
db.init_app(app)

# Verificaciones
if not GOOGLE_API_KEY:
    print("⚠️  GOOGLE_VISION_API_KEY no configurada")
else:
    print("✅ Google Vision API Key configurada")

print("="*60)
print("🚀 SISTEMA PRD ZACATECAS - MYSQL v1.1 FIXED")
print("📁 Backend: Backend/app.py")
print("🌐 Frontend: Servido por Flask")
print(f"🔑 API: {'✓' if GOOGLE_API_KEY else '✗'}")
print(f"🔐 SECRET_KEY: {'✓' if SECRET_KEY != 'fallback_secret_key_2025' else '⚠️ Usando fallback'}")
print("🗄️  DB: ✓ MySQL Railway")
print("="*60)

# ===============================================
# CREAR TABLAS EN PRIMERA EJECUCIÓN
# ===============================================

def create_tables():
    """Crear tablas si no existen"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ Tablas de MySQL verificadas/creadas")
            
            # Verificar conexión
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            if result:
                print("✅ Conexión a MySQL exitosa")
            
    except Exception as e:
        print(f"⚠️  Error con MySQL: {e}")
        print(f"Traceback: {traceback.format_exc()}")

# ===============================================
# RUTAS PARA SERVIR EL FRONTEND
# ===============================================

@app.route('/')
def index():
    """Servir la página principal"""
    return send_file('../index.html')

@app.route('/pages/<path:filename>')
def pages(filename):
    """Servir páginas"""
    return send_from_directory('../pages', filename)

@app.route('/assets/<path:filename>')
def assets(filename):
    """Servir assets (CSS, JS, imágenes)"""
    return send_from_directory('../assets', filename)

# ===============================================
# FUNCIONES DE PROCESAMIENTO DE IMÁGENES
# ===============================================

def enhance_image_for_ocr(image):
    """Mejora la imagen para OCR"""
    print("🔧 Mejorando imagen...")
    
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        height, width = gray.shape
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        binary = cv2.adaptiveThreshold(sharpened, 255, 
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 15, 10)
        
        print("✅ Imagen mejorada")
        return binary
    except Exception as e:
        print(f"❌ Error mejorando imagen: {e}")
        return image

def analyze_with_vision_api(image_data):
    """Google Vision API con mejor manejo de errores"""
    if not GOOGLE_API_KEY:
        return {'success': False, 'error': 'API Key no configurada', 'text': ''}
    
    print("🔍 Procesando con Google Vision...")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        request_body = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "TEXT_DETECTION", "maxResults": 50},
                    {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 50}
                ],
                "imageContext": {
                    "languageHints": ["es", "en"]
                }
            }]
        }
        
        response = requests.post(url, json=request_body, timeout=30)
        
        print(f"📡 Google Vision status: {response.status_code}")
        
        if response.status_code != 200:
            return {'success': False, 'error': f'Error API: {response.status_code}', 'text': ''}
        
        result = response.json()
        
        if 'responses' in result and len(result['responses']) > 0:
            response_data = result['responses'][0]
            
            if 'error' in response_data:
                return {'success': False, 'error': str(response_data['error']), 'text': ''}
            
            full_text = ""
            
            if 'fullTextAnnotation' in response_data:
                full_text += response_data['fullTextAnnotation']['text'] + " "
            
            if 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                additional_text = response_data['textAnnotations'][0]['description']
                full_text += additional_text + " "
            
            full_text = ' '.join(full_text.split())
            
            if not full_text.strip():
                return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
            return {'success': True, 'text': full_text, 'confidence': 0.95}
        else:
            return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout de Google Vision API', 'text': ''}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Error de conexión: {str(e)}', 'text': ''}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}', 'text': ''}

def extract_ine_data_prd(text):
    """Extracción básica de datos mejorada"""
    print("📊 Extrayendo datos...")
    
    data = {}
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    
    # Patrones básicos mejorados
    patterns = {
        'curp': r'([A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2})',
        'clave_elector': r'([A-Z]{6}[0-9]{8}[HM][0-9]{3})',
        'nombres': r'NOMBRE[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,40})',
        'primer_apellido': r'(?:PATERNO|APELLIDO)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'segundo_apellido': r'MATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'municipio': r'(FRESNILLO|GUADALUPE|ZACATECAS|JEREZ|SOMBRERETE|PINOS|CALERA|RÍO GRANDE|NOCHISTLÁN)',
        'codigo_postal': r'([0-9]{5})',
        'calle': r'(?:DOMICILIO|CALLE)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s\d]{5,40})',
        'colonia': r'(?:COL|COLONIA)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,30})'
    }
    
    for field, pattern in patterns.items():
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    data[field] = value
                    print(f"✅ {field}: {value}")
        except Exception as e:
            print(f"⚠️ Error extrayendo {field}: {e}")
    
    # Extraer género de CURP
    if 'curp' in data and len(data['curp']) >= 11:
        try:
            sexo_char = data['curp'][10]
            if sexo_char == 'H':
                data['sexo'] = 'masculino'
            elif sexo_char == 'M':
                data['sexo'] = 'femenino'
        except:
            pass
    
    print(f"📊 Total extraído: {len(data)} campos")
    return data

# ===============================================
# API ENDPOINTS
# ===============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check mejorado"""
    try:
        # Verificar conexión a base de datos
        total_afiliaciones = Afiliacion.query.count()
        db_status = 'OK'
        
        # Test de escritura/lectura
        test_query = db.session.execute(db.text("SELECT VERSION()")).fetchone()
        mysql_version = test_query[0] if test_query else 'Unknown'
        
    except Exception as e:
        total_afiliaciones = 'Error'
        db_status = f'Error: {str(e)}'
        mysql_version = 'Error'
    
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas - MySQL v1.1 FIXED',
        'backend': 'Backend/app.py',
        'frontend': 'Servido por Flask',
        'api_configured': bool(GOOGLE_API_KEY),
        'secret_key_configured': SECRET_KEY != 'fallback_secret_key_2025',
        'database_status': db_status,
        'database_type': 'MySQL',
        'mysql_version': mysql_version,
        'total_afiliaciones': total_afiliaciones
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """API para escaneo INE con mejor manejo de errores"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("📸 Procesando escaneo INE...")
    start_time = time.time()
    user_ip = request.remote_addr
    
    # Crear log de escaneo
    log_escaneo = LogEscaneo(
        ip_usuario=user_ip,
        fecha_escaneo=datetime.utcnow()
    )
    
    try:
        if 'imagen' not in request.files:
            log_escaneo.exito = False
            log_escaneo.error_mensaje = 'No se recibió imagen'
            try:
                db.session.add(log_escaneo)
                db.session.commit()
            except:
                pass
            
            error_response = jsonify({'success': False, 'error': 'No se recibió imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        file = request.files['imagen']
        if file.filename == '':
            log_escaneo.exito = False
            log_escaneo.error_mensaje = 'Archivo vacío'
            try:
                db.session.add(log_escaneo)
                db.session.commit()
            except:
                pass
            
            error_response = jsonify({'success': False, 'error': 'Archivo vacío'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        print(f"📎 Procesando: {file.filename}")
        
        # Leer imagen
        image_data = file.read()
        
        # Validar tamaño de archivo
        if len(image_data) > 10 * 1024 * 1024:  # 10MB max
            error_response = jsonify({'success': False, 'error': 'Archivo demasiado grande (máximo 10MB)'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Convertir imagen
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            log_escaneo.exito = False
            log_escaneo.error_mensaje = 'Imagen inválida o formato no soportado'
            try:
                db.session.add(log_escaneo)
                db.session.commit()
            except:
                pass
            
            error_response = jsonify({'success': False, 'error': 'Imagen inválida o formato no soportado'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Mejorar imagen
        enhanced_image = enhance_image_for_ocr(image)
        
        # Convertir a bytes
        success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
        if not success:
            log_escaneo.exito = False
            log_escaneo.error_mensaje = 'Error procesando imagen'
            try:
                db.session.add(log_escaneo)
                db.session.commit()
            except:
                pass
            
            error_response = jsonify({'success': False, 'error': 'Error procesando imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        enhanced_image_data = enhanced_buffer.tobytes()
        
        # Analizar con Google Vision
        vision_result = analyze_with_vision_api(enhanced_image_data)
        
        if not vision_result['success']:
            # Reintentar con imagen original
            print("🔄 Reintentando con imagen original...")
            vision_result = analyze_with_vision_api(image_data)
            
            if not vision_result['success']:
                log_escaneo.exito = False
                log_escaneo.error_mensaje = vision_result['error']
                try:
                    db.session.add(log_escaneo)
                    db.session.commit()
                except:
                    pass
                
                error_response = jsonify({'success': False, 'error': f"Error en Google Vision: {vision_result['error']}"})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
        
        print(f"📝 Texto extraído: {len(vision_result['text'])} caracteres")
        
        # Extraer datos
        extracted_data = extract_ine_data_prd(vision_result['text'])
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Actualizar log de escaneo
        log_escaneo.exito = True
        log_escaneo.campos_detectados = list(extracted_data.keys())
        log_escaneo.texto_extraido = vision_result['text'][:1000]  # Truncar para ahorrar espacio
        log_escaneo.confianza = vision_result.get('confidence', 0.95)
        log_escaneo.tiempo_procesamiento = processing_time
        
        try:
            db.session.add(log_escaneo)
            db.session.commit()
        except Exception as e:
            print(f"⚠️ Error guardando log: {e}")
        
        # Respuesta final
        response_data = {
            'success': True,
            'datos_prd': {
                'curp': extracted_data.get('curp', 'NO DETECTADO'),
                'clave_elector': extracted_data.get('clave_elector', 'NO DETECTADO'),
                'nombres': extracted_data.get('nombres', 'NO DETECTADO'),
                'primer_apellido': extracted_data.get('primer_apellido', 'NO DETECTADO'),
                'segundo_apellido': extracted_data.get('segundo_apellido', 'NO DETECTADO'),
                'sexo': extracted_data.get('sexo', 'NO DETECTADO'),
                'municipio': extracted_data.get('municipio', 'NO DETECTADO'),
                'calle': extracted_data.get('calle', 'NO DETECTADO'),
                'colonia': extracted_data.get('colonia', 'NO DETECTADO'),
                'codigo_postal': extracted_data.get('codigo_postal', 'NO DETECTADO'),
                'metodo_usado': 'Railway MySQL v1.1 FIXED'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data,
                'clave_elector_valida': 'clave_elector' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'municipio'])
            },
            'debug_info': {
                'campos_detectados': list(extracted_data.keys()),
                'texto_length': len(vision_result['text']),
                'processing_time': round(processing_time, 2)
            }
        }
        
        print(f"✅ Completado - {len(extracted_data)} campos en {processing_time:.2f}s")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        print(f"💥 ERROR: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Guardar error en log
        log_escaneo.exito = False
        log_escaneo.error_mensaje = str(e)
        log_escaneo.tiempo_procesamiento = time.time() - start_time
        
        try:
            db.session.add(log_escaneo)
            db.session.commit()
        except Exception as db_error:
            print(f"Error guardando log: {db_error}")
        
        error_response = jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/api/guardar-afiliacion', methods=['POST', 'OPTIONS'])
def guardar_afiliacion():
    """Guardar nueva afiliación en base de datos con mejor validación"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
        
        print(f"📋 Datos recibidos: {list(data.keys())}")
        
        # Verificar campos obligatorios
        required_fields = ['nombres', 'primer_apellido', 'curp', 'clave_elector', 'email', 'telefono']
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field] or data[field].strip() == '':
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Campos obligatorios faltantes: {", ".join(missing_fields)}'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Limpiar datos
        curp_clean = data['curp'].strip().upper()
        clave_elector_clean = data['clave_elector'].strip().upper()
        
        # Verificar si ya existe CURP o Clave de Elector
        existing_curp = Afiliacion.query.filter_by(curp=curp_clean).first()
        if existing_curp:
            return jsonify({'success': False, 'error': f'Ya existe una afiliación con la CURP: {curp_clean}'}), 400
        
        existing_clave = Afiliacion.query.filter_by(clave_elector=clave_elector_clean).first()
        if existing_clave:
            return jsonify({'success': False, 'error': f'Ya existe una afiliación con la Clave de Elector: {clave_elector_clean}'}), 400
        
        # Generar folio único
        folio = Afiliacion.generar_folio()
        
        # Crear nueva afiliación
        nueva_afiliacion = Afiliacion(
            folio=folio,
            afiliador=data.get('afiliador', '').strip(),
            nombres=data['nombres'].strip(),
            primer_apellido=data['primer_apellido'].strip(),
            segundo_apellido=data.get('segundo_apellido', '').strip(),
            lugar_nacimiento=data.get('lugar_nacimiento', '').strip(),
            curp=curp_clean,
            clave_elector=clave_elector_clean,
            email=data['email'].strip().lower(),
            telefono=data['telefono'].strip(),
            genero=data.get('genero', '').strip(),
            llegada_prd=data.get('llegada_prd', '').strip(),
            municipio=data.get('municipio', '').strip(),
            colonia=data.get('colonia', '').strip(),
            codigo_postal=data.get('codigo_postal', '').strip(),
            calle=data.get('calle', '').strip(),
            numero_exterior=data.get('numero_exterior', '').strip(),
            numero_interior=data.get('numero_interior', '').strip(),
            declaracion_veracidad=data.get('declaracion_veracidad', True),
            declaracion_principios=data.get('declaracion_principios', True),
            terminos_condiciones=data.get('terminos_condiciones', True),
            metodo_captura=data.get('metodo_captura', 'manual'),
            ip_registro=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        # Guardar en base de datos
        db.session.add(nueva_afiliacion)
        db.session.commit()
        
        print(f"✅ Nueva afiliación guardada: {folio}")
        
        response_data = {
            'success': True,
            'folio': folio,
            'id': nueva_afiliacion.id,
            'mensaje': 'Afiliación guardada exitosamente en MySQL'
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        db.session.rollback()
        print(f"💥 ERROR guardando afiliación: {e}")
        print(traceback.format_exc())
        
        error_response = jsonify({'success': False, 'error': f'Error guardando afiliación: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    """Obtener estadísticas básicas"""
    try:
        total_afiliaciones = Afiliacion.query.count()
        afiliaciones_hoy = Afiliacion.query.filter(
            Afiliacion.fecha_registro >= datetime.utcnow().date()
        ).count()
        
        # Top municipios
        from sqlalchemy import func
        top_municipios = db.session.query(
            Afiliacion.municipio,
            func.count(Afiliacion.municipio).label('total')
        ).group_by(Afiliacion.municipio).order_by(func.count(Afiliacion.municipio).desc()).limit(5).all()
        
        response_data = {
            'total_afiliaciones': total_afiliaciones,
            'afiliaciones_hoy': afiliaciones_hoy,
            'top_municipios': [{'municipio': m[0], 'total': m[1]} for m in top_municipios]
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        error_response = jsonify({'success': False, 'error': str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    # Crear tablas si no existen
    create_tables()
    
    print("🚀 Iniciando sistema completo con MySQL FIXED...")
    print(f"🌐 Frontend + Backend + MySQL en puerto: {PORT}")
    app.run(debug=False, host=HOST, port=PORT)