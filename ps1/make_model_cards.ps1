param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'medium'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'
$cli = 'C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py'
$checker = Join-Path $root 'check_proportions.py'
$env:OPENROUTER_ICU_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_ICU_API_KEY', 'User')

if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_ICU_API_KEY)) {
    throw 'OPENROUTER_ICU_API_KEY is missing'
}

$prompt = @(
    'Create a photorealistic full-body studio photograph of the exact same woman shown in the reference image: same face, same hairstyle, same age, same skin tone and features.'
    'She is naturally very beautiful with striking yet completely believable features: refined facial structure, expressive eyes, healthy glowing skin, and slight natural facial asymmetry that makes her look like a real person rather than a doll.'
    'She stands upright in a relaxed neutral modeling pose, facing the camera, arms hanging naturally at her sides, both feet fully visible, chin level.'
    'She wears a fitted light-gray tank top and high-waisted black full-length leggings that clearly reveal her true body shape.'
    'Enforce professional fashion-model proportions: 7.5 to 8 heads tall, small head relative to her body, shoulders about two head-widths wide, clearly high waistline, hip line at or just below the vertical midpoint of her body, and legs visibly longer than her torso.'
    'Full body from head to feet fits the frame with a small margin top and bottom.'
    'Shot with a 50mm lens at chest height with flat frontal lighting on a clean light-gray seamless studio background.'
    'Natural realistic skin with visible pores, fine peach fuzz and subtle tonal variation, matte finish, true body proportions, no retouching, no plastic AI look, no waxy or airbrushed skin, no perfect symmetry, no text, no props.'
) -join ' '

$jobs = @(
    @{
        Ref = 'model_library\modern-chinese\face-reference-v3-natural.png'
        Out = 'model_library\modern-chinese\model-card-fullbody.png'
        Extra = 'The woman is a young Chinese woman in her early twenties with a calm elegant presence.'
    },
    @{
        Ref = 'model_library\korean-minimal\face-reference-v3.png'
        Out = 'model_library\korean-minimal\model-card-fullbody.png'
        Extra = 'The woman is a young East Asian woman with a delicate clean Korean boutique presence.'
    },
    @{
        Ref = 'model_library\eurasian-editorial\face-reference-v4-natural.png'
        Out = 'model_library\eurasian-editorial\model-card-fullbody.png'
        Extra = 'The woman is a young Eurasian woman with a relaxed contemporary editorial presence.'
    }
)

foreach ($job in $jobs) {
    $preferred = Join-Path $root ((Split-Path $job.Ref -Parent) + '\face-card.png')
    $refPath = if (Test-Path -LiteralPath $preferred) { $preferred } else { Join-Path $root $job.Ref }
    $outPath = Join-Path $root $job.Out
    if (Test-Path -LiteralPath $outPath) {
        Write-Host "[$($job.Out)] exists, checking proportions"
        & $python $checker $outPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[$($job.Out)] passes QC, skipping"
            continue
        }
        Remove-Item -LiteralPath $outPath -Force
    }

    $succeeded = $false
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        Write-Host "[$($job.Out)] generating, attempt $attempt/3"
        & $python $cli edit `
            --image $refPath `
            --prompt ($prompt + ' ' + $job.Extra) `
            --model 'gpt-image-2.5-flare' `
            --size '1024x1536' `
            --quality $Quality `
            --output-format png `
            --no-stream `
            --output $outPath

        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $outPath)) {
            & $python $checker $outPath
            if ($LASTEXITCODE -eq 0) {
                $succeeded = $true
                break
            }
            Write-Host "[$($job.Out)] proportion QC failed, regenerating"
            Remove-Item -LiteralPath $outPath -Force
        }
    }

    if (-not $succeeded) {
        throw "Model card failed QC after 3 attempts: $($job.Out)"
    }
    Write-Host "[$($job.Out)] complete"
}

Write-Host 'All model cards complete'
