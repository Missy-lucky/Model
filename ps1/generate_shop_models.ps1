param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('eurasian', 'korean', 'modern-chinese')]
    [string]$ModelKey,

    [string]$OutputRoot = 'shop_model_raw',
    [string]$FinalRoot = 'shop_model_final',
    [ValidateSet('low', 'medium', 'high')]
    [string]$Quality = 'medium',
    [string]$StyleReference = 'example_library\display1.jpg'
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$python = 'D:\Software\Anaconda3-Software\python.exe'
$cli = 'C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py'
$env:OPENROUTER_ICU_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_ICU_API_KEY', 'User')

if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_ICU_API_KEY)) {
    throw 'OPENROUTER_ICU_API_KEY is missing'
}

$models = @{
    'eurasian' = @{
        Reference = 'model_library\eurasian-editorial\model-card-fullbody.png'
        Description = 'the exact same young adult Eurasian woman in the identity reference, with long loose chestnut hair, fresh natural features, healthy youthful skin, and a relaxed contemporary fashion presence'
        Background = 'a clean bright pure-white e-commerce background matching the display reference: white backdrop, soft even studio lighting, bright airy exposure, and a soft natural contact shadow under the feet'
    }
    'korean' = @{
        Reference = 'model_library\korean-minimal\model-card-fullbody.png'
        Description = 'the exact same adult East Asian woman in the identity reference, with a short black bob, delicate facial structure, and a clean modern Korean boutique presence'
        Background = 'a clean bright pure-white e-commerce background matching the display reference: white backdrop, soft even studio lighting, bright airy exposure, and a soft natural contact shadow under the feet'
    }
    'modern-chinese' = @{
        Reference = 'model_library\modern-chinese\model-card-fullbody.png'
        Description = 'the exact same young adult Chinese woman in the identity reference, with a loose low black ponytail, fresh oval face, clear eyes, healthy youthful skin, and a calm contemporary Eastern fashion presence'
        Background = 'a clean bright pure-white e-commerce background matching the display reference: white backdrop, soft even studio lighting, bright airy exposure, and a soft natural contact shadow under the feet'
    }
}

