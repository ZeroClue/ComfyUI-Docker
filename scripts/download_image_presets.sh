#!/bin/bash

WGET_OPTS="--show-progress"

if [[ "$1" == "--quiet" ]]; then
    WGET_OPTS="-q"
    shift
fi

# download_if_missing <URL> <TARGET_DIR>
download_if_missing() {
    local url="$1"
    local dest_dir="$2"

    local filename
    filename=$(basename "$url")
    local filepath="$dest_dir/$filename"

    mkdir -p "$dest_dir"

    if [ -f "$filepath" ]; then
        echo "File already exists: $filepath (skipping)"
        return
    fi

    echo "Downloading: $filename → $dest_dir"

    local tmpdir="/workspace/tmp"
    mkdir -p "$tmpdir"
    local tmpfile="$tmpdir/${filename}.part"

    if wget $WGET_OPTS -O "$tmpfile" "$url"; then
        mv -f "$tmpfile" "$filepath"
        echo "Download completed: $filepath"
    else
        echo "Download failed: $url"
        rm -f "$tmpfile"
        return 1
    fi
}

IFS=',' read -ra PRESETS <<< "$1"

echo "**** Checking image generation presets and downloading corresponding files ****"

for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        # SDXL Base Models (High Quality)
        SDXL_BASE_V1)
            echo "Preset: SDXL_BASE_V1"
            download_if_missing "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/stabilityai/sdxl-vae-fp16-fix/resolve/main/sdxl_vae_fp16_fix.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        JUGGERNAUT_XL_V8)
            echo "Preset: JUGGERNAUT_XL_V8"
            download_if_missing "https://huggingface.co/cagliostrolab/animagine-xl-3.0/resolve/main/animagine-xl-3.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        REALVIS_XL_V4)
            echo "Preset: REALVIS_XL_V4"
            download_if_missing "https://huggingface.co/SG161222/RealVisXL_V4.0/resolve/main/RealVisXL_V4.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        DREAMSHAPER_XL_V7)
            echo "Preset: DREAMSHAPER_XL_V7"
            download_if_missing "https://huggingface.co/Lykon/DreamShaper_XL_v7/resolve/main/DreamShaper_XL_v7.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        # SD 1.5 Models (Versatile)
        REALISTIC_VISION_V6)
            echo "Preset: REALISTIC_VISION_V6"
            download_if_missing "https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/realisticVision_v60B1_noVAE.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        DELIBERATE_V6)
            echo "Preset: DELIBERATE_V6"
            download_if_missing "https://huggingface.co/XpucT/Deliberate/resolve/main/Deliberate_v6.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        DREAMSHAPER_V8)
            echo "Preset: DREAMSHAPER_V8"
            download_if_missing "https://huggingface.co/Lykon/DreamShaper_8/resolve/main/DreamShaper_8_pruned.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        PROTOGEN_XL)
            echo "Preset: PROTOGEN_XL"
            download_if_missing "https://huggingface.co/darkstorm2150/Protogen_x5.8_Official_Release/resolve/main/ProtoGen_X5.8.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        # Anime/Art Style Models
        ANYTHING_V5)
            echo "Preset: ANYTHING_V5"
            download_if_missing "https://huggingface.co/ckpt/anything-v5-prerelease/resolve/main/anything-v5-prerelease.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        MEINAMIX_V12)
            echo "Preset: MEINAMIX_V12"
            download_if_missing "https://huggingface.io/Meina/MeinaMix_v12/resolve/main/MeinaMix_v12.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        COUNTERFEIT_V3)
            echo "Preset: COUNTERFEIT_V3"
            download_if_missing "https://huggingface.co/gsdf/Counterfeit-V3.0/resolve/main/Counterfeit-V3.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        # Utility Models
        SDXL_REFINER)
            echo "Preset: SDXL_REFINER"
            download_if_missing "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;

        ESRGAN_MODELS)
            echo "Preset: ESRGAN_MODELS"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus.safetensors" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus_anime_6B.safetensors" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x2plus.safetensors" "/workspace/ComfyUI/models/upscale_models"
            ;;

        INPAINTING_MODELS)
            echo "Preset: INPAINTING_MODELS"
            download_if_missing "https://huggingface.co/runwayml/stable-diffusion-inpainting/resolve/main/sd-v1-5-inpainting.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/stabilityai/stable-diffusion-xl-inpainting/resolve/main/sdxl-vae-fp16-fix.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        # Complete Workflows
        SDXL_COMPLETE_WORKFLOW)
            echo "Preset: SDXL_COMPLETE_WORKFLOW"
            download_if_missing "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/stabilityai/sdxl-vae-fp16-fix/resolve/main/sdxl_vae_fp16_fix.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        REALISTIC_COMPLETE_WORKFLOW)
            echo "Preset: REALISTIC_COMPLETE_WORKFLOW"
            download_if_missing "https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/realisticVision_v60B1_noVAE.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus.safetensors" "/workspace/ComfyUI/models/upscale_models"
            ;;

        ANIME_COMPLETE_WORKFLOW)
            echo "Preset: ANIME_COMPLETE_WORKFLOW"
            download_if_missing "https://huggingface.co/ckpt/anything-v5-prerelease/resolve/main/anything-v5-prerelease.safetensors" "/workspace/ComfyUI/models/checkpoints"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus_anime_6B.safetensors" "/workspace/ComfyUI/models/upscale_models"
            ;;

        # Qwen Image Models (Advanced 20B Parameter Models)
        QWEN_IMAGE_BASIC)
            echo "Preset: QWEN_IMAGE_BASIC (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        QWEN_IMAGE_EDIT)
            echo "Preset: QWEN_IMAGE_EDIT (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        QWEN_IMAGE_COMPLETE)
            echo "Preset: QWEN_IMAGE_COMPLETE (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        QWEN_IMAGE_CHINESE)
            echo "Preset: QWEN_IMAGE_CHINESE (ZeroClue Custom - Optimized for Chinese Text)"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;

        # Flux Image Models (State-of-the-Art 12B Parameter Models)
        FLUX_SCHNELL_BASIC)
            echo "Preset: FLUX_SCHNELL_BASIC (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/flux1-schnell.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        FLUX_DEV_BASIC)
            echo "Preset: FLUX_DEV_BASIC (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        FLUX_SCHNELL_FP8)
            echo "Preset: FLUX_SCHNELL_FP8 (ZeroClue Custom - Memory Efficient)"
            download_if_missing "https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/flux1-schnell-fp8.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        FLUX_DEV_FP8)
            echo "Preset: FLUX_DEV_FP8 (ZeroClue Custom - Memory Efficient)"
            download_if_missing "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        FLUX_COMPLETE)
            echo "Preset: FLUX_COMPLETE (ZeroClue Custom - Full Flux Collection)"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/flux1-schnell.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        FLUX_PRODUCTION)
            echo "Preset: FLUX_PRODUCTION (ZeroClue Custom - Optimized for Production)"
            download_if_missing "https://huggingface.co/Comfy-Org/flux1-schnell/resolve/main/flux1-schnell-fp8.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" "/workspace/ComfyUI/models/unet"
            download_if_missing "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "/workspace/ComfyUI/models/clip"
            download_if_missing "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/clip"
            ;;

        *)
            echo "No matching image generation preset for '${preset}', skipping."
            ;;
    esac
done

echo "**** Image generation preset download completed ****"