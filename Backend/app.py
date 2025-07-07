from flask import Flask, request, jsonify
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
# CONFIGURACIÓN PARA RAILWAY (BACKEND FOLDER)
# ===============================================

# Cargar variables de entorno desde archivo .env
# Railway busca automáticamente en la raíz del proyecto
load_dotenv()

app = Flask(__name__)

# CORS configurado para Railway
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# Variables de entorno para Railway
GOOGLE_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
PORT = int(os.getenv('PORT', 5001))  # Railway asigna automáticamente
HOST = '0.0.0.0'  # Railway requiere 0.0.0.0

# Validación de API Key
if not GOOGLE_API_KEY:
    print("⚠️  ADVERTENCIA: GOOGLE_VISION_API_KEY no configurada")
    print("📝 Ve a Railway → Variables → Add Variable")
    print("🔑 Nombre: GOOGLE_VISION_API_KEY")
    print("🔑 Valor: tu_api_key_de_google")
else:
    print("✅ Google Vision API Key configurada")

print("="*60)
print("🚀 SISTEMA PRD ZACATECAS - RAILWAY v7.0")
print("📁 Ejecutándose desde: backend/app.py")
print("="*60)
print(f"🌐 Puerto: {PORT}")
print(f"🏠 Host: {HOST}")
print(f"🔑 API configurada: {'✓' if GOOGLE_API_KEY else '✗'}")
print("="*60)

def enhance_image_for_ocr(image):
    """Mejora la imagen para OCR"""
    print("🔧 Mejorando imagen para OCR...")
    
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Redimensionar si es muy pequeña
    height, width = gray.shape
    if width < 1000:
        scale_factor = 1000 / width
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        print(f"📏 Redimensionado a: {new_width}x{new_height}")
    
    # Aplicar filtro bilateral para reducir ruido
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Mejorar contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Sharpening
    kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # Umbralización adaptativa
    binary = cv2.adaptiveThreshold(sharpened, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 15, 10)
    
    print("✅ Imagen mejorada completada")
    return binary

def analyze_with_vision_api(image_data):
    """Analiza imagen con Google Vision API - Versión Railway"""
    if not GOOGLE_API_KEY:
        return {
            'success': False, 
            'error': 'Google Vision API Key no configurada en Railway. Ve a Variables → Add Variable → GOOGLE_VISION_API_KEY', 
            'text': ''
        }
    
    print("🔍 Analizando con Google Vision API...")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    # Verificar tamaño de imagen
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_data) > max_size:
        return {'success': False, 'error': 'Imagen demasiado grande (máximo 10MB)', 'text': ''}
    
    # Encodear imagen en base64
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        return {'success': False, 'error': f'Error codificando imagen: {str(e)}', 'text': ''}
    
    # Configurar request
    request_body = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [
                {"type": "TEXT_DETECTION", "maxResults": 50},
                {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 50}
            ],
            "imageContext": {
                "textDetectionParams": {
                    "enableTextDetectionConfidenceScore": True
                },
                "languageHints": ["es", "en"]
            }
        }]
    }
    
    try:
        # Timeout de seguridad para Railway
        response = requests.post(url, json=request_body, timeout=45)
        response.raise_for_status()
        result = response.json()
        
        print(f"📊 Google Vision respuesta: {response.status_code}")
        
        if 'responses' in result and len(result['responses']) > 0:
            response_data = result['responses'][0]
            
            if 'error' in response_data:
                print(f"❌ Google Vision error: {response_data['error']}")
                return {'success': False, 'error': str(response_data['error']), 'text': ''}
            
            # Combinar texto de ambas detecciones
            full_text = ""
            
            # DOCUMENT_TEXT_DETECTION
            if 'fullTextAnnotation' in response_data:
                full_text += response_data['fullTextAnnotation']['text'] + " "
                print(f"📄 Document text: {len(response_data['fullTextAnnotation']['text'])} caracteres")
            
            # TEXT_DETECTION
            if 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                additional_text = response_data['textAnnotations'][0]['description']
                full_text += additional_text + " "
                print(f"📝 Text annotations: {len(additional_text)} caracteres")
            
            # Limpiar texto
            full_text = ' '.join(full_text.split())
            
            if not full_text.strip():
                return {'success': False, 'error': 'No se pudo extraer texto de la imagen', 'text': ''}
            
            return {
                'success': True,
                'text': full_text,
                'confidence': 0.95
            }
        else:
            return {'success': False, 'error': 'No se recibió respuesta válida de Google Vision', 'text': ''}
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout en Google Vision API")
        return {'success': False, 'error': 'Timeout: la imagen tardó demasiado en procesarse (45s)', 'text': ''}
    except requests.exceptions.RequestException as e:
        print(f"🌐 Error de conexión: {e}")
        return {'success': False, 'error': f'Error de conexión con Google Vision: {str(e)}', 'text': ''}
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        return {'success': False, 'error': f'Error interno de Google Vision: {str(e)}', 'text': ''}

