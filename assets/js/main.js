// ===============================================
// MAIN.JS - SISTEMA PRD ZACATECAS
// ===============================================

// Funcionalidad del menú lateral
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const menuBtn = document.getElementById('menuBtn');
    
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
    if (menuBtn) menuBtn.classList.toggle('active');
}

// Clase para detección y validación de datos PRD
class PRDDetector {
    constructor() {
        this.datosExtraidos = null;
    }

    // Cargar datos extraídos desde variable global
    loadExtractedData() {
        try {
            if (window.prdDatosExtraidos) {
                console.log('Datos cargados desde variable global');
                return window.prdDatosExtraidos;
            }
        } catch (error) {
            console.error('Error cargando datos:', error);
            if (window.prdDatosExtraidos) {
                return window.prdDatosExtraidos;
            }
        }
        return null;
    }

    // Validar CURP
    validateCURP(curp) {
        const curpRegex = /^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$/;
        return curpRegex.test(curp);
    }

    // Validar clave de elector
    validateClaveElector(clave) {
        const claveRegex = /^[A-Z]{6}[0-9]{8}[HM][0-9]{3}$/;
        return claveRegex.test(clave);
    }

    // Procesar datos extraídos
    procesarDatos(datos) {
        if (!datos) return null;
        
        const datosProcesados = {
            curp: datos.curp || '',
            claveElector: datos.clave_elector || '',
            nombres: datos.nombres || '',
            primerApellido: datos.primer_apellido || '',
            segundoApellido: datos.segundo_apellido || '',
            municipio: datos.municipio || '',
            calle: datos.calle || '',
            colonia: datos.colonia || '',
            codigoPostal: datos.codigo_postal || '',
            numeroExterior: datos.numero_exterior || '',
            sexo: datos.sexo || ''
        };

        return datosProcesados;
    }
}

// Inicialización de eventos del DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando Sistema PRD Zacatecas');

    // Inicializar menú lateral
    const menuBtn = document.getElementById('menuBtn');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', toggleSidebar);
    }
    
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }

    // Cerrar sidebar con tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('sidebar');
            if (sidebar && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        }
    });

    // Inicializar detector PRD
    window.prdDetector = new PRDDetector();

    // Configurar validaciones en tiempo real si estamos en el formulario
    if (document.getElementById('affiliationForm')) {
        setupRealTimeValidations();
    }

    console.log('✅ Sistema PRD inicializado correctamente');
});

// === FUNCIONES DE VALIDACIÓN ===

const validators = {
    validateName: (value) => {
        const nameRegex = /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s]{2,50}$/;
        if (!value.trim()) return 'Este campo es obligatorio';
        if (!nameRegex.test(value)) return 'Solo se permiten letras y espacios (2-50 caracteres)';
        return null;
    },
    validateCURP: (value) => {
        const curpRegex = /^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$/;
        if (!value.trim()) return 'La CURP es obligatoria';
        if (value.length !== 18) return 'La CURP debe tener exactamente 18 caracteres';
        const upperValue = value.toUpperCase();
        if (!curpRegex.test(upperValue)) return 'Formato de CURP inválido';
        return null;
    },
    validateClaveElector: (value) => {
        const claveRegex = /^[A-Z]{6}[0-9]{8}[HM][0-9]{3}$/;
        if (!value.trim()) return 'La clave de elector es obligatoria';
        if (value.length !== 18) return 'La clave de elector debe tener exactamente 18 caracteres';
        const upperValue = value.toUpperCase();
        if (!claveRegex.test(upperValue)) return 'Formato de clave de elector inválido';
        return null;
    },
    validateEmail: (value) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!value.trim()) return 'El correo electrónico es obligatorio';
        if (!emailRegex.test(value)) return 'Formato de correo electrónico inválido';
        return null;
    },
    validatePhone: (value) => {
        const phoneRegex = /^[0-9]{10}$/;
        if (!value.trim()) return 'El número de teléfono es obligatorio';
        if (!phoneRegex.test(value)) return 'El teléfono debe tener exactamente 10 dígitos';
        return null;
    },
    validatePlace: (value) => {
        const placeRegex = /^[a-zA-ZÀ-ÿ\u00f1\u00d1\s,.-]{5,100}$/;
        if (!value.trim()) return 'El lugar de nacimiento es obligatorio';
        if (!placeRegex.test(value)) return 'Formato de lugar inválido (5-100 caracteres)';
        return null;
    },
    validateRequired: (value) => {
        if (!value.trim()) return 'Este campo es obligatorio';
        return null;
    }
};

// Función para mostrar estado de validación
function showValidationState(fieldId, isValid, errorMessage = '') {
    const field = document.getElementById(fieldId);
    const icon = document.getElementById(fieldId + '-icon');
    const errorDiv = document.getElementById(fieldId + '-error');

    if (!field) return;

    field.classList.remove('is-valid', 'is-invalid');
    
    if (isValid) {
        field.classList.add('is-valid');
        if (icon) icon.style.color = '#28a745';
        if (errorDiv) errorDiv.classList.remove('show');
    } else {
        field.classList.add('is-invalid');
        if (icon) icon.style.color = '#dc3545';
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
            errorDiv.classList.add('show');
        }
    }
}

