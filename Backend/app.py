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
# CONFIGURACIÓN SEGURA
# ===============================================

# Cargar variables de entorno desde archivo .env
load_dotenv()

app = Flask(__name__)

# CORS configurado
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     supports_credentials=True)

# Variables de entorno seguraspip3 install python-dotenv
GOOGLE_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))

# Validaciones de seguridad
if not GOOGLE_API_KEY:
    raise ValueError("ERROR CRÍTICO: GOOGLE_VISION_API_KEY no encontrada en archivo .env")

if len(GOOGLE_API_KEY) < 30:
    raise ValueError("ERROR: GOOGLE_VISION_API_KEY parece inválida (muy corta)")

# Configuración de seguridad adicional
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_por_defecto_cambiar_en_produccion')

print("="*60)
print("SISTEMA PRD ZACATECAS - VERSIÓN SEGURA v6.0")
print("="*60)
print(f"Entorno: {FLASK_ENV}")
print(f"Debug: {FLASK_DEBUG}")
print(f"API Key configurada: {'✓' if GOOGLE_API_KEY else '✗'}")
print(f"Host: {FLASK_HOST}:{FLASK_PORT}")
print("="*60)

def enhance_image_for_ocr(image):
    """Mejora la imagen para OCR"""
    print("Mejorando imagen para OCR...")
    
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
        print(f"Redimensionado a: {new_width}x{new_height}")
    
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
    
    print("Imagen mejorada para OCR completada")
    return binary

def analyze_with_vision_api(image_data):
    """Analiza imagen con Google Vision API - VERSIÓN SEGURA"""
    print("Analizando con Google Vision API...")
    
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    # Verificar tamaño de imagen (límite de seguridad)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_data) > max_size:
        return {'success': False, 'error': 'Imagen demasiado grande (máximo 10MB)', 'text': ''}
    
    # Encodear imagen en base64
    try:
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        return {'success': False, 'error': f'Error codificando imagen: {str(e)}', 'text': ''}
    
    # Configurar request con timeout de seguridad
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
        # Timeout de seguridad
        response = requests.post(url, json=request_body, timeout=45)
        response.raise_for_status()
        result = response.json()
        
        print(f"Google Vision respuesta: {response.status_code}")
        
        if 'responses' in result and len(result['responses']) > 0:
            response_data = result['responses'][0]
            
            if 'error' in response_data:
                print(f"Google Vision error: {response_data['error']}")
                return {'success': False, 'error': str(response_data['error']), 'text': ''}
            
            # Combinar texto de ambas detecciones
            full_text = ""
            
            # DOCUMENT_TEXT_DETECTION
            if 'fullTextAnnotation' in response_data:
                full_text += response_data['fullTextAnnotation']['text'] + " "
                print(f"Document text extraído: {len(response_data['fullTextAnnotation']['text'])} caracteres")
            
            # TEXT_DETECTION
            if 'textAnnotations' in response_data and len(response_data['textAnnotations']) > 0:
                additional_text = response_data['textAnnotations'][0]['description']
                full_text += additional_text + " "
                print(f"Text annotations extraído: {len(additional_text)} caracteres")
            
            # Limpiar y validar texto
            full_text = ' '.join(full_text.split())
            
            # Validación de seguridad: texto no debe ser vacío
            if not full_text.strip():
                return {'success': False, 'error': 'No se pudo extraer texto de la imagen', 'text': ''}
            
            return {
                'success': True,
                'text': full_text,
                'confidence': 0.95
            }
        else:
            return {'success': False, 'error': 'No se pudo extraer texto', 'text': ''}
            
    except requests.exceptions.Timeout:
        print("Timeout en Google Vision API")
        return {'success': False, 'error': 'Timeout: la imagen tardó demasiado en procesarse', 'text': ''}
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión en Vision API: {e}")
        return {'success': False, 'error': f'Error de conexión: {str(e)}', 'text': ''}
    except Exception as e:
        print(f"Error inesperado en Vision API: {e}")
        return {'success': False, 'error': f'Error interno: {str(e)}', 'text': ''}

