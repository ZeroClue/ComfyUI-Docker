#!/bin/bash

export PYTHONUNBUFFERED=1

echo "**** Setting the timezone based on the TIME_ZONE environment variable. If not set, it defaults to Etc/UTC. ****"
export TZ=${TIME_ZONE:-"Etc/UTC"}
echo "**** Timezone set to $TZ ****"
echo "$TZ" | sudo tee /etc/timezone > /dev/null
sudo ln -sf "/usr/share/zoneinfo/$TZ" /etc/localtime
sudo dpkg-reconfigure -f noninteractive tzdata

# Update VIRTUAL_ENV paths in all text files under /workspace/venv/bin
update_venv_paths() {
    local bin_dir="/workspace/venv/bin"
    echo "Updating '/venv' to '/workspace/venv' in all text files under '$bin_dir'..."

    find "$bin_dir" -type f | while read -r file; do
        if file "$file" | grep -q "text"; then
            # VIRTUAL_ENV='/venv' → VIRTUAL_ENV='/workspace/venv'
            sed -i "s|VIRTUAL_ENV='/venv'|VIRTUAL_ENV='/workspace/venv'|g" "$file"
            
            # VIRTUAL_ENV '/venv' → VIRTUAL_ENV '/workspace/venv'
            sed -i "s|VIRTUAL_ENV '/venv'|VIRTUAL_ENV '/workspace/venv'|g" "$file"
            
            # #!/venv/bin/python → #!/workspace/venv/bin/python
            sed -i "s|#!/venv/bin/python|#!/workspace/venv/bin/python|g" "$file"

            # Uncomment to debug
            # echo "Updated: $file"
        fi
    done
}

echo "**** checking venv sync status... ****"
if [ -d /venv ]; then
    # Check if sync should be forced
    FORCE_SYNC=false
    if [ "${FORCE_SYNC_ALL,,}" = "true" ]; then
        echo "FORCE_SYNC_ALL is enabled, forcing venv sync..."
        FORCE_SYNC=true
    fi

    # Check if workspace venv is already complete
    VENV_COMPLETE=false
    if [ "$FORCE_SYNC" = false ] && [ -d /workspace/venv ] && [ -f /workspace/venv/bin/python ] && [ -f /workspace/venv/bin/pip ] && [ -f /workspace/venv/bin/activate ]; then
        echo "Workspace venv appears complete, checking if sync is needed..."

        # Quick check: compare a few key files to see if they're different
        if [ -f /venv/bin/python ] && [ -f /workspace/venv/bin/python ]; then
            # Compare file sizes as a quick integrity check
            SOURCE_SIZE=$(stat -c%s /venv/bin/python 2>/dev/null || echo "0")
            DEST_SIZE=$(stat -c%s /workspace/venv/bin/python 2>/dev/null || echo "0")

            if [ "$SOURCE_SIZE" -eq "$DEST_SIZE" ] && [ "$DEST_SIZE" -gt 0 ]; then
                echo "Venv sync appears complete, skipping rsync..."
                VENV_COMPLETE=true
                # Update paths just in case
                update_venv_paths
            fi
        fi
    fi

    # Only run rsync if venv is not complete
    if [ "$VENV_COMPLETE" = false ]; then
        echo "**** syncing venv to workspace, please wait. This could take a while on first startup! ****"
        if rsync -au --remove-source-files /venv/ /workspace/venv/ && rm -rf /venv; then
            update_venv_paths
            # Create completion marker
            touch /workspace/venv/.sync_complete
            echo "Venv sync completed successfully."
        fi
    fi
else
    echo "Skip: /venv does not exist."

    # Check if workspace venv exists and mark as complete if it does
    if [ -d /workspace/venv ] && [ -f /workspace/venv/bin/python ]; then
        touch /workspace/venv/.sync_complete
        echo "Workspace venv exists, marked as complete."
    fi
fi

