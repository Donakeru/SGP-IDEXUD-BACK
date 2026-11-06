/**
----------------------------------------
                SCHEMAS
----------------------------------------
*/

-- 1. Usuarios
CREATE TABLE tsgp_usuario (
    id_usuario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    es_activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Roles
CREATE TABLE tsgp_rol (
    id_rol BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE
        CONSTRAINT ck_tsgp_rol_codigo_formato CHECK (codigo ~ '^[a-z][a-z0-9_]*$'),
    nombre TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Usuario - Rol (RBAC)
CREATE TABLE tsgp_usuario_rol (
    id_usuario BIGINT NOT NULL,
    id_rol BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY(id_usuario, id_rol),

    CONSTRAINT fk_ur_usuario 
        FOREIGN KEY (id_usuario)
        REFERENCES tsgp_usuario(id_usuario)
        ON DELETE CASCADE,

    CONSTRAINT fk_ur_rol 
        FOREIGN KEY (id_rol)
        REFERENCES tsgp_rol(id_rol)
        ON DELETE CASCADE
);

-- 4. Permisos
CREATE TABLE tsgp_permiso (
    id_permiso BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Rol - Permiso (RBAC)
CREATE TABLE tsgp_rol_permiso (
    id_rol BIGINT NOT NULL,
    id_permiso BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id_rol, id_permiso),

    CONSTRAINT fk_rp_rol
        FOREIGN KEY (id_rol)
        REFERENCES tsgp_rol(id_rol)
        ON DELETE CASCADE,

    CONSTRAINT fk_rp_permiso
        FOREIGN KEY (id_permiso)
        REFERENCES tsgp_permiso(id_permiso)
        ON DELETE CASCADE
);

-- 6. Estados de Propuesta
CREATE TABLE tsgp_propuesta_estado (
    id_propuesta_estado BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    es_final BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Transiciones de Estado
CREATE TABLE tsgp_transicion_estado (
    id_transicion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_estado_origen BIGINT NOT NULL,
    id_estado_destino BIGINT NOT NULL,
    id_permiso BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_te_estado_origen
        FOREIGN KEY (id_estado_origen)
        REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
        ON DELETE RESTRICT,

    CONSTRAINT fk_te_estado_destino
        FOREIGN KEY (id_estado_destino)
        REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
        ON DELETE RESTRICT,

    CONSTRAINT fk_te_permiso
        FOREIGN KEY (id_permiso)
        REFERENCES tsgp_permiso(id_permiso)
        ON DELETE SET NULL,

    CONSTRAINT uq_transicion_origen_destino 
        UNIQUE (id_estado_origen, id_estado_destino)
);

-- 8. Propuestas
CREATE TABLE tsgp_propuesta (
    id_propuesta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid_expediente UUID NOT NULL,
    id_propuesta_estado BIGINT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_inicio TIMESTAMPTZ NOT NULL,
    fecha_fin TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_propuesta_uuid_expediente
        UNIQUE (uuid_expediente),

    CONSTRAINT fk_propuesta_estado
        FOREIGN KEY (id_propuesta_estado)
        REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
        ON DELETE RESTRICT
);

-- 9. Solicitante de la Propuesta
CREATE TABLE tsgp_propuesta_solicitante (
    id_propuesta_solicitante BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_propuesta BIGINT NOT NULL,
    tipo_solicitante TEXT NOT NULL,
    nombre_organizacion TEXT,
    nit TEXT,
    nombre_contacto TEXT NOT NULL,
    cargo_contacto TEXT NOT NULL,
    correo_contacto TEXT NOT NULL,
    telefono_contacto TEXT NOT NULL,
    privacidad_aceptada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_aceptacion_privacidad TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_propuesta_solicitante_propuesta
        UNIQUE (id_propuesta),

    CONSTRAINT fk_ps_propuesta
        FOREIGN KEY (id_propuesta)
        REFERENCES tsgp_propuesta(id_propuesta)
        ON DELETE CASCADE,

    CONSTRAINT chk_ps_privacidad_fecha
        CHECK (
            privacidad_aceptada = FALSE
            OR fecha_aceptacion_privacidad IS NOT NULL
        )
);

-- 10. Historial de Estados
CREATE TABLE tsgp_historial_estado (
    id_historial BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_propuesta BIGINT NOT NULL,
    id_estado_anterior BIGINT,
    id_estado_nuevo BIGINT NOT NULL,
    id_usuario BIGINT NOT NULL,
    motivo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_he_propuesta
        FOREIGN KEY (id_propuesta)
        REFERENCES tsgp_propuesta(id_propuesta)
        ON DELETE CASCADE,

    CONSTRAINT fk_he_estado_anterior
        FOREIGN KEY (id_estado_anterior)
        REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
        ON DELETE RESTRICT,

    CONSTRAINT fk_he_estado_nuevo
        FOREIGN KEY (id_estado_nuevo)
        REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
        ON DELETE RESTRICT,

    CONSTRAINT fk_he_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES tsgp_usuario(id_usuario)
        ON DELETE RESTRICT
);

-- 11. Tipos de Documento
CREATE TABLE tsgp_tipo_documento (
    id_tipo_documento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    es_inmutable BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. Documentos (Adaptada a almacenamiento local)
CREATE TABLE tsgp_documento (
    id_documento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid_archivo UUID NOT NULL,
    id_propuesta BIGINT NOT NULL,
    id_tipo_documento BIGINT NOT NULL,
    id_usuario BIGINT NOT NULL,
    id_documento_origen BIGINT,
    ruta_archivo TEXT NOT NULL UNIQUE, -- Ruta relativa/absoluta en el servidor backend
    nombre_original TEXT NOT NULL,
    tipo_mime TEXT NOT NULL,
    tamano_bytes BIGINT NOT NULL,
    hash_sha256 CHAR(64),
    numero_version INT NOT NULL DEFAULT 1,
    es_vigente BOOLEAN NOT NULL DEFAULT TRUE,
    estado_carga TEXT NOT NULL DEFAULT 'pendiente',
    fecha_carga TIMESTAMPTZ,
    es_activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_eliminacion TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_documento_uuid_archivo
        UNIQUE (uuid_archivo),

    CONSTRAINT fk_doc_propuesta
        FOREIGN KEY (id_propuesta)
        REFERENCES tsgp_propuesta(id_propuesta)
        ON DELETE CASCADE,

    CONSTRAINT fk_doc_tipo
        FOREIGN KEY (id_tipo_documento)
        REFERENCES tsgp_tipo_documento(id_tipo_documento)
        ON DELETE RESTRICT,

    CONSTRAINT fk_doc_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES tsgp_usuario(id_usuario)
        ON DELETE CASCADE,

    CONSTRAINT fk_doc_origen
        FOREIGN KEY (id_documento_origen)
        REFERENCES tsgp_documento(id_documento)
        ON DELETE CASCADE,

    CONSTRAINT chk_doc_estado_carga
        CHECK (estado_carga IN ('pendiente', 'cargado', 'fallido'))
);

-- 13. Comentarios
CREATE TABLE tsgp_comentario (
    id_comentario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_propuesta BIGINT NOT NULL,
    id_usuario BIGINT NOT NULL,
    contenido TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_com_propuesta
        FOREIGN KEY (id_propuesta)
        REFERENCES tsgp_propuesta(id_propuesta)
        ON DELETE CASCADE,

    CONSTRAINT fk_com_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES tsgp_usuario(id_usuario)
        ON DELETE CASCADE
);

/**
----------------------------------------
                ÍNDICES
----------------------------------------
*/

-- Búsquedas y filtros en Propuestas
CREATE INDEX idx_propuesta_estado ON tsgp_propuesta(id_propuesta_estado);

-- Relaciones de Documentos
CREATE INDEX idx_documento_propuesta ON tsgp_documento(id_propuesta);
CREATE INDEX idx_documento_tipo ON tsgp_documento(id_tipo_documento);
CREATE INDEX idx_documento_usuario ON tsgp_documento(id_usuario);
CREATE INDEX idx_documento_origen ON tsgp_documento(id_documento_origen);

-- Trazabilidad e Historial
CREATE INDEX idx_historial_propuesta ON tsgp_historial_estado(id_propuesta);
CREATE INDEX idx_historial_usuario ON tsgp_historial_estado(id_usuario);

-- Comentarios
CREATE INDEX idx_comentario_propuesta ON tsgp_comentario(id_propuesta);
CREATE INDEX idx_comentario_usuario ON tsgp_comentario(id_usuario);

-- Flujo de Transiciones
CREATE INDEX idx_transicion_origen ON tsgp_transicion_estado(id_estado_origen);
CREATE INDEX idx_transicion_destino ON tsgp_transicion_estado(id_estado_destino);

-- DATA

INSERT INTO tsgp_rol (codigo, nombre) VALUES
    ('administrador', 'Administrador del Sistema'),
    ('direccion', 'Dirección'),
    ('asistente_direccion', 'Asistente de Dirección'),
    ('juridica', 'Jurídica'),
    ('licitaciones', 'Licitaciones'),
    ('comite_central_extension', 'Comité Central de Extensión'),
    ('equipo_multidisciplinar', 'Equipo Multidisciplinar Calificado');


INSERT INTO tsgp_propuesta_estado (nombre, descripcion, es_final) VALUES
    ('Registrado', 'Propuesta registrada en el sistema.', FALSE),
    ('Aceptado', 'Propuesta aceptada para continuar con el proceso.', FALSE),
    ('Preaprobado', 'Propuesta con concepto de preaprobación.', FALSE),
    ('Aprobado', 'Propuesta aprobada definitivamente.', TRUE),
    ('Rechazado', 'Propuesta rechazada.', TRUE)
ON CONFLICT (nombre) DO NOTHING;


INSERT INTO tsgp_usuario (nombre, correo, es_activo) VALUES
    ('Ana Gómez', 'ana.gomez@example.com', TRUE),
    ('Carlos Rodríguez', 'carlos.rodriguez@example.com', TRUE),
    ('Laura Martínez', 'laura.martinez@example.com', TRUE),
    ('Diego Pérez', 'diego.perez@example.com', TRUE)
ON CONFLICT (correo) DO NOTHING;


INSERT INTO tsgp_usuario_rol (id_usuario, id_rol)
SELECT u.id_usuario, r.id_rol
FROM (
    VALUES
        ('ana.gomez@example.com', 'administrador'),
        ('carlos.rodriguez@example.com', 'direccion'),
        ('laura.martinez@example.com', 'asistente_direccion'),
        ('diego.perez@example.com', 'equipo_multidisciplinar')
) AS asignaciones(correo, codigo)
INNER JOIN tsgp_usuario u
    ON u.correo = asignaciones.correo
INNER JOIN tsgp_rol r
    ON r.codigo = asignaciones.codigo
ON CONFLICT (id_usuario, id_rol) DO NOTHING;
