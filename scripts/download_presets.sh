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

echo "**** Checking presets and downloading corresponding files ****"

for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        WAINSFW_V140)
            echo "Preset: WAINSFW_V140"
            download_if_missing "https://huggingface.co/Ine007/waiNSFWIllustrious_v140/resolve/main/waiNSFWIllustrious_v140.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;
        NTRMIX_V40)
            echo "Preset: NTRMIX_V40"
            download_if_missing "https://huggingface.co/personal1802/NTRMIXillustrious-XLNoob-XL4.0/resolve/main/ntrMIXIllustriousXL_v40.safetensors" "/workspace/ComfyUI/models/checkpoints"
            ;;
        WAN22_TI2V_5B)
            echo "Preset: WAN22_TI2V_5B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_T2V_A14B)
            echo "Preset: WAN22_T2V_A14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_FP8_SCALED)
            echo "Preset: WAN22_I2V_A14B_FP8_SCALED"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_FP8_E4M3FN_SCALED_KJ)
            echo "Preset: WAN22_I2V_A14B_FP8_E4M3FN_SCALED_KJ"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_FP8_E5M2_SCALED_KJ)
            echo "Preset: WAN22_I2V_A14B_FP8_E5M2_SCALED_KJ"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e5m2_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e5m2_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q8_0)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q8_0"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q8_0.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q8_0.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q8_0.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q6_K)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q6_K"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q6_K.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q6_K.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q6_K.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q5_K_S)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q5_K_S"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q5_K_S.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q5_K_S.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q5_K_S.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q5_K_M)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q5_K_M"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q5_K_M.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q5_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q5_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q4_K_S)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q4_K_S"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q4_K_S.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q4_K_S.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q4_K_S.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_I2V_A14B_GGUF_Q4_K_M)
            echo "Preset: WAN22_I2V_A14B_GGUF_Q4_K_M"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q4_K_M.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_high_noise_14B_Q4_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_i2v_low_noise_14B_Q4_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN22_LIGHTNING_LORA)
            echo "Preset: WAN22_LIGHTNING_LORA"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan22-Lightning/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan22-Lightning/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        WAN22_NSFW_LORA)
            echo "Preset: WAN22_NSFW_LORA"
            download_if_missing "https://huggingface.co/sombi/comfyui_models/resolve/main/Wan2.2_nsfw_lora_v0.08a/NSFW-22-H-e8.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/sombi/comfyui_models/resolve/main/Wan2.2_nsfw_lora_v0.08a/NSFW-22-L-e8.safetensors" "/workspace/ComfyUI/models/loras"
            ;;
        UPSCALE_MODELS)
            echo "Preset: UPSCALE_MODELS"
            download_if_missing "https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus.safetensors" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/Kim2091/2x-AnimeSharpV4/resolve/main/2x-AnimeSharpV4_RCAN.safetensors" "/workspace/ComfyUI/models/upscale_models"
            download_if_missing "https://huggingface.co/Kim2091/2x-AnimeSharpV4/resolve/main/2x-AnimeSharpV4_Fast_RCAN_PU.safetensors" "/workspace/ComfyUI/models/upscale_models"
            ;;
        WAN22_S2V_FP8_SCALED)
            echo "Preset: WAN22_S2V_FP8_SCALED"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" "/workspace/ComfyUI/models/audio_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        # ZeroClue Custom Presets
        WAN_22_5B_TIV2)
            echo "Preset: WAN_22_5B_TIV2 (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN_22_5B_TIV2_GGUF_Q8_0)
            echo "Preset: WAN_22_5B_TIV2_GGUF_Q8_0 (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q8_0.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_ti2v_5B_Q8_0.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN_22_5B_TIV2_GGUF_Q6_K)
            echo "Preset: WAN_22_5B_TIV2_GGUF_Q6_K (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q6_K.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_ti2v_5B_Q6_K.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN_22_5B_TIV2_GGUF_Q5_K_M)
            echo "Preset: WAN_22_5B_TIV2_GGUF_Q5_K_M (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q5_K_M.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_ti2v_5B_Q5_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN_22_5B_TIV2_GGUF_Q4_K_M)
            echo "Preset: WAN_22_5B_TIV2_GGUF_Q4_K_M (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/city96/umt5-xxl-encoder-gguf/resolve/main/umt5-xxl-encoder-Q4_K_M.gguf" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/bullerwins/Wan2.2-I2V-A14B-GGUF/resolve/main/wan2.2_ti2v_5B_Q4_K_M.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        WAN_22_5B_TIV2_FP8_E4M3FN)
            echo "Preset: WAN_22_5B_TIV2_FP8_E4M3FN (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan2.2_vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        # LTX-Video Presets
        LTXV_2B_FP8_SCALED)
            echo "Preset: LTXV_2B_FP8_SCALED"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.8-distilled-fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_2B_DISTILLED_FP8)
            echo "Preset: LTXV_2B_DISTILLED_FP8"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.8-distilled-fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_2B_GGUF_Q8_0)
            echo "Preset: LTXV_2B_GGUF_Q8_0"
            download_if_missing "https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-q8_0.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_2B_GGUF_Q6_K)
            echo "Preset: LTXV_2B_GGUF_Q6_K"
            download_if_missing "https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-q6_k.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_2B_GGUF_Q4_NL)
            echo "Preset: LTXV_2B_GGUF_Q4_NL"
            download_if_missing "https://huggingface.co/calcuis/ltxv-gguf/resolve/main/ltxv-2b-0.9.8-distilled-iq4_nl.gguf" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_13B_FP8_SCALED)
            echo "Preset: LTXV_13B_FP8_SCALED"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-13b-v0.9.8-dev-fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_13B_DISTILLED_FP8)
            echo "Preset: LTXV_13B_DISTILLED_FP8"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-13b-v0.9.8-distilled-fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_UPSCALERS)
            echo "Preset: LTXV_UPSCALERS"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-temporal-upscaler-v0.9.8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-spatial-upscaler-v0.9.8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        LTXV_COMPLETE_WORKFLOW)
            echo "Preset: LTXV_COMPLETE_WORKFLOW"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.8-distilled-fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-temporal-upscaler-v0.9.8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-spatial-upscaler-v0.9.8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            ;;
        # HunyuanVideo Presets
        HUNYUAN_T2V_720P)
            echo "Preset: HUNYUAN_T2V_720P"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_t2v_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        HUNYUAN_I2V_720P_V1)
            echo "Preset: HUNYUAN_I2V_720P_V1"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_image_to_video_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors" "/workspace/ComfyUI/models/clip_vision"
            ;;
        HUNYUAN_I2V_720P_V2)
            echo "Preset: HUNYUAN_I2V_720P_V2"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_v2_replace_image_to_video_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors" "/workspace/ComfyUI/models/clip_vision"
            ;;
        HUNYUAN_COMPLETE_WORKFLOW)
            echo "Preset: HUNYUAN_COMPLETE_WORKFLOW"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_t2v_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_image_to_video_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/diffusion_models/hunyuan_video_v2_replace_image_to_video_720p_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/clip_l.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/clip_vision/llava_llama3_vision.safetensors" "/workspace/ComfyUI/models/clip_vision"
            ;;
        # Cosmos Predict2 Presets
        COSMOS_PREDICT2_V2W_480P)
            echo "Preset: COSMOS_PREDICT2_V2W_480P"
            download_if_missing "https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2b_video2world_480p_16fps.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/main/text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        COSMOS_PREDICT2_COMPLETE)
            echo "Preset: COSMOS_PREDICT2_COMPLETE"
            download_if_missing "https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2b_video2world_480p_16fps.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/main/text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        # Mochi 1 Preview Presets
        MOCHI_1_PREVIEW)
            echo "Preset: MOCHI_1_PREVIEW"
            download_if_missing "https://huggingface.co/genmo/mochi-1-preview/resolve/main/mochi_preview_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/genmo/mochi-1-preview/resolve/main/vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/text_encoders/t5xxl_fp16.safetensors" "/workspace/ComfyUI/models/text_encoders"
            ;;
        MOCHI_1_PREVIEW_FP8)
            echo "Preset: MOCHI_1_PREVIEW_FP8"
            download_if_missing "https://huggingface.co/genmo/mochi-1-preview/resolve/main/mochi_preview_fp8.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/genmo/mochi-1-preview/resolve/main/vae.safetensors" "/workspace/ComfyUI/models/vae"
            download_if_missing "https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/text_encoders/t5xxl_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/text_encoders"
            ;;
        # WAN 2.2 Specialized Workflow Presets
        WAN22_ANIMATE_14B)
            echo "Preset: WAN22_ANIMATE_14B"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_ANIMATE_WITH_LORA)
            echo "Preset: WAN22_ANIMATE_WITH_LORA"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_S2V_14B_FP8)
            echo "Preset: WAN22_S2V_14B_FP8"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" "/workspace/ComfyUI/models/audio_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_S2V_14B_BF16)
            echo "Preset: WAN22_S2V_14B_BF16"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" "/workspace/ComfyUI/models/audio_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_S2V_COMPLETE)
            echo "Preset: WAN22_S2V_COMPLETE"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" "/workspace/ComfyUI/models/audio_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_FUN_INPAINT_14B)
            echo "Preset: WAN22_FUN_INPAINT_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_FUN_INPAINT_WITH_LORA)
            echo "Preset: WAN22_FUN_INPAINT_WITH_LORA"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_FUN_CONTROL_14B)
            echo "Preset: WAN22_FUN_CONTROL_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_FUN_CONTROL_WITH_LORA)
            echo "Preset: WAN22_FUN_CONTROL_WITH_LORA"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_FUN_CAMERA_14B)
            echo "Preset: WAN22_FUN_CAMERA_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_camera_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_T2V_14B_COMPLETE)
            echo "Preset: WAN22_T2V_14B_COMPLETE"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_I2V_14B_COMPLETE)
            echo "Preset: WAN22_I2V_14B_COMPLETE"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN22_COMPLETE_WORKFLOW)
            echo "Preset: WAN22_COMPLETE_WORKFLOW"
            # Animate models
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Animate/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/stable_diffusion_3_repackaged/resolve/main/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            # S2V models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_s2v_14B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/audio_encoders/wav2vec2_large_english_fp16.safetensors" "/workspace/ComfyUI/models/audio_encoders"
            # Fun Inpainting models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_inpaint_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Fun Control models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Fun Camera model
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_fun_camera_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # T2V models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # I2V models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Lightning LoRAs
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" "/workspace/ComfyUI/models/loras"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" "/workspace/ComfyUI/models/loras"
            # Shared components
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        # WAN 2.1 Specialized Workflow Presets
        WAN21_BASE_1.3B)
            echo "Preset: WAN21_BASE_1.3B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_I2V_480P_14B)
            echo "Preset: WAN21_I2V_480P_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_I2V_720P_14B)
            echo "Preset: WAN21_I2V_720P_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_VACE_1.3B)
            echo "Preset: WAN21_VACE_1.3B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_VACE_14B)
            echo "Preset: WAN21_VACE_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_ATI_14B)
            echo "Preset: WAN21_ATI_14B"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-I2V-ATI-14B_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FLF_14B_FP16)
            echo "Preset: WAN21_FLF_14B_FP16"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_flf2v_720p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FLF_14B_FP8)
            echo "Preset: WAN21_FLF_14B_FP8"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-FLF2V-14B-720P_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_CONTROL_1.3B)
            echo "Preset: WAN21_FUN_CONTROL_1.3B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_control_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_CONTROL_14B)
            echo "Preset: WAN21_FUN_CONTROL_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-Control.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_CAMERA_1.3B)
            echo "Preset: WAN21_FUN_CAMERA_1.3B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_CAMERA_14B)
            echo "Preset: WAN21_FUN_CAMERA_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_14B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_INP_1.3B)
            echo "Preset: WAN21_FUN_INP_1.3B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_inp_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_FUN_INP_14B)
            echo "Preset: WAN21_FUN_INP_14B"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-InP.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        WAN21_COMPLETE_WORKFLOW)
            echo "Preset: WAN21_COMPLETE_WORKFLOW"
            # Base models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # VACE models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # ATI model
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-I2V-ATI-14B_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # FLF models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_flf2v_720p_14B_fp16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-FLF2V-14B-720P_fp8_e4m3fn.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Fun Control models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_control_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-Control.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Fun Camera models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_camera_v1.1_14B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Fun Inpainting models
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_fun_inp_1.3B_bf16.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/Wan2.1-Fun-14B-InP.safetensors" "/workspace/ComfyUI/models/diffusion_models"
            # Shared components
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" "/workspace/ComfyUI/models/clip_vision"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" "/workspace/ComfyUI/models/vae"
            ;;
        *)
            echo "No matching preset for '${preset}', skipping."
            ;;
    esac
done
