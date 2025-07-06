// main.js - Sistema PRD Zacatecas VERSIÓN SIN EMOJIS v4.0
console.log("CARGANDO main.js VERSIÓN SIN EMOJIS v4.0 para PRD...");

// FUNCIONES ORIGINALES DEL MENÚ (mantener funcionando)
var menuBtn = document.getElementById('menuBtn');
var sidebar = document.getElementById('sidebar');
var sidebarOverlay = document.getElementById('sidebarOverlay');

function toggleSidebar() {
    if (!sidebar) return;
    const isOpen = sidebar.classList.contains('active');
    if (menuBtn) menuBtn.classList.toggle('active', !isOpen);
    sidebar.classList.toggle('active', !isOpen);
    if (sidebarOverlay) sidebarOverlay.classList.toggle('active', !isOpen);
    document.body.style.overflow = isOpen ? '' : 'hidden';
}

if (menuBtn) menuBtn.addEventListener('click', toggleSidebar);
if (sidebarOverlay) sidebarOverlay.addEventListener('click', toggleSidebar);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('active')) {
        toggleSidebar();
    }
});

// DICCIONARIO DE ESTADOS MEXICANOS PARA CURP
var ESTADOS_CURP = {
    'AS': 'Aguascalientes', 'BC': 'Baja California', 'BS': 'Baja California Sur',
    'CC': 'Campeche', 'CL': 'Coahuila', 'CM': 'Colima', 'CS': 'Chiapas',
    'CH': 'Chihuahua', 'DF': 'Ciudad de México', 'DG': 'Durango',
    'GT': 'Guanajuato', 'GR': 'Guerrero', 'HG': 'Hidalgo', 'JC': 'Jalisco',
    'MC': 'Estado de México', 'MN': 'Michoacán', 'MS': 'Morelos',
    'NT': 'Nayarit', 'NL': 'Nuevo León', 'OC': 'Oaxaca', 'PL': 'Puebla',
    'QT': 'Querétaro', 'QR': 'Quintana Roo', 'SP': 'San Luis Potosí',
    'SL': 'Sinaloa', 'SR': 'Sonora', 'TC': 'Tabasco', 'TS': 'Tamaulipas',
    'TL': 'Tlaxcala', 'VZ': 'Veracruz', 'YN': 'Yucatán', 'ZS': 'Zacatecas',
    'NE': 'Nacido en el extranjero'
};

// MUNICIPIOS DE ZACATECAS CON SINÓNIMOS Y VARIACIONES
var MUNICIPIOS_ZACATECAS = {
    'Apozol': ['Apozol'],
    'Apulco': ['Apulco'],
    'Atolinga': ['Atolinga'],
    'Benito Juárez': ['Benito Juárez', 'Benito Juarez'],
    'Calera': ['Calera', 'Calera de Víctor Rosales', 'Calera de Victor Rosales'],
    'Cañitas de Felipe Pescador': ['Cañitas de Felipe Pescador', 'Canitas de Felipe Pescador', 'Cañitas'],
    'Concepción del Oro': ['Concepción del Oro', 'Concepcion del Oro'],
    'Cuauhtémoc': ['Cuauhtémoc', 'Cuauhtemoc'],
    'Chalchihuites': ['Chalchihuites'],
    'Fresnillo': ['Fresnillo'],
    'Trinidad García de la Cadena': ['Trinidad García de la Cadena', 'Trinidad Garcia de la Cadena', 'Trinidad García'],
    'Genaro Codina': ['Genaro Codina'],
    'General Enrique Estrada': ['General Enrique Estrada', 'Enrique Estrada'],
    'General Francisco R. Murguía': ['General Francisco R. Murguía', 'Francisco Murguía', 'Murguía'],
    'El Plateado de Joaquín Amaro': ['El Plateado de Joaquín Amaro', 'El Plateado'],
    'General Pánfilo Natera': ['General Pánfilo Natera', 'Pánfilo Natera'],
    'Guadalupe': ['Guadalupe'],
    'Huanusco': ['Huanusco'],
    'Jalpa': ['Jalpa'],
    'Jerez': ['Jerez', 'Jerez de García Salinas'],
    'Jiménez del Teul': ['Jiménez del Teul', 'Jimenez del Teul'],
    'Juan Aldama': ['Juan Aldama'],
    'Juchipila': ['Juchipila'],
    'Loreto': ['Loreto'],
    'Luis Moya': ['Luis Moya'],
    'Mazapil': ['Mazapil'],
    'Melchor Ocampo': ['Melchor Ocampo'],
    'Mezquital del Oro': ['Mezquital del Oro'],
    'Miguel Auza': ['Miguel Auza'],
    'Momax': ['Momax'],
    'Monte Escobedo': ['Monte Escobedo'],
    'Morelos': ['Morelos'],
    'Moyahua de Estrada': ['Moyahua de Estrada', 'Moyahua'],
    'Nochistlán de Mejía': ['Nochistlán de Mejía', 'Nochistlan de Mejia', 'Nochistlán'],
    'Noria de Ángeles': ['Noria de Ángeles', 'Noria de Angeles'],
    'Ojocaliente': ['Ojocaliente'],
    'Pánuco': ['Pánuco', 'Panuco'],
    'Pinos': ['Pinos'],
    'Río Grande': ['Río Grande', 'Rio Grande'],
    'Saín Alto': ['Saín Alto', 'Sain Alto'],
    'El Salvador': ['El Salvador'],
    'Santa María de la Paz': ['Santa María de la Paz', 'Santa Maria de la Paz'],
    'Sombrerete': ['Sombrerete'],
    'Susticacán': ['Susticacán', 'Susticacan'],
    'Tabasco': ['Tabasco'],
    'Tepechitlán': ['Tepechitlán', 'Tepechitlan'],
    'Tepetongo': ['Tepetongo'],
    'Teúl de González Ortega': ['Teúl de González Ortega', 'Teul de Gonzalez Ortega', 'Teúl'],
    'Tlaltenango de Sánchez Román': ['Tlaltenango de Sánchez Román', 'Tlaltenango de Sanchez Roman', 'Tlaltenango'],
    'Valparaíso': ['Valparaíso', 'Valparaiso'],
    'Vetagrande': ['Vetagrande'],
    'Villa de Cos': ['Villa de Cos'],
    'Villa García': ['Villa García', 'Villa Garcia'],
    'Villa González Ortega': ['Villa González Ortega', 'Villa Gonzalez Ortega'],
    'Villa Hidalgo': ['Villa Hidalgo'],
    'Villanueva': ['Villanueva'],
    'Zacatecas': ['Zacatecas']
};

