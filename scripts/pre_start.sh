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

# Optimized venv sync with parallel processing
optimized_venv_sync() {
    echo "**** starting venv sync to workspace... ****"

    local start_time=$(date +%s)

    # Create destination directory if it doesn't exist
    mkdir -p /workspace/venv

    # Sync critical directories first in parallel
    (
        rsync -auz --compress-level=6 --partial --inplace \
              --include="bin/python*" --include="bin/pip*" --include="bin/activate*" \
              --exclude="*" /venv/ /workspace/venv/ &

        rsync -auz --compress-level=6 --partial --inplace \
              --include="lib/python*/site-packages/***" --exclude="*" \
              /venv/ /workspace/venv/ &

        wait
    )

    # Sync remaining files
    rsync -auz --compress-level=6 --partial --inplace /venv/ /workspace/venv/

    # Remove source files
    rm -rf /venv

    # Update paths
    update_venv_paths

    # Create completion marker
    touch /workspace/venv/.sync_complete
    echo "$(date +%Y-%m-%d_%H:%M:%S)" > /workspace/venv/.sync_timestamp

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo "✅ venv sync completed in ${duration}s"
}

echo "**** checking venv sync status... ****"
if [ -d /venv ]; then
    # Check if sync should be forced
    FORCE_SYNC=false
    if [ "${FORCE_SYNC_ALL,,}" = "true" ]; then
        echo "FORCE_SYNC_ALL is enabled, forcing venv sync..."
        FORCE_SYNC=true
    fi

    # Enhanced workspace venv integrity check
    VENV_COMPLETE=false
    if [ "$FORCE_SYNC" = false ] && [ -d /workspace/venv ] && [ -f /workspace/venv/bin/python ] && [ -f /workspace/venv/bin/pip ] && [ -f /workspace/venv/bin/activate ]; then
        echo "Workspace venv appears complete, performing enhanced integrity check..."

        # Multi-point integrity verification
        INTEGRITY_CHECKS_PASSED=true

        # Check 1: Core binaries exist and are executable
        if [ ! -x /workspace/venv/bin/python ] || [ ! -x /workspace/venv/bin/pip ]; then
            echo "⚠️  Core binaries missing or not executable"
            INTEGRITY_CHECKS_PASSED=false
        fi

        # Check 2: Python version matches
        if [ -f /venv/bin/python ] && [ -f /workspace/venv/bin/python ]; then
            SOURCE_VERSION=$(/venv/bin/python --version 2>/dev/null || echo "unknown")
            DEST_VERSION=$(/workspace/venv/bin/python --version 2>/dev/null || echo "unknown")
            if [ "$SOURCE_VERSION" != "$DEST_VERSION" ]; then
                echo "⚠️  Python version mismatch: source=$SOURCE_VERSION, dest=$DEST_VERSION"
                INTEGRITY_CHECKS_PASSED=false
            fi
        fi

        # Check 3: Key packages are available
        if ! /workspace/venv/bin/python -c "import torch, numpy" 2>/dev/null; then
            echo "⚠️  Key packages (torch, numpy) not importable"
            INTEGRITY_CHECKS_PASSED=false
        fi

        # Check 4: File count comparison (quick sanity check)
        if [ -f /workspace/venv/.sync_complete ]; then
            SOURCE_COUNT=$(find /venv -type f 2>/dev/null | wc -l)
            DEST_COUNT=$(find /workspace/venv -type f 2>/dev/null | wc -l)

            # Allow 5% variance to account for small differences
            VARIANCE=$((SOURCE_COUNT / 20))
            DIFFERENCE=$((SOURCE_COUNT - DEST_COUNT))

            if [ "${DIFFERENCE#-}" -gt "$VARIANCE" ]; then
                echo "⚠️  File count difference too large: source=$SOURCE_COUNT, dest=$DEST_COUNT"
                INTEGRITY_CHECKS_PASSED=false
            fi
        fi

        if [ "$INTEGRITY_CHECKS_PASSED" = true ]; then
            echo "✅ All integrity checks passed, venv sync is complete"
            VENV_COMPLETE=true
            # Update paths just in case
            update_venv_paths
        else
            echo "⚠️  Integrity checks failed, will re-sync venv"
        fi
    fi

    # Only run optimized sync if venv is not complete
    if [ "$VENV_COMPLETE" = false ]; then
        echo "**** starting optimized venv sync - this will be much faster than the original process ****"
        if optimized_venv_sync; then
            echo "✅ Venv sync completed successfully with optimizations"
        else
            echo "❌ Optimized sync failed, falling back to original method"
            # Fallback to original sync method
            if rsync -au --remove-source-files /venv/ /workspace/venv/ && rm -rf /venv; then
                update_venv_paths
                touch /workspace/venv/.sync_complete
                echo "✅ Fallback sync completed successfully."
            else
                echo "❌ Both optimized and fallback sync failed"
                exit 1
            fi
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
        FORCE_SYNC=true
    fi

    # Check if workspace ComfyUI is already complete
    COMFYUI_COMPLETE=false
    if [ "$FORCE_SYNC" = false ] && [ -d /workspace/ComfyUI ] && [ -f /workspace/ComfyUI/main.py ] && [ -f /workspace/ComfyUI/web.py ] && [ -f /workspace/ComfyUI/requirements.txt ]; then
        if [ -f /ComfyUI/main.py ] && [ -f /workspace/ComfyUI/main.py ]; then
            SOURCE_TIME=$(stat -c%Y /ComfyUI/main.py 2>/dev/null || echo "0")
            DEST_TIME=$(stat -c%Y /workspace/ComfyUI/main.py 2>/dev/null || echo "0")
            if [ -f /workspace/ComfyUI/.sync_complete ] && [ "$SOURCE_TIME" -le "$DEST_TIME" ]; then
                COMFYUI_COMPLETE=true
            fi
        fi
    fi

    # Only run rsync if ComfyUI is not complete
    if [ "$COMFYUI_COMPLETE" = false ]; then
        echo "**** syncing ComfyUI to workspace... ****"

        SRC_MODELS="/ComfyUI/models"
        DST_MODELS="/workspace/ComfyUI/models"
        EXCLUDE_MODELS=""

        if [ -d "$DST_MODELS" ] && [ "$(ls -A "$DST_MODELS")" ]; then
            for d in "$DST_MODELS"/*/; do
                [ -d "$d" ] || continue
                folder_name=$(basename "$d")
                EXCLUDE_MODELS="$EXCLUDE_MODELS --exclude='models/$folder_name/**'"
            done
        fi

        if [ -d /workspace/ComfyUI/output ]; then
            EXCLUDE_MODELS="$EXCLUDE_MODELS --exclude='output/'"
        fi

        if rsync -auz --compress-level=6 --partial --inplace \
                  --exclude='__pycache__/' --exclude='*.pyc' --exclude='.git/' \
                  $EXCLUDE_MODELS /ComfyUI/ /workspace/ComfyUI/ && rm -rf /ComfyUI; then
            touch /workspace/ComfyUI/.sync_complete
            echo "✅ ComfyUI sync completed"
        else
            if rsync -au --remove-source-files $EXCLUDE_MODELS /ComfyUI/ /workspace/ComfyUI/ && rm -rf /ComfyUI; then
                touch /workspace/ComfyUI/.sync_complete
                echo "✅ ComfyUI sync completed"
            else
                echo "❌ ComfyUI sync failed"
                exit 1
            fi
        fi
    else
        echo "Skip: ComfyUI already synced"
    fi

else
    echo "Skip: /ComfyUI does not exist."
    if [ -d /workspace/ComfyUI ] && [ -f /workspace/ComfyUI/main.py ]; then
        touch /workspace/ComfyUI/.sync_complete
    fi
fi

# Update preset configurations from GitHub
echo "**** checking for preset configuration updates... ****"
if [ -f /scripts/preset_updater.py ]; then
    # Check if we should force preset updates
    FORCE_PRESET_UPDATE=false
    if [ "${FORCE_SYNC_ALL,,}" = "true" ]; then
        echo "FORCE_SYNC_ALL is enabled, forcing preset configuration update..."
        FORCE_PRESET_UPDATE=true
    fi

    # Run preset updater
    echo "**** updating preset configurations from GitHub... ****"
    if [ "$FORCE_PRESET_UPDATE" = "true" ]; then
        python3 /scripts/preset_updater.py update --force
    else
        python3 /scripts/preset_updater.py update
    fi
    if [ $? -eq 0 ]; then
        echo "**** preset configuration update completed successfully ****"
    else
        echo "**** preset configuration update failed, continuing with existing configuration ****"
    fi
else
    echo "**** preset updater not found, skipping configuration update ****"
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

# Unified preset download handling
echo "**** checking for preset downloads... ****"
if [ -f /scripts/unified_preset_downloader.py ]; then
    # Check if any preset download variables are set
    PRESET_VARS_SET=false

    if [ -n "${PRESET_DOWNLOAD}" ] || [ -n "${IMAGE_PRESET_DOWNLOAD}" ] || [ -n "${AUDIO_PRESET_DOWNLOAD}" ] || [ -n "${UNIFIED_PRESET_DOWNLOAD}" ]; then
        PRESET_VARS_SET=true
    fi

    if [ "$PRESET_VARS_SET" = "true" ]; then
        echo "**** downloading presets using unified downloader... ****"

        # Show environment status for debugging
        python3 /scripts/unified_preset_downloader.py status

        # Download all specified presets
        if python3 /scripts/unified_preset_downloader.py download --quiet; then
            echo "**** unified preset download completed successfully ****"
        else
            echo "**** unified preset download failed, attempting fallback to legacy scripts ****"

            # Fallback to legacy script downloads
            if [ -n "${PRESET_DOWNLOAD}" ]; then
                echo "**** downloading video presets using legacy script ****"
                /download_presets.sh --quiet "${PRESET_DOWNLOAD}"
            fi

            if [ -n "${IMAGE_PRESET_DOWNLOAD}" ]; then
                echo "**** downloading image presets using legacy script ****"
                /download_image_presets.sh --quiet "${IMAGE_PRESET_DOWNLOAD}"
            fi

            if [ -n "${AUDIO_PRESET_DOWNLOAD}" ]; then
                echo "**** downloading audio presets using legacy script ****"
                /download_audio_presets.sh --quiet "${AUDIO_PRESET_DOWNLOAD}"
            fi
        fi
    else
        echo "**** no preset download variables set, skipping downloads ****"
    fi
else
    echo "**** unified preset downloader not found, using legacy script approach ****"

    # Legacy fallback - download individual preset types
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
fi