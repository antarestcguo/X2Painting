BaseConfig = {
    "base_model_path": "./models/stable-diffusion-xl-base-1.0",
    "base_model_file": "./models/dreamshaperXL_lightningDPMSDE.safetensors",
    "image_encoder_path": "./models/IP-Adapter/sdxl_model/image_encoder",
    "ip_ckpt": "./models/IP-Adapter/sdxl_model/ip-adapter_sdxl.safetensors",
}

GenConfig = {
    "num_inference_steps": 20,
    "fast_num_inference_steps": 8,
    "gen_num": 4,
}

WordArtImg2ImgConfig = BaseConfig.copy()
