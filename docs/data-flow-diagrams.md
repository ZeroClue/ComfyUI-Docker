# ComfyUI-Docker Revolutionary: Data Flow Diagrams

## Overview

This document contains detailed ASCII art diagrams showing data flows through the revolutionary ComfyUI-Docker architecture.

---

## 1. Container Startup Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Container Start                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Volume Health Check (Target: 5 seconds)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Verify /workspace mount point                                       │
│     └─> If not mounted: FAIL and exit                                   │
│                                                                          │
│  2. Test write access                                                   │
│     └─> Create /workspace/.write_test                                   │
│     └─> If fails: FAIL and exit                                        │
│     └─> Remove test file                                               │
│                                                                          │
│  3. Create directory structure                                         │
│     ├─> /workspace/models/checkpoints/                                 │
│     ├─> /workspace/models/text_encoders/                               │
│     ├─> /workspace/models/vae/                                         │
│     ├─> /workspace/models/clip_vision/                                 │
│     ├─> /workspace/models/loras/                                       │
│     ├─> /workspace/output/                                             │
│     ├─> /workspace/workflows/                                          │
│     ├─> /workspace/uploads/                                            │
│     └─> /workspace/config/                                             │
│                                                                          │
│  4. Check network volume connectivity                                   │
│     └─> Verify RunPod network volume is accessible                     │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ [PASS]
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Configuration Generation (Target: 3 seconds)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Generate extra_model_paths.yaml                                    │
│     ├─> Run /app/tools/generate_extra_paths.py                         │
│     ├─> Read model path mappings                                       │
│     ├─> Create YAML configuration                                      │
│     └─> Write to /workspace/ComfyUI/models/extra_model_paths.yaml      │
│                                                                          │
│  2. Validate configuration                                             │
│     ├─> Parse YAML file                                                │
│     ├─> Check all model paths exist                                    │
│     └─> If invalid: FAIL and exit                                      │
│                                                                          │
│  3. Create legacy compatibility symlinks (optional)                     │
│     ├─> Link /app/comfyui/ComfyUI/models/checkpoints                    │
│     │       -> /workspace/models/checkpoints                           │
│     ├─> Link /app/comfyui/ComfyUI/models/text_encoders                  │
│     │       -> /workspace/models/text_encoders                         │
│     └─> (Repeat for all model types)                                   │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ [PASS]
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Service Initialization (Target: 15 seconds)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Start Nginx (2 seconds)                                            │
│     ├─> Load configuration from /etc/nginx/nginx.conf                  │
│     ├─> Start listening on ports 80, 443                               │
│     └─> Verify nginx is running                                        │
│                                                                          │
│  2. Start ComfyUI (8 seconds)                                          │
│     ├─> cd /app/comfyui/ComfyUI                                        │
│     ├─> Execute: python main.py --listen 0.0.0.0 --port 3000           │
│     ├─> Load extra_model_paths.yaml                                   │
│     ├─> Initialize custom nodes                                        │
│     ├─> Start WebSocket server                                         │
│     └─> Wait for HTTP response on /system_stats                       │
│                                                                          │
│  3. Start Dashboard FastAPI (3 seconds)                                │
│     ├─> cd /app/dashboard                                              │
│     ├─> Execute: uvicorn api.main:app --host 0.0.0.0 --port 8080       │
│     ├─> Load API routes                                               │
│     ├─> Initialize WebSocket server                                    │
│     └─> Wait for HTTP response on /health                             │
│                                                                          │
│  4. Start Preset Manager (2 seconds)                                   │
│     ├─> Load presets.yaml from /workspace/config/                     │
│     ├─> Initialize download orchestrator                              │
│     └─> Register with dashboard API                                    │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ [PASS]
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Health Checks (Target: 5 seconds)                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Dashboard Health Check                                             │
│     ├─> GET http://localhost:8080/health                               │
│     └─> Expect 200 OK with status: "healthy"                           │
│                                                                          │
│  2. ComfyUI Health Check                                               │
│     ├─> GET http://localhost:3000/system_stats                         │
│     └─> Expect 200 OK with system statistics                          │
│                                                                          │
│  3. Volume Health Check                                                │
│     ├─> Verify /workspace is still mounted                            │
│     └─> Test write access                                              │
│                                                                          │
│  4. Service Connectivity Check                                         │
│     ├─> Verify Dashboard -> ComfyUI connection                         │
│     └─> Check WebSocket endpoints                                      │
│                                                                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ [ALL PASS]
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           READY STATE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ✓ Startup complete in <30 seconds                                     │
│  ✓ Dashboard accessible at http://localhost:8080                      │
│  ✓ ComfyUI accessible at http://localhost:3000                        │
│  ✓ All services healthy                                               │
│  ✓ Network volume mounted and ready                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Preset Installation Flow

