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

# ===============================================
# CONFIGURACIÓN PARA RAILWAY - FRONTEND + BACKEND
# ===============================================

load_dotenv()

# Flask configurado para servir archivos estáticos
app = Flask(__name__, static_folder='..', static_url_path='')

# CORS configurado
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# Variables de entorno
GOOGLE_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
PORT = int(os.getenv('PORT', 5001))
HOST = '0.0.0.0'

if not GOOGLE_API_KEY:
    print("⚠️  GOOGLE_VISION_API_KEY no configurada")
else:
    print("✅ Google Vision API Key configurada")

print("="*60)
print("🚀 SISTEMA PRD ZACATECAS - COMPLETO v9.0")
print("📁 Backend: Backend/app.py")
print("🌐 Frontend: Servido por Flask")
print(f"🔑 API: {'✓' if GOOGLE_API_KEY else '✗'}")
print("="*60)

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

def analyze_with_vision_api(image_data):
    """Google Vision API"""
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
        
        response = requests.post(url, json=request_body, timeout=45)
        response.raise_for_status()
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
            
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}', 'text': ''}

def extract_ine_data_prd(text):
    """Extracción básica de datos"""
    print("📊 Extrayendo datos...")
    
    data = {}
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    
    # Patrones básicos
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
                print(f"✅ {field}: {value}")
    
    # Extraer género de CURP
    if 'curp' in data and len(data['curp']) >= 11:
        sexo_char = data['curp'][10]
        if sexo_char == 'H':
            data['sexo'] = 'masculino'
        elif sexo_char == 'M':
            data['sexo'] = 'femenino'
    
    print(f"📊 Total extraído: {len(data)} campos")
    return data

# ===============================================
# API ENDPOINTS
# ===============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas - Completo v9.0',
        'backend': 'Backend/app.py',
        'frontend': 'Servido por Flask',
        'api_configured': bool(GOOGLE_API_KEY)
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """API para escaneo INE"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("📸 Procesando escaneo INE...")
    
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

        print(f"📎 Procesando: {file.filename}")
        
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
            error_response = jsonify({'success': False, 'error': 'Error procesando imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
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
        
        print(f"📝 Texto extraído: {len(vision_result['text'])} caracteres")
        
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
                'metodo_usado': 'Railway Completo v9.0'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data,
                'clave_elector_valida': 'clave_elector' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'municipio'])
            },
            'debug_info': {
                'campos_detectados': list(extracted_data.keys()),
                'texto_length': len(vision_result['text'])
            }
        }
        
        print(f"✅ Completado - {len(extracted_data)} campos")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        print(f"💥 ERROR: {e}")
        error_response = jsonify({'success': False, 'error': f'Error interno: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    print("🚀 Iniciando sistema completo...")
    print(f"🌐 Frontend + Backend en puerto: {PORT}")
    app.run(debug=False, host=HOST, port=PORT)