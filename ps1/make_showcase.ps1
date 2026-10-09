param(
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'high',
    [string]$Garment = 'generated_800\1.png',
    [string]$StyleReference = 'example_library\display1.jpg'
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

$proportion = @(
    'Full body from head to feet fills 88 to 92 percent of the frame height with small even margins.'
    'Strict professional fashion model proportions: 7.5 to 8 heads tall, small head, long neck, shoulders about two head-widths wide, high waistline, hip line at or just below the body midpoint, legs clearly longer than torso.'
    'Slim toned fashion-model body: slender arms, visible collarbones, clean shoulder line, flat waist. Never five-five split, never oversized head, never short legs, never wide-angle distortion.'
    'Shot with a 50mm lens at chest height, flat even light, natural contact shadow, no pose exaggeration.'
) -join ' '

$reality = @(
    'Real unretouched photography look: matte skin with visible pores and fine texture, slight natural facial asymmetry, a few stray hairs.'
    'Avoid AI look, plastic skin, doll face, airbrushing, beauty filter, heavy makeup, dead stare, CGI, illustration, text, watermark.'
) -join ' '

function Invoke-Gen {
    param([string[]]$Images, [string]$Prompt, [string]$Out, [string]$Size, [string]$Q)
    $args = @($cli, 'edit')
    foreach ($img in $Images) { $args += @('--image', $img) }
    $args += @('--prompt', $Prompt, '--model', 'gpt-image-2.5-flare', '--size', $Size, '--quality', $Q, '--output-format', 'png', '--no-stream', '--output', $Out)
    & $python @args
}

foreach ($m in $models) {
    $dir = Join-Path $root ("model_library\{0}" -f $m.Dir)

    # 1) Full-body model card
    $out1 = Join-Path $dir 'fullbody.png'
    $p1 = @(
        'Using the identity reference image, create a photorealistic full-body model card of the exact same woman, same face, same hair, same age, same skin.'
        'She stands upright in a relaxed neutral stance facing the camera, arms hanging naturally, both feet fully visible, no pose.'
        'She wears a fitted light-gray tank top and high-waisted black full-length leggings so her true body shape and proportions are fully readable.'
        'Clean bright pure-white studio background with soft even store-display lighting.'
        $proportion
        $reality
    ) -join ' '
    Write-Host "[$($m.Label)] fullbody"
    if (Test-Path -LiteralPath $out1) {
        Write-Host "[$($m.Label)] fullbody exists, skipping"
    } else {
        for ($i = 1; $i -le 3; $i++) {
            Invoke-Gen -Images @($m.Face) -Prompt $p1 -Out $out1 -Size '1024x1536' -Q $Quality
            if ($LASTEXITCODE -eq 0 -and (Test-Path $out1)) {
                & $python $checker --min-heads 6.8 --min-legs 1.3 --min-fill 0.8 $out1
                if ($LASTEXITCODE -eq 0) { break }
                Write-Host "[$($m.Label)] fullbody QC failed, retry $i"
                Remove-Item -LiteralPath $out1 -Force
            }
        }
    }

    # 2) Display-style shot wearing the sample garment
    $out2 = Join-Path $dir 'display.png'
    $p2 = @(
        'Create a natural ecommerce display photograph on a clean white background: the exact garment from the first reference image worn by the exact same woman from the second reference image (same face, hair, age, skin).'
        'The third reference defines only the final presentation style: white background, bright clean lighting, vertical framing, commercial feel. Do not copy the person, face, hairstyle, body, pose or clothing from the third reference.'
        'Preserve the garment exactly: black high-waisted tailored wide-leg trousers with clean flat front, waistband, center button and fly, belt loops, welt details, very wide straight legs, original hem. Pair with a fitted white square-neck sleeveless tank tucked in, minimal black shoes, no belt.'
        'Composition from top of head to just below the lower calves with small breathing room.'
        'Relaxed three-quarter stance, weight on one leg, one hand near pocket, other arm natural.'
        $proportion
        $reality
    ) -join ' '
    Write-Host "[$($m.Label)] display shot"
    if (Test-Path -LiteralPath $out2) {
        Write-Host "[$($m.Label)] display exists, skipping"
    } else {
        for ($i = 1; $i -le 3; $i++) {
            Invoke-Gen -Images @($Garment, $m.Face, $StyleReference) -Prompt $p2 -Out $out2 -Size '1152x1536' -Q $Quality
            if ($LASTEXITCODE -eq 0 -and (Test-Path $out2)) {
                & $python $checker --min-heads 6.5 --min-legs 1.25 --min-fill 0.75 $out2
                if ($LASTEXITCODE -eq 0) { break }
                Write-Host "[$($m.Label)] display QC failed, retry $i"
                Remove-Item -LiteralPath $out2 -Force
            }
        }
    }

    # 3) 3D digital-human version
    $out3 = Join-Path $dir 'model3d.png'
    $p3 = @(
        'Create a premium 3D digital-human character render of the exact same woman from the reference image: same face, same hair, same age, same skin tone, converted into a high-quality realistic 3D character model.'
        'Full body A-pose, front view, feet visible, in the same fitted light-gray tank top and high-waisted black leggings.'
        'High-end game studio character render quality: realistic skin shading with subsurface scattering, detailed hair strands, clean topology silhouette, soft studio HDRI lighting, neutral light-gray gradient background, subtle ground shadow.'
        $proportion
        'No text, no watermark, no extra props, no background elements.'
    ) -join ' '
    Write-Host "[$($m.Label)] 3D"
    if (Test-Path -LiteralPath $out3) {
        Write-Host "[$($m.Label)] 3D exists, skipping"
    } else {
        Invoke-Gen -Images @($m.Face) -Prompt $p3 -Out $out3 -Size '1024x1536' -Q 'medium'
    }
}

# Overview sheets
& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; kinds=[('fullbody','FULL BODY'),('display','DISPLAY'),('model3d','3D')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]*3+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,k+'.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30+y*(cell[1]+14))), d.text((16+x*(cell[0]+16), 8+(y*(cell[1]+14))), f'{label} {name}', fill='black')) for y,(label,m) in enumerate(models) for x,(k,name) in enumerate(kinds)]; sheet.save(os.path.join('model_library','showcase_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Showcase complete'
