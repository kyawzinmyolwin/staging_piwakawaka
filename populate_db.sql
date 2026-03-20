-- ============================================================
-- COMP639 Project 1 - Predator Free Lincoln University (PF-LU)
-- Database Population Script (PostgreSQL)
-- NOTE: Passwords are hashed using Bcrypt
--       All sample passwords = "Password1!"
--       Hash generated via: bcrypt.hashpw("Password1!")
-- ============================================================

-- ============================================================
-- 1. ROLES
-- ============================================================
INSERT INTO role (name) VALUES
    ('Observer'),
    ('Operator'),
    ('Admin');

-- ============================================================
-- 2. SPECIES (trap.nz spec)
-- ============================================================
INSERT INTO species (name) VALUES
    ('Ferret'),
    ('Hedgehog'),
    ('Mouse'),
    ('Possum'),
    ('Kiore Rat'),
    ('Norway Rat'),
    ('Ship Rat'),
    ('Stoat'),
    ('Weasel'),
    ('Unspecified'),
    ('None');

-- ============================================================
-- 3. BAIT TYPES (trap.nz spec)
-- ============================================================
INSERT INTO bait_type (name) VALUES
    ('Carrot'),
    ('Cereal'),
    ('Cheese'),
    ('Chocolate'),
    ('Dehydrated Rabbit'),
    ('Dried fruit'),
    ('Ferret bedding'),
    ('Fish'),
    ('Fresh Possum'),
    ('Fresh Rabbit'),
    ('Fresh fruit'),
    ('Fresh meat'),
    ('Golf ball'),
    ('Good Nature Chocolate'),
    ('Good Nature Meat Lovers'),
    ('Goodnature Blood'),
    ('Goodnature Cinnamon pre feed'),
    ('Goodnature Nut Butter'),
    ('Lure'),
    ('Lure-it Salmon Spray'),
    ('Mayo'),
    ('Mustelid and Cat Lure'),
    ('NARA Blocks'),
    ('NZAT Lure - Original'),
    ('None'),
    ('Nut'),
    ('Nutella'),
    ('Other (please specify)'),
    ('Peanut butter'),
    ('PoaUku'),
    ('Possum Dough'),
    ('Rabbit oil'),
    ('Rat and Possum Lure'),
    ('Rat oil'),
    ('Salmon'),
    ('Salmon oil'),
    ('Salted Possum'),
    ('Salted Rabbit'),
    ('Salted meat'),
    ('Smooth'),
    ('Terracotta Lures'),
    ('Tinned Sardines'),
    ('Whole egg');

-- ============================================================
-- 4. TRAP STATUSES (trap.nz spec)
-- ============================================================
INSERT INTO trap_status (name) VALUES
    ('Initial set'),
    ('Removed for Repair'),
    ('Sprung'),
    ('Still set, bait OK'),
    ('Still set, bait bad'),
    ('Still set, bait missing'),
    ('Trap Replaced'),
    ('Trap gone'),
    ('Trap interfered with');

-- ============================================================
-- 5. TRAP CONDITIONS
-- ============================================================
INSERT INTO trap_condition (name) VALUES
    ('OK'),
    ('Needs maintenance'),
    ('Repaired'),
    ('Regassed'),
    ('Recurred'),
    ('Battery charge');

-- ============================================================
-- 6. USERS (Bcrypt hash of "Password1!")
-- ============================================================

-- 2 Admins
INSERT INTO "user" (username, email, password_hash, first_name, last_name, phone,
    emergency_contact_name, emergency_contact_phone, role_id, is_active)
VALUES
    ('admin_sarah', 'sarah.admin@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Sarah', 'Thompson', '03-325-2800',
     'John Thompson', '027-111-0001', 3, TRUE),

    ('admin_james', 'james.admin@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'James', 'Wilson', '03-325-2801',
     'Maria Wilson', '027-111-0002', 3, TRUE);

-- 10 Operators
INSERT INTO "user" (username, email, password_hash, first_name, last_name, phone,
    emergency_contact_name, emergency_contact_phone, role_id, is_active)
