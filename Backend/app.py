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
print("🚀 SISTEMA PRD ZACATECAS - MYSQL v1.2 DEBUG")
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
    print("🔧 [DEBUG] Mejorando imagen...")
    
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        height, width = gray.shape
        print(f"📐 [DEBUG] Dimensiones originales: {width}x{height}")
        
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"📐 [DEBUG] Redimensionado a: {new_width}x{new_height}")
        
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        binary = cv2.adaptiveThreshold(sharpened, 255, 
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 15, 10)
        
        print("✅ [DEBUG] Imagen mejorada exitosamente")
        return binary
        
    except Exception as e:
        print(f"❌ [DEBUG] Error mejorando imagen: {e}")
        return image

def extract_ine_data_advanced(text):
    """Extracción avanzada de datos con mejor debugging"""
    print("📊 [DEBUG] Iniciando extracción de datos...")
    print(f"📝 [DEBUG] Texto a procesar (primeros 200 chars): {text[:200]}")
    
    data = {}
    text_clean = text.replace('\n', ' ').replace('\r', ' ')
    text_clean = ' '.join(text_clean.split())
    text_upper = text_clean.upper()
    
    # Patrones mejorados con debugging
    patterns = {
        'curp': r'([A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2})',
        'clave_elector': r'([A-Z]{6}[0-9]{8}[HM][0-9]{3})',
        'nombres': r'(?:NOMBRE|NOM)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,40})',
        'primer_apellido': r'(?:PATERNO|APELLIDO)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'segundo_apellido': r'MATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'municipio': r'(FRESNILLO|GUADALUPE|ZACATECAS|JEREZ|SOMBRERETE|PINOS|CALERA|RÍO GRANDE|NOCHISTLÁN|MAZAPIL)',
        'codigo_postal': r'([0-9]{5})',
        'calle': r'(?:DOMICILIO|CALLE)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s\d]{5,40})',
        'colonia': r'(?:COL|COLONIA)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,30})'
    }
    
    for field, pattern in patterns.items():
        try:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    data[field] = value
                    print(f"✅ [DEBUG] {field}: {value}")
                else:
                    print(f"⚠️ [DEBUG] {field}: valor muy corto: '{value}'")
            else:
                print(f"❌ [DEBUG] {field}: no encontrado")
        except Exception as e:
            print(f"⚠️ [DEBUG] Error extrayendo {field}: {e}")
    
    # Extraer género de CURP
    if 'curp' in data and len(data['curp']) >= 11:
        try:
            sexo_char = data['curp'][10]
            if sexo_char == 'H':
                data['sexo'] = 'masculino'
                print(f"✅ [DEBUG] sexo: masculino (desde CURP)")
            elif sexo_char == 'M':
                data['sexo'] = 'femenino'
                print(f"✅ [DEBUG] sexo: femenino (desde CURP)")
        except Exception as e:
            print(f"⚠️ [DEBUG] Error extrayendo sexo de CURP: {e}")
    
    print(f"📊 [DEBUG] Total de campos extraídos: {len(data)}")
    return data

