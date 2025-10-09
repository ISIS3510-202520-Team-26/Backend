\set ON_ERROR_STOP on

-- Extensiones (idempotentes)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;

-- ======================
-- USERS (upsert por email)
-- ======================
INSERT INTO "user"(name,email,hashed_password,campus,created_at)
VALUES
 ('Tomas Alberto Rodriguez','tomas@uniandes.edu.co','***seed-only***','Uniandes', now()-interval '15 days'),
 ('Carlos Casadiego','carlos@uniandes.edu.co','***seed-only***','Uniandes', now()-interval '12 days'),
 ('Sebastian Umaña','sebastian@uniandes.edu.co','***seed-only***','Uniandes', now()-interval '10 days'),
 ('Juan Andrés Eslava','juan@uniandes.edu.co','***seed-only***','Uniandes', now()-interval '8 days')
ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name;

-- IDs de users
SELECT id AS u_tomas    FROM "user" WHERE email='tomas@uniandes.edu.co';
\gset
SELECT id AS u_carlos   FROM "user" WHERE email='carlos@uniandes.edu.co';
\gset
SELECT id AS u_sebastian FROM "user" WHERE email='sebastian@uniandes.edu.co';
\gset
SELECT id AS u_juan     FROM "user" WHERE email='juan@uniandes.edu.co';
\gset

-- ======================
-- CATEGORIES (upsert por slug)
-- ======================
INSERT INTO category(slug,name) VALUES
 ('laptops','Laptops'),
 ('phones','Phones'),
 ('accessories','Accessories'),
 ('textbooks','Textbooks'),
 ('services','Services')
ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name;

-- IDs de categorías
SELECT id AS cat_laptops     FROM category WHERE slug='laptops';
\gset
SELECT id AS cat_phones      FROM category WHERE slug='phones';
\gset
SELECT id AS cat_accessories FROM category WHERE slug='accessories';
\gset
SELECT id AS cat_textbooks   FROM category WHERE slug='textbooks';
\gset
SELECT id AS cat_services    FROM category WHERE slug='services';
\gset

-- ======================
-- BRANDS (upsert por slug)
-- ======================
INSERT INTO brand(name,slug,category_id) VALUES
 ('Lenovo','lenovo',        :'cat_laptops'),
 ('Apple','apple',          :'cat_laptops'),
 ('Samsung','samsung',      :'cat_phones'),
 ('Logitech','logitech',    :'cat_accessories')
ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name, category_id=EXCLUDED.category_id;

-- IDs de brands
SELECT id AS brand_lenovo   FROM brand WHERE slug='lenovo';
\gset
SELECT id AS brand_apple    FROM brand WHERE slug='apple';
\gset
SELECT id AS brand_samsung  FROM brand WHERE slug='samsung';
\gset
SELECT id AS brand_logitech FROM brand WHERE slug='logitech';
\gset

-- ======================
-- LISTINGS (ON CONFLICT id DO NOTHING)
-- ======================
-- Generamos UUIDs determinísticos (valen si ejecutas varias veces)
\set L1 'cccc0000-0000-0000-0000-000000000001'
\set L2 'cccc0000-0000-0000-0000-000000000002'
\set L3 'cccc0000-0000-0000-0000-000000000003'
\set L4 'cccc0000-0000-0000-0000-000000000004'
\set L5 'cccc0000-0000-0000-0000-000000000005'

INSERT INTO listing(id, seller_id, title, description, category_id, brand_id, price_cents, currency,
                    condition, quantity, is_active, latitude, longitude, price_suggestion_used,
                    quick_view_enabled, created_at, updated_at)
VALUES
 (:'L1', :'u_tomas',   'Lenovo ThinkPad T14','16GB RAM, buen estado', :'cat_laptops',    :'brand_lenovo',  2500000,'COP','used',1,TRUE,4.601,-74.066,TRUE, TRUE,  now()-interval '7 days', now()-interval '1 days'),
 (:'L2', :'u_carlos',  'Samsung Galaxy S21', '128GB, con cargador',   :'cat_phones',     :'brand_samsung', 1800000,'COP','used',1,TRUE,4.606,-74.070,FALSE,TRUE,  now()-interval '6 days', now()-interval '1 days'),
 (:'L3', :'u_carlos',  'Logitech MX Master 3','Como nuevo',           :'cat_accessories',:'brand_logitech', 380000,'COP','used',1,TRUE,4.604,-74.069,FALSE,TRUE,   now()-interval '5 days', now()-interval '1 days'),
 (:'L4', :'u_juan',    'Libro Cálculo Stewart','Octava edición',      :'cat_textbooks',  NULL,              95000,'COP','used',1,TRUE,4.598,-74.065,FALSE,TRUE,    now()-interval '4 days', now()-interval '1 days'),
 (:'L5', :'u_sebastian','Servicio: Reparación Laptop','Pasta térmica',:'cat_services',   NULL,              70000,'COP','new',10,TRUE,4.609,-74.072,FALSE,TRUE,    now()-interval '3 days', now()-interval '1 days')
