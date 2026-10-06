-- Schemas of the KKBox database. Run as the project role in the database `kkbox`.
--   staging   : the source files copied as they are, every column as text
--   analytics : typed tables with keys and constraints, built from staging
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