# ===============================================
# API ENDPOINTS
# ===============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check con debugging"""
    print("🏥 [DEBUG] Health check solicitado")
    
    try:
        # Verificar conexión a base de datos
        total_afiliaciones = Afiliacion.query.count()
        db_status = 'OK'
        
        # Test de escritura/lectura
        test_query = db.session.execute(db.text("SELECT VERSION()")).fetchone()
        mysql_version = test_query[0] if test_query else 'Unknown'
        
        print(f"✅ [DEBUG] DB OK - {total_afiliaciones} afiliaciones")
        
    except Exception as e:
        total_afiliaciones = 'Error'
        db_status = f'Error: {str(e)}'
        mysql_version = 'Error'
        print(f"❌ [DEBUG] DB Error: {e}")
    
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas - MySQL v1.2 DEBUG',
        'backend': 'Backend/app.py',
        'frontend': 'Servido por Flask',
        'api_configured': bool(GOOGLE_API_KEY),
        'secret_key_configured': SECRET_KEY != 'fallback_secret_key_2025',
        'database_status': db_status,
        'database_type': 'MySQL',
        'mysql_version': mysql_version,
        'total_afiliaciones': total_afiliaciones,
        'debug_info': {
            'google_api_key_length': len(GOOGLE_API_KEY) if GOOGLE_API_KEY else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """API para escaneo INE - VERSIÓN CON DEBUG COMPLETO"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("="*50)
    print("📸 [DEBUG] INICIANDO PROCESAMIENTO DE IMAGEN INE")
    print("="*50)
    
    start_time = time.time()
    user_ip = request.remote_addr
    
    # Crear log de escaneo básico
    log_data = {
        'ip_usuario': user_ip,
        'fecha_escaneo': datetime.utcnow(),
        'exito': False,
        'error_mensaje': ''
    }
    
    try:
        # PASO 1: Verificar que se recibió archivo
        print("🔍 [DEBUG] PASO 1: Verificando archivo recibido...")
        
        if 'imagen' not in request.files:
            error_msg = 'No se recibió imagen en request.files'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': error_msg})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        file = request.files['imagen']
        if file.filename == '':
            error_msg = 'Archivo con nombre vacío'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': error_msg})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        print(f"✅ [DEBUG] Archivo recibido: {file.filename}")
        print(f"📊 [DEBUG] Content-Type: {file.content_type}")
        
        # PASO 2: Leer y validar imagen
        print("🔍 [DEBUG] PASO 2: Leyendo imagen...")
        
        try:
            image_data = file.read()
            file_size = len(image_data)
            print(f"📊 [DEBUG] Tamaño de archivo: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        except Exception as e:
            error_msg = f'Error leyendo imagen: {str(e)}'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': error_msg})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Validar tamaño
        if file_size > 10 * 1024 * 1024:  # 10MB max
            error_msg = 'Archivo demasiado grande (máximo 10MB)'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': error_msg})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # PASO 3: Verificar Google Vision API
        print("🔍 [DEBUG] PASO 3: Verificando Google Vision API...")
        
        if not GOOGLE_API_KEY:
            error_msg = 'Google Vision API Key no configurada'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': error_msg})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        print(f"✅ [DEBUG] API Key configurada (longitud: {len(GOOGLE_API_KEY)})")
        
        # PASO 4: Procesar imagen con OpenCV
        print("🔍 [DEBUG] PASO 4: Procesando imagen con OpenCV...")
        
        try:
            # Convertir a array numpy
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                error_msg = 'Imagen inválida o formato no soportado'
                print(f"❌ [DEBUG] {error_msg}")
                log_data['error_mensaje'] = error_msg
                
                error_response = jsonify({'success': False, 'error': error_msg})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 400
            
            print(f"✅ [DEBUG] Imagen decodificada: {image.shape}")
            
            # Mejorar imagen
            enhanced_image = enhance_image_for_ocr(image)
            
            # Convertir imagen mejorada a bytes
            success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
            if not success:
                print("⚠️ [DEBUG] Error mejorando imagen, usando original")
                enhanced_image_data = image_data
            else:
                enhanced_image_data = enhanced_buffer.tobytes()
                print(f"✅ [DEBUG] Imagen mejorada: {len(enhanced_image_data)} bytes")
            
        except Exception as e:
            error_msg = f'Error procesando imagen con OpenCV: {str(e)}'
            print(f"❌ [DEBUG] {error_msg}")
            print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
            
            # Usar imagen original si falla el procesamiento
            enhanced_image_data = image_data
            print("⚠️ [DEBUG] Usando imagen original sin procesamiento")
        
        # PASO 5: Enviar a Google Vision API
        print("🔍 [DEBUG] PASO 5: Enviando a Google Vision API...")
        
        try:
            image_base64 = base64.b64encode(enhanced_image_data).decode('utf-8')
            print(f"📊 [DEBUG] Imagen codificada en base64: {len(image_base64)} caracteres")
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
            
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
            
            print("📡 [DEBUG] Enviando request a Google Vision...")
            
            # Hacer request
            response = requests.post(url, json=request_body, timeout=45)
            print(f"📡 [DEBUG] Google Vision status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "Sin detalles"
                error_msg = f'Error Google Vision API (status {response.status_code}): {error_text}'
                print(f"❌ [DEBUG] {error_msg}")
                log_data['error_mensaje'] = error_msg
                
                error_response = jsonify({'success': False, 'error': f'Error Google Vision: {response.status_code}'})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
            
            result = response.json()
            print(f"📄 [DEBUG] Google Vision response keys: {list(result.keys())}")
            
            if 'responses' in result and len(result['responses']) > 0:
                response_data = result['responses'][0]
                print(f"📄 [DEBUG] Response data keys: {list(response_data.keys())}")
                
                if 'error' in response_data:
                    error_msg = f'Google Vision API error: {response_data["error"]}'
                    print(f"❌ [DEBUG] {error_msg}")
                    log_data['error_mensaje'] = error_msg
                    
                    error_response = jsonify({'success': False, 'error': error_msg})
                    error_response.headers.add('Access-Control-Allow-Origin', '*')
                    return error_response, 500
                
                # Extraer texto
                full_text = ""
                
                if 'fullTextAnnotation' in response_data:
                    full_text += response_data['fullTextAnnotation']['text'] + " "
                    print("✅ [DEBUG] Texto de fullTextAnnotation extraído")
                
                if 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                    additional_text = response_data['textAnnotations'][0]['description']
                    full_text += additional_text + " "
                    print("✅ [DEBUG] Texto de textAnnotations extraído")
                
                full_text = ' '.join(full_text.split())
                text_length = len(full_text)
                print(f"📝 [DEBUG] Texto total extraído: {text_length} caracteres")
                
                if text_length == 0:
                    error_msg = 'No se pudo extraer texto de la imagen'
                    print(f"❌ [DEBUG] {error_msg}")
                    log_data['error_mensaje'] = error_msg
                    
                    error_response = jsonify({'success': False, 'error': 'No se pudo leer texto. Intenta con mejor iluminación.'})
                    error_response.headers.add('Access-Control-Allow-Origin', '*')
                    return error_response, 400
                
            else:
                error_msg = 'Respuesta vacía de Google Vision'
                print(f"❌ [DEBUG] {error_msg}")
                log_data['error_mensaje'] = error_msg
                
                error_response = jsonify({'success': False, 'error': 'No se pudo procesar la imagen'})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
            
        except requests.exceptions.Timeout:
            error_msg = 'Timeout en Google Vision API (45s)'
            print(f"❌ [DEBUG] {error_msg}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': 'Timeout procesando imagen. Intenta de nuevo.'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
            
        except Exception as e:
            error_msg = f'Error en Google Vision API: {str(e)}'
            print(f"❌ [DEBUG] {error_msg}")
            print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
            log_data['error_mensaje'] = error_msg
            
            error_response = jsonify({'success': False, 'error': f'Error procesando imagen: {str(e)}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        # PASO 6: Extraer datos de la imagen
        print("🔍 [DEBUG] PASO 6: Extrayendo datos de la imagen...")
        
        extracted_data = extract_ine_data_advanced(full_text)
        
        # PASO 7: Preparar respuesta
        print("🔍 [DEBUG] PASO 7: Preparando respuesta...")
        
        processing_time = time.time() - start_time
        
        # Actualizar log
        log_data['exito'] = True
        log_data['campos_detectados'] = list(extracted_data.keys())
        log_data['texto_extraido'] = full_text[:1000]  # Truncar
        log_data['confianza'] = 0.95
        log_data['tiempo_procesamiento'] = processing_time
        
        # Guardar log en base de datos
        try:
            log_escaneo = LogEscaneo(**log_data)
            db.session.add(log_escaneo)
            db.session.commit()
            print("✅ [DEBUG] Log guardado en base de datos")
        except Exception as e:
            print(f"⚠️ [DEBUG] Error guardando log: {e}")
        
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
                'metodo_usado': 'Railway MySQL v1.2 DEBUG'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data,
                'clave_elector_valida': 'clave_elector' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'municipio'])
            },
            'debug_info': {
                'campos_detectados': list(extracted_data.keys()),
                'texto_length': len(full_text),
                'processing_time': round(processing_time, 2),
                'file_size_mb': round(file_size / 1024 / 1024, 2)
            }
        }
        
        print(f"✅ [DEBUG] PROCESAMIENTO COMPLETADO - {len(extracted_data)} campos en {processing_time:.2f}s")
        print("="*50)
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f'Error general: {str(e)}'
        
        print(f"💥 [DEBUG] ERROR GENERAL: {error_msg}")
        print(f"💥 [DEBUG] Traceback completo:")
        print(traceback.format_exc())
        print("="*50)
        
        # Guardar error en log
        log_data['exito'] = False
        log_data['error_mensaje'] = error_msg
        log_data['tiempo_procesamiento'] = processing_time
        
        try:
            log_escaneo = LogEscaneo(**log_data)
            db.session.add(log_escaneo)
            db.session.commit()
        except Exception as db_error:
            print(f"⚠️ [DEBUG] Error guardando log de error: {db_error}")
        
        error_response = jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/api/guardar-afiliacion', methods=['POST', 'OPTIONS'])
def guardar_afiliacion():
    """Guardar nueva afiliación en base de datos con debugging"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("="*50)
    print("💾 [DEBUG] GUARDANDO NUEVA AFILIACIÓN")
    print("="*50)
    
    try:
        data = request.get_json()
        
        if not data:
            print("❌ [DEBUG] No se recibieron datos JSON")
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
        
        print(f"📋 [DEBUG] Datos recibidos - {len(data)} campos:")
        for key, value in data.items():
            if value and str(value).strip():
                print(f"  ✅ {key}: '{value}'")
            else:
                print(f"  ❌ {key}: VACÍO/NULO")
        
        # Verificar campos obligatorios
        required_fields = ['nombres', 'primer_apellido', 'curp', 'clave_elector', 'email', 'telefono']
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field] or str(data[field]).strip() == '':
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Campos obligatorios faltantes: {", ".join(missing_fields)}'
            print(f"❌ [DEBUG] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        print("✅ [DEBUG] Todos los campos obligatorios presentes")
        
        # Limpiar datos
        curp_clean = str(data['curp']).strip().upper()
        clave_elector_clean = str(data['clave_elector']).strip().upper()
        
        print(f"🧹 [DEBUG] CURP limpia: {curp_clean}")
        print(f"🧹 [DEBUG] Clave elector limpia: {clave_elector_clean}")
        
        # Verificar duplicados
        print("🔍 [DEBUG] Verificando duplicados...")
        
        existing_curp = Afiliacion.query.filter_by(curp=curp_clean).first()
        if existing_curp:
            error_msg = f'Ya existe una afiliación con la CURP: {curp_clean}'
            print(f"❌ [DEBUG] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        existing_clave = Afiliacion.query.filter_by(clave_elector=clave_elector_clean).first()
        if existing_clave:
            error_msg = f'Ya existe una afiliación con la Clave de Elector: {clave_elector_clean}'
            print(f"❌ [DEBUG] {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        print("✅ [DEBUG] No hay duplicados")
        
        # Generar folio único
        folio = Afiliacion.generar_folio()
        print(f"🎫 [DEBUG] Folio generado: {folio}")
        
        # Crear nueva afiliación
        print("📝 [DEBUG] Creando objeto Afiliacion...")
        
        nueva_afiliacion = Afiliacion(
            folio=folio,
            afiliador=str(data.get('afiliador', '')).strip(),
            nombres=str(data['nombres']).strip(),
            primer_apellido=str(data['primer_apellido']).strip(),
            segundo_apellido=str(data.get('segundo_apellido', '')).strip(),
            lugar_nacimiento=str(data.get('lugar_nacimiento', '')).strip(),
            curp=curp_clean,
            clave_elector=clave_elector_clean,
            email=str(data['email']).strip().lower(),
            telefono=str(data['telefono']).strip(),
            genero=str(data.get('genero', '')).strip(),
            llegada_prd=str(data.get('llegada_prd', '')).strip(),
            municipio=str(data.get('municipio', '')).strip(),
            colonia=str(data.get('colonia', '')).strip(),
            codigo_postal=str(data.get('codigo_postal', '')).strip(),
            calle=str(data.get('calle', '')).strip(),
            numero_exterior=str(data.get('numero_exterior', '')).strip(),
            numero_interior=str(data.get('numero_interior', '')).strip(),
            declaracion_veracidad=bool(data.get('declaracion_veracidad', True)),
            declaracion_principios=bool(data.get('declaracion_principios', True)),
            terminos_condiciones=bool(data.get('terminos_condiciones', True)),
            metodo_captura=str(data.get('metodo_captura', 'manual')),
            ip_registro=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        print("✅ [DEBUG] Objeto Afiliacion creado")
        
        # Guardar en base de datos
        print("💾 [DEBUG] Guardando en MySQL...")
        
        db.session.add(nueva_afiliacion)
        db.session.commit()
        
        print(f"✅ [DEBUG] AFILIACIÓN GUARDADA EXITOSAMENTE: {folio}")
        print("="*50)
        
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
        error_msg = f'Error guardando afiliación: {str(e)}'
        
        print(f"💥 [DEBUG] ERROR GUARDANDO: {error_msg}")
        print(f"💥 [DEBUG] Traceback:")
        print(traceback.format_exc())
        print("="*50)
        
        error_response = jsonify({'success': False, 'error': error_msg})
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
    
    print("🚀 Iniciando sistema completo con MySQL y DEBUG completo...")
    print(f"🌐 Frontend + Backend + MySQL en puerto: {PORT}")
    app.run(debug=False, host=HOST, port=PORT)
    
@app.route('/api/test-google-vision', methods=['GET'])
def test_google_vision():
    """Probar Google Vision API con imagen simple"""
    
    print("🧪 [TEST] Probando Google Vision API...")
    
    try:
        if not GOOGLE_API_KEY:
            return jsonify({
                'success': False, 
                'error': 'API Key no configurada',
                'details': 'GOOGLE_VISION_API_KEY no está en las variables de entorno'
            })
        
        print(f"🔑 [TEST] API Key longitud: {len(GOOGLE_API_KEY)}")
        print(f"🔑 [TEST] API Key primeros 10 chars: {GOOGLE_API_KEY[:10]}...")
        
        # Crear una imagen de prueba simple (1x1 pixel blanco)
        import base64
        
        # Imagen PNG 1x1 blanca en base64
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
        
        request_body = {
            "requests": [{
                "image": {"content": test_image_b64},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}]
            }]
        }
        
        print("📡 [TEST] Enviando request de prueba...")
        
        response = requests.post(url, json=request_body, timeout=30)
        
        print(f"📡 [TEST] Status Code: {response.status_code}")
        print(f"📡 [TEST] Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ [TEST] API Key FUNCIONA - Response: {result}")
            
            return jsonify({
                'success': True,
                'message': 'Google Vision API funciona correctamente',
                'api_key_valid': True,
                'response': result
            })
        else:
            error_text = response.text
            print(f"❌ [TEST] API Key ERROR - Status: {response.status_code}")
            print(f"❌ [TEST] Error Response: {error_text}")
            
            return jsonify({
                'success': False,
                'error': f'API Key inválida o expirada (Status: {response.status_code})',
                'details': error_text,
                'api_key_length': len(GOOGLE_API_KEY)
            })
            
    except Exception as e:
        print(f"💥 [TEST] Exception: {e}")
        return jsonify({
            'success': False,
            'error': f'Error probando API: {str(e)}',
            'details': traceback.format_exc()
        })