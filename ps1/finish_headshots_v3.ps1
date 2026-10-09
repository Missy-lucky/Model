param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'high'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'
$cli = 'C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py'
$env:OPENROUTER_ICU_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_ICU_API_KEY', 'User')

$base = @(
    'Authentic ecommerce clothing-store display photo, head-and-shoulders framing, shot the way a real online fashion store photographs its models: clean pure-white background, large flat even soft lighting with no dramatic shadows and no glamour effect, bright airy exposure.'
    'The woman looks like a real young shop model with a natural fresh face, minimal everyday makeup, natural unstyled hair, calm pleasant approachable expression, eyes to camera, head upright and level with no tilt, both shoulders visible, shoulders about two head-widths wide, face centered slightly above the middle of the square frame.'
    'She has a slim slender fashion-model body type: thin toned arms with no visible fleshiness, defined collarbones, a clean shoulder line and slender neck.'
    'The photo should look almost unretouched and straight out of camera: real skin texture with visible pores, slight natural unevenness, faint under-eye shading, natural brows and lashes, a few stray hairs.'
    'Shot on a normal 85mm lens at f/5.6, catalog realism, not a magazine editorial, not an art portrait, no beauty dish lighting, no heavy retouching, no glamour makeup, no AI-generated look, no plastic skin, no doll face, no text, no watermark.'
) -join ' '

$jobs = @(
    @{
        Mode = 'edit'
        Ref = 'model_library\modern-chinese\headshot-v3.png'
        Out = 'model_library\modern-chinese\headshot-v4-slim.png'
        Extra = 'Keep this exact same young Chinese woman, same face, same black loose low ponytail, same pure-white background and same flat even ecommerce lighting, but make her body slim: thin toned arms with no visible fleshiness, defined collarbones, clean slender shoulder line, slender neck, and a slim fashion-model frame.'
    },
    @{
        Mode = 'edit'
        Ref = 'model_library\korean-minimal\headshot-v2.png'
        Out = 'model_library\korean-minimal\headshot-v3.png'
        Extra = 'The exact same young East Asian woman as the reference: short black bob, delicate clean presence, about 22 years old.'
    },
    @{
        Mode = 'generate'
        Ref = $null
        Out = 'model_library\eurasian-editorial\headshot-X2.png'
        Extra = 'A young Western woman, 21 years old, cool-toned Scandinavian minimalist look, soft dark-blonde straight hair, youthful fresh premium features, balanced face, light clear eyes, very good skin, calm modern high-end but young presence.'
    },
    @{
        Mode = 'generate'
        Ref = $null
        Out = 'model_library\eurasian-editorial\headshot-Y2.png'
        Extra = 'A young Western woman, 22 years old, soft light-brown long hair, fresh youthful high-fashion presence, clean balanced beautiful features, gentle hazel eyes, refined minimal aesthetic, looks expensive but never older than her age.'
    }
)

foreach ($job in $jobs) {
    $outPath = Join-Path $root $job.Out
    if (Test-Path -LiteralPath $outPath) {
        Write-Host "[$($job.Out)] exists, skipping"
        continue
    }

    $succeeded = $false
    for ($attempt = 1; $attempt -le 4; $attempt++) {
        Write-Host "[$($job.Out)] generating, attempt $attempt/4"
        $args = @($cli, $job.Mode)
        if ($job.Mode -eq 'edit') {
            $args += @('--image', (Join-Path $root $job.Ref))
        }
        $args += @(
            '--prompt', ($base + ' ' + $job.Extra),
            '--model', 'gpt-image-2.5-flare',
            '--size', '1024x1024',
            '--quality', $Quality,
            '--output-format', 'png',
            '--no-stream',
            '--output', $outPath
        )
        & $python @args
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $outPath)) {
            $succeeded = $true
            break
        }
        Start-Sleep -Seconds 30
    }

    if (-not $succeeded) {
        Write-Warning "Could not generate $($job.Out); rerun this script after the relay balance is restored"
    }
}
