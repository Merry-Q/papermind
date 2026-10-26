param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$cleanupPlan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cleanup-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$verifiedFiles = @()
$verifiedDirs = @{}
foreach ($entry in $cleanupPlan.files) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $entry.path))
    if (-not $candidate.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "路径越出工作区: $candidate" }
    # Resolve every ancestor too: a link above a file must never redirect deletion.
    $ancestor = Split-Path -Parent $candidate
    while ($ancestor -ne $workspaceRoot) {
        if ($verifiedDirs.ContainsKey($ancestor)) { break }
        if (-not $ancestor.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "父路径越界: $ancestor" }
        if (Test-Path -LiteralPath $ancestor) {
            $ancestorInfo = Get-Item -LiteralPath $ancestor -Force
            if ($ancestorInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "拒绝链接目录: $ancestor" }
            $verifiedDirs[$ancestor] = $true
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    $info = Get-Item -LiteralPath $candidate -Force
    if ($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $info.Length -ne $entry.bytes) { throw "文件发生变化，请重新检查: $candidate" }
    $verifiedFiles += $candidate
}
if (-not $Apply) {
    Write-Output "预览：$($verifiedFiles.Count) 个文件；清单原始总大小 $([math]::Round($cleanupPlan.total_bytes/1MB,2)) MiB。"
    Write-Output '查看 cleanup-manifest.json 中的 files 字段；确认后使用 -Apply 执行。'
    return
}
foreach ($candidate in $verifiedFiles) { Remove-Item -LiteralPath $candidate -Force }
# No recursive deletion. Remove only empty directories encountered above.
foreach ($directory in ($verifiedDirs.Keys | Sort-Object Length -Descending)) {
    if ((Test-Path -LiteralPath $directory) -and -not (Get-ChildItem -LiteralPath $directory -Force | Select-Object -First 1)) {
        Remove-Item -LiteralPath $directory
    }
}
Write-Output "已删除 $($verifiedFiles.Count) 个清单文件。论文、运行数据和数据库不在删除清单内。"
