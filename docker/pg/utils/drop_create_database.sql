DROP DATABASE IF EXISTS graphedu WITH (FORCE);
CREATE DATABASE graphedu
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LOCALE_PROVIDER 'icu'
    ICU_LOCALE 'en-US'
    TEMPLATE template0
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE graphedu IS 'GraphEdu 教育平台主数据库';