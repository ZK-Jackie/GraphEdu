#!/usr/bin/env pwsh
<#
.SYNOPSIS
    脚本工具函数库
.DESCRIPTION
    提供可复用的工具函数，如环境变量加载等
#>

function Load-EnvFile {
    <#
    .SYNOPSIS
        加载 .env 文件到环境变量

    .DESCRIPTION
        从指定的 .env 文件中读取环境变量并设置到当前进程。
        支持注释、空行、引号包裹的值等。

    .PARAMETER Path
        .env 文件路径，默认为脚本目录下的 .env 文件

    .PARAMETER Prefix
        环境变量前缀（可选），用于区分不同来源的变量

    .EXAMPLE
        # 使用默认路径 (脚本目录下的 .env)
        Load-EnvFile

    .EXAMPLE
        # 指定自定义路径
        Load-EnvFile -Path ".env.production"

    .EXAMPLE
        # 从项目根目录加载
        Load-EnvFile -Path (Join-Path $PSScriptRoot "..\.env")
    #>
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [string]$Path = (Join-Path $PSScriptRoot ".env"),

        [Parameter()]
        [string]$Prefix = ""
    )

    # 解析相对路径
    if (!(Split-Path $Path -IsAbsolute)) {
        $Path = Join-Path $PSScriptRoot $Path
    }

    # 检查文件是否存在
    if (!(Test-Path $Path)) {
        Write-Warning "未找到 .env 文件: $Path"
        return
    }

    $loaded = 0
    $skipped = 0

    Get-Content $Path -ErrorAction SilentlyContinue | ForEach-Object {
        $line = $_.Trim()

        # 跳过空行和注释
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#') -or $line.StartsWith(';')) {
            return
        }

        # 解析 KEY=VALUE 格式
        # 支持的格式:
        # KEY=VALUE
        # KEY = VALUE
        # KEY="VALUE"
        # KEY='VALUE'
        if ($line -match '^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$') {
            $name = $matches[1]
            $value = $matches[2].Trim()

            # 移除引号 (单引号或双引号)
            if ($value -match '^["''](.*)["'']$') {
                $value = $matches[1]
            }

            # 展开变量引用 ${VAR} 或 $VAR
            $value = [regex]::Replace($value, '\$\{([A-Z_][A-Z0-9_]*)\}', {
                param($match)
                $varName = $match.Groups[1].Value
                [Environment]::GetEnvironmentVariable($varName)
            })

            # 添加前缀（如果指定）
            $envName = if ($Prefix) { "$Prefix$name" } else { $name }

            # 设置环境变量到当前进程
            [Environment]::SetEnvironmentVariable($envName, $value, "Process")
            Set-Item -Path "env:$envName" -Value $value

            $loaded++
        }
        else {
            $skipped++
        }
    }

    Write-Host "已从 $Path 加载 $loaded 个环境变量" -ForegroundColor Green

    if ($skipped -gt 0) {
        Write-Warning "跳过 $skipped 行无法解析的内容"
    }
}

function Get-EnvValue {
    <#
    .SYNOPSIS
        获取环境变量，支持默认值和必需验证

    .DESCRIPTION
        从环境变量中获取值，可以设置默认值或标记为必需。

    .PARAMETER Name
        环境变量名称

    .PARAMETER Default
        默认值，当变量不存在时返回

    .PARAMETER Required
        是否必需，如果为 $true 且变量不存在会抛出异常

    .EXAMPLE
        # 获取变量，使用默认值
        $dbHost = Get-EnvValue "DB_HOST" -Default "localhost"

    .EXAMPLE
        # 获取必需变量（不存在会报错）
        $dbPass = Get-EnvValue "DB_PASSWORD" -Required
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Name,

        [Parameter()]
        [string]$Default = "",

        [Parameter()]
        [switch]$Required
    )

    $value = [Environment]::GetEnvironmentVariable($Name)

    if ([string]::IsNullOrEmpty($value)) {
        if ($Required) {
            throw "必需的环境变量 '$Name' 未设置"
        }
        return $Default
    }

    return $value
}

# 导出函数
Export-ModuleMember -Function Load-EnvFile, Get-EnvValue