VALUES
    ('op_alice',  'alice.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Alice', 'Brown', '027-201-0001', 'Bob Brown', '027-202-0001', 2, TRUE),

    ('op_ben',    'ben.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Ben', 'Clark', '027-201-0002', 'Nina Clark', '027-202-0002', 2, TRUE),

    ('op_cara',   'cara.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Cara', 'Davies', '027-201-0003', 'Tom Davies', '027-202-0003', 2, TRUE),

    ('op_dan',    'dan.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Dan', 'Evans', '027-201-0004', 'Sue Evans', '027-202-0004', 2, TRUE),

    ('op_emma',   'emma.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Emma', 'Foster', '027-201-0005', 'Leo Foster', '027-202-0005', 2, TRUE),

    ('op_frank',  'frank.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Frank', 'Gray', '027-201-0006', 'Ann Gray', '027-202-0006', 2, TRUE),

    ('op_grace',  'grace.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Grace', 'Hall', '027-201-0007', 'Mike Hall', '027-202-0007', 2, TRUE),

    ('op_henry',  'henry.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Henry', 'Ingram', '027-201-0008', 'Rose Ingram', '027-202-0008', 2, TRUE),

    ('op_iris',   'iris.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Iris', 'Jones', '027-201-0009', 'Carl Jones', '027-202-0009', 2, TRUE),

    ('op_jake',   'jake.op@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Jake', 'King', '027-201-0010', 'Lena King', '027-202-0010', 2, TRUE);

-- 10 Observers
INSERT INTO "user" (username, email, password_hash, first_name, last_name, phone,
    emergency_contact_name, emergency_contact_phone, role_id, is_active)
VALUES
    ('obs_kate',   'kate.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Kate', 'Lewis', '027-301-0001', 'Paul Lewis', '027-302-0001', 1, TRUE),

    ('obs_liam',   'liam.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Liam', 'Moore', '027-301-0002', 'Zoe Moore', '027-302-0002', 1, TRUE),

    ('obs_mia',    'mia.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Mia', 'Nash', '027-301-0003', 'Sam Nash', '027-302-0003', 1, TRUE),

    ('obs_noah',   'noah.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Noah', 'Owen', '027-301-0004', 'Amy Owen', '027-302-0004', 1, TRUE),

    ('obs_olivia', 'olivia.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Olivia', 'Park', '027-301-0005', 'Eric Park', '027-302-0005', 1, TRUE),

    ('obs_peter',  'peter.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Peter', 'Quinn', '027-301-0006', 'Jane Quinn', '027-302-0006', 1, TRUE),

    ('obs_quinn',  'quinn.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Quinn', 'Reed', '027-301-0007', 'Mark Reed', '027-302-0007', 1, TRUE),

    ('obs_ruby',   'ruby.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Ruby', 'Scott', '027-301-0008', 'Neil Scott', '027-302-0008', 1, TRUE),

    ('obs_sam',    'sam.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Sam', 'Taylor', '027-301-0009', 'Dana Taylor', '027-302-0009', 1, TRUE),

    ('obs_tara',   'tara.obs@pflu.nz',
     '$2b$12$fezzISpLv6MZb1JLRaln6.tuT0s3YFsRq0d.uEJTrXGjFyAYqpVvm',
     'Tara', 'Upton', '027-301-0010', 'Glen Upton', '027-302-0010', 1, TRUE);

-- ============================================================
-- 7. TRAP LINES (5 lines as required)
-- ============================================================
INSERT INTO line (name, line_type, is_retired) VALUES
    ('North Campus Line',    'Trap', FALSE),
    ('South Campus Line',    'Trap', FALSE),
    ('East Wetlands Line',   'Trap', FALSE),
    ('West Orchard Line',    'Trap', FALSE),
    ('Central Reserve Line', 'Trap', FALSE);

-- ============================================================
-- 8. ASSIGN OPERATORS TO LINES
-- ============================================================
INSERT INTO operator_line (operator_id, line_id, assignment_date) VALUES
    (3,  1, '2026-01-15'), (3,  2, '2026-01-15'),
    (4,  1, '2026-01-15'), (4,  2, '2026-01-15'),
    (5,  3, '2026-01-15'), (5,  4, '2026-01-15'),
    (6,  3, '2026-01-15'), (6,  4, '2026-01-15'),
    (7,  5, '2026-01-15'), (7,  1, '2026-01-15'),
    (8,  5, '2026-01-15'), (8,  1, '2026-01-15'),
    (9,  2, '2026-01-15'), (9,  3, '2026-01-15'),
    (10, 4, '2026-01-15'), (10, 5, '2026-01-15'),
    (11, 1, '2026-01-15'),
    (12, 2, '2026-01-15');

-- ============================================================
-- 9. TRAPS (5 per line = 25 total)
-- ============================================================

