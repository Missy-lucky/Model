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

$slimPrompt = @(
    'Edit this photo with one precise change only: slim and narrow her face into an elegant oval egg shape.'
    'Cheekbone width becomes about 75 percent of her face height (currently about 84 percent). Gently taper the cheek sides and jawline inward; keep the same identity, same eyes, same nose, same lips, same expression, same skin, same age. The face must stay harmonious and natural, never gaunt or skeletal.'
    'Keep absolutely everything else unchanged: same head size and head-to-body proportion, same hairstyle, same body, same height, same long legs, same slim limbs, same outfit, same pose, same framing, same pure-white background, same lighting.'
    'Render the entire photograph crisp and sharp with fine detail everywhere, no blur, no softening. Unretouched real-photo look, no AI look, no text, no watermark.'
) -join ' '

$models = @(
    @{ Label = 'M1'; Dir = 'modern-chinese';     Slim = $true }
    @{ Label = 'M2'; Dir = 'korean-minimal';     Slim = $true }
    @{ Label = 'M3'; Dir = 'eurasian-editorial'; Slim = $false }
)

foreach ($m in $models) {
    $src = "model_library\$($m.Dir)\fullbody-final.png"
    $out = "model_library\$($m.Dir)\fullbody-final2.png"
    if ($m.Slim) {
        Write-Host "[$($m.Label)] narrowing face"
        & $python $cli edit `
            --image $src `
            --prompt $slimPrompt `
            --model 'gpt-image-2.5-flare' `
            --size '1536x2304' `
            --quality $Quality `
            --output-format png `
            --no-stream `
            --output $out
    }
    else {
        Copy-Item -LiteralPath $src -Destination $out
    }

    if (Test-Path $out) {
        Write-Host "[$($m.Label)] sharpening"
        & $python -c "from PIL import Image, ImageFilter; p=r'$out'; im=Image.open(p).convert('RGB'); im=im.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=2)); im.save(p)"
        & $python (Join-Path $root 'measure_face_ratio.py') $out
        if ($LASTEXITCODE -ne 0) { Write-Host "[$($m.Label)] face ratio still wide, kept for review" }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,'fullbody-final2.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_final2_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Face fix and sharpen complete'