# AQUÍ van todas tus funciones de extracción existentes
# (extraer_colonia_ultra_simple, limpiar_ultra_simple, extract_ine_data_prd, etc.)
# Copia y pega exactamente las mismas funciones que ya tienes funcionando

def extract_ine_data_prd(text):
    """Tu función de extracción existente - cópiala aquí exactamente como la tienes"""
    # Por ahora devuelvo un ejemplo, pero reemplaza con tu función completa
    print("📊 Extrayendo datos con algoritmo ultra simple...")
    
    data = {}
    
    # Aquí va tu código completo de extracción...
    # (Copia exactamente las funciones que ya tienes en tu app.py actual)
    
    return data

# ===============================================
# ENDPOINTS PARA RAILWAY
# ===============================================

@app.route('/', methods=['GET'])
def home():
    """Endpoint raíz para verificar que el backend funciona"""
    return jsonify({
        'message': 'PRD Zacatecas Backend - Railway',
        'status': 'OK',
        'version': '7.0',
        'endpoints': ['/health', '/api/health', '/api/extract-ine-prd']
    })

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check para Railway"""
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas Backend',
        'version': '7.0 - Railway',
        'location': 'backend/app.py',
        'port': PORT,
        'host': HOST,
        'api_configured': bool(GOOGLE_API_KEY),
        'endpoints': {
            'health': '/health',
            'api_health': '/api/health', 
            'extract_ine': '/api/extract-ine-prd'
        },
        'environment': {
            'python_version': '3.x',
            'flask_cors': 'enabled',
            'opencv': 'installed'
        }
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """Endpoint principal para escaneo INE - Railway optimizado"""
    
    # Manejar preflight OPTIONS
    if request.method == 'OPTIONS':
        print("✋ Petición OPTIONS (preflight) recibida")
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("📸 Petición POST de escaneo INE recibida en Railway")
    
    try:
        # Verificar imagen
        if 'imagen' not in request.files:
            print("❌ No se recibió archivo de imagen")
            error_response = jsonify({'success': False, 'error': 'No se recibió imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        file = request.files['imagen']
        if file.filename == '':
            print("❌ Archivo sin nombre")
            error_response = jsonify({'success': False, 'error': 'Archivo vacío'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        # Validación de tipo de archivo
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            print(f"❌ Tipo de archivo no permitido: {file_ext}")
            error_response = jsonify({'success': False, 'error': f'Tipo de archivo no permitido: {file_ext}. Usa: {", ".join(allowed_extensions)}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        print(f"📎 Imagen recibida: {file.filename} ({file_ext})")
        
        # Leer imagen con límite de tamaño
        image_data = file.read()
        max_size = 15 * 1024 * 1024  # 15MB
        
        if len(image_data) > max_size:
            print(f"❌ Imagen demasiado grande: {len(image_data)} bytes")
            error_response = jsonify({'success': False, 'error': 'Imagen demasiado grande (máximo 15MB)'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        print(f"📏 Tamaño imagen: {len(image_data)} bytes ({len(image_data)/1024/1024:.1f}MB)")
        
        # Convertir a OpenCV
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Imagen corrupta o formato inválido")
            
            # Validar dimensiones
            height, width = image.shape[:2]
            if width < 100 or height < 100:
                raise ValueError("Imagen demasiado pequeña (mínimo 100x100)")
            
            print(f"🖼️  Imagen válida: {width}x{height}")
                
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            error_response = jsonify({'success': False, 'error': f'Error procesando imagen: {str(e)}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Mejorar imagen para OCR
        enhanced_image = enhance_image_for_ocr(image)
        
        # Convertir imagen mejorada a bytes
        success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
        if not success:
            error_response = jsonify({'success': False, 'error': 'Error interno al procesar imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        enhanced_image_data = enhanced_buffer.tobytes()
        
        # Analizar con Google Vision API
        print("🔍 Enviando a Google Vision API...")
        vision_result = analyze_with_vision_api(enhanced_image_data)
        
        if not vision_result['success']:
            # Intentar con imagen original
            print("🔄 Reintentando con imagen original...")
            vision_result = analyze_with_vision_api(image_data)
            
            if not vision_result['success']:
                print(f"❌ Google Vision falló: {vision_result['error']}")
                error_response = jsonify({'success': False, 'error': vision_result['error']})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
        
        print(f"📝 Texto extraído: {len(vision_result['text'])} caracteres")
        
        # Extraer datos específicos para PRD
        extracted_data = extract_ine_data_prd(vision_result['text'])
        
        # Crear nombre completo
        nombre_parts = []
        if 'primer_apellido' in extracted_data:
            nombre_parts.append(extracted_data['primer_apellido'])
        if 'segundo_apellido' in extracted_data:
            nombre_parts.append(extracted_data['segundo_apellido'])
        if 'nombres' in extracted_data:
            nombre_parts.append(extracted_data['nombres'])
        
        nombre_completo = ' '.join(nombre_parts) if nombre_parts else "NO DETECTADO"
        
        # Respuesta final estructurada
        response_data = {
            'success': True,
            'datos_prd': {
                # Datos personales
                'curp': extracted_data.get('curp', 'NO DETECTADO'),
                'clave_elector': extracted_data.get('clave_elector', 'NO DETECTADO'),
                'nombres': extracted_data.get('nombres', 'NO DETECTADO'),
                'primer_apellido': extracted_data.get('primer_apellido', 'NO DETECTADO'),
                'segundo_apellido': extracted_data.get('segundo_apellido', 'NO DETECTADO'),
                'nombre_completo': nombre_completo,
                'fecha_nacimiento': extracted_data.get('fecha_nacimiento', 'NO DETECTADO'),
                'sexo': extracted_data.get('sexo', 'NO DETECTADO'),
                
                # Datos de domicilio
                'municipio': extracted_data.get('municipio', 'NO DETECTADO'),
                'calle': extracted_data.get('calle', 'NO DETECTADO'),
                'numero_exterior': extracted_data.get('numero_exterior', 'NO DETECTADO'),
                'numero_interior': extracted_data.get('numero_interior', 'NO DETECTADO'),
                'colonia': extracted_data.get('colonia', 'NO DETECTADO'),
                'codigo_postal': extracted_data.get('codigo_postal', 'NO DETECTADO'),
                
                # Metadatos
                'metodo_usado': 'Railway + Google Vision API v7.0',
                'backend_location': 'backend/app.py',
                'calidad_extraccion': 'EXCELENTE' if len(extracted_data) >= 10 else 'BUENA' if len(extracted_data) >= 6 else 'REGULAR'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data and len(extracted_data.get('curp', '')) == 18,
                'clave_elector_valida': 'clave_elector' in extracted_data and len(extracted_data.get('clave_elector', '')) >= 15,
                'nombres_detectados': 'nombres' in extracted_data,
                'apellidos_detectados': 'primer_apellido' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'codigo_postal', 'municipio']),
                'domicilio_completo': all(k in extracted_data for k in ['calle', 'colonia', 'municipio', 'codigo_postal'])
            },
            'debug_info': {
                'campos_detectados': list(extracted_data.keys()),
                'texto_length': len(vision_result['text']),
                'imagen_size': f"{width}x{height}",
                'archivo_size_mb': round(len(image_data)/1024/1024, 2),
                'backend_version': '7.0',
                'railway_optimized': True
            }
        }
        
        print(f"✅ Procesamiento completado - Campos detectados: {len(extracted_data)}")
        for key, value in extracted_data.items():
            tipo = "DOMICILIO" if key in ['calle', 'numero_exterior', 'numero_interior', 'colonia', 'codigo_postal', 'municipio'] else "PERSONAL"
            print(f"   {tipo} {key}: {value}")
        
        # Crear respuesta con headers CORS
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO en Railway: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = jsonify({
            'success': False, 
            'error': f'Error interno del servidor Railway: {str(e)}',
            'backend_location': 'backend/app.py'
        })
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

# ===============================================
# PUNTO DE ENTRADA PARA RAILWAY
# ===============================================

if __name__ == '__main__':
    print("🚀 Iniciando servidor PRD en Railway...")
    print(f"📁 Ubicación: backend/app.py")
    print(f"🌐 Puerto: {PORT}")
    print(f"🏠 Host: {HOST}")
    print(f"🔑 Google Vision: {'✓ Configurada' if GOOGLE_API_KEY else '✗ Faltante'}")
    print("="*60)
    
    # Configuración para Railway
    app.run(debug=False, host=HOST, port=PORT)