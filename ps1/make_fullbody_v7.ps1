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

$base = @(
    'Create a standard full-body fashion model card using two references.'
    'Reference 1 (head-and-shoulders photo) defines her exact identity: same face, hair, age and skin.'
    'Reference 2 (store display photo) defines the professional fashion-model body proportion standard: very long legs, small head, high waist. Do not copy its pose, outfit, face or styling.'
    'Height, mandatory: she is noticeably tall and willowy, like a 175-180cm runway fashion model. Elongate the whole figure: longer neck, higher waist, longer slimmer legs. Her head looks small on this tall frame.'
    'Neck, mandatory: visibly long and elegant, clearly longer than in a normal snapshot; the neckline stretches, chin lifted slightly, no short thick neck.'
    'Body build: runway-fashion slim, low body fat. Very slender arms with fine wrists, narrow shoulders with crisp collarbones, visibly narrow waist, flat stomach, slim hips, slim straight thighs, narrow knees, thin ankles. Never thick legs, never a heavy silhouette.'
    'Proportions: 7.5 to 8 heads tall; hip and crotch line clearly below the vertical midpoint; legs occupy well over half of her visible height; no 1:1 split, no oversized head, no short legs.'
    'Pose: standard fashion model card stance, front view, symmetrical and neutral: standing tall, chin level, shoulders level and relaxed, arms hanging naturally with a small visible gap between each arm and the body, feet placed slightly apart about hip width pointing forward, knees relaxed, weight even on both legs.'
    'Outfit: fitted light-gray tank top and high-waisted black full-length leggings with the waistband at her natural high waist, plus simple black flats.'
    'Full body from head to feet fills 88 to 92 percent of the frame height, feet fully visible.'
    'Clean bright pure-white background, soft flat even store-display light, natural contact shadow, 50mm lens at chest height.'
    'Unretouched real-photo look: matte skin with visible pores, slight asymmetry, a few stray hairs. No AI look, no plastic skin, no text, no watermark.'
) -join ' '

$models = @(
    @{
        Label = 'M1'
        Dir = 'modern-chinese'
        Face = 'model_library\modern-chinese\headshoulder-flare-A.png'
        Extra = 'She must look young, in her early twenties, fresh and radiant.'
    },
    @{
        Label = 'M2'
        Dir = 'korean-minimal'
        Face = 'model_library\korean-minimal\headshoulder-flare-B.png'
        Extra = 'Critical: she must look clearly young, early twenties, youthful fresh skin, bright girlish energy, absolutely not middle-aged, not aunt-like, not mature.'
    }
)

foreach ($m in $models) {
    $out = "model_library\$($m.Dir)\fullbody-v7.png"
    Write-Host "[$($m.Label)] fullbody v7 tall + long neck"
    & $python $cli edit `
        --image $m.Face `
        --image 'example_library\display1.jpg' `
        --prompt ($base + ' ' + $m.Extra) `
        --model 'gpt-image-2.5-flare' `
        --size '1024x1536' `
        --quality $Quality `
        --output-format png `
        --no-stream `
        --output $out

    if (Test-Path $out) {
        & $python $checker --min-heads 7.2 --min-legs 1.6 --min-fill 0.8 $out
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[$($m.Label)] kept for visual review despite QC flags"
        }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1-v7','modern-chinese','fullbody-v7.png'),('M2-v7','korean-minimal','fullbody-v7.png'),('M3-v5','eurasian-editorial','fullbody-v5.png')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,f)).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m,f) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_v7_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Fullbody v7 complete'
