#!/usr/bin/env pwsh
<#
.SYNOPSIS
    使用 pgcli 连接到 PostgreSQL 数据库
.DESCRIPTION
    从 .env 文件加载数据库配置并启动 pgcli 客户端
#>

# 导入工具函数
. "./utils.ps1"

# 加载环境变量
Load-EnvFile

# 构建数据库连接字符串（使用辅助函数，支持默认值）
$dbHost = Get-EnvValue "POSTGREQL_HOST" -Default "localhost"
$dbPort = Get-EnvValue "POSTGREQL_PORT" -Default "5432"
$dbUser = Get-EnvValue "POSTGREQL_USERNAME" -Default "postgres"
$dbPass = Get-EnvValue "POSTGREQL_PASSWORD" -Required
$dbName = Get-EnvValue "POSTGREQL_DBNAME" -Default "graphedu"

# 启动 pgcli
Write-Host "正在连接到数据库: $dbUser@$dbHost\:$dbPort/$dbName" -ForegroundColor Cyan

uvx pgcli -h $dbHost -p $dbPort -U $dbUser -d $dbName