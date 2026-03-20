-- ============================================================
-- COMP639 Project 1 - Predator Free Lincoln University (PF-LU)
-- Database Creation Script (PostgreSQL)
-- ============================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS incidental_obs CASCADE;
DROP TABLE IF EXISTS trap_catch CASCADE;
DROP TABLE IF EXISTS trap_condition CASCADE;
DROP TABLE IF EXISTS trap_status CASCADE;
DROP TABLE IF EXISTS bait_type CASCADE;
DROP TABLE IF EXISTS species CASCADE;
DROP TABLE IF EXISTS operator_line CASCADE;
DROP TABLE IF EXISTS trap CASCADE;
DROP TABLE IF EXISTS line CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS role CASCADE;

-- ============================================================
-- LOOKUP / REFERENCE TABLES
-- ============================================================

CREATE TABLE role (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE species (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE bait_type (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE trap_status (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE trap_condition (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
);

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE "user" (
    id                      SERIAL PRIMARY KEY,
    username                VARCHAR(50)  NOT NULL UNIQUE,
    email                   VARCHAR(100) NOT NULL UNIQUE,
    password_hash           VARCHAR(255) NOT NULL,
    first_name              VARCHAR(50)  NOT NULL,
    last_name               VARCHAR(50)  NOT NULL,
    phone                   VARCHAR(20),
    emergency_contact_name  VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    role_id                 INT          NOT NULL REFERENCES role(id),
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE line (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    line_type  VARCHAR(20)  NOT NULL DEFAULT 'Trap'
                            CHECK (line_type = 'Trap'),  -- ✅ 스펙: Trap만 허용
    is_retired BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE trap (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(30)   NOT NULL UNIQUE,
    trap_type  VARCHAR(30)   NOT NULL,
    line_id    INT           NOT NULL REFERENCES line(id),
    latitude   NUMERIC(10,6) NOT NULL,
    longitude  NUMERIC(10,6) NOT NULL,
    is_retired BOOLEAN       NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_trap_type CHECK (
        trap_type IN (
            'A24', 'DOC 150', 'DOC 200', 'DOC 250',
            'Flipping Timmy', 'Rat trap', 'T-Rex Rat Trap',
            'Trapinator', 'Victor'
        )
    )
);

CREATE TABLE operator_line (
    operator_id     INT  NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    line_id         INT  NOT NULL REFERENCES line(id)   ON DELETE CASCADE,
    assignment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (operator_id, line_id)
);

CREATE TABLE trap_catch (
    id           SERIAL PRIMARY KEY,
    trap_id      INT         NOT NULL REFERENCES trap(id),
    date_checked TIMESTAMP   NOT NULL,
    recorded_by  INT         REFERENCES "user"(id),
    species_id   INT         NOT NULL REFERENCES species(id),
    sex          VARCHAR(10) CHECK (sex IN ('Male', 'Female') OR sex IS NULL),
    maturity     VARCHAR(10) CHECK (maturity IN ('Juvenile', 'Adult') OR maturity IS NULL),
    status_id    INT         NOT NULL REFERENCES trap_status(id),
    rebaited     BOOLEAN     NOT NULL DEFAULT FALSE,
    bait_type_id INT         NOT NULL REFERENCES bait_type(id),
    condition_id INT         NOT NULL REFERENCES trap_condition(id),
    strikes      INT         NOT NULL DEFAULT 0 CHECK (strikes >= 0),
    notes        TEXT
);

CREATE TABLE incidental_obs (
    id          SERIAL PRIMARY KEY,
    operator_id INT          NOT NULL REFERENCES "user"(id),
    line_id     INT          NOT NULL REFERENCES line(id),
    obs_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    obs_type    VARCHAR(50)  NOT NULL,
    description TEXT,
    latitude    NUMERIC(10,6),
    longitude   NUMERIC(10,6)
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_trap_line    ON trap(line_id);
CREATE INDEX idx_catch_trap   ON trap_catch(trap_id);
CREATE INDEX idx_catch_by     ON trap_catch(recorded_by);
CREATE INDEX idx_op_line_op   ON operator_line(operator_id);
CREATE INDEX idx_op_line_line ON operator_line(line_id);
CREATE INDEX idx_obs_operator ON incidental_obs(operator_id);
CREATE INDEX idx_obs_line     ON incidental_obs(line_id);

-- ============================================================
-- END OF SCHEMA
-- ============================================================