param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'high'
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

$models = @(
    @{ Label = 'M1'; Dir = 'modern-chinese';     Face = 'model_library\modern-chinese\headshoulder-flare-A.png' }
    @{ Label = 'M2'; Dir = 'korean-minimal';     Face = 'model_library\korean-minimal\headshoulder-flare-B.png' }
    @{ Label = 'M3'; Dir = 'eurasian-editorial'; Face = 'model_library\eurasian-editorial\headshoulder-flare-A.png' }
)

$prompt = @(
    'Create a standard full-body fashion model card using two references.'
    'Reference 1 (head-and-shoulders photo) defines her exact identity: same face, hair, age and skin.'
    'Reference 2 (store display photo) defines the professional fashion-model body proportion standard: very long legs, small head, high waist. Do not copy its pose, outfit, face or styling.'
    'Body build, mandatory: runway-fashion slim, low body fat like a working fashion model. Very slender arms with fine wrists, narrow shoulders but crisp collarbones, visibly narrow waist, flat stomach, slim hips. Both thighs together clearly narrower than her shoulders, narrow knees, thin ankles. Never thick legs, never muscular calves, never a heavy or stocky silhouette.'
    'Proportions, mandatory: 7.5 to 8 heads tall with a visibly small head; head width clearly less than half her shoulder width; long neck; hip and crotch line clearly below the vertical midpoint of her body; legs occupy well over half of her visible height; absolutely no 1:1 upper-lower split, no oversized head, no short legs.'
    'Pose: standard upright attention stance, front view, symmetrical: arms straight and relaxed at her sides, palms lightly against her thighs, feet together pointing forward, shoulders level, chin level, weight even on both legs.'
    'Outfit: fitted light-gray tank top and high-waisted black full-length leggings with the waistband at her natural high waist, plus simple black flats; the true body line must stay fully readable.'
    'Full body from head to feet fills 88 to 92 percent of the frame height, feet fully visible.'
    'Clean bright pure-white background, soft flat even store-display light, natural contact shadow, 50mm lens at chest height.'
    'Unretouched real-photo look: matte skin with visible pores, slight asymmetry, a few stray hairs. No AI look, no plastic skin, no text, no watermark.'
) -join ' '

foreach ($m in $models) {
    $out = "model_library\$($m.Dir)\fullbody-v4.png"
    Write-Host "[$($m.Label)] fullbody v4"
    for ($i = 1; $i -le 3; $i++) {
        & $python $cli edit `
            --image $m.Face `
            --image 'example_library\display1.jpg' `
            --prompt $prompt `
            --model 'gpt-image-2.5-flare' `
            --size '1024x1536' `
            --quality $Quality `
            --output-format png `
            --no-stream `
            --output $out
        if ($LASTEXITCODE -eq 0 -and (Test-Path $out)) {
            & $python $checker --min-heads 7.0 --min-legs 1.5 --min-fill 0.8 --max-thigh 0.95 --max-calf 0.68 $out
            if ($LASTEXITCODE -eq 0) { break }
            Write-Host "[$($m.Label)] fullbody v4 QC failed, retry $i"
            Remove-Item -LiteralPath $out -Force
        }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,'fullbody-v4.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_v4_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Fullbody v4 complete'