// Función para validar un campo individual
function validateField(fieldId, validator) {
    const field = document.getElementById(fieldId);
    if (!field) return true;
    
    const value = field.value;
    const error = validator(value);
    
    showValidationState(fieldId, !error, error);
    return !error;
}

// Configurar validaciones en tiempo real
function setupRealTimeValidations() {
    const personalFields = [
        ['afiliador', validators.validateRequired],
        ['nombres', validators.validateName],
        ['primerApellido', validators.validateName],
        ['lugarNacimiento', validators.validatePlace],
        ['curp', validators.validateCURP],
        ['claveElector', validators.validateClaveElector],
        ['email', validators.validateEmail],
        ['telefono', validators.validatePhone],
        ['llegadaPRD', validators.validateRequired]
    ];

    personalFields.forEach(([fieldId, validator]) => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', () => {
                validateField(fieldId, validator);
            });
        }
    });

    // Segundo apellido (opcional)
    const segundoApellido = document.getElementById('segundoApellido');
    if (segundoApellido) {
        segundoApellido.addEventListener('blur', () => {
            const value = segundoApellido.value;
            if (value.trim()) {
                validateField('segundoApellido', validators.validateName);
            } else {
                showValidationState('segundoApellido', true);
            }
        });
    }

    // CURP y Clave de elector en mayúsculas
    ['curp', 'claveElector'].forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase();
            });
        }
    });

    // Teléfono y código postal solo números
    ['telefono', 'codigoPostal'].forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
            });
        }
    });

    // Validación en tiempo real para campos de domicilio
    const addressFields = ['municipio', 'colonia', 'codigoPostal', 'calle'];
    addressFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        }
    });
}

// === FUNCIONES DE ESCANEO INE ===

// Función para escanear INE - PRD Zacatecas
function scanINE() {
    console.log("🔍 Iniciando escaneo de INE...");
    
    const input = document.createElement('input');
    input.type = 'file';    
    input.accept = 'image/*';
    input.style.display = 'none';
    
    input.onchange = async function(event) {
        const file = event.target.files[0];
        if (!file) {
            alert('❌ No se seleccionó ninguna imagen');
            return;
        }
        
        console.log(`📎 Archivo seleccionado: ${file.name}`);
        
        const loadingBtn = document.querySelector('.ine-btn');
        const originalText = loadingBtn.textContent;
        loadingBtn.textContent = '🔄 Procesando imagen...';
        loadingBtn.disabled = true;
        
        try {
            const formData = new FormData();
            formData.append('imagen', file);
            
            console.log('📤 Enviando imagen al servidor Railway...');
            
            const BACKEND_URL = 'https://prd-afiliacion-production.up.railway.app/api/extract-ine-prd';
            
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData
            });
            
            console.log(`📊 Respuesta del servidor: ${response.status}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ Datos recibidos:', result);
            
            if (result.success) {
                fillFormWithINEData(result.datos_prd);
                
                const camposDetectados = result.debug_info.campos_detectados.length;
                const calidad = result.datos_prd.calidad_extraccion;
                
                alert(`🎉 ¡INE escaneada exitosamente!

📊 Resumen:
• Campos detectados: ${camposDetectados}
• Calidad: ${calidad}

✅ Los campos se han llenado automáticamente.`);
            } else {
                throw new Error(result.error || 'Error desconocido');
            }
            
        } catch (error) {
            console.error('💥 Error:', error);
            
            let errorMessage = '❌ Error al procesar la imagen';
            
            if (error.message.includes('Failed to fetch')) {
                errorMessage = `🔗 No se pudo conectar al servidor Railway.

🔧 Verifica: https://prd-afiliacion-production.up.railway.app/health`;
            } else if (error.message.includes('404')) {
                errorMessage = `📍 Endpoint no encontrado (404).`;
            } else if (error.message.includes('500')) {
                errorMessage = `⚙️ Error interno del servidor (500).`;
            } else if (error.message.includes('API Key no configurada')) {
                errorMessage = `🔑 Google Vision API Key no configurada.`;
            } else {
                errorMessage = `❌ Error: ${error.message}`;
            }
            
            alert(errorMessage);
            
        } finally {
            loadingBtn.textContent = originalText;
            loadingBtn.disabled = false;
        }
    };
    
    input.click();
}

