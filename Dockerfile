# Python 3.11 slim
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema para OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto
COPY . .

# Verificar estructura (debugging)
RUN echo "🔍 Verificando estructura del proyecto:"
RUN ls -la /app/
RUN echo "📁 Contenido de Backend/:"
RUN ls -la /app/Backend/ || echo "❌ No existe /app/Backend/"
RUN echo "🔍 Buscando todos los app.py:"
RUN find /app -name "app.py" -type f || echo "❌ No se encontró app.py"

# Exponer puerto
EXPOSE $PORT

# Ejecutar desde Backend/ (con B mayúscula) - RUTA CORREGIDA
CMD ["python", "/app/Backend/app.py"]