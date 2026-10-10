# Segmentation models

This directory is intentionally excluded from Git except for this README.

Download the lightweight ONNX model:

```powershell
Invoke-WebRequest `
  -Uri "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx" `
  -OutFile ".\LongY_Studio\assets\models\u2netp.onnx"
```

Expected MD5:

```text
8e83ca70e441ab06c318d82300c84806
```

For higher-quality but slower segmentation, `u2net.onnx` can be downloaded to the same directory and selected through `LONGY_SEGMENTATION_MODEL`.