ON CONFLICT (id) DO NOTHING;

-- Fotos (storage_key NOT NULL)
INSERT INTO listingphoto(id, listing_id, storage_key, image_url, width, height, created_at) VALUES
 (gen_random_uuid(), :'L1', 'listings/l1/1.jpg','https://cdn.example/listings/l1.jpg',1200,800,  now()-interval '6 days'),
 (gen_random_uuid(), :'L2', 'listings/l2/1.jpg','https://cdn.example/listings/l2.jpg',1080,1080, now()-interval '5 days'),
 (gen_random_uuid(), :'L3', 'listings/l3/1.jpg','https://cdn.example/listings/l3.jpg',1024,768,  now()-interval '4 days'),
 (gen_random_uuid(), :'L4', 'listings/l4/1.jpg','https://cdn.example/listings/l4.jpg',900,1200,  now()-interval '3 days')
ON CONFLICT DO NOTHING;

-- ======================
-- CHATS / PARTICIPANTS / MENSAJES
-- ======================
\set C1 'dddd0000-0000-0000-0000-000000000001'
\set C2 'dddd0000-0000-0000-0000-000000000002'

INSERT INTO chat(id, listing_id, created_at) VALUES
 (:'C1', :'L1', now()-interval '6 days'),
 (:'C2', :'L2', now()-interval '5 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO chatparticipant(chat_id,user_id,role,joined_at) VALUES
 (:'C1', :'u_tomas',  'seller', now()-interval '6 days'),
 (:'C1', :'u_carlos', 'buyer',  now()-interval '6 days'),
 (:'C2', :'u_carlos', 'seller', now()-interval '5 days'),
 (:'C2', :'u_juan',   'buyer',  now()-interval '5 days')
ON CONFLICT DO NOTHING;

-- message_type es enum; usamos 'text'
INSERT INTO message(id,chat_id,sender_id,message_type,content,created_at) VALUES
 (gen_random_uuid(), :'C1', :'u_carlos','text','¿Sigue disponible?', now()-interval '6 days'),
 (gen_random_uuid(), :'C1', :'u_tomas', 'text','Sí, ¿cuándo te queda bien?', now()-interval '6 days'),
 (gen_random_uuid(), :'C2', :'u_juan',  'text','¿Último precio?', now()-interval '5 days')
ON CONFLICT DO NOTHING;

-- ======================
-- ORDERS / HISTORY / PAYMENTS
-- ======================
\set O1 'eeee0000-0000-0000-0000-000000000001'
\set O2 'eeee0000-0000-0000-0000-000000000002'

INSERT INTO "order"(id,buyer_id,seller_id,listing_id,total_cents,currency,status,created_at,updated_at) VALUES
 (:'O1', :'u_carlos', :'u_tomas',  :'L1', 2500000,'COP','completed', now()-interval '5 days', now()-interval '4 days'),
 (:'O2', :'u_juan',   :'u_carlos', :'L2', 1800000,'COP','cancelled', now()-interval '4 days', now()-interval '4 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO orderstatushistory(id,order_id,from_status,to_status,reason,created_at) VALUES
 (gen_random_uuid(), :'O1', NULL,'created', NULL,                      now()-interval '5 days'),
 (gen_random_uuid(), :'O1', 'created','paid','escrow funded',         now()-interval '5 days' + interval '2 hours'),
 (gen_random_uuid(), :'O1', 'paid','completed','seller delivered OK', now()-interval '4 days'),
 (gen_random_uuid(), :'O2', NULL,'created', NULL,                     now()-interval '4 days'),
 (gen_random_uuid(), :'O2', 'created','cancelled','buyer cancelled',  now()-interval '4 days' + interval '2 hours')
ON CONFLICT DO NOTHING;

INSERT INTO payment(id,order_id,provider,provider_ref,amount_cents,status,created_at) VALUES
 (gen_random_uuid(), :'O1','mock_pay','pay-001',2500000,'captured', now()-interval '5 days'),
 (gen_random_uuid(), :'O2','mock_pay','pay-002',1800000,'cancelled', now()-interval '4 days')
ON CONFLICT DO NOTHING;

-- ======================
-- ESCROW + EVENTS (para BQ 1.2)
-- ======================
\set E1 'ffff0000-0000-0000-0000-000000000001'
\set E2 'ffff0000-0000-0000-0000-000000000002'

INSERT INTO escrow(id,order_id,provider,status,created_at,updated_at) VALUES
 (:'E1', :'O1','mock_escrow','released',  now()-interval '5 days', now()-interval '4 days'),
 (:'E2', :'O2','mock_escrow','cancelled', now()-interval '4 days', now()-interval '4 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO escrowevent(id,escrow_id,step,result,created_at) VALUES
 (gen_random_uuid(), :'E1','listing_viewed','success',  now()-interval '6 days'),
 (gen_random_uuid(), :'E1','chat_initiated','success',  now()-interval '5 days 22:00'),
 (gen_random_uuid(), :'E1','payment_made','success',    now()-interval '5 days 20:00'),
 (gen_random_uuid(), :'E2','listing_viewed','success',  now()-interval '4 days'),
 (gen_random_uuid(), :'E2','chat_initiated','cancelled',now()-interval '4 days 20:00')
ON CONFLICT DO NOTHING;

-- ======================
-- PRICE SUGGESTIONS
-- ======================
INSERT INTO pricesuggestion(id,listing_id,suggested_price_cents,algorithm,created_at) VALUES
 (gen_random_uuid(), :'L1', 2480000,'median_90d', now()-interval '7 days'),
 (gen_random_uuid(), :'L5',   70000,'median_90d', now()-interval '3 days')
ON CONFLICT DO NOTHING;

-- ======================
-- TELEMETRÍA (para BQ 1.1 y 2.x/3.x)
-- ======================
INSERT INTO event(id,event_type,user_id,session_id,listing_id,step,properties,occurred_at) VALUES
 (gen_random_uuid(),'listing.created', :'u_tomas',   's1', :'L1', NULL, '{}'::jsonb, now()-interval '7 days'),
 (gen_random_uuid(),'listing.created', :'u_carlos',  's2', :'L2', NULL, '{}'::jsonb, now()-interval '6 days'),
 (gen_random_uuid(),'listing.created', :'u_carlos',  's2', :'L3', NULL, '{}'::jsonb, now()-interval '5 days'),
 (gen_random_uuid(),'listing.created', :'u_juan',    's3', :'L4', NULL, '{}'::jsonb, now()-interval '4 days'),
 (gen_random_uuid(),'listing.created', :'u_sebastian','s1', :'L5', NULL, '{}'::jsonb, now()-interval '3 days');

-- filtros (BQ 2.2)
INSERT INTO event(id,event_type,user_id,session_id,properties,occurred_at) VALUES
 (gen_random_uuid(),'search.filter.used', :'u_carlos','s2','{"filter_type":"price"}',    now()-interval '6 days'),
 (gen_random_uuid(),'search.filter.used', :'u_carlos','s2','{"filter_type":"category"}', now()-interval '6 days'),
 (gen_random_uuid(),'search.filter.used', :'u_juan',  's3','{"filter_type":"brand"}',    now()-interval '4 days');

-- chat (BQ 2.3)
INSERT INTO event(id,event_type,user_id,session_id,chat_id,step,properties,occurred_at) VALUES
 (gen_random_uuid(),'chat.initiated', :'u_carlos','s2', :'C1', NULL, '{}'::jsonb, now()-interval '6 days'),
 (gen_random_uuid(),'chat.initiated', :'u_juan',  's3', :'C2', NULL, '{}'::jsonb, now()-interval '5 days'),
 (gen_random_uuid(),'chat.abandoned', :'u_juan',  's3', :'C2', 'after_price','{"reason":"too_expensive"}', now()-interval '5 days' + interval '1 hour');

-- checkout (BQ 2.1)
INSERT INTO event(id,event_type,user_id,session_id,order_id,step,properties,occurred_at) VALUES
 (gen_random_uuid(),'checkout.step', :'u_carlos','s2', :'O1','payment','{"abandoned":false}', now()-interval '5 days'),
 (gen_random_uuid(),'checkout.step', :'u_juan',  's3', :'O2','payment','{"abandoned":true}',  now()-interval '4 days');

-- product view mode (BQ 3.3)
INSERT INTO event(id,event_type,user_id,session_id,listing_id,properties,occurred_at) VALUES
 (gen_random_uuid(),'product.view_mode', :'u_carlos','s2', :'L1','{"mode":"quick_view"}', now()-interval '6 days'),
 (gen_random_uuid(),'product.view_mode', :'u_juan',  's3', :'L2','{"mode":"full_page"}',  now()-interval '4 days');

-- features (3.1/3.2)
INSERT INTO feature(key,name,deployed_at)
VALUES ('insights_dashboard','Insights Dashboard', now()-interval '10 days')
ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name, deployed_at=EXCLUDED.deployed_at;

INSERT INTO feature(key,name,deployed_at)
VALUES ('quick_view','Quick View Overlay', now()-interval '12 days')
ON CONFLICT (key) DO UPDATE SET name=EXCLUDED.name, deployed_at=EXCLUDED.deployed_at;

-- habilitar flags globales si faltan
INSERT INTO featureflag(feature_id,scope,enabled,created_at)
SELECT f.id,'global',true,now() FROM feature f
LEFT JOIN featureflag ff ON ff.feature_id=f.id AND ff.scope='global'
WHERE ff.id IS NULL;