$products = @(
    @{
        Id = 1
        Crop = 'full'
        Garment = 'the exact black high-waisted tailored wide-leg trousers from the garment reference: same deep black fabric, clean flat front, waistband, center button and fly, belt loops, two narrow horizontal welt details, very wide straight legs, and original hem length'
        Styling = 'Pair them with a fitted white square-neck sleeveless tank tucked cleanly into the waistband and minimal black pointed shoes. Do not add a belt.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the trouser hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. The model has a believable professional fashion proportion of about 7.5 to 8 heads tall: normal head size, shoulders and hips in balance, waist above the body midpoint, long but believable legs, arms reaching naturally to mid-thigh. The trousers must occupy most of the frame, with the waistband and leg shape clearly readable.'
        Pose = 'Her torso is turned slightly three-quarter, weight resting on one leg, one hand relaxed near a pocket and the other arm hanging naturally.'
    },
    @{
        Id = 2
        Crop = 'full'
        Garment = 'the exact charcoal-black high-waisted pleated wide-leg trousers from the garment reference: same subtle textured fabric, multiple front pleats, very wide draping legs, narrow matching belt, and small rectangular gold buckle centered at the waist'
        Styling = 'Pair them with a fitted ivory sleeveless scoop-neck top tucked in so the original belt and gold buckle remain fully visible, plus minimal black leather shoes. Do not replace or cover the belt.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the trouser hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. Keep a believable 7.5 to 8 head fashion proportion with normal head size, natural shoulders, a clear waistline and long but realistic legs. The waist, pleats, belt hardware and wide-leg drape are prominent.'
        Pose = 'She is paused during a slow step, hips naturally shifted, one hand loosely near the waistband without covering the buckle, and the other arm relaxed.'
    },
    @{
        Id = 3
        Crop = 'full'
        Garment = 'the exact muted olive-green high-rise wide-leg trousers from the garment reference: same softly textured linen-like fabric, brown center button, clean fly, curved front pockets, straight wide legs, seams, and original length'
        Styling = 'Pair them with a fitted matte black sleeveless scoop-neck tank tucked into the waistband and simple dark leather flats. Do not add a belt.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the trouser hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. Keep a believable 7.5 to 8 head fashion proportion, normal head size and realistic leg length. Keep the waistband, pockets and complete relaxed leg silhouette large and unobstructed.'
        Pose = 'She stands at a gentle diagonal with relaxed shoulders and natural hip shift, one hand lightly inside a pocket and the other hand loose beside her thigh.'
    },
    @{
        Id = 4
        Crop = 'full'
        Garment = 'the exact deep indigo high-rise wide-leg jeans from the garment reference: same dark blue wash and subtle front fading, five-pocket construction, metal rivets, center fly, wide straight legs, red leather belt, and rounded rectangular silver buckle'
        Styling = 'Pair them with a fitted white ribbed scoop-neck tank tucked in and understated dark loafers. Preserve the original red belt and silver buckle exactly and keep them visible.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the jean hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. Keep a believable 7.5 to 8 head fashion proportion with normal head size and long but realistic legs. The waistband, pockets, belt, denim wash and wide legs dominate the frame.'
        Pose = 'Capture a natural walking pause with a small turn through the shoulders, one hand brushing the side seam and the other arm swinging softly.'
    },
    @{
        Id = 5
        Crop = 'three-quarter'
        Garment = 'the exact warm-ivory textured mock-neck long-sleeve top from the garment reference: same creamy tone, subtle fuzzy knit texture, relaxed straight body, low mock neck, shoulder shape, sleeve width and length, and straight hem'
        Styling = 'Pair it with simple charcoal tailored trousers. Keep the top untucked so its full hem and silhouette are visible, with minimal dark shoes outside or near the lower crop.'
        Composition = 'Use a natural three-quarter store composition in a vertical 3:4 portrait frame, from the top of the head to mid-thigh, with the entire top visible from collar through hem and both sleeves. Use a normal 50mm full-frame perspective, no wide-angle stretching, and a believable 7.5 to 8 head body proportion. Keep the head normal in size, shoulders balanced, torso natural and hands anatomically proportioned. The garment fills most of the frame while facial detail stays clear.'
        Pose = 'Her body is angled slightly, shoulders relaxed, one hand naturally adjusting the opposite cuff while the other arm falls softly.'
    },
    @{
        Id = 6
        Crop = 'three-quarter'
        Garment = 'the exact pure-white smooth mock-neck long-sleeve top from the garment reference: same clean white fine-knit jersey, moderately fitted straight silhouette, low mock neck, shoulder line, sleeve length, curved lower hem, and subtle hem stitching'
        Styling = 'Pair it with black tailored straight-leg trousers. Keep the top untucked and fully visible, with no jewelry or distracting accessories.'
        Composition = 'Use a natural three-quarter store composition in a vertical 3:4 portrait frame, from the top of the head to mid-thigh, with the full collar, torso, curved hem and both sleeves visible. Use a normal 50mm full-frame perspective, no wide-angle stretching, and a believable 7.5 to 8 head body proportion. Keep the head normal in size, shoulders balanced, torso natural and hands anatomically proportioned. The top occupies most of the frame and the face remains detailed.'
        Pose = 'She has just turned gently toward the light, one hand resting loosely near a trouser pocket and the other arm relaxed, with a natural breathing posture.'
    },
    @{
        Id = 7
        Crop = 'full'
        Garment = 'the exact muted sage-gray green layered wide-leg trousers from the garment reference: same high waist, structured skirt-like hip overlay, tied bows at both sides with long hanging ties, central seam structure, extremely wide flowing legs, diagonal lower seam details, and original length'
        Styling = 'Pair them with a fitted matte black thin-strap camisole tucked in and simple black footwear. Keep both side bows, all hanging ties and the complete layered waist construction visible.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. Keep a believable 7.5 to 8 head fashion proportion, normal head size and realistic leg length. The unusual layered waist, side ties and broad leg volume must be large and fully readable.'
        Pose = 'She stands in a fluid three-quarter stance with one foot slightly forward, one hand hovering naturally near but not covering a side tie, and the other arm relaxed.'
    },
    @{
        Id = 8
        Crop = 'full'
        Garment = 'the exact washed-black high-rise cargo wide-leg jeans from the garment reference: same black denim, bright contrast stitching, silver waist button, curved front pockets and panel seams, large flap cargo pocket on each outer thigh, very wide straight legs, and original hems'
        Styling = 'Pair them with a fitted white racer-style sleeveless tank tucked in and black low-profile shoes. Add no belt and do not obscure either cargo pocket.'
        Composition = 'Use a natural three-quarter store composition from the top of the head to just below the lower calves, leaving a small amount of breathing room above the hair and below the jean hems. Use a normal 50mm full-frame perspective at eye or waist height, with no wide-angle stretching. Keep a believable 7.5 to 8 head fashion proportion with normal head size and realistic leg length. The waistband, contrast seams, both cargo pockets and wide-leg shape are prominent.'
        Pose = 'Capture a relaxed forward step with slight movement in the shoulders, arms naturally separated from the cargo pockets, and weight visibly transferring between the legs.'
    }
)

$model = $models[$ModelKey]
$reference = Join-Path $root $model.Reference
$styleRef = Join-Path $root $StyleReference
$checker = Join-Path $root 'check_proportions.py'
$rawDir = Join-Path $root ("{0}\{1}" -f $OutputRoot, $ModelKey)
$finalDir = Join-Path $root ("{0}\{1}" -f $FinalRoot, $ModelKey)
[System.IO.Directory]::CreateDirectory($rawDir) | Out-Null
[System.IO.Directory]::CreateDirectory($finalDir) | Out-Null

if (-not (Test-Path -LiteralPath $reference)) {
    throw "Model card missing: $reference. Run .\make_model_cards.ps1 first to create the full-body model cards."
}
if (-not (Test-Path -LiteralPath $styleRef)) {
    throw "Style reference missing: $styleRef"
}

