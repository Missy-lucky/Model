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
    @{ Label = 'M1'; Dir = 'modern-chinese' }
    @{ Label = 'M2'; Dir = 'korean-minimal' }
    @{ Label = 'M3'; Dir = 'eurasian-editorial' }
)

function Invoke-Gen {
    param([string]$Image, [string]$Prompt, [string]$Out, [string]$Size, [string]$Q)
    & $python $cli edit `
        --image $Image `
        --prompt $Prompt `
        --model 'gpt-image-2.5-flare' `
        --size $Size `
        --quality $Q `
        --output-format png `
        --no-stream `
        --output $Out
}

foreach ($m in $models) {
    $display = "model_library\$($m.Dir)\display.png"
    $outFull = "model_library\$($m.Dir)\fullbody-v2.png"
    $out3d = "model_library\$($m.Dir)\model3d-v2.png"

    $pFull = @(
        'Edit the reference photo: change only her outfit to a fitted light-gray tank top and high-waisted black full-length leggings, and extend the framing slightly downward so both feet are fully visible with simple black flats.'
        'Keep everything else exactly unchanged: the same woman, same face, same hair, same body build, same height, same limb length and thickness, same shoulder width, same stance, same weight distribution, same camera height and distance, same white background and lighting.'
        'Her body proportions are already correct in the reference and must be preserved one-to-one. Do not restyle, re-pose, slim, lengthen or rebalance her body.'
        'Unretouched real-photo look: matte skin, visible pores, natural asymmetry. No AI look, no plastic skin, no text, no watermark.'
    ) -join ' '
    Write-Host "[$($m.Label)] fullbody v2 from display anchor"
    for ($i = 1; $i -le 3; $i++) {
        Invoke-Gen -Image $display -Prompt $pFull -Out $outFull -Size '1024x1536' -Q $Quality
        if ($LASTEXITCODE -eq 0 -and (Test-Path $outFull)) {
            & $python $checker --min-heads 6.5 --min-legs 1.3 --min-fill 0.75 $outFull
            if ($LASTEXITCODE -eq 0) { break }
            Write-Host "[$($m.Label)] fullbody v2 QC failed, retry $i"
            Remove-Item -LiteralPath $outFull -Force
        }
    }

    $p3d = @(
        'Convert the reference photo into a premium 3D digital-human character render while keeping the exact same woman and the exact same body: same face, same hair, same outfit, same stance, same limb length and thickness, same shoulder width, same proportions, same camera angle and framing.'
        'Change only the rendering style from photograph to high-end realistic 3D character render: skin shading with subsurface scattering, detailed hair strands, clean silhouette, soft studio HDRI lighting, neutral light-gray gradient background, subtle ground shadow.'
        'Do not change her body proportions, pose, clothing or face structure. No text, no watermark, no extra props.'
    ) -join ' '
    Write-Host "[$($m.Label)] 3D v2 from display anchor"
    Invoke-Gen -Image $display -Prompt $p3d -Out $out3d -Size '1152x1536' -Q 'medium'
}

& $python -c "from PIL import Image, ImageDraw; import os; models=[('M1','modern-chinese'),('M2','korean-minimal'),('M3','eurasian-editorial')]; kinds=[('display','DISPLAY (ANCHOR)'),('fullbody-v2','FULL BODY V2'),('model3d-v2','3D V2')]; cell=(380,540); sheet=Image.new('RGB',(cell[0]*3+48, cell[1]*3+70),'white'); d=ImageDraw.Draw(sheet); [(sheet.paste(Image.open(os.path.join('model_library',m,k+'.png')).convert('RGB').resize(cell, Image.LANCZOS),(16+x*(cell[0]+16), 30+y*(cell[1]+14))), d.text((16+x*(cell[0]+16), 8+(y*(cell[1]+14))), f'{label} {name}', fill='black')) for y,(label,m) in enumerate(models) for x,(k,name) in enumerate(kinds)]; sheet.save(os.path.join('model_library','showcase_v2_sheet.jpg'), quality=92); print('sheet saved')"

Write-Host 'Body-from-display complete'
