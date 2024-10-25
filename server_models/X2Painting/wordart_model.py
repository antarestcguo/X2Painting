from utils.utils import get_torch_device
from diffusers import StableDiffusionXLImg2ImgPipeline
from server_models.X2Painting.ip_adapter import IPAdapterXL
from server_models.X2Painting.enhance_pipeline.SDImg2Img_multidiffusion import StableDiffusionXLImg2ImgPanoramaPipeline
import torch


class IPAdapterImg2ImgBaseModel:
    def __init__(self, wordart_model_config):
        device = get_torch_device()
        dtype = torch.float16 if str(device).__contains__("cuda") else torch.float32
        self.baseSDpipe = StableDiffusionXLImg2ImgPanoramaPipeline.from_pretrained(
            wordart_model_config["base_model_path"],
            torch_dtype=dtype,
            add_watermarker=False,
        )  # modify to StableDiffusionXLImg2ImgPanoramaPipeline , compatibility to multidiffusion

        self.fastSDpipe = StableDiffusionXLImg2ImgPanoramaPipeline.from_single_file(
            wordart_model_config["base_model_file"],
            torch_dtype=torch.float16,
            use_safetensors=True,
        )

        # reduce GPU MEM
        self.baseSDpipe.enable_vae_slicing()
        self.baseSDpipe.enable_xformers_memory_efficient_attention()
        self.fastSDpipe.enable_vae_slicing()
        self.fastSDpipe.enable_xformers_memory_efficient_attention()
        # load ip-adapter
        self.ip_model = IPAdapterXL(self.baseSDpipe, wordart_model_config["image_encoder_path"],
                                    wordart_model_config["ip_ckpt"], device)

        self.ip_fast_model = IPAdapterXL(self.fastSDpipe, wordart_model_config["image_encoder_path"],
                                         wordart_model_config["ip_ckpt"], device)