```
┌──────────────────┐
│ User clicks      │
│ "Install Preset" │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Frontend (htmx)                                               │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Capture user interaction                                           │
│  2. Send POST request to /api/presets/{id}/install                     │
│  3. Show loading indicator                                             │
│  4. Open WebSocket connection for progress updates                     │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ POST /api/presets/{id}/install
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard FastAPI Backend                                              │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Receive installation request                                       │
│  2. Validate preset ID exists                                          │
│  3. Check if already installed                                         │
│  4. Verify sufficient disk space                                       │
│  5. Create download task                                               │
│  6. Return download ID to client                                       │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ Queue background task
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Download Orchestrator (Background Task)                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Parse Preset Configuration                                         │
│     ├─> Load /workspace/config/presets.yaml                           │
│     ├─> Extract preset files list                                     │
│     ├─> Validate all URLs                                              │
│     └─> Calculate total download size                                 │
│                                                                          │
│  2. Create Download Queue                                               │
│     ├─> Prioritize files by dependencies                              │
│     ├─> Text encoders first (needed for most models)                  │
│     ├─> Checkpoints second                                             │
│     ├─> VAE models third                                               │
│     └─> Auxiliary files last                                          │
│                                                                          │
│  3. Execute Downloads (async)                                          │
│     │                                                                   │
│     ├─> For each file in queue:                                       │
│     │   ├─> Determine download source (HuggingFace, direct URL)       │
│     │   ├─> Create target directory structure                        │
│     │   ├─> Start async download with progress tracking               │
│     │   ├─> Update progress via WebSocket                            │
│     │   ├─> Verify checksum if available                             │
│     │   └─> Mark file as complete                                    │
│     │                                                                   │
│     └─> Handle errors:                                                 │
│         ├─> Retry failed downloads (3 attempts)                       │
│         ├─> Pause on network errors                                   │
│         └─> Report completion status                                  │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ WebSocket Updates
                             │ (Real-time progress)
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ WebSocket Broadcast                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Progress Update Messages (sent every 1 second):                       │
│  {                                                                      │
│    "type": "download_progress",                                        │
│    "data": {                                                            │
│      "download_id": "dl_123456",                                       │
│      "preset_id": "WAN_22_5B_TIV2",                                   │
│      "progress": 45.2,                                                 │
│      "current_file": "checkpoints/wan21.safetensors",                 │
│      "speed": "125 MB/s",                                              │
│      "eta": "2m 30s",                                                  │
│      "files": {"total": 5, "completed": 2}                            │
│    }                                                                    │
│  }                                                                      │
│                                                                          │
│  Completion Message:                                                    │
│  {                                                                      │
│    "type": "download_complete",                                        │
│    "data": {                                                            │
│      "download_id": "dl_123456",                                       │
│      "preset_id": "WAN_22_5B_TIV2",                                   │
│      "status": "success",                                              │
│      "time_taken_seconds": 300                                        │
│    }                                                                    │
│  }                                                                      │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ Update UI
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Frontend (htmx + Alpine.js)                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Receive WebSocket message                                          │
│  2. Update progress bar                                                 │
│  3. Show current file downloading                                      │
│  4. Display download speed and ETA                                      │
│  5. On completion:                                                      │
│     ├─> Hide progress indicator                                        │
│     ├─> Show success notification                                      │
│     ├─> Update preset status to "Installed"                           │
│     └─> Enable workflow buttons for this preset                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workflow Execution Flow

```
┌──────────────────┐
│ User submits     │
│ workflow         │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Frontend                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Validate workflow JSON structure                                   │
│  2. Check all required models are installed                            │
│  3. Verify input parameters                                            │
│  4. Show validation errors if any                                      │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ POST /api/comfyui/execute
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard FastAPI Backend                                              │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Receive workflow execution request                                 │
│  2. Validate workflow format                                           │
│  3. Check model availability                                           │
│  4. Transform workflow to ComfyUI format                               │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ Forward to ComfyUI
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ ComfyUI Bridge (Dashboard -> ComfyUI)                                  │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Prepare ComfyUI prompt                                             │
│  2. Generate unique client_id                                          │
│  3. POST to http://localhost:3000/prompt                               │
│     {                                                                  │
│       "prompt": {<workflow nodes>},                                    │
│       "client_id": "<unique_id>"                                       │
│     }                                                                  │
│  4. Receive prompt_id from ComfyUI                                     │
│  5. Return prompt_id to client                                         │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ Establish WebSocket
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ WebSocket Connection (Dashboard -> ComfyUI)                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Connect to: ws://localhost:3000/ws?clientId=<unique_id>                │
│                                                                          │
│  Receive Messages:                                                      │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Queue Update:                                                  │    │
│  │ {                                                              │    │
│  │   "type": "status",                                           │    │
│  │   "data": {                                                   │    │
│  │     "sid": <socket_id>,                                       │    │
│  │     "queue_running": [<prompt_info>],                         │    │
│  │     "queue_pending": [<prompt_info>]                          │    │
│  │   }                                                           │    │
│  │ }                                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Execution Progress:                                            │    │
│  │ {                                                              │    │
│  │   "type": "executing",                                        │    │
│  │   "data": {                                                   │    │
│  │     "node": "<node_id>",                                      │    │
│  │     "prompt_id": "<prompt_id>"                                │    │
│  │   }                                                           │    │
│  │ }                                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Execution Complete:                                            │    │
│  │ {                                                              │    │
│  │   "type": "executing",                                        │    │
│  │   "data": {                                                   │    │
│  │     "node": null                                              │    │
│  │   }                                                           │    │
│  │ }                                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ Forward to Dashboard Clients
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard WebSocket Server                                              │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Receive message from ComfyUI                                       │
│  2. Format for dashboard clients                                       │
│  3. Broadcast to all connected clients                                 │
│                                                                          │
│  Broadcast Message:                                                     │
│  {                                                                      │
│    "type": "workflow_progress",                                        │
│    "data": {                                                            │
│      "prompt_id": "<prompt_id>",                                       │
│      "node": "<node_id>",                                              │
│      "progress": 0.5                                                   │
│    }                                                                    │
│  }                                                                      │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Frontend (Client)                                            │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Receive WebSocket message                                          │
│  2. Update UI based on message type                                    │
│  3. Show execution progress                                            │
│  4. Display preview images as they generate                            │
│  5. Show final outputs when complete                                   │
└──────────────────────────────────────────────────────────────────────────┘
                             │
                             │ Retrieve outputs
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Output Retrieval                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  1. GET /api/comfyui/history/{prompt_id}                               │
│  2. Retrieve output file paths                                         │
│  3. Display images/videos in dashboard                                 │
│  4. Save to /workspace/output/                                         │
│  5. Generate download links for user                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Model Loading Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ComfyUI Node Needs Model                                               │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ ComfyUI Model Path Resolution                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Node requests model (e.g., "wan21.safetensors")                     │
│  2. ComfyUI checks extra_model_paths.yaml                              │
│  3. Maps checkpoint path to: /workspace/models/checkpoints/            │
│  4. Loads model from network volume                                     │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Model Loading Process                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Traditional Approach (OLD):                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 1. Copy model from container to workspace (rsync)                │  │
│  │ 2. Wait for copy to complete (60-120 seconds)                   │  │
│  │ 3. Load model into GPU memory                                    │  │
│  │ 4. Start execution                                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Revolutionary Approach (NEW):                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 1. Read model directly from /workspace/models/ (network volume) │  │
│  │ 2. Load model into GPU memory (<5 seconds)                       │  │
│  │ 3. Start execution immediately                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ GPU Memory Loading                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Read model file from network volume                                │
│  2. Load into GPU memory                                               │
│  3. Initialize model weights                                           │
│  4. Ready for inference                                                │
│                                                                          │
│  Time: <5 seconds (vs 60-120 seconds with rsync)                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. WebSocket Message Flow

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Client 1   │         │   Client 2   │         │   Client 3   │
│  (Browser)   │         │  (Browser)   │         │  (Browser)   │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ Connect                │ Connect                │ Connect
       ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Dashboard WebSocket Server                          │