echo "**** checking ComfyUI sync status... ****"
if [ -d /ComfyUI ]; then
    # Check if sync should be forced
    FORCE_SYNC=false
    if [ "${FORCE_SYNC_ALL,,}" = "true" ]; then
        echo "FORCE_SYNC_ALL is enabled, forcing ComfyUI sync..."
        FORCE_SYNC=true
    fi

    # Check if workspace ComfyUI is already complete
    COMFYUI_COMPLETE=false
    if [ "$FORCE_SYNC" = false ] && [ -d /workspace/ComfyUI ] && [ -f /workspace/ComfyUI/main.py ] && [ -f /workspace/ComfyUI/web.py ] && [ -f /workspace/ComfyUI/requirements.txt ]; then
        echo "Workspace ComfyUI appears complete, checking if sync is needed..."

        # Quick check: compare key files to see if they're different
        if [ -f /ComfyUI/main.py ] && [ -f /workspace/ComfyUI/main.py ]; then
            # Compare file modification times as a quick check
            SOURCE_TIME=$(stat -c%Y /ComfyUI/main.py 2>/dev/null || echo "0")
            DEST_TIME=$(stat -c%Y /workspace/ComfyUI/main.py 2>/dev/null || echo "0")

            # Also check for completion marker
            if [ -f /workspace/ComfyUI/.sync_complete ] && [ "$SOURCE_TIME" -le "$DEST_TIME" ]; then
                echo "ComfyUI sync appears complete, skipping rsync..."
                COMFYUI_COMPLETE=true
            fi
        fi
    fi

    # Only run rsync if ComfyUI is not complete
    if [ "$COMFYUI_COMPLETE" = false ]; then
        echo "**** syncing ComfyUI to workspace, please wait ****"

        SRC_MODELS="/ComfyUI/models"
        DST_MODELS="/workspace/ComfyUI/models"

        EXCLUDE_MODELS=""

        if [ -d "$DST_MODELS" ] && [ "$(ls -A "$DST_MODELS")" ]; then
            for d in "$DST_MODELS"/*/; do
                [ -d "$d" ] || continue
                folder_name=$(basename "$d")
                EXCLUDE_MODELS="$EXCLUDE_MODELS --exclude='models/$folder_name/**'"
            done
            echo "**** Excluding existing model folders: $EXCLUDE_MODELS ****"
        fi

        if [ -d /workspace/ComfyUI/output ]; then
            EXCLUDE_MODELS="$EXCLUDE_MODELS --exclude='output/'"
            echo "**** Excluding existing output folder ****"
        fi

        if rsync -au --remove-source-files $EXCLUDE_MODELS /ComfyUI/ /workspace/ComfyUI/ && rm -rf /ComfyUI; then
            # Create completion marker
            touch /workspace/ComfyUI/.sync_complete
            echo "ComfyUI sync completed successfully."
        fi
    fi

else
    echo "Skip: /ComfyUI does not exist."

    # Check if workspace ComfyUI exists and mark as complete if it does
    if [ -d /workspace/ComfyUI ] && [ -f /workspace/ComfyUI/main.py ]; then
        touch /workspace/ComfyUI/.sync_complete
        echo "Workspace ComfyUI exists, marked as complete."
    fi
fi


if [ "${INSTALL_SAGEATTENTION,,}" = "true" ]; then
    if pip show sageattention > /dev/null 2>&1; then
        echo "**** SageAttention2 is already installed. Skipping installation. ****"
    else
        echo "**** SageAttention2 is not installed. Installing, please wait.... (This may take a long time, approximately 5+ minutes.) ****"
        git clone https://github.com/thu-ml/SageAttention.git /SageAttention
        cd /SageAttention
        export EXT_PARALLEL=4 NVCC_APPEND_FLAGS="--threads 8" MAX_JOBS=32
        python setup.py install
        echo "**** SageAttention2 installation completed. ****"
    fi
fi

if [ "${INSTALL_CUSTOM_NODES,,}" = "true" ]; then
    if [ -f /install_custom_nodes.sh ]; then
        echo "**** INSTALL_CUSTOM_NODES is set. Running /install_custom_nodes.sh ****"
        /install_custom_nodes.sh
    else
        echo "**** /install_custom_nodes.sh not found. Skipping. ****"
    fi
fi

/download_presets.sh --quiet "${PRESET_DOWNLOAD}"

# Download image generation presets if specified
if [ -n "${IMAGE_PRESET_DOWNLOAD}" ]; then
    echo "**** IMAGE_PRESET_DOWNLOAD is set. Downloading image generation presets... ****"
    /download_image_presets.sh --quiet "${IMAGE_PRESET_DOWNLOAD}"
fi

# Download audio generation presets if specified
if [ -n "${AUDIO_PRESET_DOWNLOAD}" ]; then
    echo "**** AUDIO_PRESET_DOWNLOAD is set. Downloading audio generation presets... ****"
    /download_audio_presets.sh --quiet "${AUDIO_PRESET_DOWNLOAD}"
fi