def extraer_colonia_ultra_simple(texto):
    """ALGORITMO ULTRA SIMPLE - Captura TODO"""
    if not texto:
        return None
    
    print(f"ALGORITMO ULTRA SIMPLE para: '{texto}'")
    
    # Buscar TODOS los candidatos posibles sin límites
    candidatos = []
    
    # MÉTODO 1: Buscar FRACC y capturar TODO hasta números o mayúsculas
    fracc_matches = re.finditer(r'(?:FRACC|FRACCIONAMIENTO)\s+(.{5,200})', texto, re.IGNORECASE)
    for match in fracc_matches:
        candidato = match.group(1)
        candidatos.append(('FRACC', candidato))
        print(f"FRACC encontrado: '{candidato}'")
    
    # MÉTODO 2: Buscar COL y capturar TODO
    col_matches = re.finditer(r'(?:COL|COLONIA)\s+(.{3,200})', texto, re.IGNORECASE)
    for match in col_matches:
        candidato = match.group(1)
        candidatos.append(('COL', candidato))
        print(f"COL encontrado: '{candidato}'")
    
    # MÉTODO 3: Buscar todo lo que está antes de un código postal
    cp_matches = re.finditer(r'([A-ZÁÉÍÓÚÑ].{10,200}?)\s+\d{5}', texto, re.IGNORECASE)
    for match in cp_matches:
        candidato = match.group(1)
        candidatos.append(('ANTES_CP', candidato))
        print(f"ANTES_CP encontrado: '{candidato}'")
    
    if not candidatos:
        print("No se encontraron candidatos")
        return None
    
    # LIMPIAR CADA CANDIDATO DE FORMA MÍNIMA
    mejores_candidatos = []
    
    for tipo, candidato_raw in candidatos:
        candidato_limpio = limpiar_ultra_simple(candidato_raw)
        
        if candidato_limpio and len(candidato_limpio) >= 3:
            score = calcular_score_simple(candidato_limpio, tipo)
            mejores_candidatos.append((candidato_limpio, score, tipo))
            print(f"CANDIDATO LIMPIO: '{candidato_limpio}' (Score: {score}, Tipo: {tipo})")
    
    if not mejores_candidatos:
        print("No hay candidatos válidos después de limpiar")
        return None
    
    # Ordenar por score y tomar el mejor
    mejores_candidatos.sort(key=lambda x: x[1], reverse=True)
    mejor_candidato = mejores_candidatos[0]
    
    print(f"GANADOR ULTRA SIMPLE: '{mejor_candidato[0]}' (Score: {mejor_candidato[1]}, Tipo: {mejor_candidato[2]})")
    return mejor_candidato[0]

def limpiar_ultra_simple(texto):
    """Limpieza ULTRA SIMPLE - Solo quitar lo obvio"""
    if not texto:
        return texto
    
    print(f"Limpiando ULTRA SIMPLE: '{texto[:50]}...'")
    
    # Solo quitar prefijos muy obvios
    texto = re.sub(r'^(COL|COLONIA|FRACC|FRACCIONAMIENTO)\s*', '', texto, flags=re.IGNORECASE)
    
    # Solo quitar código postal al final SI ESTÁ CLARAMENTE AL FINAL
    texto = re.sub(r'\s+\d{5}$', '', texto)
    
    # Solo quitar ciudades/estados al final
    texto = re.sub(r'\s+(ZACATECAS|ZAC|GUADALUPE|EDO|ESTADO)$', '', texto, flags=re.IGNORECASE)
    
    # Quitar solo algunas palabras problemáticas al final
    texto = re.sub(r'\s+(CP|C\.P\.).*$', '', texto, flags=re.IGNORECASE)
    
    # Buscar el primer trozo significativo (hasta la primera palabra rara)
    # Dividir en palabras y quedarse con las primeras palabras que parezcan nombre de colonia
    palabras = texto.split()
    palabras_buenas = []
    
    for palabra in palabras:
        # Si es una palabra normal (letras), mantenerla
        if re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ]+$', palabra):
            palabras_buenas.append(palabra)
        # Si tiene números pero es corta, también mantenerla (ej: "98608")
        elif len(palabra) <= 6 and re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ0-9]+$', palabra):
            palabras_buenas.append(palabra)
        # Si encontramos algo raro, parar aquí
        else:
            break
    
    # Tomar máximo 4-5 palabras para evitar texto demasiado largo
    if len(palabras_buenas) > 5:
        palabras_buenas = palabras_buenas[:5]
    
    resultado = ' '.join(palabras_buenas)
    
    # Capitalizar correctamente
    if resultado:
        resultado_capitalizado = ' '.join(palabra.capitalize() for palabra in resultado.split())
        print(f"ULTRA SIMPLE resultado: '{texto[:30]}...' -> '{resultado_capitalizado}'")
        return resultado_capitalizado
    
    return resultado

