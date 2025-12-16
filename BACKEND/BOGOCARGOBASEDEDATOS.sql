CREATE DATABASE bogocargobasededatos;
USE bogocargobasededatos;

-- ##################################################################
-- PASO 2: CREACIÓN DE TABLAS
-- ##################################################################

-- 1. Tabla usuarios (CORREGIDA: Sincronizada con el modelo Django para incluir campos de vehículo)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Campos básicos de usuario
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    tipo ENUM('MINORISTA','CONDUCTOR','ADMIN') NOT NULL,
    
    -- Campos de Vehículo (Añadidos para CONDUCTOR, como en el modelo de Django)
    placas VARCHAR(10) UNIQUE NULL, 
    marca_vehiculo VARCHAR(50) NULL,
    referencia_vehiculo VARCHAR(50) NULL,
    tipo_vehiculo ENUM('CAMIONETA','FURGON','CAMION_PEQUEÑO','CAMION_GRANDE','MOTO') NULL,
    
    -- Campos de Django
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login DATETIME,
    date_joined DATETIME DEFAULT NOW()
);

-- 2. Tabla empresas (Sin cambios)
CREATE TABLE empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    nit VARCHAR(20) UNIQUE NOT NULL,
    direccion VARCHAR(200),
    ciudad VARCHAR(100),
    tipo ENUM('MAYORISTA','MINORISTA') NOT NULL,
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- 3. Tabla localidades (Sin cambios)
CREATE TABLE localidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    codigo_postal VARCHAR(10)
);

-- 4. Tabla productos (Sin cambios)
CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    peso_kg DECIMAL(10,2),
    altura_cm DECIMAL(10,2),
    ancho_cm DECIMAL(10,2),
    largo_cm DECIMAL(10,2),
    precio DECIMAL(10,2),
    empresa_id INT NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

-- 5. Tabla pedidos (CORREGIDA: Sincronizada con el modelo Django, usando los ENUM correctos)
CREATE TABLE pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Relaciones
    minorista_id INT NOT NULL,
    conductor_id INT,
    
    -- Datos del Envío y Carga
    origen VARCHAR(255) NOT NULL,
    destino VARCHAR(255) NOT NULL,
    fecha_recoleccion DATE NOT NULL,
    hora_recoleccion TIME NULL,
    observaciones TEXT,
    
    -- Datos de la Carga (Múltiples unidades por un solo registro)
    tipo_mercancia VARCHAR(50) NOT NULL,
    peso_total DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    volumen DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    valor_declarado DECIMAL(10,0) NOT NULL DEFAULT 0,
    unidades INT UNSIGNED NOT NULL DEFAULT 1,
    largo DECIMAL(5,2) NOT NULL DEFAULT 0.1,
    alto DECIMAL(5,2) NOT NULL DEFAULT 0.1,
    ancho DECIMAL(5,2) NOT NULL DEFAULT 0.1,
    
    -- Datos de Asignación/Facturación
    empresa_mayorista VARCHAR(200) NULL,
    precio_estimado DECIMAL(10,0) NOT NULL DEFAULT 0,
    
    -- Estado y Trazabilidad (ENUMs de Django)
    estado ENUM('PENDIENTE','ASIGNADO','EN_RUTA','ENTREGADO','CANCELADO') DEFAULT 'PENDIENTE',
    fecha_creacion DATETIME DEFAULT NOW(),
    fecha_actualizacion DATETIME DEFAULT NOW(),

    FOREIGN KEY (minorista_id) REFERENCES usuarios(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 6. Tabla detalle_pedido (Sin cambios)
CREATE TABLE detalle_pedido (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- 7. Tabla factura (AÑADIDA y Sincronizada)
CREATE TABLE factura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT UNIQUE NOT NULL, -- Relación OneToOne con Pedidos
    monto_total DECIMAL(10,0) NOT NULL,
    fecha_emision DATE NOT NULL DEFAULT (CURRENT_DATE()),
    fecha_vencimiento DATE NOT NULL,
    fecha_pago DATE,
    estado ENUM('PENDIENTE_PAGO','PAGADA','VENCIDA','ANULADA') NOT NULL DEFAULT 'PENDIENTE_PAGO',
    referencia VARCHAR(100) UNIQUE,
    
    FOREIGN KEY (orden_id) REFERENCES pedidos(id)
);

-- 8. Tabla asignaciones (Sin cambios - Mantiene la lógica de oferta/aceptación)
CREATE TABLE asignaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    conductor_id INT NOT NULL,
    fecha_asignacion DATETIME DEFAULT NOW(),
    estado ENUM('PENDIENTE','ACEPTADA','RECHAZADA') DEFAULT 'PENDIENTE',
    
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 9. Tabla envios (Sin cambios - Mantiene la trazabilidad y la relación con el conductor, pero ya NO necesita vehiculo_id)
-- NOTA: Como eliminamos la tabla vehiculos, esta tabla ahora asume que el vehículo está implícito en el conductor asignado al pedido.
CREATE TABLE envios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL UNIQUE,
    conductor_id INT, -- Conductor que ejecuta
    fecha_salida DATETIME,
    fecha_entrega DATETIME,
    estado ENUM('ASIGNADO','EN_RUTA','ENTREGADO','FALLIDO') DEFAULT 'ASIGNADO',
    
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 10. Tabla rastreo_envio (Sin cambios)
CREATE TABLE rastreo_envio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    envio_id INT NOT NULL,
    ubicacion VARCHAR(255) NOT NULL DEFAULT 'Ubicación no registrada',
    fecha_hora DATETIME DEFAULT NOW(),
    estado VARCHAR(30) NOT NULL DEFAULT 'RECOLECCIÓN',
    observaciones TEXT,
    
    FOREIGN KEY (envio_id) REFERENCES envios(id)
);