// Función para llenar el formulario con los datos extraídos
function fillFormWithINEData(datos) {
    console.log('📝 Llenando formulario con datos:', datos);
    
    const fieldMapping = {
        'nombres': 'nombres',
        'primer_apellido': 'primerApellido', 
        'segundo_apellido': 'segundoApellido',
        'curp': 'curp',
        'clave_elector': 'claveElector',
        'municipio': 'municipio',
        'calle': 'calle',
        'numero_exterior': 'numeroExterior',
        'colonia': 'colonia',
        'codigo_postal': 'codigoPostal',
        'sexo': 'gender'
    };
    
    let camposLlenados = 0;
    
    for (const [dataKey, fieldId] of Object.entries(fieldMapping)) {
        if (datos[dataKey] && datos[dataKey] !== 'NO DETECTADO') {
            const field = document.getElementById(fieldId);
            
            if (field) {
                if (fieldId === 'gender') {
                    const genderValue = datos[dataKey] === 'masculino' ? 'masculino' : 
                                       datos[dataKey] === 'femenino' ? 'femenino' : null;
                    
                    if (genderValue) {
                        const radio = document.querySelector(`input[name="gender"][value="${genderValue}"]`);
                        if (radio) {
                            radio.checked = true;
                            camposLlenados++;
                        }
                    }
                } else {
                    field.value = datos[dataKey];
                    field.dispatchEvent(new Event('blur'));
                    camposLlenados++;
                }
                
                console.log(`✅ ${fieldId}: ${datos[dataKey]}`);
            }
        }
    }
    
    const estadoField = document.getElementById('estado');
    if (estadoField) {
        estadoField.value = 'Zacatecas';
    }
    
    console.log(`📊 Campos llenados automáticamente: ${camposLlenados}/${Object.keys(fieldMapping).length}`);
    
    setTimeout(() => {
        alert(`📋 Campos llenados automáticamente: ${camposLlenados}

📝 Por favor verifica y completa:
• Lugar de nacimiento
• Correo electrónico  
• Teléfono
• Responsable de afiliación
• ¿Cómo llegas al PRD?`);
    }, 1000);
}

// === FUNCIONES DE NAVEGACIÓN ===

// Validar formulario completo
function validateForm() {
    let isValid = true;
    
    const personalValidations = [
        ['afiliador', validators.validateRequired],
        ['nombres', validators.validateName],
        ['primerApellido', validators.validateName],
        ['lugarNacimiento', validators.validatePlace],
        ['curp', validators.validateCURP],
        ['claveElector', validators.validateClaveElector],
        ['email', validators.validateEmail],
        ['telefono', validators.validatePhone],
        ['llegadaPRD', validators.validateRequired]
    ];

    personalValidations.forEach(([fieldId, validator]) => {
        if (!validateField(fieldId, validator)) {
            isValid = false;
        }
    });

    // Validar segundo apellido si tiene valor
    const segundoApellido = document.getElementById('segundoApellido');
    if (segundoApellido && segundoApellido.value.trim()) {
        if (!validateField('segundoApellido', validators.validateName)) {
            isValid = false;
        }
    }

    // Validar género
    const genderRadios = document.querySelectorAll('input[name="gender"]');
    const genderSelected = Array.from(genderRadios).some(radio => radio.checked);
    const genderError = document.getElementById('gender-error');
    
    if (!genderSelected) {
        if (genderError) {
            genderError.textContent = 'Debes seleccionar un género';
            genderError.classList.add('show');
        }
        isValid = false;
    } else {
        if (genderError) genderError.classList.remove('show');
    }

    // Validar campos de domicilio
    const requiredAddressFields = ['municipio', 'colonia', 'codigoPostal', 'calle'];
    requiredAddressFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('is-invalid');
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        }
    });

    return isValid;
}

// Función para el siguiente paso
function nextStep() {
    if (validateForm()) {
        const formData = {
            afiliador: document.getElementById('afiliador').value,
            nombres: document.getElementById('nombres').value,
            primerApellido: document.getElementById('primerApellido').value,
            segundoApellido: document.getElementById('segundoApellido').value,
            lugarNacimiento: document.getElementById('lugarNacimiento').value,
            curp: document.getElementById('curp').value,
            claveElector: document.getElementById('claveElector').value,
            email: document.getElementById('email').value,
            telefono: document.getElementById('telefono').value,
            gender: document.querySelector('input[name="gender"]:checked')?.value,
            llegadaPRD: document.getElementById('llegadaPRD').value,
            estado: document.getElementById('estado').value,
            municipio: document.getElementById('municipio').value,
            colonia: document.getElementById('colonia').value,
            codigoPostal: document.getElementById('codigoPostal').value,
            calle: document.getElementById('calle').value,
            numeroExterior: document.getElementById('numeroExterior').value,
            numeroInterior: document.getElementById('numeroInterior').value
        };
        
        console.log('Datos del formulario:', formData);
        alert('✅ Formulario válido! Procediendo al siguiente paso...');
        window.location.href = "paso 2.html";
    } else {
        alert('❌ Por favor corrige los errores marcados en el formulario.');
        
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
    }
}

// === UTILIDADES ===

// Función para formatear números de teléfono
function formatPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    }
    return phone;
}

// Función para limpiar y formatear CURP
function formatCURP(curp) {
    return curp.toUpperCase().replace(/[^A-Z0-9]/g, '');
}

// Función para limpiar y formatear clave de elector
function formatClaveElector(clave) {
    return clave.toUpperCase().replace(/[^A-Z0-9]/g, '');
}

// Debug - Información del sistema
console.log('🏛️ Sistema PRD Zacatecas v2.0');
console.log('📅 Cargado:', new Date().toLocaleString());
console.log('🌐 URL:', window.location.href);
console.log('📱 UserAgent:', navigator.userAgent);