// CLASE PRD DETECTOR SIN EMOJIS
class PRDDetector {
    constructor() {
        this.backendUrl = 'prd-afiliacion-production.up.railway.app';
        this.selectedFile = null;
        this.extractedData = null;
        this.currentStep = this.detectCurrentStep();
        console.log('PRDDetector SIN EMOJIS v4.0 inicializado - Paso actual: ' + this.currentStep);
    }

    // DETECTAR EN QUÉ PASO ESTAMOS
    detectCurrentStep() {
        const url = window.location.pathname;
        if (url.includes('paso 1') || url.includes('paso1')) return 1;
        if (url.includes('paso 2') || url.includes('paso2')) return 2;
        if (url.includes('paso 3') || url.includes('paso3')) return 3;
        return 1;
    }

    // GUARDAR DATOS EXTRAÍDOS
    saveExtractedData(data) {
        try {
            if (typeof Storage !== "undefined" && localStorage) {
                localStorage.setItem('prd_datos_extraidos', JSON.stringify(data));
                localStorage.setItem('prd_timestamp', new Date().getTime().toString());
                console.log('Datos guardados en localStorage');
            } else {
                window.prdDatosExtraidos = data;
                console.log('Datos guardados en variable global (fallback)');
            }
        } catch (error) {
            window.prdDatosExtraidos = data;
            console.log('Datos guardados en variable global (localStorage falló):', error);
        }
    }

