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
# CONFIGURACIÓN PARA RAILWAY - BACKEND/
# ===============================================

load_dotenv()
app = Flask(__name__)

# CORS configurado para Railway
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# Variables de entorno para Railway
GOOGLE_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
PORT = int(os.getenv('PORT', 5001))
HOST = '0.0.0.0'

# Validación de API Key
if not GOOGLE_API_KEY:
    print("⚠️  GOOGLE_VISION_API_KEY no configurada en Railway")
else:
    print("✅ Google Vision API Key configurada")

print("="*60)
print("🚀 SISTEMA PRD ZACATECAS - RAILWAY v8.0")
print("📁 Ejecutándose desde: Backend/app.py")
print(f"🌐 Puerto: {PORT}")
print(f"🔑 API configurada: {'✓' if GOOGLE_API_KEY else '✗'}")
print("="*60)

def enhance_image_for_ocr(image):
    """Mejora la imagen para OCR"""
    print("🔧 Mejorando imagen para OCR...")
    
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
    """Analiza imagen con Google Vision API"""
    if not GOOGLE_API_KEY:
        return {'success': False, 'error': 'API Key no configurada en Railway', 'text': ''}
    
    print("🔍 Analizando con Google Vision API...")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    max_size = 10 * 1024 * 1024
    if len(image_data) > max_size:
        return {'success': False, 'error': 'Imagen demasiado grande (máximo 10MB)', 'text': ''}
    
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        return {'success': False, 'error': f'Error codificando imagen: {str(e)}', 'text': ''}
    
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
                return {'success': False, 'error': 'No se pudo extraer texto de la imagen', 'text': ''}
            
            return {'success': True, 'text': full_text, 'confidence': 0.95}
        else:
            return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout: la imagen tardó demasiado en procesarse', 'text': ''}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Error de conexión: {str(e)}', 'text': ''}
    except Exception as e:
        return {'success': False, 'error': f'Error interno: {str(e)}', 'text': ''}

def extraer_colonia_ultra_simple(texto):
    """Extracción ultra simple de colonia"""
    if not texto:
        return None
    
    print(f"🏘️  Extrayendo colonia de: '{texto[:50]}...'")
    
    candidatos = []
    
    # Buscar FRACC
    fracc_matches = re.finditer(r'(?:FRACC|FRACCIONAMIENTO)\s+(.{5,50})', texto, re.IGNORECASE)
    for match in fracc_matches:
        candidato = match.group(1)
        candidatos.append(('FRACC', candidato))
    
    # Buscar COL
    col_matches = re.finditer(r'(?:COL|COLONIA)\s+(.{3,50})', texto, re.IGNORECASE)
    for match in col_matches:
        candidato = match.group(1)
        candidatos.append(('COL', candidato))
    
    # Buscar antes de código postal
    cp_matches = re.finditer(r'([A-ZÁÉÍÓÚÑ].{10,50}?)\s+\d{5}', texto, re.IGNORECASE)
    for match in cp_matches:
        candidato = match.group(1)
        candidatos.append(('ANTES_CP', candidato))
    
    if not candidatos:
        return None
    
    # Limpiar candidatos
    mejores_candidatos = []
    for tipo, candidato_raw in candidatos:
        candidato_limpio = limpiar_ultra_simple(candidato_raw)
        if candidato_limpio and len(candidato_limpio) >= 3:
            score = calcular_score_simple(candidato_limpio, tipo)
            mejores_candidatos.append((candidato_limpio, score, tipo))
    
    if not mejores_candidatos:
        return None
    
    # Mejor candidato
    mejores_candidatos.sort(key=lambda x: x[1], reverse=True)
    mejor_candidato = mejores_candidatos[0]
    
    print(f"✅ Colonia extraída: '{mejor_candidato[0]}'")
    return mejor_candidato[0]

