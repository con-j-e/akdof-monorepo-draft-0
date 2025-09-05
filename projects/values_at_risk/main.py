import asyncio

from config.wfigs_inputs_config import INPUT_FEATURE_LAYERS_CONFIG

async def refresh_wfigs_features():
    await asyncio.gather(*(layer.refresh_features() for layer in INPUT_FEATURE_LAYERS_CONFIG))

async def main():
    """Entry point for taking a snapshot of 2025 wfigs data, to be used for 2026 testing purposes."""
    try:
        await refresh_wfigs_features()
    finally:
        await INPUT_FEATURE_LAYERS_CONFIG.close_requesters()
        INPUT_FEATURE_LAYERS_CONFIG.shutdown_thread_executors()

if __name__ == "__main__":
    asyncio.run(main())