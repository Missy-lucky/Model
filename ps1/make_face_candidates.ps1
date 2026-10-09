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

$base = @(
    'Professional fashion ecommerce model reference photo of the exact same woman shown in the reference image: same identity, same age, same hair type.'
    'Waist-up composition in a vertical 3:4 frame: head, shoulders, chest and waist visible; head height only 20 to 25 percent of frame height; normal realistic head size; shoulders about two head-widths wide.'
    'Natural relaxed posture, shoulders down, arms relaxed, no stiff pose.'
    'Clean bright light-gray seamless studio background, soft even daylight-style beauty lighting, crisp focus on the eyes, matte healthy skin with visible pores and fine skin texture, subtle natural makeup.'
    'Real photography look shot on an 85mm lens at f/4: slight natural facial asymmetry, individually drawn eyebrows and eyelashes, a few natural stray hairs, natural catchlights in the eyes.'
    'Absolutely avoid AI-generated appearance, oversized head, plastic or waxy skin, airbrush smoothing, beauty filter, doll face, dead stare, frozen pose, CGI, 3D render, illustration, text, watermark.'
) -join ' '

$variants = @{
    'A' = 'Expression A: calm, quietly confident and present; lips relaxed and closed, eyes soft but focused right at the lens, chin level or one degree down, breathing naturally.'
    'B' = 'Expression B: candid and relaxed as if caught between poses; head turned about fifteen degrees, eyes toward the camera, the faint beginning of a genuine asymmetric smile, completely unforced.'
}

$models = @(
    @{
        Dir = 'modern-chinese'
        Ref = 'model_library\modern-chinese\face-card.png'
        Extra = 'The woman is a young Chinese woman with a black loose low ponytail and a calm elegant presence.'
    },
    @{
        Dir = 'korean-minimal'
        Ref = 'model_library\korean-minimal\face-card.png'
        Extra = 'The woman is a young East Asian woman with a short black bob and a delicate clean presence.'
    },
    @{
        Dir = 'eurasian-editorial'
        Ref = 'model_library\eurasian-editorial\face-card.png'
        Extra = 'The woman is a young Eurasian woman with long loose chestnut hair and a relaxed editorial presence; harmonious balanced attractive features.'
    }
)

foreach ($model in $models) {
    $refPath = Join-Path $root $model.Ref
    foreach ($key in @('A', 'B')) {
        $outPath = Join-Path $root ("model_library\{0}\face-candidate-{1}.png" -f $model.Dir, $key)
        $prompt = "$base $($variants[$key]) $($model.Extra)"
        $succeeded = $false

        for ($attempt = 1; $attempt -le 2; $attempt++) {
            Write-Host "[$($model.Dir)/$key] generating, attempt $attempt/2"
            & $python $cli edit `
                --image $refPath `
                --prompt $prompt `
                --model 'gpt-image-2.5-flare' `
                --size '1024x1536' `
                --quality $Quality `
                --output-format png `
                --no-stream `
                --output $outPath

            if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $outPath)) {
                & $python -c "import sys; sys.path.insert(0, r'$root'); import cv2, numpy as np; from check_proportions import detect_face, imread_unicode; img=imread_unicode(r'$outPath'); g=cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); f=detect_face(g); h=img.shape[0]; border=np.concatenate([img[0,:],img[-1,:],img[:,0],img[:,-1]]); bg=int(np.median(border)); ratio=(0 if f is None else f[3]/h); print('head_ratio=', round(ratio,3), 'bg=', bg); sys.exit(0 if (bg>=140 and (f is None or ratio<=0.34)) else 1)"
                if ($LASTEXITCODE -eq 0) {
                    $succeeded = $true
                    break
                }
                Write-Host "[$($model.Dir)/$key] candidate QC failed"
                if ($attempt -lt 2 -and (Test-Path -LiteralPath $outPath)) {
                    Remove-Item -LiteralPath $outPath -Force
                }
            }
        }

        if (-not $succeeded) {
            Write-Warning "Candidate kept for review despite QC: $outPath"
        }
    }
}

# Contact sheet: 3 rows (models) x 2 columns (A/B), labeled.
& $python -c "from PIL import Image, ImageDraw; import os; root=r'$root'; models=['modern-chinese','korean-minimal','eurasian-editorial']; labels=['M1','M2','M3']; cell=(420,630); sheet=Image.new('RGB',(cell[0]*2+36, cell[1]*3+64),'white'); d=ImageDraw.Draw(sheet); [sheet.paste(Image.open(os.path.join(root,'model_library',m,f'face-candidate-{v}.png')).resize(cell, Image.LANCZOS),(12+x*(cell[0]+12), 28+y*(cell[1]+12))) for y,m in enumerate(models) for x,v in enumerate(['A','B'])]; [(d.text((12+x*(cell[0]+12), 6+(y*(cell[1]+12))), f'{labels[y]}-{v}', fill='black'),) for y in range(3) for x,v in enumerate(['A','B'])]; sheet.save(os.path.join(root,'model_library','face_candidates_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'All candidates complete'
