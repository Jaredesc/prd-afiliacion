# Python 3.11 slim (rápido y estable)
FROM python:3.11-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Variables para Python
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

# Instalar Python packages
RUN pip install --no-cache-dir --upgrade pip==23.3.1
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Puerto dinámico de Railway
EXPOSE $PORT

# Comando de inicio
CMD cd backend && python app.py