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

# clone_custom_node_if_missing <URL> <TARGET_DIR>
clone_custom_node_if_missing() {
    local repo_url="$1"
    local target_dir="$2"
    local repo_name=$(basename "$repo_url" .git)

    if [ ! -d "/workspace/ComfyUI/custom_nodes/$repo_name" ]; then
        echo "Installing custom node: $repo_name"
        mkdir -p "/workspace/ComfyUI/custom_nodes"
        cd "/workspace/ComfyUI/custom_nodes"
        if git clone "$repo_url" "$repo_name"; then
            echo "Custom node $repo_name installed successfully"
            # Install requirements if present
            if [ -f "$repo_name/requirements.txt" ]; then
                pip install --no-cache-dir -r "$repo_name/requirements.txt"
            fi
            # Run install script if present
            if [ -f "$repo_name/install.py" ]; then
                cd "$repo_name"
                python install.py
            fi
        else
            echo "Failed to clone custom node: $repo_name"
        fi
    else
        echo "Custom node $repo_name already exists"
    fi
}

IFS=',' read -ra PRESETS <<< "$1"

echo "**** Checking audio generation presets and downloading corresponding files ****"

for preset in "${PRESETS[@]}"; do
    case "${preset}" in
        # Text-to-Speech Models
        BARK_BASIC)
            echo "Preset: BARK_BASIC (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/suno/bark/resolve/main/model.safetetensors" "/workspace/ComfyUI/models/TTS"
            clone_custom_node_if_missing "https://github.com/Kosinkadink/ComfyUI-ComfyUI_Custom-Scripts.git"
            ;;

        TTS_AUDIO_SUITE)
            echo "Preset: TTS_AUDIO_SUITE (ZeroClue Custom)"
            clone_custom_node_if_missing "https://github.com/diodiogod/TTS-Audio-Suite.git"
            # Basic TTS model will be downloaded via the custom node
            ;;

        PARLER_TTS)
            echo "Preset: PARLER_TTS (ZeroClue Custom)"
            clone_custom_node_if_missing "https://github.com/smthemex/ComfyUI_ParlerTTS.git"
            # Model will be downloaded via the custom node
            ;;

        # Music Generation Models
        MUSICGEN_SMALL)
            echo "Preset: MUSICGEN_SMALL (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/config.json" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/compression_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/decoder_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/enCodec_model_4cb68.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/ArtVentureX/ComfyUI-ComfyUI_Custom-Scripts.git"
            ;;

        MUSICGEN_MEDIUM)
            echo "Preset: MUSICGEN_MEDIUM (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/config.json" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/compression_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/decoder_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/enCodec_model_32khz.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/ArtVentureX/ComfyUI-ComfyUI_Custom-Scripts.git"
            ;;

        ACE_STEP)
            echo "Preset: ACE_STEP (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/LonelyNights/AceStep-Base/resolve/main/Ace-Step-v1.0.safetensors" "/workspace/ComfyUI/models/TTS"
            clone_custom_node_if_missing "https://github.com/LonelyNights/AceStep-ComfyUI-Nodes.git"
            ;;

        SONGBLOOM)
            echo "Preset: SONGBLOOM (ZeroClue Custom)"
            download_if_missing "https://huggingface.com/CookieConsistency/songbloom/resolve/main/songbloom-v1.0.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/daveshaparia724/SongBloom-ComfyUI.git"
            ;;

        # Sound Effects & Audio Processing
        STABLE_AUDIO_OPEN)
            echo "Preset: STABLE_AUDIO_OPEN (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/autoencoder.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/diffusion_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/text_encoder.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/vae.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/MoonHugo/ComfyUI-StableAudioOpen.git"
            ;;

        # Complete Audio Workflows
        AUDIO_SPEECH_COMPLETE)
            echo "Preset: AUDIO_SPEECH_COMPLETE (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/suno/bark/resolve/main/model.safetensors" "/workspace/ComfyUI/models/TTS"
            clone_custom_node_if_missing "https://github.com/diodiogod/TTS-Audio-Suite.git"
            clone_custom_node_if_missing "https://github.com/Kosinkadink/ComfyUI-ComfyUI_Custom-Scripts.git"
            ;;

        AUDIO_MUSIC_COMPLETE)
            echo "Preset: AUDIO_MUSIC_COMPLETE (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/config.json" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/compression_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/decoder_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_custom_node_if_missing "https://github.com/facebook/musicgen/resolve/main/enCodec_model_32khz.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/LonelyNights/AceStep-ComfyUI-Nodes.git"
            clone_custom_node_if_missing "https://github.com/ArtVentureX/ComfyUI-ComfyUI_Custom-Scripts.git"
            ;;

        AUDIO_PRODUCTION)
            echo "Preset: AUDIO_PRODUCTION (ZeroClue Custom)"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/autoencoder.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/diffusion_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/text_encoder.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/vae.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/suno/bark/resolve/main/model.safetensors" "/workspace/ComfyUI/models/TTS"
            download_if_missing "https://huggingface.co/facebook/musicgen-small/resolve/main/model.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/MoonHugo/ComfyUI-StableAudioOpen.git"
            clone_custom_node_if_missing "https://github.com/LonelyNights/AceStep-ComfyUI-Nodes.git"
            clone_custom_node_if_missing "https://github.com/diodiogod/TTS-Audio-Suite.git"
            ;;

        AUDIO_ALL)
            echo "Preset: AUDIO_ALL (ZeroClue Custom - Complete Audio Collection)"
            download_if_missing "https://huggingface.co/suno/bark/resolve/main/model.safetensors" "/workspace/ComfyUI/models/TTS"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/config.json" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/compression_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/decoder_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/facebook/musicgen-medium/resolve/main/enCodec_model_32khz.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/autoencoder.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/diffusion_model.safetensors" "/workspace/ComfyUI/models/audio"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/text_encoder.safetensors" "/workspace/ComfyUI/models/text_encoders"
            download_if_missing "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/vae.safetensors" "/workspace/ComfyUI/models/audio"
            clone_custom_node_if_missing "https://github.com/MoonHugo/ComfyUI-StableAudioOpen.git"
            clone_custom_node_if_missing "https://github.com/LonelyNights/AceStep-ComfyUI-Nodes.git"
            clone_custom_node_if_missing "https://github.com/diodiogod/TTS-Audio-Suite.git"
            clone_custom_node_if_missing "https://github.com/smthemex/ComfyUI_ParlerTTS.git"
            clone_custom_node_if_missing "https://github.com/Kosinkadink/ComfyUI-ComfyUI_Custom-Scripts.git"
            clone_custom_node_if_missing "https://github.com/daveshaparia724/SongBloom-ComfyUI.git"
            ;;

        *)
            echo "No matching audio generation preset for '${preset}', skipping."
            ;;
    esac
done

echo "**** Audio generation preset download completed ****"