def limpiar_ultra_simple(texto):
    """Limpieza ultra simple"""
    if not texto:
        return texto
    
    # Quitar prefijos
    texto = re.sub(r'^(COL|COLONIA|FRACC|FRACCIONAMIENTO)\s*', '', texto, flags=re.IGNORECASE)
    
    # Quitar código postal al final
    texto = re.sub(r'\s+\d{5}$', '', texto)
    
    # Quitar ciudades/estados
    texto = re.sub(r'\s+(ZACATECAS|ZAC|GUADALUPE|EDO|ESTADO)$', '', texto, flags=re.IGNORECASE)
    
    # Quedarse con primeras palabras válidas
    palabras = texto.split()
    palabras_buenas = []
    
    for palabra in palabras:
        if re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ]+$', palabra):
            palabras_buenas.append(palabra)
        elif len(palabra) <= 6 and re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ0-9]+$', palabra):
            palabras_buenas.append(palabra)
        else:
            break
    
    if len(palabras_buenas) > 5:
        palabras_buenas = palabras_buenas[:5]
    
    resultado = ' '.join(palabras_buenas)
    
    if resultado:
        resultado_capitalizado = ' '.join(palabra.capitalize() for palabra in resultado.split())
        return resultado_capitalizado
    
    return resultado

def calcular_score_simple(candidato, tipo):
    """Score simple para candidatos"""
    score = 0
    
    if tipo == 'FRACC':
        score += 50
    elif tipo == 'COL':
        score += 45
    elif tipo == 'ANTES_CP':
        score += 30
    
    if 5 <= len(candidato) <= 25:
        score += 20
    elif 3 <= len(candidato) <= 40:
        score += 10
    
    candidato_upper = candidato.upper()
    palabras_comunes = ['CAMPO', 'BRAVO', 'PASEOS', 'VALLE', 'DEL', 'CENTRO', 'LOMAS', 'VISTA']
    
    for palabra in palabras_comunes:
        if palabra in candidato_upper:
            score += 15
    
    return score

