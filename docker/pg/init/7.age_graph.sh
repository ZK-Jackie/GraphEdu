#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
BEGIN;
SET LOCAL search_path = ag_catalog, postgres, public;
SELECT ag_catalog.create_graph('edu_visualized_graph');
COMMIT;
EOSQL