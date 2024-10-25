import gradio

from utils.data_convert import base64_to_image
from interface_modules.X2Painting.template_config import font_style_dict
from server_models.X2Painting.wordart_pipeline_v11 import wordart_pipeline_v11


def send_to_server(word, style_name, WordArtModel):
    send_data = {}
    # fill send_data
    send_data["gen_num"] = 4  #

    # task specific
    send_data['extra_input_infor'] = {
        'WordArt':
            {
                "style": style_name,
                "word": word,
            }
    }

    result_img_list, extra_infor, err_code = wordart_pipeline_v11(send_data, WordArtModel)

    if err_code != 0:
        print("error", "-" * 30)
        print(extra_infor)
        return [None]

    enhance_output = []
    loop1_output = []
    for i, img_obj in enumerate(result_img_list):
        final_img = base64_to_image(img_obj["image"])  # 最终结果图片 PIL格式
        enhance_output.append((final_img, "{}_{}_enhance.jpg".format(word, i)))

        if "loop1_images" in img_obj['extra_image']:
            loop1_images = img_obj['extra_image']["loop1_images"]
            img = base64_to_image(loop1_images)
            loop1_output.append((img, "{}_{}_loop1_images.jpg".format(word, i)))

    return enhance_output + loop1_output
