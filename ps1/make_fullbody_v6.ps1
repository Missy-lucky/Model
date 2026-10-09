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

# Step 1: build a reusable 8-head fashion croquis template.
$croquis = 'model_library\proportion-template.png'
if (-not (Test-Path $croquis)) {
    Write-Host '[template] generating 8-head croquis'
    & $python $cli generate `
        --prompt 'Clean minimalist fashion design croquis template on pure white background: a full-body female figure drawn as a simple thin black outline, exactly 8 head-heights tall, standing straight in a neutral model stance with feet slightly apart and arms hanging slightly away from the body. Very small narrow oval head, long thin neck, slim shoulders, narrow waist, elongated slender legs with narrow knees and thin ankles, fashion-illustration proportions. Add eight faint thin horizontal guide lines dividing the figure into equal head units from crown to sole. Flat schematic line drawing only, no shading, no color, no face details, no clothing, no text.' `
        --model 'gpt-image-2.5-flare' `
        --size '1024x1536' `
        --quality high `
        --output-format png `
        --no-stream `
        --output $croquis
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $croquis)) {
        throw 'croquis template generation failed'
    }
}
else {
    Write-Host '[template] exists, reusing'
}

$models = @(
    @{ Label = 'M1'; Dir = 'modern-chinese';     Face = 'model_library\modern-chinese\headshoulder-flare-A.png'; Youth = 'She must look young, in her early twenties, fresh and radiant.' }
    @{ Label = 'M2'; Dir = 'korean-minimal';     Face = 'model_library\korean-minimal\headshoulder-flare-B.png'; Youth = 'Critical: she must look clearly young, early twenties, youthful fresh skin, bright girlish energy, absolutely not middle-aged, not aunt-like, not mature.' }
    @{ Label = 'M3'; Dir = 'eurasian-editorial'; Face = 'model_library\eurasian-editorial\headshoulder-flare-A.png'; Youth = 'She must look very young, 21-23, cool high-end but youthful.' }
)

$base = @(
    'Create a photorealistic standard full-body fashion model card using two references.'
    'Reference 1 (head-and-shoulders photo) supplies ONLY her face, hairstyle, age and skin tone. Do not copy its framing, head size or crop.'
    'Reference 2 (croquis template) is the mandatory body proportion blueprint: her body must match this template exactly. Her total height equals exactly 8 head units; her head is as small as in the template; waist, hip and knee positions follow the template guide lines; legs are as long and as slender as the template; shoulders as narrow as the template. The template is the law of this image.'
    'Body: tall, willowy runway model. Very slim arms, narrow shoulders, crisp collarbones, small waist, flat stomach, slim hips, long slender thighs, narrow knees, thin ankles. Never thick legs, never short legs, never a heavy silhouette.'
    'Pose: standard fashion model card stance, front view: standing tall, chin level, arms hanging naturally with a small gap from the body, feet slightly apart pointing forward, weight even.'
    'Outfit: fitted light-gray tank top and high-waisted black full-length leggings, simple black flats.'
    'Full body from head to feet fills 88 to 92 percent of the frame height, feet fully visible.'
    'Clean bright pure-white background, soft flat even store-display light, natural contact shadow, 50mm lens at chest height.'
    'Unretouched real-photo look: matte skin with visible pores, slight asymmetry, a few stray hairs. No AI look, no plastic skin, no text, no watermark.'
) -join ' '

foreach ($m in $models) {
    $out = "model_library\$($m.Dir)\fullbody-v6.png"
    Write-Host "[$($m.Label)] fullbody v6 with proportion template"
    & $python $cli edit `
        --image $m.Face `
        --image $croquis `
        --prompt ($base + ' ' + $m.Youth) `
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

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,'fullbody-v6.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_v6_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Fullbody v6 complete'