foreach ($product in $products) {
    $garmentImage = Join-Path $root ("generated_800\{0}.png" -f $product.Id)
    $output = Join-Path $rawDir ("{0}.png" -f $product.Id)

    if (Test-Path -LiteralPath $output) {
        Write-Host "[$ModelKey/$($product.Id)] exists, skipping"
        continue
    }

    $prompt = @(
        'Create a natural fashion ecommerce photograph on a clean white background that looks like a real human photographer took it for a premium clothing store, with a real adult woman wearing the garment from the first reference image.'
        "The woman must be $($model.Description). The second reference image is her official full-body model card: copy her exact identity, face, hair, age, skin character, and above all match her body proportions and head-to-body ratio exactly as shown in that card."
        'The third reference image defines only the final presentation style: white background, bright clean lighting, vertical 3:4 framing and overall commercial feel. Do not copy the person, face, hairstyle, body, pose or clothing from the third reference.'
        "Preserve $($product.Garment)."
        $product.Styling
        $product.Composition
        'Body proportion hard rules: 7.5 to 8 heads tall with a small head relative to the body, shoulders about two head-widths wide, a clearly high waistline, hip line at or just below the vertical midpoint of the body, legs visibly longer than the torso, and no five-five split, no oversized head, no short legs, no wide-angle distortion.'
        $product.Pose
        "Set the scene in $($model.Background)."
        'Her expression is alive and unforced: soft attentive eyes looking slightly beside the lens, relaxed jaw and cheeks, subtle natural facial asymmetry, and either gently parted lips or a very slight asymmetric smile.'
        'Use a human fashion photographer, a normal full-frame 50mm lens, eye-level or waist-level camera, soft window daylight, modest contrast, ordinary exposure, authentic color and natural depth of field. Preserve natural anatomy and hands. Skin should look like healthy real skin with subtle pores, faint peach fuzz and small tonal variation, matte rather than shiny. Keep an alert relaxed expression, slight facial asymmetry, and a little natural motion in the pose.'
        'Absolutely avoid an AI-generated appearance, 3D render, CGI, illustration, anime, game model, plastic skin, airbrushing, over-smoothing, perfect symmetry, doll face, studio lighting, polished retouching, HDR, oversaturation, oily or waxy skin, rigid mannequin pose, frozen catalog stare, heavy makeup, text, logos, props, jackets, bags, or extra accessories.'
    ) -join ' '

    $succeeded = $false
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        Write-Host "[$ModelKey/$($product.Id)] generating, attempt $attempt/3"
        & $python $cli edit `
            --image $garmentImage `
            --image $reference `
            --prompt $prompt `
            --model 'gpt-image-2.5-flare' `
            --image $styleRef `
            --size '1152x1536' `
            --quality $Quality `
            --output-format png `
            --stream true `
            --partial-images 2 `
            --output $output

        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $output)) {
            $succeeded = $true
            break
        }

        if ($attempt -lt 3) {
            $delay = 5 * $attempt
            Write-Host "[$ModelKey/$($product.Id)] retrying after ${delay}s"
            Start-Sleep -Seconds $delay
        }
    }

    if (-not $succeeded) {
        throw "Generation failed for $ModelKey/$($product.Id) after 3 attempts"
    }

    $qcArgs = @($checker, $output)
    if ($product.Crop -eq 'three-quarter') {
        $qcArgs = @($checker, '--min-heads', '0', '--min-legs', '0', $output)
    }
    & $python @qcArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[$ModelKey/$($product.Id)] proportion QC failed, removing and regenerating"
        Remove-Item -LiteralPath $output -Force
        $succeeded = $false
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            Write-Host "[$ModelKey/$($product.Id)] QC retry, attempt $attempt/2"
            & $python $cli edit `
                --image $garmentImage `
                --image $reference `
                --image $styleRef `
                --prompt $prompt `
                --model 'gpt-image-2.5-flare' `
                --size '1152x1536' `
                --quality $Quality `
                --output-format png `
                --no-stream `
                --output $output
            if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $output)) {
                $recheckArgs = @($checker)
                if ($product.Crop -eq 'three-quarter') { $recheckArgs += @('--min-heads', '0', '--min-legs', '0') }
                $recheckArgs += $output
                & $python @recheckArgs
                if ($LASTEXITCODE -eq 0) { $succeeded = $true; break }
            }
            if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
        }
        if (-not $succeeded) {
            throw "Proportion QC failed for $ModelKey/$($product.Id) after retries"
        }
    }

    $finalJpg = Join-Path $finalDir ("{0}.jpg" -f $product.Id)
    & $python -c "from PIL import Image; p=r'''$output'''; o=r'''$finalJpg'''; im=Image.open(p).convert('RGB').resize((900,1200), Image.LANCZOS); im.save(o, quality=92)"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $finalJpg)) {
        throw "Final export failed for $ModelKey/$($product.Id)"
    }

    Write-Host "[$ModelKey/$($product.Id)] complete"
    Start-Sleep -Seconds 1
}

Write-Host "[$ModelKey] all products complete"