│                            (Port 8080)                                   │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ Server broadcasts to all connected clients
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │Download │         │  Queue  │         │ System  │
   │Progress │         │ Updates │         │ Status  │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Backend Services                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │ Download        │  │ ComfyUI Bridge  │  │ System Monitor  │          │
│  │ Orchestrator    │  │                 │  │                 │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Storage Architecture Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Container Layer                                  │
│                     (Immutable - Ephemeral)                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  /app/comfyui/ComfyUI/models/ ──────┐                                  │
│  └─> Symlinks to network volume    │                                  │
│                                   │                                    │
│  /workspace/ ──────────────────────┘                                  │
│  └─> Mount point for network volume                                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Network Volume Layer                               │
│                      (Persistent - RunPod)                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  /workspace/models/                                                     │
│  ├─ checkpoints/              (Primary diffusion models)                │
│  ├─ text_encoders/           (T5, CLIP, etc.)                          │
│  ├─ vae/                     (Variational autoencoders)                 │
│  ├─ clip_vision/             (Image encoders)                          │
│  ├─ loras/                   (LoRA adapters)                           │
│  ├─ upscale_models/          (Image upscaling)                         │
│  ├─ audio_encoders/          (Audio processing)                        │
│  └─ [other model types]                                                │
│                                                                          │
│  /workspace/output/                                                     │
│  ├─ images/                 (Generated images)                         │
│  ├─ videos/                 (Generated videos)                         │
│  └─ temp/                   (Temporary files)                          │
│                                                                          │
│  /workspace/workflows/                                                  │
│  ├─ user/                   (User-created workflows)                   │
│  ├─ templates/              (Preset workflows)                         │
│  └─ presets/                (Workflow presets)                         │
│                                                                          │
│  /workspace/uploads/                                                     │
│  ├─ input/                  (User uploads for processing)               │
│  └─ assets/                 (Static assets)                             │
│                                                                          │
│  /workspace/config/                                                     │
│  ├─ extra_model_paths.yaml  (Generated at startup)                     │
│  ├─ presets.yaml            (Preset definitions)                       │
│  └─ user_settings.yaml      (User configuration)                       │
│                                                                          │
│  /workspace/cache/                                                      │
│  ├─ .cache/huggingface/     (HuggingFace cache)                        │
│  ├─ .cache/pip/             (pip cache)                                │
│  └─ .cache/uv/              (UV package manager cache)                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Access via ReadPod API
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      RunPod Cloud Infrastructure                        │
├──────────────────────────────────────────────────────────────────────────┤
│  - Network Volume Storage ($0.07/GB/month)                              │
│  - Persistent across pod restarts                                       │
│  - Shared between multiple pods                                         │
│  - High-performance SSD storage                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Error Handling Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Error Occurs in Background Task                                         │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Error Detection & Classification                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Error Types:                                                           │
│  ┌──────────────────────┬────────────────────────────────────────┐      │
│  │ Network Errors       │ - Connection timeout                   │      │
│  │                      │ - DNS resolution failure               │      │
│  │                      │ - SSL certificate errors               │      │
│  ├──────────────────────┼────────────────────────────────────────┤      │
│  │ Storage Errors       │ - Disk full                            │      │
│  │                      │ - Permission denied                    │      │
│  │                      │ - Network volume unmounted             │      │
│  ├──────────────────────┼────────────────────────────────────────┤      │
│  │ Download Errors      │ - File not found (404)                 │      │
│  │                      │ - Checksum mismatch                    │      │
│  │                      │ - Incomplete download                  │      │
│  ├──────────────────────┼────────────────────────────────────────┤      │
│  │ ComfyUI Errors       │ - Model load failure                   │      │
│  │                      │ - CUDA out of memory                   │      │
│  │                      │ - Workflow validation error            │      │
│  └──────────────────────┴────────────────────────────────────────┘      │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Error Handling Strategy                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Retry Logic                                                         │
│     ├─> Transient errors: Retry with exponential backoff               │
│     ├─> Max retries: 3                                                 │
│     └─> Backoff: 1s, 2s, 4s                                            │
│                                                                          │
│  2. Fallback Mechanisms                                                 │
│     ├─> Primary download source fails → Try mirror                     │
│     ├─> HuggingFace fails → Try direct URL                             │
│     └─> Network volume full → Alert user, pause downloads              │
│                                                                          │
│  3. User Notification                                                   │
│     ├─> WebSocket error message to all connected clients               │
│     ├─> Log error details to /workspace/logs/                          │
│     └─> Store error state for UI display                               │
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Error Recovery                                                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Recoverable Errors:                                                    │
│  ├─> Resume operation after retry                                      │
│  ├─> Update UI to reflect recovery                                     │
│  └─> Log recovery for audit trail                                      │
│                                                                          │
│  Fatal Errors:                                                          │
│  ├─> Stop current operation                                            │
│  ├─> Mark task as failed                                               │
│  ├─> Provide user with actionable error message                       │
│  └─> Offer retry option                                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

*Document Version: 1.0.0*
*Last Updated: 2026-02-15*
