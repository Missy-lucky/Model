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

$state = @(
    'Unretouched head-and-shoulders shop display photo, square composition, like a real clothing store model photo taken in-house.'
    'Her head is upright, eyes level, looking calmly at the camera; lips relaxed and closed, friendly neutral expression; no posing, no hand gestures, no head tilt, no smile.'
    'Both shoulders fully visible in frame, shoulder line level, shoulders clearly wider than the head, about 2.2 head widths.'
    'Face height about 40 to 45 percent of the frame height; the head must not look oversized.'
    'Crop from just above the hair to the upper chest; no hands, no waist, no body pose.'
    'Pure white background, very bright and clean; soft flat even lighting like a store display photo; no dramatic shadows, no rim light.'
    'Natural realistic skin: visible pores, slight uneven tone, faint under-eye shadow; no beautification, no smoothing, no glossy retouch.'
    'Looks shot on a real camera with an 85mm lens; natural slight facial asymmetry, a few natural stray hairs.'
    'Absolutely avoid AI look, plastic skin, doll face, beauty filter, heavy makeup, weird expression, dead stare, CGI, illustration, text, watermark.'
) -join ' '

$variants = @{
    'A' = 'She faces the camera straight-on with shoulders square, completely at rest.'
    'B' = 'Her body is angled about ten degrees while her face stays toward the camera; completely natural, still no pose feeling.'
}

$models = @(
    @{
        Label = 'M1'
        Dir = 'modern-chinese'
        Identity = 'a young Chinese woman, 23-25 years old, elegant goose-egg face, soft refined features, bright clear eyes, naturally fair skin with a warm undertone, black hair in a loose low ponytail, calm graceful presence.'
    },
    @{
        Label = 'M2'
        Dir = 'korean-minimal'
        Identity = 'a young Korean woman, 23-25 years old, small delicate face, gentle refined features, translucent bright natural skin, neat short black bob haircut, clean minimal boutique presence.'
    },
    @{
        Label = 'M3'
        Dir = 'eurasian-editorial'
        Identity = 'a young Northern European woman, 21-23 years old, clearly Scandinavian appearance: light grey-blue eyes, high straight nose bridge, defined brow bone, cool very-fair skin, long straight natural blonde to dark-blonde hair, minimal makeup, cool high-end but visibly young like a young Scandinavian editorial model. Not East Asian, not mixed, not mature.'
    }
)

foreach ($model in $models) {
    foreach ($key in @('A', 'B')) {
        $outPath = Join-Path $root ("model_library\{0}\headshoulder-flare-{1}.png" -f $model.Dir, $key)
        $prompt = "$state $($variants[$key]) Subject: $($model.Identity)"
        Write-Host "[$($model.Label)-$key] generating via flare"

        for ($attempt = 1; $attempt -le 2; $attempt++) {
            & $python $cli generate `
                --prompt $prompt `
                --model 'gpt-image-2.5-flare' `
                --size '1024x1024' `
                --quality $Quality `
                --output-format png `
                --no-stream `
                --output $outPath

            if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $outPath)) {
                & $python -c "import sys; sys.path.insert(0, r'$root'); import cv2, numpy as np; from check_proportions import detect_face, imread_unicode; img=imread_unicode(r'$outPath'); g=cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); f=detect_face(g); h=img.shape[0]; border=np.concatenate([img[0,:],img[-1,:],img[:,0],img[:,-1]]); bg=int(np.median(border)); ratio=(0 if f is None else f[3]/h); print('face_ratio=', round(ratio,3), 'bg=', bg); sys.exit(0 if (bg>=175 and f is not None and 0.34<=ratio<=0.52) else 1)"
                if ($LASTEXITCODE -eq 0) { break }
                Write-Host "[$($model.Label)-$key] QC failed"
                if ($attempt -lt 2 -and (Test-Path -LiteralPath $outPath)) { Remove-Item -LiteralPath $outPath -Force }
            }
        }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; root=r'$root'; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; cell=(430,430); sheet=Image.new('RGB',(cell[0]*2+36, cell[1]*3+64),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join(root,'model_library',m,f'headshoulder-flare-{v}.png')).convert('RGB').resize(cell, Image.LANCZOS),(12+x*(cell[0]+12), 28+y*(cell[1]+12))), d.text((12+x*(cell[0]+12), 8+(y*(cell[1]+12))), f'{label}-{v}', fill='black')) for y,(label,m) in enumerate(models) for x,v in enumerate(['A','B'])]; sheet.save(os.path.join(root,'model_library','headshoulder_flare_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'All flare head-shoulder cards complete'
