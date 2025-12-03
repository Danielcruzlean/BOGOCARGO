CREATE DATABASE bogocargobasededatos;
USE bogocargobasededatos;

-- 1. Tabla usuarios (SIN CAMBIOS CRÍTICOS)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    -- Django usa TIPO_CHOICES, aquí lo mantenemos simple para MySQL
    tipo ENUM('MINORISTA','CONDUCTOR','ADMIN') NOT NULL, 
    email VARCHAR(120) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    disponibilidad ENUM('DISPONIBLE','EN_RUTA','DESCANSO') DEFAULT 'DISPONIBLE',
    fecha_registro DATETIME DEFAULT NOW(),
    -- CAMPOS ADICIONALES DE DJANGO: is_active, is_staff, is_superuser, groups, user_permissions
    is_active BOOLEAN DEFAULT TRUE, 
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login DATETIME,
    date_joined DATETIME DEFAULT NOW()
);

-- 2. Tabla empresas (SIN CAMBIOS)
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

-- 3. Tabla localidades (SIN CAMBIOS)
CREATE TABLE localidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    codigo_postal VARCHAR(10)
);

-- 4. Tabla productos (SIN CAMBIOS)
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

-- 5. Tabla pedidos (ACTUALIZADA PARA COINCIDIR CON DJANGO)
CREATE TABLE pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Django usa conductor_id en lugar de mayorista_id
    minorista_id INT NOT NULL, 
    conductor_id INT, 

    fecha_creacion DATETIME DEFAULT NOW(),
    
    -- ESTADOS ACTUALES DEL MODELO DE DJANGO
    estado ENUM('PENDIENTE','ASIGNADO','EN_TRANSITO','COMPLETADO','CANCELADO') DEFAULT 'PENDIENTE',

    -- CORRECCIÓN CRÍTICA: Cambiado 'peso_total' a 'peso_total_kg'
    peso_total_kg DECIMAL(10,2) NOT NULL DEFAULT 0.0, 
    -- NUEVO CAMPO NECESARIO
    descripcion_carga VARCHAR(100) NOT NULL DEFAULT 'Carga no especificada',

    -- SIMPLIFICACIÓN: Django usa ORÍGEN y DESTINO (como CharField)
    origen VARCHAR(255) NOT NULL, 
    destino VARCHAR(255) NOT NULL,
    
    -- Se eliminaron campos de geolocalización lat/lng que no están en el modelo final de Django
    
    FOREIGN KEY (minorista_id) REFERENCES usuarios(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 6. Tabla detalle_pedido (SIN CAMBIOS)
CREATE TABLE detalle_pedido (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- 7. Tabla vehiculos (SIN CAMBIOS CRÍTICOS)
CREATE TABLE vehiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    tipo ENUM('MOTO','CAMIONETA','CAMION') NOT NULL,
    capacidad_kg INT NOT NULL,
    conductor_id INT,
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 8. Tabla conductores_zonas (SIN CAMBIOS)
CREATE TABLE conductores_zonas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conductor_id INT NOT NULL,
    localidad_id INT NOT NULL, 
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id),
    FOREIGN KEY (localidad_id) REFERENCES localidades(id)
);

-- 9. Tabla envios (SIN CAMBIOS CRÍTICOS)
CREATE TABLE envios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL UNIQUE, -- Se asume OneToOneField en Django
    vehiculo_id INT, -- NULLABLE: Puede ser models.SET_NULL
    conductor_id INT, -- NULLABLE: Puede ser models.SET_NULL
    fecha_salida DATETIME,
    fecha_entrega DATETIME,
    estado ENUM('ASIGNADO','EN_RUTA','ENTREGADO','FALLIDO') DEFAULT 'ASIGNADO',
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
);

-- 10. Tabla rastreo_envio (ACTUALIZADA PARA COINCIDIR CON DJANGO)
CREATE TABLE rastreo_envio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    envio_id INT NOT NULL,
    -- CORRECCIÓN CRÍTICA: lat/lng eliminados, reemplazados por ubicacion
    ubicacion VARCHAR(255) NOT NULL DEFAULT 'Ubicación no registrada',
    -- CORRECCIÓN CRÍTICA: Renombrado 'fecha' a 'fecha_hora'
    fecha_hora DATETIME DEFAULT NOW(), 
    -- NUEVO CAMPO NECESARIO
    estado VARCHAR(30) NOT NULL DEFAULT 'RECOLECCIÓN',
    observaciones TEXT,
    
    FOREIGN KEY (envio_id) REFERENCES envios(id)
);

-- 11. Tabla asignaciones (ACTUALIZADA PARA COINCIDIR CON DJANGO)
CREATE TABLE asignaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    conductor_id INT NOT NULL,
    fecha_asignacion DATETIME DEFAULT NOW(),
    -- CAMPO CRÍTICO: Eliminación de 'vehiculo_id' y 'criterio', se añadió 'estado'
    estado ENUM('PENDIENTE','ACEPTADA','RECHAZADA') DEFAULT 'PENDIENTE', 
    
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (conductor_id) REFERENCES usuarios(id)
    -- FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
);