-- North Campus Line (line_id=1)
INSERT INTO trap (code, trap_type, line_id, latitude, longitude) VALUES
    ('NC-001', 'DOC 200',        1, -43.643100, 172.469200),
    ('NC-002', 'Victor',         1, -43.643300, 172.469500),
    ('NC-003', 'T-Rex Rat Trap', 1, -43.643500, 172.469800),
    ('NC-004', 'DOC 150',        1, -43.643700, 172.470100),
    ('NC-005', 'Trapinator',     1, -43.643900, 172.470400);

-- South Campus Line (line_id=2)
INSERT INTO trap (code, trap_type, line_id, latitude, longitude) VALUES
    ('SC-001', 'DOC 250',        2, -43.648100, 172.469200),
    ('SC-002', 'Flipping Timmy', 2, -43.648300, 172.469500),
    ('SC-003', 'Victor',         2, -43.648500, 172.469800),
    ('SC-004', 'DOC 200',        2, -43.648700, 172.470100),
    ('SC-005', 'Rat trap',       2, -43.648900, 172.470400);

-- East Wetlands Line (line_id=3)
INSERT INTO trap (code, trap_type, line_id, latitude, longitude) VALUES
    ('EW-001', 'A24',            3, -43.645000, 172.474000),
    ('EW-002', 'DOC 200',        3, -43.645300, 172.474300),
    ('EW-003', 'Trapinator',     3, -43.645600, 172.474600),
    ('EW-004', 'DOC 150',        3, -43.645900, 172.474900),
    ('EW-005', 'Victor',         3, -43.646200, 172.475200);

-- West Orchard Line (line_id=4)
INSERT INTO trap (code, trap_type, line_id, latitude, longitude) VALUES
    ('WO-001', 'DOC 200',        4, -43.645000, 172.464000),
    ('WO-002', 'T-Rex Rat Trap', 4, -43.645300, 172.464300),
    ('WO-003', 'DOC 250',        4, -43.645600, 172.464600),
    ('WO-004', 'Flipping Timmy', 4, -43.645900, 172.464900),
    ('WO-005', 'Rat trap',       4, -43.646200, 172.465200);

-- Central Reserve Line (line_id=5)
INSERT INTO trap (code, trap_type, line_id, latitude, longitude) VALUES
    ('CR-001', 'DOC 200',        5, -43.645500, 172.469000),
    ('CR-002', 'Victor',         5, -43.645700, 172.469300),
    ('CR-003', 'DOC 150',        5, -43.645900, 172.469600),
    ('CR-004', 'A24',            5, -43.646100, 172.469900),
    ('CR-005', 'Trapinator',     5, -43.646300, 172.470200);

-- ============================================================
-- 10. TRAP CATCH RECORDS (5 per line = 25 total)
-- ============================================================

-- North Campus Line (trap_id 1-5)
INSERT INTO trap_catch
    (trap_id, date_checked, recorded_by, species_id, sex, maturity, status_id, rebaited, bait_type_id, condition_id, strikes, notes)
VALUES
    (1, '2026-03-01 09:00:00', 3,  8, 'Male',   'Adult',    3, TRUE,  29, 1, 1, 'Stoat caught, trap reset'),
    (2, '2026-03-01 09:15:00', 3, 11, NULL, NULL,            4, TRUE,  29, 1, 0, 'No catch, bait OK'),
    (3, '2026-03-08 09:00:00', 4,  7, 'Female', 'Adult',    3, TRUE,  29, 1, 1, 'Ship rat caught'),
    (4, '2026-03-08 09:20:00', 4,  4, 'Female', 'Juvenile', 3, TRUE,   1, 1, 1, 'Possum - juvenile female'),
    (5, '2026-03-15 09:00:00', 7, 11, NULL, NULL,            6, FALSE, 25, 2, 0, 'Bait missing, not rebaited');

-- South Campus Line (trap_id 6-10)
INSERT INTO trap_catch
    (trap_id, date_checked, recorded_by, species_id, sex, maturity, status_id, rebaited, bait_type_id, condition_id, strikes, notes)
VALUES
    (6,  '2026-03-02 10:00:00', 3,  4, 'Male',   'Adult', 3, TRUE,   1, 1, 1, 'Possum male'),
    (7,  '2026-03-02 10:20:00', 3, 11, NULL, NULL,          4, TRUE,  29, 1, 0, 'Set OK'),
    (8,  '2026-03-09 10:00:00', 4,  6, 'Male',   'Adult', 3, TRUE,  29, 1, 1, 'Norway rat'),
    (9,  '2026-03-09 10:20:00', 4, 11, NULL, NULL,          4, TRUE,  29, 1, 0, 'Nothing caught'),
    (10, '2026-03-16 10:00:00', 9,  8, 'Female', 'Adult', 3, TRUE,  22, 1, 1, 'Stoat - female');