def calcular_score_simple(candidato, tipo):
    """Score simple para candidatos"""
    score = 0
    
    # Score por tipo
    if tipo == 'FRACC':
        score += 50
    elif tipo == 'COL':
        score += 45
    elif tipo == 'ANTES_CP':
        score += 30
    
    # Score por longitud razonable
    if 5 <= len(candidato) <= 25:
        score += 20
    elif 3 <= len(candidato) <= 40:
        score += 10
    
    # Score por palabras comunes en colonias
    candidato_upper = candidato.upper()
    palabras_comunes = ['CAMPO', 'BRAVO', 'PASEOS', 'VALLE', 'DEL', 'CENTRO', 'LOMAS', 'VISTA']
    
    for palabra in palabras_comunes:
        if palabra in candidato_upper:
            score += 15
    
    # Bonus por combinaciones específicas
    if 'CAMPO' in candidato_upper and 'BRAVO' in candidato_upper:
        score += 25
    if 'PASEOS' in candidato_upper and 'VALLE' in candidato_upper:
        score += 25
    
    return score

def limpiar_calle(texto):
    """Limpia específicamente el campo calle"""
    if not texto or texto == "NO DETECTADO":
        return texto
    
    # Remover prefijos comunes
    texto = re.sub(r'^(DOMICILIO|CALLE|AV|AVENIDA|BOULEVARD|BLVD|PRIVADA|PRIV)\s+', '', texto, flags=re.IGNORECASE)
    
    # Remover números y datos que no son parte del nombre de la calle
    texto = re.sub(r'\s+\d+\s+(COL|COLONIA|CP|C\.P\.).*$', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s+\d{5}\s*.*$', '', texto)
    texto = re.sub(r'\s+(NUM|#|\d+)\s*.*$', '', texto)
    
    # Limpiar caracteres especiales
    texto = re.sub(r'[^A-ZÁÉÍÓÚÑa-záéíóúñ\s]', ' ', texto)
    texto = ' '.join(texto.split())
    
    # Capitalizar correctamente
    palabras = []
    for palabra in texto.split():
        if len(palabra) > 1:
            palabras.append(palabra.capitalize())
    
    resultado = ' '.join(palabras)
    print(f"Calle limpia: '{resultado}'")
    return resultado

def extract_ine_data_prd(text):
    """Extracción con ALGORITMO ULTRA SIMPLE v6.0"""
    print("=== ALGORITMO ULTRA SIMPLE v6.0 ===")
    
    data = {}
    
    # Limpiar y normalizar texto
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    print(f"Texto procesado: {len(text)} caracteres")
    
    # === PATRONES PARA DATOS PERSONALES ===
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
        ],
        'sexo': [
            r'SEXO[\s:]*([HM])',
        ],
        'fecha_nacimiento': [
            r'FECHA\s+DE\s+NACIMIENTO[\s:]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{4})',
            r'NACIMIENTO[\s:]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{4})',
        ]
    }
    
    # === PATRONES PARA DOMICILIO ===
    patterns_domicilio = {
        'calle': [
            r'(?:DOMICILIO|CALLE)[\s:]*([A-ZÁÉÍÓÚÑ][^0-9]{5,50})(?=\s*(?:\d|NUM|#|COL|COLONIA))',
            r'(?:DOMICILIO|CALLE)[\s:]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{5,50})',
            r'((?:CALLE|AV|AVENIDA|BOULEVARD|BLVD|PRIVADA|PRIV)\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{3,40})',
            r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]{8,40})\s+(?:\d{1,5})\s+(?:COL|COLONIA)',
        ],
        'numero_exterior': [
            r'(?:NUM|NUMERO|#)[\s:]*(?:EXT[\s:]*)?([0-9A-Z\-]{1,6})',
            r'(?:EXTERIOR|EXT)[\s:]*([0-9A-Z\-]{1,6})',
            r'(?:CALLE|AV)[^0-9]*([0-9]{1,5})(?:\s|$|[A-Z])',
            r'\s([0-9]{1,5})\s+(?:COL|COLONIA)',
        ],
        'numero_interior': [
            r'(?:NUM|NUMERO|#)[\s:]*(?:INT|INTERIOR)[\s:]*([A-Z0-9\-]{1,8})',
            r'(?:INTERIOR|INT)[\s:]*([A-Z0-9\-]{1,8})',
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
                    print(f"EXTRAÍDO {field}: {value}")
                    break
    
    # === EXTRACCIÓN DE DOMICILIO ===
    print("\n=== EXTRAYENDO DOMICILIO ===")
    
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
            print(f"Sección encontrada: {domicilio_section}")
            break
    
    if not domicilio_section:
        domicilio_section = text
        print("Usando texto completo")
    
    # === EXTRAER COLONIA CON ALGORITMO ULTRA SIMPLE ===
    print(f"\n=== EXTRAYENDO COLONIA ULTRA SIMPLE ===")
    colonia_extraida = extraer_colonia_ultra_simple(domicilio_section)
    if colonia_extraida:
        data['colonia'] = colonia_extraida
        print(f"COLONIA ULTRA SIMPLE: {colonia_extraida}")
    else:
        print("ULTRA SIMPLE: No se pudo extraer colonia")
    
    # Extraer otros campos de domicilio
    for field, pattern_list in patterns_domicilio.items():
        for i, pattern in enumerate(pattern_list):
            for search_text in [domicilio_section, text]:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    value = re.sub(r'\s+', ' ', value)
                    
                    # Validaciones básicas
                    if field == 'codigo_postal' and len(value) != 5:
                        continue
                    if field in ['numero_exterior', 'numero_interior'] and len(value) > 8:
                        continue
                    if field in ['calle'] and len(value) < 3:
                        continue
                    
                    if value and len(value) > 1:
                        data[field] = value
                        print(f"EXTRAÍDO {field}: {value}")
                        break
            if field in data:
                break
    
    # === POST-PROCESAMIENTO MÍNIMO ===
    print("\n=== POST-PROCESAMIENTO MÍNIMO ===")
    
    # Limpiar calle
    if 'calle' in data:
        data['calle'] = limpiar_calle(data['calle'])
        if not data['calle'] or len(data['calle']) < 3:
            del data['calle']
    
    # Limpiar municipio
    if 'municipio' in data:
        municipio = data['municipio']
        municipio = re.sub(r'^(MUNICIPIO|DELEGACION)\s+', '', municipio, flags=re.IGNORECASE)
        municipio = re.sub(r'\s+(ESTADO|EDO|ZACATECAS|ZAC).*$', '', municipio, flags=re.IGNORECASE)
        municipio = re.sub(r'[^A-ZÁÉÍÓÚÑa-záéíóúñ\s]', ' ', municipio)
        municipio = ' '.join(word.capitalize() for word in municipio.split() if word.strip())
        
        if len(municipio) >= 3:
            data['municipio'] = municipio
            print(f"municipio limpio: {municipio}")
        else:
            del data['municipio']
    
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
            print(f"CURP válido: {curp}, Género: {data.get('sexo', 'No detectado')}")
        else:
            del data['curp']
    
    # Validar clave de elector
    if 'clave_elector' in data:
        clave = re.sub(r'[^A-Z0-9]', '', data['clave_elector'].upper())
        if len(clave) >= 15 and len(clave) <= 20:
            data['clave_elector'] = clave
            print(f"Clave elector válida: {clave}")
        else:
            del data['clave_elector']
    
    # Validar código postal
    if 'codigo_postal' in data:
        cp = re.sub(r'[^0-9]', '', data['codigo_postal'])
        if len(cp) == 5:
            data['codigo_postal'] = cp
            print(f"CP válido: {cp}")
        else:
            del data['codigo_postal']
    
    print(f"\n=== RESUMEN FINAL ULTRA SIMPLE ===")
    print(f"Total campos extraídos: {len(data)}")
    
    for key, value in data.items():
        tipo = "DOMICILIO" if key in ['calle', 'numero_exterior', 'numero_interior', 'colonia', 'codigo_postal', 'municipio'] else "PERSONAL"
        print(f"   {tipo} {key}: {value}")
    
    return data

# ===============================================
# ENDPOINTS SEGUROS
# ===============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check seguro"""
    response = jsonify({
        'status': 'OK',
        'service': 'Sistema de Afiliación PRD Zacatecas',
        'version': '6.0 - Segura',
        'environment': FLASK_ENV,
        'endpoints': ['/api/health', '/api/extract-ine-prd'],
        'security': 'Environment variables configured'
    })
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.route('/api/extract-ine-prd', methods=['POST', 'OPTIONS'])
def extract_ine_for_prd():
    """Endpoint principal para PRD con algoritmo ultra simple - VERSIÓN SEGURA"""
    
    # Manejar OPTIONS
    if request.method == 'OPTIONS':
        print("Petición OPTIONS recibida")
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    print("=== ANÁLISIS INE PRD SEGURO v6.0 ===")
    
    try:
        # Verificar imagen con validaciones de seguridad
        if 'imagen' not in request.files:
            print("SEGURIDAD: No se recibió imagen")
            error_response = jsonify({'success': False, 'error': 'No se recibió imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        file = request.files['imagen']
        if file.filename == '':
            print("SEGURIDAD: Archivo vacío")
            error_response = jsonify({'success': False, 'error': 'Archivo vacío'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        # Validación de tipo de archivo
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_extensions:
            print(f"SEGURIDAD: Tipo de archivo no permitido: {file_ext}")
            error_response = jsonify({'success': False, 'error': f'Tipo de archivo no permitido: {file_ext}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400

        print(f"Imagen recibida: {file.filename} ({file_ext})")
        
        # Leer imagen con límite de tamaño
        image_data = file.read()
        max_size = 15 * 1024 * 1024  # 15MB
        
        if len(image_data) > max_size:
            print(f"SEGURIDAD: Imagen demasiado grande: {len(image_data)} bytes")
            error_response = jsonify({'success': False, 'error': 'Imagen demasiado grande (máximo 15MB)'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        print(f"Tamaño imagen: {len(image_data)} bytes")
        
        # Convertir a OpenCV con validación
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Imagen corrupta o formato inválido")
            
            # Validar dimensiones mínimas
            height, width = image.shape[:2]
            if width < 100 or height < 100:
                raise ValueError("Imagen demasiado pequeña (mínimo 100x100)")
                
        except Exception as e:
            print(f"SEGURIDAD: Error procesando imagen: {e}")
            error_response = jsonify({'success': False, 'error': f'Error procesando imagen: {str(e)}'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 400
        
        # Mejorar imagen
        enhanced_image = enhance_image_for_ocr(image)
        
        # Convertir a bytes para Vision API
        success, enhanced_buffer = cv2.imencode('.png', enhanced_image)
        if not success:
            error_response = jsonify({'success': False, 'error': 'Error al procesar imagen'})
            error_response.headers.add('Access-Control-Allow-Origin', '*')
            return error_response, 500
        
        enhanced_image_data = enhanced_buffer.tobytes()
        
        # Analizar con Vision API
        vision_result = analyze_with_vision_api(enhanced_image_data)
        
        if not vision_result['success']:
            # Intentar con imagen original
            print("Reintentando con imagen original...")
            vision_result = analyze_with_vision_api(image_data)
            
            if not vision_result['success']:
                error_response = jsonify({'success': False, 'error': vision_result['error']})
                error_response.headers.add('Access-Control-Allow-Origin', '*')
                return error_response, 500
        
        print(f"Texto extraído: {len(vision_result['text'])} caracteres")
        
        # Extraer datos PRD con ALGORITMO ULTRA SIMPLE
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
        
        # Formatear respuesta final
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
                
                # Datos de domicilio con ULTRA SIMPLE
                'municipio': extracted_data.get('municipio', 'NO DETECTADO'),
                'calle': extracted_data.get('calle', 'NO DETECTADO'),
                'numero_exterior': extracted_data.get('numero_exterior', 'NO DETECTADO'),
                'numero_interior': extracted_data.get('numero_interior', 'NO DETECTADO'),
                'colonia': extracted_data.get('colonia', 'NO DETECTADO'),
                'codigo_postal': extracted_data.get('codigo_postal', 'NO DETECTADO'),
                
                # Metadatos
                'metodo_usado': 'Google Vision API + Ultra Simple v6.0 SEGURA',
                'calidad_extraccion': 'EXCELENTE' if len(extracted_data) >= 10 else 'BUENA' if len(extracted_data) >= 6 else 'REGULAR'
            },
            'validaciones': {
                'curp_valida': 'curp' in extracted_data and len(extracted_data.get('curp', '')) == 18,
                'clave_elector_valida': 'clave_elector' in extracted_data and len(extracted_data.get('clave_elector', '')) >= 15,
                'nombres_detectados': 'nombres' in extracted_data,
                'apellidos_detectados': 'primer_apellido' in extracted_data,
                'domicilio_detectado': any(k in extracted_data for k in ['calle', 'colonia', 'codigo_postal', 'municipio']),
                'domicilio_completo': all(k in extracted_data for k in ['calle', 'colonia', 'municipio', 'codigo_postal']),
                'colonia_ultra_simple': 'colonia' in extracted_data
            },
            'campos_detectados': list(extracted_data.keys()),
            'debug_info': {
                'texto_length': len(vision_result['text']),
                'campos_domicilio': [k for k in extracted_data.keys() if k in ['calle', 'numero_exterior', 'numero_interior', 'colonia', 'codigo_postal', 'municipio']],
                'version': '6.0 - Segura',
                'environment': FLASK_ENV
            }
        }
        
        print(f"RESULTADOS FINALES PRD SEGURO:")
        for key, value in extracted_data.items():
            tipo = "DOMICILIO" if key in ['calle', 'numero_exterior', 'numero_interior', 'colonia', 'codigo_postal', 'municipio'] else "PERSONAL"
            print(f"   {tipo} {key}: {value}")
        
        # Crear respuesta con CORS
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        print("=== ANÁLISIS SEGURO COMPLETADO ===")
        return response
        
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    print("="*60)
    print("SISTEMA PRD ZACATECAS - VERSIÓN SEGURA v6.0")
    print("="*60)
    print("Endpoints disponibles:")
    print("   - /api/health")
    print("   - /api/extract-ine-prd")
    print("Características de seguridad:")
    print("   - Variables de entorno configuradas")
    print("   - Validación de tipos de archivo")
    print("   - Límites de tamaño de imagen")
    print("   - Timeouts de seguridad")
    print("   - Manejo robusto de errores")
    print(f"Servidor corriendo en: http://{FLASK_HOST}:{FLASK_PORT}")
    print("="*60)
    
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)