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

load_dotenv()

# Flask configurado para servir archivos estáticos
app = Flask(__name__, static_folder='..', static_url_path='')

# CORS configurado
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

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
    app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URL
elif DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    mysql_config = {
        'host': 'maglev.proxy.rlwy.net',
        'port': 26954,
        'user': 'root',
        'password': 'KdjBgzwzRqIRkMkWKdIpYPOUvTrIpKUD',
        'database': 'railway'
    }
    mysql_url = f"mysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'max_overflow': 0,
    'echo': False
}

# Inicializar base de datos
db.init_app(app)

print("🚀 SISTEMA PRD ZACATECAS - MYSQL SIMPLE")
print(f"🔑 API: {'✓' if GOOGLE_API_KEY else '✗'}")
print("🗄️  DB: ✓ MySQL Railway")

# ===============================================
# RUTAS PARA SERVIR EL FRONTEND
# ===============================================

@app.route('/')
def index():
    return send_file('../index.html')

@app.route('/pages/<path:filename>')
def pages(filename):
    return send_from_directory('../pages', filename)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('../assets', filename)

# ===============================================
# FUNCIONES BÁSICAS
# ===============================================

def enhance_image_for_ocr(image):
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
        return binary
    except:
        return image

def analyze_with_vision_api(image_data):
    if not GOOGLE_API_KEY:
        return {'success': False, 'error': 'API Key no configurada', 'text': ''}
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        request_body = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "TEXT_DETECTION", "maxResults": 50}
                ]
            }]
        }
        
        response = requests.post(url, json=request_body, timeout=30)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'Error API: {response.status_code}', 'text': ''}
        
        result = response.json()
        
        if 'responses' in result and len(result['responses']) > 0:
            response_data = result['responses'][0]
            
            if 'error' in response_data:
                return {'success': False, 'error': str(response_data['error']), 'text': ''}
            
            full_text = ""
            
            if 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                full_text = response_data['textAnnotations'][0]['description']
            
            if not full_text.strip():
                return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
            return {'success': True, 'text': full_text, 'confidence': 0.95}
        else:
            return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}', 'text': ''}

def extract_ine_data_prd(text):
    data = {}
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    
    patterns = {
        'curp': r'([A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2})',
        'clave_elector': r'([A-Z]{6}[0-9]{8}[HM][0-9]{3})',
        'nombres': r'NOMBRE[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,40})',
        'primer_apellido': r'PATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'segundo_apellido': r'MATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        'municipio': r'(FRESNILLO|GUADALUPE|ZACATECAS|JEREZ|SOMBRERETE|PINOS|CALERA)',
        'codigo_postal': r'([0-9]{5})',
        'calle': r'DOMICILIO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{5,40})',
        'colonia': r'COL[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,30})'
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                data[field] = value
    
    # Extraer género de CURP
    if 'curp' in data and len(data['curp']) >= 11:
        sexo_char = data['curp'][10]
        if sexo_char == 'H':
            data['sexo'] = 'masculino'
        elif sexo_char == 'M':
            data['sexo'] = 'femenino'
    
    return data

# ===============================================
# API ENDPOINTS
# ===============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        total_afiliaciones = Afiliacion.query.count()
        db_status = 'OK'
        test_query = db.session.execute(db.text("SELECT VERSION()")).fetchone()
        mysql_version = test_query[0] if test_query else 'Unknown'
    except Exception as e:
        total_afiliaciones = 'Error'
        db_status = f'Error: {str(e)}'
        mysql_version = 'Error'
    
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas - MySQL SIMPLE',
        'api_configured': bool(GOOGLE_API_KEY),
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
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        if 'imagen' not in request.files:
            error_response = jsonify({'success': False, 'error': 'No se recibió imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        file = request.files['imagen']
        if file.filename == '':
            error_response = jsonify({'success': False, 'error': 'Archivo vacío'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        # Leer imagen
        image_data = file.read()
        
        # Convertir imagen
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            error_response = jsonify({'success': False, 'error': 'Imagen inválida'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Mejorar imagen
        enhanced_image = enhance_image_for_ocr(image)
        
        # Convertir a bytes
        success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
        if not success:
            enhanced_image_data = image_data
        else:
            enhanced_image_data = enhanced_buffer.tobytes()
        
        # Analizar con Google Vision
        vision_result = analyze_with_vision_api(enhanced_image_data)
        
        if not vision_result['success']:
            # Reintentar con imagen original
            vision_result = analyze_with_vision_api(image_data)
            
            if not vision_result['success']:
                error_response = jsonify({'success': False, 'error': vision_result['error']})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
        
        # Extraer datos
        extracted_data = extract_ine_data_prd(vision_result['text'])
        
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
                'metodo_usado': 'Railway MySQL SIMPLE'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data,
                'clave_elector_valida': 'clave_elector' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'municipio'])
            }
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        error_response = jsonify({'success': False, 'error': f'Error interno: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/api/guardar-afiliacion', methods=['POST', 'OPTIONS'])
def guardar_afiliacion():
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
        
        # Verificar campos obligatorios
        required_fields = ['nombres', 'primer_apellido', 'curp', 'clave_elector', 'email', 'telefono']
        missing_fields = []
        
        for field in required_fields:
            if field not in data or not data[field] or str(data[field]).strip() == '':
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Campos obligatorios faltantes: {", ".join(missing_fields)}'
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Limpiar datos
        curp_clean = str(data['curp']).strip().upper()
        clave_elector_clean = str(data['clave_elector']).strip().upper()
        
        # Verificar duplicados
        existing_curp = Afiliacion.query.filter_by(curp=curp_clean).first()
        if existing_curp:
            return jsonify({'success': False, 'error': f'Ya existe una afiliación con esta CURP: {curp_clean}'}), 400
        
        existing_clave = Afiliacion.query.filter_by(clave_elector=clave_elector_clean).first()
        if existing_clave:
            return jsonify({'success': False, 'error': f'Ya existe una afiliación con esta Clave de Elector: {clave_elector_clean}'}), 400
        
        # Generar folio único
        folio = Afiliacion.generar_folio()
        
        # Crear nueva afiliación
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
        
        # Guardar en base de datos
        db.session.add(nueva_afiliacion)
        db.session.commit()
        
        response_data = {
            'success': True,
            'folio': folio,
            'id': nueva_afiliacion.id,
            'mensaje': 'Afiliación guardada exitosamente'
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        db.session.rollback()
        error_response = jsonify({'success': False, 'error': f'Error guardando afiliación: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    try:
        total_afiliaciones = Afiliacion.query.count()
        afiliaciones_hoy = Afiliacion.query.filter(
            Afiliacion.fecha_registro >= datetime.utcnow().date()
        ).count()
        
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
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas verificadas/creadas")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    print("🚀 Iniciando sistema SIMPLE...")
    app.run(debug=False, host=HOST, port=PORT)