def extract_ine_data_prd(text):
    """Extracción completa de datos de INE para PRD"""
    print("📊 === EXTRACCIÓN PRD COMPLETA ===")
    
    data = {}
    
    # Limpiar texto
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    print(f"📝 Texto procesado: {len(text)} caracteres")
    
    # Patrones para datos personales
    patterns_personales = {
        'curp': [
            r'CURP[\s:]*([A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2})',
            r'([A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2})',
        ],
        'clave_elector': [
            r'CLAVE\s+DE\s+ELECTOR[\s:]*([A-Z0-9]{15,20})',
            r'ELECTOR[\s:]*([A-Z0-9]{15,20})',
            r'([A-Z]{6}[0-9]{8}[HM][0-9]{3})',
        ],
        'nombres': [
            r'NOMBRE[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,40})(?=\s+(?:SEXO|APELLIDO|DOMICILIO))',
            r'NOMBRE[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,40})',
        ],
        'primer_apellido': [
            r'APELLIDO\s+PATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
            r'PATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        ],
        'segundo_apellido': [
            r'APELLIDO\s+MATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
            r'MATERNO[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{2,30})',
        ]
    }
    
    # Patrones para domicilio
    patterns_domicilio = {
        'calle': [
            r'(?:DOMICILIO|CALLE)[\s:]*([A-ZÁÉÍÓÚÑ][^0-9]{5,50})(?=\s*(?:\d|NUM|#|COL|COLONIA))',
            r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{8,40})\s+(?:\d{1,5})\s+(?:COL|COLONIA)',
        ],
        'numero_exterior': [
            r'(?:NUM|NUMERO|#)[\s:]*(?:EXT[\s:]*)?([0-9A-Z\-]{1,6})',
            r'\s([0-9]{1,5})\s+(?:COL|COLONIA)',
        ],
        'codigo_postal': [
            r'(?:CP|CODIGO\s+POSTAL|C\.P\.)[\s:]*([0-9]{5})',
            r'([0-9]{5})\s+(?:ZACATECAS|ZAC|GUADALUPE)',
            r'(?<!\d)([0-9]{5})(?!\d)',
        ],
        'municipio': [
            r'(?:MUNICIPIO|DELEGACION)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,25})',
            r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,20})\s+(?:ESTADO|EDO|ZACATECAS|ZAC)',
            r'(FRESNILLO|GUADALUPE|ZACATECAS|JEREZ|RÍO\s+GRANDE|SOMBRERETE|PINOS|CALERA|OJOCALIENTE)',
        ]
    }
    
    # Extraer datos personales
    for field, pattern_list in patterns_personales.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'\s+', ' ', value)
                if value and len(value) > 1:
                    data[field] = value
                    print(f"✅ {field}: {value}")
                    break
    
    # Extraer domicilio
    print("\n🏠 === EXTRAYENDO DOMICILIO ===")
    
    # Buscar sección de domicilio
    domicilio_patterns = [
        r'DOMICILIO[^A-Z]*([^A-Z]*(?:[A-Z][^A-Z]*){0,30})',
        r'(?:CALLE|AV|AVENIDA)[^A-Z]*([^A-Z]*(?:[A-Z][^A-Z]*){0,25})',
    ]
    
    domicilio_section = ""
    for pattern in domicilio_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            domicilio_section = match.group(0)
            break
    
    if not domicilio_section:
        domicilio_section = text
    
    # Extraer colonia con algoritmo ultra simple
    colonia_extraida = extraer_colonia_ultra_simple(domicilio_section)
    if colonia_extraida:
        data['colonia'] = colonia_extraida
    
    # Extraer otros campos de domicilio
    for field, pattern_list in patterns_domicilio.items():
        for pattern in pattern_list:
            for search_text in [domicilio_section, text]:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    value = re.sub(r'\s+', ' ', value)
                    
                    # Validaciones básicas
                    if field == 'codigo_postal' and len(value) != 5:
                        continue
                    if field in ['numero_exterior'] and len(value) > 8:
                        continue
                    if field in ['calle'] and len(value) < 3:
                        continue
                    
                    if value and len(value) > 1:
                        data[field] = value
                        print(f"🏠 {field}: {value}")
                        break
            if field in data:
                break
    
    # Post-procesamiento
    print("\n🔧 === POST-PROCESAMIENTO ===")
    
    # Validar CURP y extraer género
    if 'curp' in data:
        curp = re.sub(r'[^A-Z0-9]', '', data['curp'].upper())
        if len(curp) == 18:
            data['curp'] = curp
            sexo_char = curp[10]
            if sexo_char == 'H':
                data['sexo'] = 'masculino'
            elif sexo_char == 'M':
                data['sexo'] = 'femenino'
            print(f"✅ CURP válido: {curp}, Género: {data.get('sexo', 'No detectado')}")
        else:
            del data['curp']
    
    # Validar clave de elector
    if 'clave_elector' in data:
        clave = re.sub(r'[^A-Z0-9]', '', data['clave_elector'].upper())
        if len(clave) >= 15 and len(clave) <= 20:
            data['clave_elector'] = clave
            print(f"✅ Clave elector válida: {clave}")
        else:
            del data['clave_elector']
    
    # Validar código postal
    if 'codigo_postal' in data:
        cp = re.sub(r'[^0-9]', '', data['codigo_postal'])
        if len(cp) == 5:
            data['codigo_postal'] = cp
            print(f"✅ CP válido: {cp}")
        else:
            del data['codigo_postal']
    
    print(f"\n📊 === RESUMEN FINAL ===")
    print(f"Total campos extraídos: {len(data)}")
    for key, value in data.items():
        tipo = "DOMICILIO" if key in ['calle', 'numero_exterior', 'colonia', 'codigo_postal', 'municipio'] else "PERSONAL"
        print(f"   {tipo} {key}: {value}")
    
    return data

# ===============================================
# ENDPOINTS PARA RAILWAY
# ===============================================

