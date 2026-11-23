-- Vincula tsgp_usuario con la cuenta de Keycloak (claim "sub" del token).
-- Para bases existentes. Es idempotente: se puede ejecutar más de una vez.
-- Los usuarios actuales quedan con keycloak_sub NULL y se vinculan por correo
-- en su primer ingreso.

BEGIN;

ALTER TABLE tsgp_usuario
    ADD COLUMN IF NOT EXISTS keycloak_sub UUID;

-- Un índice único permite varios NULL y evita dos usuarios con el mismo sub.
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_keycloak_sub
    ON tsgp_usuario (keycloak_sub);

COMMIT;
