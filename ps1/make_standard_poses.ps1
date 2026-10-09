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

function Invoke-Gen {
    param([string[]]$Images, [string]$Prompt, [string]$Out, [string]$Size, [string]$Q)
    $args = @($cli, 'edit')
    foreach ($img in $Images) { $args += @('--image', $img) }
    $args += @('--prompt', $Prompt, '--model', 'gpt-image-2.5-flare', '--size', $Size, '--quality', $Q, '--output-format', 'png', '--no-stream', '--output', $Out)
    & $python @args
}

foreach ($m in $models) {
    $display = "model_library\$($m.Dir)\display.png"
    $outFull = "model_library\$($m.Dir)\fullbody-v3.png"
    $out3d = "model_library\$($m.Dir)\model3d-v3.png"

    $pFull = @(
        'Create a standard full-body model card using two references.'
        'Reference 1 (head-and-shoulders photo) defines her exact identity: same face, hair, age and skin.'
        'Reference 2 (display photo of the same woman) defines ONLY her body build calibration: same height, same head size relative to body, same limb lengths and thickness, same shoulder width, same waist and hip proportions, same slim toned build. Ignore its pose, outfit and styling completely.'
        'New pose: a standard upright attention stance, front view, symmetrical: arms straight and relaxed at her sides, palms lightly against her thighs, feet together pointing forward, shoulders level, chin level, weight evenly balanced on both legs. No hand on hip, no weight shift, no walking, no lean.'
        'Outfit: fitted light-gray tank top and high-waisted black full-length leggings, simple black flats, so the true body line is fully readable.'
        'Full body from head to feet fills 88 to 92 percent of the frame height.'
        'Strict proportions: 7.5 to 8 heads tall, small head, long neck, shoulders about two head-widths wide, high waistline, hip line at or just below body midpoint, legs clearly longer than torso. Never five-five split, oversized head, short legs or wide-angle distortion.'
        'Clean bright pure-white background, soft flat even store-display light, natural contact shadow, 50mm lens at chest height.'
        'Unretouched real-photo look: matte skin with visible pores, slight asymmetry, a few stray hairs. No AI look, no plastic skin, no text, no watermark.'
    ) -join ' '
    Write-Host "[$($m.Label)] fullbody v3 standard stance"
    for ($i = 1; $i -le 3; $i++) {
        Invoke-Gen -Images @($m.Face, $display) -Prompt $pFull -Out $outFull -Size '1024x1536' -Q $Quality
        if ($LASTEXITCODE -eq 0 -and (Test-Path $outFull)) {
            & $python $checker --min-heads 6.5 --min-legs 1.3 --min-fill 0.8 $outFull
            if ($LASTEXITCODE -eq 0) { break }
            Write-Host "[$($m.Label)] fullbody v3 QC failed, retry $i"
            Remove-Item -LiteralPath $outFull -Force
        }
    }

    $p3d = @(
        'Convert this full-body photo into a premium 3D digital-human character render in standard A-pose.'
        'Keep the exact same woman: same face, same hair, same outfit, and the exact same body build: same height, head size, limb lengths and thickness, shoulder width, waist and hips.'
        'Change only the pose to a neutral A-pose, front view: arms straight, angled about 45 degrees down and away from the body, palms open and facing the camera, legs straight and slightly apart, feet pointing forward, symmetrical and balanced.'
        'High-end realistic 3D character render quality: skin shading with subsurface scattering, detailed hair strands, clean silhouette, soft studio HDRI lighting, neutral light-gray gradient background, subtle ground shadow.'
        'Do not change her body proportions or face structure. No text, no watermark, no extra props.'
    ) -join ' '
    Write-Host "[$($m.Label)] 3D v3 A-pose"
    Invoke-Gen -Images $outFull -Prompt $p3d -Out $out3d -Size '1024x1536' -Q 'medium'
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; kinds=[('display','DISPLAY'),('fullbody-v3','FULL BODY V3'),('model3d-v3','3D V3')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]*3+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,k+'.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30+y*(cell[1]+14))), d.text((16+x*(cell[0]+16), 8+(y*(cell[1]+14))), f'{label} {name}', fill='black')) for y,(label,m) in enumerate(models) for x,(k,name) in enumerate(kinds)]; sheet.save(os.path.join('model_library','showcase_v3_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Standard poses complete'
