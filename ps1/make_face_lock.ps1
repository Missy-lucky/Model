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
    @{ Label = 'M1'; Dir = 'modern-chinese';     Body = 'model_library\modern-chinese\fullbody-v10.png';     Face = 'model_library\modern-chinese\headshoulder-flare-A.png' }
    @{ Label = 'M2'; Dir = 'korean-minimal';     Body = 'model_library\korean-minimal\fullbody-v10.png';     Face = 'model_library\korean-minimal\headshoulder-flare-B.png' }
    @{ Label = 'M3'; Dir = 'eurasian-editorial'; Body = 'model_library\eurasian-editorial\fullbody-v5.png'; Face = 'model_library\eurasian-editorial\headshoulder-flare-A.png' }
)

$prompt = @(
    'Image 1 is an approved full-body fashion model card. Image 2 is the official face reference of the same woman.'
    'Make one change only: replace the face in image 1 with the exact face from image 2, pixel-faithful to her identity: same bone structure, same eyes, same nose, same lips, same skin tone, same age, same expression, same hairline. Render the face crisp and sharp with full facial detail, no blur, no softening.'
    'Keep absolutely everything else in image 1 unchanged: same head size and head-to-body proportion, same hairstyle, same body, same height, same long legs, same slim limbs, same outfit, same pose, same framing, same pure-white background, same lighting.'
    'Unretouched real-photo look: matte skin with visible pores, slight asymmetry. No AI look, no plastic skin, no text, no watermark.'
) -join ' '

foreach ($m in $models) {
    $out = "model_library\$($m.Dir)\fullbody-final.png"
    Write-Host "[$($m.Label)] face lock"
    & $python $cli edit `
        --image $m.Body `
        --image $m.Face `
        --prompt $prompt `
        --model 'gpt-image-2.5-flare' `
        --size '1536x2304' `
        --quality $Quality `
        --output-format png `
        --no-stream `
        --output $out

    if (Test-Path $out) {
        & $python $checker --min-heads 7.4 --min-legs 1.6 --min-fill 0.8 $out
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[$($m.Label)] kept for visual review despite QC flags"
        }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1-final','modern-chinese'),('M2-final','korean-minimal'),('M3-final','eurasian-editorial')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,'fullbody-final.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_final_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Face lock complete'