@app.route('/', methods=['GET'])
def home():
    """Endpoint raíz"""
    return jsonify({
        'message': 'PRD Zacatecas Backend - Railway v8.0',
        'status': 'OK',
        'location': 'Backend/app.py',
        'endpoints': ['/health', '/api/health', '/api/extract-ine-prd']
    })

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    response_data = {
        'status': 'OK',
        'service': 'PRD Zacatecas Backend v8.0',
        'location': 'Backend/app.py',
        'port': PORT,
        'host': HOST,
        'api_configured': bool(GOOGLE_API_KEY),
        'endpoints': {
            'health': '/health',
            'api_health': '/api/health', 
            'extract_ine': '/api/extract-ine-prd'
        }
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """Endpoint principal para escaneo INE"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("📸 === PETICIÓN DE ESCANEO INE ===")
    
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

        # Validación de archivo
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            error_response = jsonify({'success': False, 'error': f'Tipo de archivo no permitido: {file_ext}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        print(f"📎 Imagen: {file.filename} ({file_ext})")
        
        # Leer imagen
        image_data = file.read()
        max_size = 15 * 1024 * 1024
        
        if len(image_data) > max_size:
            error_response = jsonify({'success': False, 'error': 'Imagen demasiado grande (máximo 15MB)'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        print(f"📏 Tamaño: {len(image_data)/1024/1024:.1f}MB")
        
        # Convertir imagen
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Imagen corrupta")
            
            height, width = image.shape[:2]
            if width < 100 or height < 100:
                raise ValueError("Imagen demasiado pequeña")
            
            print(f"🖼️  Dimensiones: {width}x{height}")
                
        except Exception as e:
            error_response = jsonify({'success': False, 'error': f'Error procesando imagen: {str(e)}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Mejorar imagen
        enhanced_image = enhance_image_for_ocr(image)
        
        success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
        if not success:
            error_response = jsonify({'success': False, 'error': 'Error al procesar imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        enhanced_image_data = enhanced_buffer.tobytes()
        
        # Google Vision API
        print("🔍 Enviando a Google Vision...")
        vision_result = analyze_with_vision_api(enhanced_image_data)
        
        if not vision_result['success']:
            print("🔄 Reintentando con imagen original...")
            vision_result = analyze_with_vision_api(image_data)
            
            if not vision_result['success']:
                error_response = jsonify({'success': False, 'error': vision_result['error']})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
        
        print(f"📝 Texto extraído: {len(vision_result['text'])} caracteres")
        
        # Extraer datos PRD
        extracted_data = extract_ine_data_prd(vision_result['text'])
        
        # Crear respuesta
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
                'numero_exterior': extracted_data.get('numero_exterior', 'NO DETECTADO'),
                'colonia': extracted_data.get('colonia', 'NO DETECTADO'),
                'codigo_postal': extracted_data.get('codigo_postal', 'NO DETECTADO'),
                'metodo_usado': 'Railway + Google Vision v8.0 - Backend/',
                'calidad_extraccion': 'EXCELENTE' if len(extracted_data) >= 8 else 'BUENA' if len(extracted_data) >= 5 else 'REGULAR'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data and len(extracted_data.get('curp', '')) == 18,
                'clave_elector_valida': 'clave_elector' in extracted_data and len(extracted_data.get('clave_elector', '')) >= 15,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'municipio'])
            },
            'debug_info': {
                'campos_detectados': list(extracted_data.keys()),
                'texto_length': len(vision_result['text']),
                'backend_version': '8.0',
                'backend_location': 'Backend/app.py'
            }
        }
        
        print(f"✅ Procesamiento completado - {len(extracted_data)} campos")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = jsonify({'success': False, 'error': f'Error interno: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    print("🚀 Iniciando servidor PRD en Railway...")
    print(f"📁 Ubicación: Backend/app.py")
    print(f"🌐 Puerto: {PORT}")
    print(f"🔑 Google Vision: {'✓' if GOOGLE_API_KEY else '✗'}")
    
    app.run(debug=False, host=HOST, port=PORT)