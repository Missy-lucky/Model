# Open-source options for one-click garment plan-view editing

Date: 2026-10-10

## Conclusion

"One-click image editing" programs are usually orchestration layers around an image-conditioned diffusion model. They are not implementing garment flattening with ordinary image filters. For this project, the practical open-source route is:

1. Use an image-editing model that accepts the original garment photo plus a plan-view style reference.
2. Keep deterministic preprocessing and QC in Python.
3. Expose the whole sequence as one local batch command.

The strongest current candidate is **Qwen-Image-Edit** run through **DiffSynth-Studio** or **ComfyUI**. It is designed for image-to-image editing and supports multiple reference images. It is a much closer match to the current cloud pipeline than Zhipu CogView-4, which is text-to-image only through the local proxy.

## Relevant projects

| Project | Role | Notes |
| --- | --- | --- |
| [Qwen-Image](https://github.com/QwenLM/Qwen-Image) | Open-source image generation/editing models | Official repository states that Qwen-Image is a 20B MMDiT foundation model for generation and precise editing. It links `Qwen/Qwen-Image-Edit-2511` on Hugging Face and includes Diffusers code for multi-image editing. Repository code is Apache-2.0. |
| [DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio) | Low-VRAM inference and training framework | Supports Qwen-Image and Qwen-Image-Edit, including low-VRAM inference examples, CPU/model offload, quantization, LoRA, and ControlNet-related workflows. This is the best candidate for an RTX 5070 Laptop GPU with 8GB VRAM. |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Node-based workflow engine, API, and backend | Allows a fixed workflow to be saved and invoked repeatedly. Community workflows exist for Qwen-Image-Edit and quantized GGUF models. Useful once the desired graph is tuned. |
| [AUTOMATIC1111 Stable-Diffusion-WebUI](https://github.com/AUTOMATIC1111/Stable-Diffusion-WebUI) | Classic local image-editing UI | Provides img2img and inpainting, but requires extensions/custom workflows for stable garment plan-view conversion. |
| [ControlNet](https://github.com/lllyasviel/ControlNet) | Structural conditioning for diffusion models | Canny, depth, OpenPose, and related controls can constrain garment shape. Useful with SDXL, but garment detail fidelity is weaker than modern image-editing models. |
| [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) | Image-prompt adapter | Helps preserve visual identity of a garment in SD/SDXL generation. It is not a complete garment-flattening solution by itself. |
| [IDM-VTON](https://github.com/yisol/IDM-VTON) | Virtual try-on | Strong for fitting a garment onto a person, but not directly for producing a garment-only plan-view sheet. Could be useful for auxiliary product/model images. |
| [IOPaint](https://github.com/Sanster/IOPaint) | Inpainting and object removal | Useful for removing hangers, spots, and background remnants after segmentation. Not a layout converter. |
| [Rembg](https://github.com/danielgatis/rembg) | Background removal | Useful for deterministic preprocessing and white-background composition. Does not solve flattening. |

## Why pure OpenCV failed

The rejected prototype performed segmentation, mask cleanup, geometric warping, illumination flattening, and white-background composition. It failed because a single ordinary photo does not contain the hidden garment geometry needed for a convincing flat lay:

- Sleeves or trouser legs may be occluded or folded.
- Cloth volume changes when a garment moves from a body/hanger to a flat surface.
- The reference plan view has a different silhouette and soft volume distribution.
- Exact buttons, seams, linings, and fabric details must be synthesized into regions that were not visible.

Classical warping preserves pixels but cannot reconstruct these missing regions. A diffusion image-editing model is needed for the geometry synthesis while the original image remains available as the detail authority.

## Recommended local pipeline

1. **Inventory and mapping**
   - Read `work_library/final_plan_view_mapping.csv`.
   - Deduplicate by SHA-256.
   - Skip completed outputs.

2. **Preprocess**
   - EXIF-orient and downscale the source photo.
   - Run Rembg or SAM-style segmentation.
   - Generate high-resolution detail crops.
   - Attach the approved `example_library/plan-view.png` as a style/composition reference.

3. **Image edit**
   - Primary model: Qwen-Image-Edit, ideally the latest official edit checkpoint.
   - Inputs: original garment image, plan-view reference, optional detail crops.
   - Prompt: preserve exact garment construction while laying it flat.
   - For sets, process upper garment and trousers as separate components or explicitly request separate complete pieces in one composition.

4. **Postprocess**
   - Normalize to 1536×1536.
   - Composite to a clean white canvas.
   - Preserve source-detail crops for comparison.

5. **QC**
   - Pixel checks: size, border whiteness, foreground coverage, bounds.
   - Vision QC: flat-lay score, composition similarity, garment accuracy.
   - Retry failed candidates with corrected prompt constraints.

6. **One-click interface**
   - Wrap steps 1-5 in a Python CLI.
   - Keep cache and resume state.
   - Export a contact sheet for human review.

## Hardware and storage implications

The local GPU is an RTX 5070 Laptop GPU with 8151 MiB VRAM.

- The full `Qwen/Qwen-Image-Edit-2511` repository is about 53.75GB on Hugging Face.
- A Q4_K_M GGUF transformer is about 12.4GB before adding text encoder and VAE files.
- DiffSynth-Studio's low-VRAM/offload support makes an 8GB card plausible, but inference will be slower than a cloud API.
- A practical first test should use the lowest official/quantized configuration that supports multi-image editing, then increase quality only if needed.

## Suggested pilot

Run three representative items before committing to the full library:

1. A simple single garment, such as number 172.
2. A detail-critical garment with buttons and seams.
3. A multi-piece set similar to number 389.

Compare each against the approved cloud result. If the local model matches the accepted flat-lay feeling and retains construction details, wrap the workflow into a batch script.