    // CARGAR DATOS EXTRAÍDOS
    loadExtractedData() {
        try {
            if (typeof Storage !== "undefined" && localStorage) {
                const data = localStorage.getItem('prd_datos_extraidos');
                const timestamp = localStorage.getItem('prd_timestamp');
                
                // Verificar que los datos no sean muy viejos (1 hora)
                if (data && timestamp) {
                    const now = new Date().getTime();
                    const dataTime = parseInt(timestamp);
                    if (now - dataTime < 3600000) { // 1 hora
                        return JSON.parse(data);
                    }
                }
            }
            
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

    // FUNCIÓN PRINCIPAL DE ESCANEO
    async scanINE() {
        console.log('scanINE() ejecutado - versión SIN EMOJIS v4.0');
        
        // Verificar conexión primero
        try {
            console.log('Verificando conexión con backend...');
            var healthResponse = await fetch(this.backendUrl + '/api/health');
            if (!healthResponse.ok) {
                throw new Error('Backend no disponible: ' + healthResponse.status);
            }
            var healthData = await healthResponse.json();
            console.log('Backend conectado:', healthData.service, healthData.version);
        } catch (error) {
            console.error('Error de conexión:', error);
            alert('No se puede conectar al servidor:\n\n' + error.message + '\n\n¿Está corriendo app.py en el puerto 5001?');
            return;
        }

        // Crear input de archivo
        var input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.display = 'none';
        document.body.appendChild(input);

        var self = this;
        input.onchange = function(event) {
            var file = event.target.files[0];
            if (file) {
                console.log('Archivo seleccionado:', file.name, '(' + (file.size / 1024 / 1024).toFixed(2) + ' MB)');
                self.selectedFile = file;
                self.analyzeImage();
            }
            document.body.removeChild(input);
        };

        input.click();
    }

    async analyzeImage() {
        if (!this.selectedFile) {
            this.showError('Por favor selecciona una imagen primero');
            return;
        }

        try {
            console.log('Iniciando análisis SIN EMOJIS...');
            this.showLoading(true);
            this.hideError();

            const formData = new FormData();
            formData.append('imagen', this.selectedFile);

            console.log('Enviando imagen al backend PRD v4.0...', {
                fileName: this.selectedFile.name,
                fileSize: this.selectedFile.size,
                endpoint: this.backendUrl + '/api/extract-ine-prd'
            });

            const response = await fetch(this.backendUrl + '/api/extract-ine-prd', {
                method: 'POST',
                body: formData
            });

            console.log('Respuesta del servidor PRD:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error del servidor:', errorText);
                throw new Error('Error ' + response.status + ': ' + errorText);
            }

            const data = await response.json();
            console.log('Datos recibidos del backend v4.0:', data);

            if (data.success && data.datos_prd) {
                console.log('Datos del INE extraídos:', data.datos_prd);
                this.extractedData = data.datos_prd;
                
                // MEJORAR LOS DATOS ANTES DE MOSTRAR
                const datosCompletos = this.completarDatos(data.datos_prd);
                
                // GUARDAR DATOS PARA USAR EN OTROS PASOS
                this.saveExtractedData(datosCompletos);
                
                this.displayResults(datosCompletos, data.validaciones);
                
                // Llenar formulario después de mostrar resultados
                const self = this;
                setTimeout(function() {
                    self.fillCurrentStep(datosCompletos);
                }, 2000);
                
            } else {
                console.warn('No se encontraron datos en la respuesta:', data);
                throw new Error(data.error || 'No se pudieron extraer datos del INE de la imagen');
            }

        } catch (error) {
            console.error('Error completo:', error);
            this.showError('Error al analizar la imagen: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    // COMPLETAR Y MEJORAR DATOS
    completarDatos(datos) {
        console.log('Completando datos extraídos...');
        var datosCompletos = Object.assign({}, datos);

        // 1. SEPARAR NOMBRES Y APELLIDOS CORRECTAMENTE
        if (datos.nombre_completo && datos.nombre_completo !== "NO DETECTADO") {
            var partes = datos.nombre_completo.split(' ').filter(function(p) { return p.length > 0; });
            
            if (partes.length >= 3) {
                datosCompletos.primer_apellido = partes[0];
                datosCompletos.segundo_apellido = partes[1];
                datosCompletos.nombres = partes.slice(2).join(' ');
            } else if (partes.length === 2) {
                datosCompletos.primer_apellido = partes[0];
                datosCompletos.nombres = partes[1];
            }
        }

        // 2. EXTRAER LUGAR DE NACIMIENTO DE LA CURP
        if (datos.curp && datos.curp.length >= 12) {
            var estadoClave = datos.curp.substring(11, 13);
            var estadoNombre = ESTADOS_CURP[estadoClave];
            if (estadoNombre) {
                datosCompletos.lugar_nacimiento = estadoNombre;
                console.log('Lugar de nacimiento extraído de CURP:', estadoNombre);
            }
        }

        // 3. EXTRAER FECHA DE NACIMIENTO DE LA CURP
        if (datos.curp && datos.curp.length >= 10) {
            try {
                var year = parseInt(datos.curp.substring(4, 6));
                var month = datos.curp.substring(6, 8);
                var day = datos.curp.substring(8, 10);
                
                var fullYear = year <= 30 ? 2000 + year : 1900 + year;
                
                datosCompletos.fecha_nacimiento = day + '/' + month + '/' + fullYear;
                console.log('Fecha de nacimiento extraída de CURP:', datosCompletos.fecha_nacimiento);
            } catch (error) {
                console.log('No se pudo extraer fecha de CURP');
            }
        }

        // 4. NORMALIZAR GÉNERO
        if (datos.sexo) {
            if (datos.sexo.toLowerCase().includes('masculino') || datos.sexo === 'H') {
                datosCompletos.sexo = 'masculino';
            } else if (datos.sexo.toLowerCase().includes('femenino') || datos.sexo === 'M') {
                datosCompletos.sexo = 'femenino';
            }
        }

        // 5. MAPEAR MUNICIPIO DE ZACATECAS
        if (datos.municipio && datos.municipio !== "NO DETECTADO") {
            var municipioDetectado = datos.municipio.toLowerCase().trim();
            var municipioEncontrado = null;
            
            // Buscar coincidencia exacta en cualquier variación
            for (var municipioOficial in MUNICIPIOS_ZACATECAS) {
                var variaciones = MUNICIPIOS_ZACATECAS[municipioOficial];
                for (var i = 0; i < variaciones.length; i++) {
                    if (variaciones[i].toLowerCase() === municipioDetectado) {
                        municipioEncontrado = municipioOficial;
                        break;
                    }
                }
                if (municipioEncontrado) break;
            }
            
            // Si no hay exacta, buscar que contenga
            if (!municipioEncontrado) {
                for (var municipioOficial2 in MUNICIPIOS_ZACATECAS) {
                    var variaciones2 = MUNICIPIOS_ZACATECAS[municipioOficial2];
                    for (var j = 0; j < variaciones2.length; j++) {
                        var variacion = variaciones2[j].toLowerCase();
                        if (variacion.includes(municipioDetectado) || municipioDetectado.includes(variacion)) {
                            municipioEncontrado = municipioOficial2;
                            break;
                        }
                    }
                    if (municipioEncontrado) break;
                }
            }
            
            if (municipioEncontrado) {
                datosCompletos.municipio = municipioEncontrado;
                console.log('Municipio mapeado:', municipioDetectado, '->', municipioEncontrado);
            }
        }

        console.log('Datos completados:', datosCompletos);
        return datosCompletos;
    }

    // FUNCIÓN PRINCIPAL DE LLENADO
    fillCurrentStep(datos) {
        console.log('=== LLENADO SIN EMOJIS v4.0 INICIADO ===');
        console.log('Paso actual:', this.currentStep);
        console.log('Datos completos:', datos);
        
        var totalCampos = 0;
        
        if (this.currentStep === 1) {
            console.log('Procesando paso 1...');
            totalCampos += this.fillStep1(datos);
            
            // También llenar domicilio si estamos en paso 1 y los campos existen
            var camposDomicilio = this.fillDomicilio(datos);
            totalCampos += camposDomicilio;
            
        } else if (this.currentStep === 2) {
            console.log('Procesando paso 2...');
            totalCampos += this.fillDomicilio(datos);
        }
        
        // Mensaje final
        if (totalCampos > 0) {
            this.showSuccess(`¡Formulario completado! ${totalCampos} campos llenados automáticamente desde tu INE`);
        } else {
            this.showSuccess('Datos extraídos. Por favor verifica y completa los campos manualmente.');
        }
        
        console.log(`Llenado completado: ${totalCampos} campos`);
    }

    // LLENAR PASO 1
    fillStep1(datos) {
        console.log('=== LLENANDO PASO 1 ===');
        
        var camposLlenados = 0;
        var detector = this;
        
        // Función para llenar campos
        var llenarCampo = function(selector, valor, nombre) {
            if (!valor || valor === "NO DETECTADO" || valor.toString().trim() === "") {
                console.log(`${nombre}: Sin valor válido`);
                return false;
            }
            
            var campo = document.querySelector(selector);
            if (!campo) {
                console.log(`${nombre}: Campo no encontrado - ${selector}`);
                return false;
            }
            
            try {
                // Limpiar y establecer valor
                campo.value = valor.toString().trim();
                
                // Disparar eventos de validación
                ['input', 'change', 'blur'].forEach(function(evento) {
                    campo.dispatchEvent(new Event(evento, { bubbles: true, cancelable: true }));
                });
                
                // Aplicar estilos de validación
                campo.classList.remove('is-invalid');
                campo.classList.add('is-valid');
                
                // Highlight visual
                detector.highlightField(campo, nombre);
                
                console.log(`${nombre} llenado: "${campo.value}"`);
                return true;
            } catch (error) {
                console.error(`Error llenando ${nombre}:`, error);
                return false;
            }
        };
        
        // Campos personales a llenar
        var camposPersonales = [
            ['#nombres', datos.nombres, 'Nombres'],
            ['#primerApellido', datos.primer_apellido, 'Primer Apellido'],
            ['#segundoApellido', datos.segundo_apellido, 'Segundo Apellido'],
            ['#lugarNacimiento', datos.lugar_nacimiento, 'Lugar de Nacimiento'],
            ['#curp', datos.curp, 'CURP'],
            ['#claveElector', datos.clave_elector, 'Clave de Elector']
        ];
        
        camposPersonales.forEach(function(item) {
            if (llenarCampo(item[0], item[1], item[2])) {
                camposLlenados++;
            }
        });
        
        // Llenar género
        if (datos.sexo && datos.sexo !== "NO DETECTADO") {
            var genero = datos.sexo.toLowerCase();
            var radioButtons = document.querySelectorAll('input[type="radio"][name="gender"]');
            var generoLlenado = false;
            
            radioButtons.forEach(function(radio) {
                if (radio.value.toLowerCase() === genero) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                    detector.highlightRadio(radio, 'Género');
                    generoLlenado = true;
                    console.log(`Género seleccionado: ${genero}`);
                }
            });
            
            if (generoLlenado) camposLlenados++;
        }
        
        console.log(`PASO 1 - Campos llenados: ${camposLlenados}`);
        return camposLlenados;
    }

    // FUNCIÓN PARA DOMICILIO
    fillDomicilio(datos) {
        console.log('\n=== LLENADO DE DOMICILIO v4.0 ===');
        console.log('Datos de domicilio recibidos:', {
            calle: datos.calle,
            numero_exterior: datos.numero_exterior,
            numero_interior: datos.numero_interior,
            colonia: datos.colonia,
            codigo_postal: datos.codigo_postal,
            municipio: datos.municipio
        });
        
        var camposLlenados = 0;
        var detector = this;
        
        // Función específica para campos de texto
        var llenarCampoTexto = function(selector, valor, nombre) {
            if (!valor || valor === "NO DETECTADO" || valor.toString().trim() === "") {
                console.log(`${nombre}: Sin valor`);
                return false;
            }
            
            var campo = document.querySelector(selector);
            if (!campo) {
                console.log(`${nombre}: Campo no encontrado - ${selector}`);
                return false;
            }
            
            try {
                // Establecer valor
                campo.value = valor.toString().trim();
                
                // Disparar eventos
                ['input', 'change', 'blur'].forEach(function(evento) {
                    campo.dispatchEvent(new Event(evento, { bubbles: true }));
                });
                
                // Aplicar estilos
                campo.classList.remove('is-invalid');
                campo.classList.add('is-valid');
                
                // Highlight específico para domicilio
                detector.highlightFieldDomicilio(campo, nombre);
                
                console.log(`${nombre} llenado: "${campo.value}"`);
                return true;
            } catch (error) {
                console.error(`Error llenando ${nombre}:`, error);
                return false;
            }
        };
        
        // Función para selects (municipio)
        var llenarSelect = function(selector, valor, nombre) {
            if (!valor || valor === "NO DETECTADO" || valor.toString().trim() === "") {
                console.log(`${nombre}: Sin valor para select`);
                return false;
            }
            
            var select = document.querySelector(selector);
            if (!select) {
                console.log(`${nombre}: Select no encontrado - ${selector}`);
                return false;
            }
            
            var valorBusqueda = valor.toString().toLowerCase().trim();
            var opcionEncontrada = false;
            
            console.log(`Buscando municipio: "${valorBusqueda}"`);
            
            // Buscar opción exacta primero
            Array.from(select.options).forEach(function(opcion) {
                if (!opcionEncontrada && opcion.value && opcion.value.toLowerCase() === valorBusqueda) {
                    select.value = opcion.value;
                    opcionEncontrada = true;
                    console.log(`${nombre} - Coincidencia exacta: ${opcion.value}`);
                }
            });
            
            // Si no hay exacta, buscar parcial
            if (!opcionEncontrada) {
                Array.from(select.options).forEach(function(opcion) {
                    if (!opcionEncontrada && opcion.value) {
                        var opcionTexto = opcion.text.toLowerCase();
                        var opcionValor = opcion.value.toLowerCase();
                        
                        if (opcionTexto.includes(valorBusqueda) || valorBusqueda.includes(opcionTexto) ||
                            opcionValor.includes(valorBusqueda) || valorBusqueda.includes(opcionValor)) {
                            select.value = opcion.value;
                            opcionEncontrada = true;
                            console.log(`${nombre} - Coincidencia parcial: ${opcion.value}`);
                        }
                    }
                });
            }
            
            if (opcionEncontrada) {
                // Disparar eventos
                ['change', 'input', 'blur'].forEach(function(evento) {
                    select.dispatchEvent(new Event(evento, { bubbles: true }));
                });
                
                select.classList.remove('is-invalid');
                select.classList.add('is-valid');
                detector.highlightFieldDomicilio(select, nombre);
                
                return true;
            } else {
                console.log(`${nombre}: No se encontró opción para "${valor}"`);
                return false;
            }
        };
        
        // === MAPEO DE CAMPOS ===
        var mapeoCompleto = [
            // Municipio primero (dropdown)
            ['#municipio', datos.municipio, 'Municipio', 'select'],
            // Luego campos de texto
            ['#colonia', datos.colonia, 'Colonia', 'text'],
            ['#calle', datos.calle, 'Calle', 'text'],
            ['#codigoPostal', datos.codigo_postal, 'Código Postal', 'text'],
            ['#numeroExterior', datos.numero_exterior, 'Número Exterior', 'text'],
            ['#numeroInterior', datos.numero_interior, 'Número Interior', 'text']
        ];
        
        // Procesar cada campo
        mapeoCompleto.forEach(function(item) {
            var selector = item[0];
            var valor = item[1];
            var nombre = item[2];
            var tipo = item[3];
            
            console.log(`\nProcesando ${nombre} (${tipo}): "${valor}"`);
            
            var exito = false;
            
            // Intentar llenar 3 veces con pequeño delay
            for (var intento = 0; intento < 3 && !exito; intento++) {
                if (intento > 0) {
                    console.log(`Reintentando ${nombre} (intento ${intento + 1})`);
                }
                
                if (tipo === 'select') {
                    exito = llenarSelect(selector, valor, nombre);
                } else {
                    exito = llenarCampoTexto(selector, valor, nombre);
                }
                
                if (!exito && intento < 2) {
                    // Pequeño delay antes del siguiente intento
                    setTimeout(function() {}, 100);
                }
            }
            
            if (exito) {
                camposLlenados++;
            }
        });
        
        console.log(`\nDOMICILIO - Total campos llenados: ${camposLlenados}`);
        
        // Validación final con delay
        setTimeout(function() {
            detector.validarFormularioDomicilio();
        }, 1500);
        
        return camposLlenados;
    }

    // FUNCIÓN DE HIGHLIGHT ESPECÍFICA PARA DOMICILIO
    highlightFieldDomicilio(campo, nombre) {
        var estilosOriginales = {
            border: campo.style.border,
            backgroundColor: campo.style.backgroundColor,
            transform: campo.style.transform,
            boxShadow: campo.style.boxShadow
        };

        // Aplicar highlight verde para domicilio
        campo.style.border = '3px solid #28a745';
        campo.style.backgroundColor = '#d4edda';
        campo.style.transform = 'scale(1.03)';
        campo.style.boxShadow = '0 0 15px rgba(40, 167, 69, 0.6)';
        campo.style.transition = 'all 0.5s ease';

        // Scroll suave al campo
        setTimeout(function() {
            campo.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 200);

        // Restaurar estilos después de 6 segundos
        setTimeout(function() {
            Object.assign(campo.style, estilosOriginales);
        }, 6000);
        
        console.log(`${nombre} resaltado en verde`);
    }

    // FUNCIÓN DE VALIDACIÓN
    validarFormularioDomicilio() {
        console.log('Validando formulario de domicilio...');
        
        var camposRequeridos = [
            { selector: '#municipio', nombre: 'Municipio' },
            { selector: '#colonia', nombre: 'Colonia' },
            { selector: '#calle', nombre: 'Calle' },
            { selector: '#codigoPostal', nombre: 'Código Postal' }
        ];
        
        var camposValidos = 0;
        
        camposRequeridos.forEach(function(item) {
            var campo = document.querySelector(item.selector);
            if (campo && campo.value.trim()) {
                campo.classList.add('is-valid');
                campo.classList.remove('is-invalid');
                camposValidos++;
                console.log(`${item.nombre}: válido ("${campo.value}")`);
            } else {
                console.log(`${item.nombre}: vacío o inválido`);
            }
        });
        
        console.log(`Validación final: ${camposValidos}/${camposRequeridos.length} campos válidos`);
        
        if (camposValidos === camposRequeridos.length) {
            this.showSuccess(`¡Domicilio completo! Todos los campos requeridos están llenos`);
        }
    }

    displayResults(datos, validaciones) {
        console.log('Mostrando resultados PRD SIN EMOJIS:', datos);
        this.createResultModal(datos, validaciones);
    }

    createResultModal(datos, validaciones) {
        var existingModal = document.querySelector('.prd-modal-overlay');
        if (existingModal) {
            document.body.removeChild(existingModal);
        }

        var overlay = document.createElement('div');
        overlay.className = 'prd-modal-overlay';
        overlay.style.cssText = 
            'position: fixed; top: 0; left: 0; width: 100%; height: 100%;' +
            'background: rgba(0,0,0,0.85); z-index: 10000;' +
            'display: flex; align-items: center; justify-content: center;' +
            'padding: 20px; box-sizing: border-box;';

        var modal = document.createElement('div');
        modal.style.cssText = 
            'background: white; padding: 30px; border-radius: 15px;' +
            'max-width: 900px; width: 100%; max-height: 90%; overflow-y: auto;' +
            'border: 3px solid #FFD700; box-shadow: 0 10px 30px rgba(0,0,0,0.3);';

        var contenido = 
            '<div style="text-align: center; margin-bottom: 25px;">' +
                '<h2 style="color: #000; margin-bottom: 10px;">Datos Completos de tu INE</h2>' +
                '<div style="color: #666; font-size: 0.9rem;">Sistema PRD Zacatecas v4.0 - Extracción Sin Emojis</div>' +
            '</div>' +
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; font-family: -apple-system, sans-serif;">';

        // Columna 1: Datos Personales
        contenido += 
            '<div>' +
                '<h3 style="color: #000; margin-bottom: 15px; border-bottom: 2px solid #FFD700; padding-bottom: 5px;">' +
                    'Datos Personales' +
                '</h3>';

        var datosPersonales = [
            ['Nombres', datos.nombres],
            ['Primer Apellido', datos.primer_apellido],
            ['Segundo Apellido', datos.segundo_apellido],
            ['Lugar de Nacimiento', datos.lugar_nacimiento],
            ['CURP', datos.curp],
            ['Clave de Elector', datos.clave_elector],
            ['Género', datos.sexo],
            ['Fecha de Nacimiento', datos.fecha_nacimiento]
        ];

        datosPersonales.forEach(function(item) {
            var etiqueta = item[0];
            var valor = item[1];
            if (valor && valor !== "NO DETECTADO") {
                var colorFondo = '#f8f9fa';
                if (['CURP', 'Clave de Elector'].includes(etiqueta)) {
                    colorFondo = '#e8f5e8'; // Verde claro para datos importantes
                }
                
                contenido += 
                    '<div style="margin-bottom: 10px; padding: 8px; background: ' + colorFondo + '; border-radius: 5px;">' +
                        '<strong style="color: #333; font-size: 0.85rem;">' + etiqueta + ':</strong><br>' +
                        '<span style="color: #000; font-weight: 500;">' + valor + '</span>' +
                    '</div>';
            }
        });

        contenido += '</div>';

        // Columna 2: Domicilio
        contenido += 
            '<div>' +
                '<h3 style="color: #000; margin-bottom: 15px; border-bottom: 2px solid #28a745; padding-bottom: 5px;">' +
                    'Domicilio' +
                '</h3>';

        var datosDomicilio = [
            ['Municipio', datos.municipio],
            ['Colonia', datos.colonia],
            ['Calle', datos.calle],
            ['Número Exterior', datos.numero_exterior],
            ['Número Interior', datos.numero_interior],
            ['Código Postal', datos.codigo_postal]
        ];

        var camposDomicilioLlenos = 0;
        datosDomicilio.forEach(function(item) {
            var etiqueta = item[0];
            var valor = item[1];
            if (valor && valor !== "NO DETECTADO") {
                camposDomicilioLlenos++;
                var colorFondo = '#e8f5e8'; // Verde claro para domicilio
                
                contenido += 
                    '<div style="margin-bottom: 10px; padding: 8px; background: ' + colorFondo + '; border-radius: 5px; border-left: 3px solid #28a745;">' +
                        '<strong style="color: #333; font-size: 0.85rem;">' + etiqueta + ':</strong><br>' +
                        '<span style="color: #000; font-weight: 500;">' + valor + '</span>' +
                    '</div>';
            }
        });

        // Mensaje de estado del domicilio
        var estadoDomicilio = '';
        if (camposDomicilioLlenos >= 4) {
            estadoDomicilio = '<div style="color: #28a745; font-weight: bold; text-align: center; margin-top: 10px;">Domicilio Completo</div>';
        } else if (camposDomicilioLlenos >= 2) {
            estadoDomicilio = '<div style="color: #ffc107; font-weight: bold; text-align: center; margin-top: 10px;">Domicilio Parcial</div>';
        } else {
            estadoDomicilio = '<div style="color: #dc3545; font-weight: bold; text-align: center; margin-top: 10px;">Completar Manualmente</div>';
        }
        
        contenido += estadoDomicilio + '</div></div>';

        contenido += 
            '<div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee;">' +
                '<button onclick="window.prdDetector.closeModal()" ' +
                        'style="padding: 15px 30px; background: #FFD700; color: #000; ' +
                               'border: none; border-radius: 8px; cursor: pointer; font-weight: bold;' +
                               'font-size: 1.1rem; transition: all 0.3s ease; margin-right: 10px;">' +
                    'Cerrar y Completar Formulario' +
                '</button>' +
                '<button onclick="window.prdDetector.debugFormFields()" ' +
                        'style="padding: 15px 30px; background: #6c757d; color: white; ' +
                               'border: none; border-radius: 8px; cursor: pointer; font-weight: bold;' +
                               'font-size: 0.9rem; transition: all 0.3s ease;">' +
                    'Debug Campos' +
                '</button>' +
            '</div>';

        modal.innerHTML = contenido;
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        overlay.style.opacity = '0';
        setTimeout(function() {
            overlay.style.transition = 'opacity 0.3s ease';
            overlay.style.opacity = '1';
        }, 10);
    }

    closeModal() {
        var modal = document.querySelector('.prd-modal-overlay');
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(function() {
                if (modal.parentNode) {
                    document.body.removeChild(modal);
                }
            }, 300);
        }
    }

    // FUNCIÓN DE DEBUG MEJORADA
    debugFormFields() {
        console.log('DEBUG: Campos disponibles en el formulario:');
        
        var campos = [
            '#municipio', '#colonia', '#codigoPostal', '#calle', 
            '#numeroExterior', '#numeroInterior', '#estado',
            '#nombres', '#primerApellido', '#segundoApellido'
        ];
        
        console.log('\nVERIFICACIÓN DE CAMPOS:');
        campos.forEach(function(selector) {
            var campo = document.querySelector(selector);
            if (campo) {
                var info = {
                    selector: selector,
                    encontrado: true,
                    tipo: campo.type || campo.tagName,
                    valor: campo.value,
                    clases: campo.className
                };
                console.log('[OK]', selector, ':', info);
            } else {
                console.log('[ERROR]', selector, ': NO encontrado');
            }
        });
        
        // Mostrar todos los inputs del formulario
        var todosInputs = document.querySelectorAll('input, select, textarea');
        console.log('\nTODOS LOS CAMPOS ENCONTRADOS (' + todosInputs.length + '):');
        todosInputs.forEach(function(input, index) {
            var info = input.tagName + (input.id ? '#' + input.id : '') + 
                      (input.name ? '[name="' + input.name + '"]' : '') +
                      (input.placeholder ? ' ("' + input.placeholder + '")' : '');
            console.log('   ' + (index + 1) + ': ' + info);
        });

        // Mostrar datos guardados
        var datosGuardados = this.loadExtractedData();
        if (datosGuardados) {
            console.log('\nDATOS GUARDADOS:');
            console.log(datosGuardados);
        }
    }

    highlightField(campo, nombre) {
        var estilosOriginales = {
            border: campo.style.border,
            backgroundColor: campo.style.backgroundColor,
            transform: campo.style.transform
        };

        campo.style.border = '3px solid #FFD700';
        campo.style.backgroundColor = '#FFF8E1';
        campo.style.transform = 'scale(1.02)';
        campo.style.transition = 'all 0.5s ease';

        setTimeout(function() {
            campo.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);

        setTimeout(function() {
            Object.assign(campo.style, estilosOriginales);
        }, 5000);
    }

    highlightRadio(radio, nombre) {
        var label = radio.closest('label') || radio.parentElement;
        if (label) {
            var estilosOriginales = {
                backgroundColor: label.style.backgroundColor,
                color: label.style.color,
                transform: label.style.transform
            };

            label.style.backgroundColor = '#FFD700';
            label.style.color = '#000';
            label.style.fontWeight = 'bold';
            label.style.transform = 'scale(1.05)';
            label.style.transition = 'all 0.5s ease';
            label.style.borderRadius = '8px';
            label.style.padding = '8px';

            setTimeout(function() {
                Object.assign(label.style, estilosOriginales);
            }, 5000);
        }
    }

    showLoading(show) {
        var loadingDiv = document.getElementById('prd-loading');
        
        if (show) {
            if (!loadingDiv) {
                loadingDiv = document.createElement('div');
                loadingDiv.id = 'prd-loading';
                loadingDiv.style.cssText = 
                    'position: fixed; top: 0; left: 0; width: 100%; height: 100%;' +
                    'background: rgba(0,0,0,0.9); z-index: 9999;' +
                    'display: flex; align-items: center; justify-content: center;' +
                    'flex-direction: column; color: white;';
                loadingDiv.innerHTML = 
                    '<div style="border: 4px solid #f3f3f3; border-top: 4px solid #FFD700; ' +
                                'border-radius: 50%; width: 60px; height: 60px; ' +
                                'animation: spin 1s linear infinite; margin-bottom: 20px;"></div>' +
                    '<div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">Extrayendo datos...</div>' +
                    '<div style="font-size: 1rem; opacity: 0.8;">Procesando INE con algoritmo v4.0</div>';
                document.body.appendChild(loadingDiv);
                
                var style = document.createElement('style');
                style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
                document.head.appendChild(style);
            }
        } else {
            if (loadingDiv) {
                loadingDiv.style.opacity = '0';
                setTimeout(function() {
                    if (loadingDiv.parentNode) {
                        document.body.removeChild(loadingDiv);
                    }
                }, 300);
            }
        }
    }

    showError(message) {
        console.error('Error:', message);
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        console.log('Éxito:', message);
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        var colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };

        var notification = document.createElement('div');
        notification.style.cssText = 
            'position: fixed; top: 20px; right: 20px; z-index: 10001;' +
            'background: ' + colors[type] + '; color: white;' +
            'padding: 15px 20px; border-radius: 10px;' +
            'font-weight: bold; max-width: 400px;' +
            'box-shadow: 0 4px 15px rgba(0,0,0,0.3);' +
            'font-size: 1rem; display: flex; align-items: center; gap: 10px;';
        notification.innerHTML = message;
        document.body.appendChild(notification);

        notification.style.transform = 'translateX(100%)';
        setTimeout(function() {
            notification.style.transition = 'transform 0.3s ease';
            notification.style.transform = 'translateX(0)';
        }, 10);

        setTimeout(function() {
            notification.style.transform = 'translateX(100%)';
            setTimeout(function() {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 7000);
    }

    hideError() {
        // Implementación para ocultar errores si es necesario
    }
}

// FUNCIÓN GLOBAL scanINE
async function scanINE() {
    console.log('Función global scanINE() SIN EMOJIS v4.0 ejecutada');
    
    if (!window.prdDetector) {
        console.log('Creando instancia de PRDDetector SIN EMOJIS v4.0...');
        window.prdDetector = new PRDDetector();
    }
    
    await window.prdDetector.scanINE();
}

// FUNCIÓN PARA APLICAR DATOS EN EL PASO 2 (al cargar la página)
function aplicarDatosEnPaso2() {
    var detector = window.prdDetector;
    if (!detector) {
        console.log('No hay detector disponible');
        return;
    }
    
    var datos = detector.loadExtractedData();
    console.log('Datos cargados del storage:', datos);
    
    if (datos && detector.currentStep === 2) {
        console.log('Aplicando datos guardados en paso 2...');
        
        setTimeout(function() {
            console.log('Ejecutando llenado de paso 2...');
            detector.fillDomicilio(datos);
        }, 1000);
    } else {
        console.log('No hay datos guardados o no estamos en paso 2');
    }
}

// INICIALIZACIÓN
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado - Inicializando PRD Detector SIN EMOJIS v4.0...');
    
    // Crear instancia global
    window.prdDetector = new PRDDetector();
    
    // Debug de campos disponibles con delay
    setTimeout(function() {
        if (window.location.search.includes('debug=1')) {
            window.prdDetector.debugFormFields();
        }
    }, 1000);
    
    // Si estamos en paso 2, aplicar datos guardados
    if (window.prdDetector.currentStep === 2) {
        console.log('Detectado paso 2, aplicando datos guardados...');
        aplicarDatosEnPaso2();
    }
    
    // Test de conectividad con timeout
    Promise.race([
        fetch('http://127.0.0.1:5001/api/health'),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
    ])
    .then(function(response) { 
        return response.json(); 
    })
    .then(function(data) {
        console.log('CONEXIÓN PRD SIN EMOJIS OK:', data.service, data.version);
        window.prdDetector.showNotification('Servidor conectado: ' + data.version, 'success');
    })
    .catch(function(error) {
        console.error('CONEXIÓN PRD FALLÓ:', error);
        if (error.message !== 'Timeout') {
            window.prdDetector.showNotification('Servidor desconectado. Verificar app.py', 'warning');
        }
    });
    
    console.log('PRD Detector SIN EMOJIS v4.0 inicializado correctamente');
});

// HACER FUNCIÓN GLOBAL
window.scanINE = scanINE;

// FUNCIÓN GLOBAL PARA DEBUG
window.debugPRD = function() {
    if (window.prdDetector) {
        window.prdDetector.debugFormFields();
    } else {
        console.log('PRD Detector no inicializado');
    }
};