-- East Wetlands Line (trap_id 11-15)
INSERT INTO trap_catch
    (trap_id, date_checked, recorded_by, species_id, sex, maturity, status_id, rebaited, bait_type_id, condition_id, strikes, notes)
VALUES
    (11, '2026-03-03 08:00:00', 5,  1, 'Male',   'Adult', 3, TRUE,   7, 1, 1, 'Ferret caught near wetland'),
    (12, '2026-03-03 08:20:00', 5, 11, NULL, NULL,          5, TRUE,  29, 1, 0, 'Bait bad - replaced'),
    (13, '2026-03-10 08:00:00', 6,  9, 'Female', 'Adult', 3, TRUE,  22, 1, 1, 'Weasel'),
    (14, '2026-03-10 08:20:00', 6, 11, NULL, NULL,          4, TRUE,  43, 1, 0, 'Whole egg bait OK'),
    (15, '2026-03-17 08:00:00', 9,  5, 'Male',   'Adult', 3, TRUE,  29, 1, 2, 'Two Kiore rats caught');

-- West Orchard Line (trap_id 16-20)
INSERT INTO trap_catch
    (trap_id, date_checked, recorded_by, species_id, sex, maturity, status_id, rebaited, bait_type_id, condition_id, strikes, notes)
VALUES
    (16, '2026-03-04 11:00:00', 5,  4, 'Female', 'Adult',    3, TRUE,   1, 1, 1, 'Possum in orchard area'),
    (17, '2026-03-04 11:20:00', 5, 11, NULL, NULL,            4, TRUE,  29, 1, 0, 'Nothing caught'),
    (18, '2026-03-11 11:00:00', 6,  7, 'Male',   'Juvenile', 3, TRUE,  29, 1, 1, 'Young ship rat'),
    (19, '2026-03-11 11:20:00', 6, 11, NULL, NULL,            6, FALSE, 25, 2, 0, 'Bait missing, needs maintenance'),
    (20, '2026-03-17 11:00:00',10,  4, 'Male',   'Adult',    3, TRUE,   1, 1, 1, 'Possum male - large');

-- Central Reserve Line (trap_id 21-25)
INSERT INTO trap_catch
    (trap_id, date_checked, recorded_by, species_id, sex, maturity, status_id, rebaited, bait_type_id, condition_id, strikes, notes)
VALUES
    (21, '2026-03-05 09:30:00', 7,  8, 'Male',   'Adult', 3, TRUE,  22, 1, 1, 'Stoat - central area'),
    (22, '2026-03-05 09:50:00', 7, 11, NULL, NULL,          4, TRUE,  29, 1, 0, 'No catch'),
    (23, '2026-03-12 09:30:00', 8,  4, 'Female', 'Adult', 3, TRUE,   1, 1, 1, 'Possum female'),
    (24, '2026-03-12 09:50:00', 8, 11, NULL, NULL,          1, TRUE,  29, 1, 0, 'Initial set - new trap location'),
    (25, '2026-03-17 09:30:00',11,  6, 'Female', 'Adult', 3, TRUE,  29, 1, 1, 'Norway rat near reserve');

-- ============================================================
-- 11. INCIDENTAL OBSERVATIONS
-- ============================================================
INSERT INTO incidental_obs (operator_id, line_id, obs_date, obs_type, description, latitude, longitude)
VALUES
    (3, 1, '2026-03-01 09:30:00', 'Bird sighting',
     'Tui seen feeding in native plantings near North Line trap NC-003',
     -43.643500, 172.469800),
    (5, 3, '2026-03-03 08:45:00', 'Predator sign',
     'Fresh possum scratches on tree trunk near EW-002',
     -43.645300, 172.474300),
    (7, 5, '2026-03-05 10:00:00', 'Native species tracks',
     'Gecko sighting under log near Central Reserve Line',
     -43.645700, 172.469300),
    (4, 2, '2026-03-08 09:40:00', 'Bird sighting',
     'Fantail pair nesting near South campus boundary',
     -43.648300, 172.469500),
    (9, 2, '2026-03-09 11:00:00', 'Predator sighting',
     'Stoat observed crossing path near SC-003 at 10:55am',
     -43.648500, 172.469800);

-- ============================================================
-- END OF POPULATION SCRIPT
-- ============================================================