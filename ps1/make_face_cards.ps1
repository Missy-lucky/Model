param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'high'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'
$cli = 'C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py'
$env:OPENROUTER_ICU_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_ICU_API_KEY', 'User')

if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_ICU_API_KEY)) {
    throw 'OPENROUTER_ICU_API_KEY is missing'
}

$prompt = @(
    'Professional fashion model agency card photograph of the exact same woman shown in the reference image: same identity, same age, same hair type and hairline.'
    'Head-and-shoulders beauty framing: her face occupies 50 to 60 percent of the frame height, centered slightly above the middle, both shoulders visible.'
    'She looks toward the camera with a calm, confident, alive model expression: soft attentive eyes with catchlights, relaxed jaw, very slight asymmetric smile or a neutral editorial look.'
    'Clean light-gray seamless studio background, bright soft beauty lighting from a large octabox, crisp focus, matte healthy skin, subtle natural makeup with defined brows and separated lashes.'
    'She is naturally very beautiful with striking yet completely believable refined features.'
    'Keep completely realistic photography shot on an 85mm portrait lens at f/2.8: visible skin pores, fine peach fuzz, slight natural redness and tonal variation, individually drawn eyebrow hairs and eyelashes, a few natural stray hairs, slight natural facial asymmetry.'
    'Absolutely avoid an AI-generated appearance, plastic or waxy skin, airbrushing, smoothing, beauty filters, doll face, perfect symmetry, heavy makeup, CGI, 3D render, illustration, text, watermark.'
) -join ' '

$jobs = @(
    @{
        Ref = 'model_library\modern-chinese\face-reference-v3-natural.png'
        Out = 'model_library\modern-chinese\face-card.png'
        Extra = 'The woman is a young Chinese woman with a black loose low ponytail and a calm elegant presence.'
    },
    @{
        Ref = 'model_library\korean-minimal\face-reference-v3.png'
        Out = 'model_library\korean-minimal\face-card.png'
        Extra = 'The woman is a young East Asian woman with a short black bob and a delicate clean presence.'
    },
    @{
        Ref = 'model_library\eurasian-editorial\face-reference-v4-natural.png'
        Out = 'model_library\eurasian-editorial\face-card.png'
        Extra = 'The woman is a young Eurasian woman with long loose chestnut hair and a relaxed editorial presence.'
    }
)

foreach ($job in $jobs) {
    $refPath = Join-Path $root $job.Ref
    $outPath = Join-Path $root $job.Out
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
            & $python -c "import sys; sys.path.insert(0, r'$root'); import cv2, numpy as np; from check_proportions import detect_face, imread_unicode; img=imread_unicode(r'$outPath'); g=cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); f=detect_face(g); h=img.shape[0]; border=np.concatenate([img[0,:],img[-1,:],img[:,0],img[:,-1]]); bg=int(np.median(border)); ratio=0 if f is None else f[3]/h; print('face_ratio=', ratio, 'bg=', bg); sys.exit(0 if (bg>=140 and (f is None or ratio>=0.30)) else 1)"
            if ($LASTEXITCODE -eq 0) {
                $succeeded = $true
                break
            }
            Write-Host "[$($job.Out)] face-card QC failed, regenerating"
            if ($attempt -lt 3 -and (Test-Path -LiteralPath $outPath)) {
                Remove-Item -LiteralPath $outPath -Force
            }
        }
    }

    if (-not $succeeded) {
        throw "Face card failed QC after 3 attempts: $($job.Out)"
    }
    Write-Host "[$($job.Out)] complete"
}

Write-Host 'All face cards complete'
