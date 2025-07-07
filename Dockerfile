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

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto
COPY . .

# Verificar que la estructura esté correcta
RUN ls -la /app/
RUN ls -la /app/backend/ || echo "❌ No existe /app/backend/"

# Exponer puerto
EXPOSE $PORT

# Ejecutar directamente desde backend/ usando ruta absoluta
CMD ["python", "/app/backend/app.py"]