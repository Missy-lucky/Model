param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'high'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'
$cli = 'C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py'
$checker = Join-Path $root 'check_proportions.py'
$faceRatio = Join-Path $root 'measure_face_ratio.py'
$env:OPENROUTER_ICU_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_ICU_API_KEY', 'User')

if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_ICU_API_KEY)) {
    throw 'OPENROUTER_ICU_API_KEY is missing'
}

$base = @(
    'Create a photorealistic standard full-body fashion model card using two references, rendered as one clean high-detail photograph.'
    'Reference 1 (head-and-shoulders photo) supplies ONLY her identity: same person, same age, same skin tone. Do not copy its framing or head size.'
    'Reference 2 (croquis template) is the mandatory body blueprint: exactly 8 head-heights tall, small head, long neck, high waist, long slender legs, narrow knees, thin ankles. Follow its proportions strictly.'
    'She is a tall willowy runway fashion model, 175-180cm presence: narrow shoulders with crisp collarbones, very slender arms, small waist, flat stomach, slim hips, slim straight thighs. Never thick legs, never heavy silhouette.'
    'Face shape: elegant slim oval egg face, cheekbone width about 75 percent of face height. The jaw narrows gently and softly with a smooth rounded chin. ABSOLUTELY NOT a pointed V-shaped cone face, not a gaunt face, not a widened round face.'
    'Pose: standard fashion model card stance, front view: standing tall, chin level, shoulders level, arms hanging naturally with a small gap from the body, feet slightly apart about hip width, weight even.'
    'Outfit: fitted light-gray tank top and high-waisted black full-length leggings, simple black flats.'
    'Full body from head to feet fills 88 to 92 percent of the frame height, feet fully visible.'
    'Clean bright pure-white background, soft flat even store-display light, natural contact shadow, 50mm lens at chest height.'
    'Image quality: crisp, sharp, high micro-detail across the whole photograph: fabric texture, skin pores, hair strands, clean edges. No blur, no softness, no haze, no watercolor smoothing.'
    'Unretouched real-photo look: matte skin, visible pores, slight asymmetry, a few stray hairs. No AI look, no plastic skin, no text, no watermark.'
) -join ' '

$models = @(
    @{
        Label = 'M1'
        Dir = 'modern-chinese'
        Face = 'model_library\modern-chinese\headshoulder-flare-A.png'
        Extra = 'Her face keeps an elegant Chinese goose-egg oval: softly tapered sides, gentle rounded jawline, refined and graceful. Slim but never pointed, never cone-shaped.'
    },
    @{
        Label = 'M2'
        Dir = 'korean-minimal'
        Face = 'model_library\korean-minimal\headshoulder-flare-B.png'
        Extra = 'Her face is a small slim Korean oval: delicate pretty features, bright youthful early-twenties look, soft fresh skin, gentle rounded jaw. Slim and pretty, never chubby, never ugly, never distorted, never cone-shaped, never aunt-like.'
    },
    @{
        Label = 'M3'
        Dir = 'eurasian-editorial'
        Face = 'model_library\eurasian-editorial\headshoulder-flare-A.png'
        Extra = 'Her Scandinavian face is naturally slim and harmonious: refined bone structure, balanced pretty features, very young 21-23, cool high-end but youthful.'
    }
)

foreach ($m in $models) {
    $out = "model_library\$($m.Dir)\fullbody-clean.png"
    Write-Host "[$($m.Label)] clean high-res regeneration"
    & $python $cli edit `
        --image $m.Face `
        --image 'model_library\proportion-template.png' `
        --prompt ($base + ' ' + $m.Extra) `
        --model 'gpt-image-2.5-flare' `
        --size '2048x3072' `
        --quality $Quality `
        --output-format png `
        --no-stream `
        --output $out

    if (Test-Path $out) {
        & $python $checker --min-heads 7.4 --min-legs 1.6 --min-fill 0.8 $out
        & $python $faceRatio $out
        if ($LASTEXITCODE -ne 0) { Write-Host "[$($m.Label)] face ratio flagged, kept for review" }
    }
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1-clean','modern-chinese'),('M2-clean','korean-minimal'),('M3-clean','eurasian-editorial')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,'fullbody-clean.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30)), d.text((16+x*(cell[0]+16), 8), label, fill='black')) for x,(label,m) in enumerate(models)]; sheet.save(os.path.join('model_library','fullbody_clean_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Clean regeneration complete'
