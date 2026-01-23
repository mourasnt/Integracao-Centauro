-- Migration 0001: add nfs_json to cte_cliente
-- Run this via SQL client or use the provided Python runner script:

ALTER TABLE cte_cliente ADD COLUMN nfs_json TEXT;
