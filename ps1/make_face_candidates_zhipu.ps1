param(
    [string]$Endpoint = 'http://127.0.0.1:15721/v1/images/generations',
    [string]$ImageModel = 'cogview-4'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'

$framing = @(
    'Professional ecommerce fashion model reference photograph, vertical 3:4 portrait, clean bright pure-white studio background with soft even light like a real clothing store display photo.'
    'Three-quarter body composition from the top of the head to mid-thigh: small head relative to a tall slim elegant frame, long neck, shoulders about two head-widths wide, high waistline and long believable legs.'
    'The head height is only 15 to 20 percent of the frame height. Never an oversized head, never a big-head effect.'
    'Slim fashion-model body: slender toned arms, visible collarbones, clean shoulder line, flat waist; not heavy, not rounded.'
    'She wears a fitted light-gray tank top and high-waisted black trousers so her true body proportions stay readable.'
    'She stands relaxed with a natural weight shift, arms comfortable, completely normal unforced posture.'
    'Real photography look on a 50mm lens at chest height: matte healthy skin with visible pores and fine texture, slight natural facial asymmetry, natural catchlights, a few stray hairs.'
    'Absolutely avoid AI-generated appearance, oversized head, plastic waxy skin, airbrushing, doll face, weird expression, dead stare, frozen pose, aged face, CGI, 3D render, illustration, text, watermark.'
) -join ' '

$variants = @{
    'A' = 'Expression: completely normal and relaxed, like a real shop model between poses; calm pleasant eyes toward the camera, lips relaxed and closed, face at rest.'
    'B' = 'Expression: soft genuine near-smile, eyes slightly warmer, like quietly greeting a customer in a nice store; light, friendly, never exaggerated.'
}

$models = @(
    @{
        Label = 'M1'
        Dir = 'modern-chinese'
        Identity = 'a young Chinese fashion model, 22-26 years old, clear oval face, open warm brow-eye area, clean bright eyes, naturally fair luminous skin, black loose low ponytail, calm elegant presence.'
    },
    @{
        Label = 'M2'
        Dir = 'korean-minimal'
        Identity = 'a young East Asian fashion model, 22-26 years old, delicate small facial structure, light refined features, translucent natural skin, short black bob haircut, clean minimal Korean boutique presence.'
    },
    @{
        Label = 'M3'
        Dir = 'eurasian-editorial'
        Identity = 'a young European / Eurasian fashion model, 21-23 years old, cool high-end but visibly young: refined elegant bone structure, harmonious balanced attractive features, luminous youthful skin, groomed natural eyebrows, minimal clean expensive-looking makeup, long straight dark-blonde to light-brown hair. Scandinavian minimalist editorial presence. Expensive and refined, never mature, never aged, never heavy makeup.'
    }
)

function Save-ZhipuImage {
    param([string]$Prompt, [string]$OutPath)
    $sizes = @('864x1152', '1024x1024')
    foreach ($size in $sizes) {
        $body = @{ model = $ImageModel; prompt = $Prompt; size = $size } | ConvertTo-Json
        try {
            $response = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 180
        }
        catch {
            Write-Host "  request failed at ${size}: $($_.Exception.Message)"
            continue
        }
        $url = $response.data[0].url
        if (-not $url) {
            Write-Host "  no image url at ${size}"
            continue
        }
        Invoke-WebRequest -Uri $url -OutFile $OutPath -TimeoutSec 180 | Out-Null
        if (Test-Path -LiteralPath $OutPath) {
            Write-Host "  generated ${size}"
            return $true
        }
    }
    return $false
}

foreach ($model in $models) {
    foreach ($key in @('A', 'B')) {
        $outPath = Join-Path $root ("model_library\{0}\candidate-z-{1}.png" -f $model.Dir, $key)
        $prompt = "$framing $($variants[$key]) Subject: $($model.Identity)"
        Write-Host "[$($model.Label)-$key] generating via Zhipu"

        for ($attempt = 1; $attempt -le 2; $attempt++) {
            if (Save-ZhipuImage -Prompt $prompt -OutPath $outPath) {
                & $python -c "import sys; sys.path.insert(0, r'$root'); import cv2, numpy as np; from check_proportions import detect_face, imread_unicode; img=imread_unicode(r'$outPath'); g=cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)); f=detect_face(g); h=img.shape[0]; border=np.concatenate([img[0,:],img[-1,:],img[:,0],img[:,-1]]); bg=int(np.median(border)); ratio=(0 if f is None else f[3]/h); print('head_ratio=', round(ratio,3), 'bg=', bg); sys.exit(0 if (bg>=150 and (f is None or ratio<=0.24)) else 1)"
                if ($LASTEXITCODE -eq 0) { break }
                Write-Host "[$($model.Label)-$key] QC failed"
                if ($attempt -lt 2 -and (Test-Path -LiteralPath $outPath)) { Remove-Item -LiteralPath $outPath -Force }
            }
        }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; root=r'$root'; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; cell=(480,640); sheet=Image.new('RGB',(cell[0]*2+36, cell[1]*3+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join(root,'model_library',m,f'candidate-z-{v}.png')).convert('RGB').resize(cell, Image.LANCZOS),(12+x*(cell[0]+12), 30+y*(cell[1]+14))), d.text((12+x*(cell[0]+12), 8+(y*(cell[1]+14))), f'{label}-{v}', fill='black')) for y,(label,m) in enumerate(models) for x,v in enumerate(['A','B'])]; sheet.save(os.path.join(root,'model_library','candidates_zhipu_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'All Zhipu candidates complete'
