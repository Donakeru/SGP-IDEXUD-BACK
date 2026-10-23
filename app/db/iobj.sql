/**
----------------------------------------
                SCHEMAS
----------------------------------------
*/

CREATE TABLE tsgp_usuario (
	id_usuario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	nombre TEXT NOT NULL,
	correo TEXT NOT NULL UNIQUE,
	es_activo BOOLEAN NOT NULL DEFAULT TRUE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tsgp_rol (
	id_rol BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	nombre TEXT UNIQUE NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

CREATE TABLE tsgp_propuesta_estado (
	id_propuesta_estado BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	nombre TEXT NOT NULL UNIQUE,
	descripcion TEXT,
	es_final BOOLEAN NOT NULL DEFAULT FALSE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tsgp_propuesta (
	id_propuesta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	id_propuesta_estado BIGINT NOT NULL,
	nombre TEXT NOT NULL,
	descripcion TEXT,
	fecha_inicio TIMESTAMPTZ NOT NULL,
	fecha_fin TIMESTAMPTZ NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

	CONSTRAINT fk_propuesta_estado
		FOREIGN KEY (id_propuesta_estado)
		REFERENCES tsgp_propuesta_estado(id_propuesta_estado)
		ON DELETE RESTRICT
);

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

CREATE TABLE tsgp_documento (
	id_documento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	id_propuesta BIGINT NOT NULL,
	id_usuario BIGINT NOT NULL,
	s3_key TEXT NOT NULL UNIQUE,
	nombre_original TEXT NOT NULL,
	bucket_nombre TEXT NOT NULL,
	tipo_mime TEXT NOT NULL,
	tamano_bytes BIGINT NOT NULL,
	es_activo BOOLEAN NOT NULL DEFAULT TRUE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

	CONSTRAINT fk_doc_propuesta
		FOREIGN KEY (id_propuesta)
		REFERENCES tsgp_propuesta(id_propuesta)
		ON DELETE CASCADE,

	CONSTRAINT fk_doc_usuario
		FOREIGN KEY (id_usuario)
		REFERENCES tsgp_usuario(id_usuario)
		ON DELETE CASCADE
);

/**
----------------------------------------
                DATA
----------------------------------------
*/