from server_models.X2Painting.template_config import style_path, style_config_dict, default_style_name, font_file_dict, \
    v11_base_config, EN_default_font_path, CN_default_font_path
from server_models.X2Painting.gen_baseword_v11 import is_chinese, gen_character, gen_word_CN, \
    enhance_character, enhance_word_CN, gen_word_EN
from server_models.X2Painting.model_config import GenConfig
from utils.data_convert import image_to_base64
from utils.data_type import ImageOutput
import os
from random import choice
from PIL import Image
import json
from datetime import datetime


def wordart_pipeline_v11(receive_infor: dict, WordArtModel):
    # log path
    # WordArt_param = receive_infor["extra_input_infor"].get("WordArt")
    # platform = WordArt_param.get("platform", "chongqingpark")
    # base_path = os.path.join("./log/gen_WordArt", platform)
    # if not os.path.exists(base_path):
    #     os.makedirs(base_path)
    # now = datetime.now()
    # formatted_time = now.strftime('%Y-%m-%d-%H-%M-%S')
    # log_path = os.path.join(base_path, formatted_time)
    # if not os.path.exists(log_path):
    #     os.makedirs(log_path)
    # print("save log, call from:", platform)
    # # receive infor
    # json_file = os.path.join(log_path, "receive_infor.json")
    # json_str = json.dumps(receive_infor)
    # with open(json_file, 'w') as f:
    #     f.write(json_str)

    # define output
    output_image_list = []  # extra_image: loop1_images,preenhance_images
    extra_infor = dict()
    err_code = 0

    # instantID config from receive_infor
    receive_WordArt_config = receive_infor["extra_input_infor"].get("WordArt").copy()

    style_name = receive_WordArt_config.get('style', None)
    text = receive_WordArt_config.get('word', None)
    print('-' * 30)
    print("receive style: {}, receive text: {}".format(style_name, text))

    # check input
    if not isinstance(style_name, str) or style_name not in style_config_dict:
        style_name = default_style_name
    if not isinstance(text, str):
        extra_infor["pipeline_err"] = "input word must be a string"
        err_code = 13200
        return output_image_list, extra_infor, err_code

    # obtain style
    style_folder = os.path.join(style_path, style_name)
    style_image_list = os.listdir(style_folder)
    style_img_name = choice(style_image_list)
    b_success = False
    while not b_success:
        try:
            full_style_name = os.path.join(style_folder, style_img_name)
            image = Image.open(full_style_name)
            b_success = True
        except:
            style_img_name = choice(style_image_list)

    # obtain style config fixed
    bg_color = style_config_dict[style_name]['bg_color']
    fg_color = style_config_dict[style_name]['fg_color']
    font_size = style_config_dict[style_name]['font_size']

    # gen base image
    text_to_draw = text.strip().split(' ')[0]

    # obtain prompt
    prompt = style_config_dict[style_name]["prompt"]
    negative_prompt = style_config_dict[style_name]["negative_prompt"]

    # update according the receive_infor
    receive_param = receive_WordArt_config.get('prompt', None)
    if isinstance(receive_param, str):
        prompt = receive_param
    receive_param = receive_WordArt_config.get('negative_prompt', None)
    if isinstance(receive_param, str):
        negative_prompt = receive_param

    # base receive infor
    gen_num = receive_infor.get("gen_num", GenConfig["gen_num"])
    if not isinstance(gen_num, int) or gen_num <= 0 or gen_num > GenConfig["gen_num"]:
        gen_num = GenConfig["gen_num"]
    num_inference_steps = receive_infor.get("num_inference_steps", GenConfig["num_inference_steps"])
    if not isinstance(num_inference_steps, int) or num_inference_steps <= 0:
        num_inference_steps = GenConfig["num_inference_steps"]
    fast_num_inference_steps = receive_infor.get("fast_num_inference_steps", GenConfig["fast_num_inference_steps"])
    if not isinstance(num_inference_steps, int) or num_inference_steps <= 0:
        fast_num_inference_steps = GenConfig["fast_num_inference_steps"]

    if len(text_to_draw) == 1:
        # character
        char_type = "CN" if is_chinese(text_to_draw) else "EN"

        # get font param
        default_font_path_list = eval(char_type + "_default_font_path")
        font_style = choice(style_config_dict[style_name][(char_type + "_font_style").replace("CN_", "")])
        # update according the receive_infor
        receive_param = receive_WordArt_config.get('font_style', None)
        if isinstance(receive_param, str) and receive_param in font_file_dict:
            font_style = receive_param
        font_path = font_file_dict[font_style]['file_path']

        # gen base image
        base_img, resize_crop_grey, \
            start_x, start_y, b_complex = gen_character(text_to_draw,
                                                        font_path,
                                                        default_font_path_list,
                                                        fg_color, bg_color, char_type)
        if base_img is None:
            extra_infor["pipeline_err"] = "input character is too complexity to draw"
            err_code = 13201
            return output_image_list, extra_infor, err_code

        # strength
        strength = choice(style_config_dict[style_name][
                              (char_type + '_strength').replace("CN_", "")]) if not b_complex else min(
            style_config_dict[style_name][(char_type + '_strength').replace("CN_", "")])

        # update according the receive_infor
        receive_param = receive_WordArt_config.get('strength', None)
        if isinstance(receive_param, float) and receive_param > 0 and receive_param < 1:
            strength = receive_param

        # gen image loop1
        loop1_images = WordArtModel.ip_model.generate(pil_image=image,
                                                      num_samples=4, num_inference_steps=num_inference_steps,
                                                      image=base_img, strength=strength,
                                                      prompt=prompt,
                                                      negative_prompt=negative_prompt
                                                      )


    else:  # multi char
        word_type = "EN" if text_to_draw.encode('utf-8').isalpha() else "CN"
        # get font param
        default_font_path_list = eval(word_type + "_default_font_path")
        font_style = choice(style_config_dict[style_name][(word_type + "_font_style").replace("CN_", "")])
        # update according the receive_infor
        receive_param = receive_WordArt_config.get('font_style', None)
        if isinstance(receive_param, str) and receive_param in font_file_dict:
            font_style = receive_param
        font_path = font_file_dict[font_style]['file_path']

        # gen base image
        final_img, views, resize_crop_list, start_x, start_y, b_complex_list = \
            eval("gen_word_" + word_type)(
                text_to_draw,
                font_path, default_font_path_list, fg_color,
                bg_color)

        b_complex = None

        if final_img is None:
            extra_infor["pipeline_err"] = "input character is too complexity to draw"
            err_code = 13201
            return output_image_list, extra_infor, err_code

        # obtain strength
        strength_template = style_config_dict[style_name][
            (word_type + '_strength').replace("CN_", "")]
        choice_strength = choice(strength_template)

        # update according the receive_infor
        receive_param = receive_WordArt_config.get('strength', None)
        if isinstance(receive_param, float) and receive_param > 0 and receive_param < 1:
            choice_strength = receive_param
        strength_list = [min(strength_template) if it else choice_strength for it in b_complex_list]
        strength = None

        # gen loop1_images
        loop1_images, _ = \
            WordArtModel.ip_fast_model.word_generate(pil_image=image,
                                                     views=views,
                                                     full_image=final_img,
                                                     num_samples=4, num_inference_steps=fast_num_inference_steps,
                                                     strength_list=strength_list,
                                                     prompt=prompt,
                                                     negative_prompt=negative_prompt,
                                                     )

    # obtain enhance param,will be updated
    if "enhance" in style_config_dict[style_name]:
        refine_prompt = style_config_dict[style_name]['enhance']['prompt']
        refine_negative_prompt = style_config_dict[style_name]['enhance']['negative_prompt']
        enhance_param = receive_WordArt_config.get('enhance', None)
        if isinstance(enhance_param, dict):
            receive_param = enhance_param.get("prompt", None)
            if isinstance(receive_param, str):
                refine_prompt = receive_param
            receive_param = enhance_param.get("negative_prompt", None)
            if isinstance(receive_param, str):
                refine_negative_prompt = receive_param
        for i, it_img in enumerate(loop1_images):
            if len(text_to_draw) == 1:
                refine_strength = choice(style_config_dict[style_name]['enhance']['strength'])
                if char_type == "EN":
                    alpha_ratio = 0
                    refine_strength += 0.1
                else:
                    alpha_ratio = max(
                        style_config_dict[style_name]['enhance']['alpha_ratio']) if b_complex else choice(
                        style_config_dict[style_name]['enhance']['alpha_ratio'])
                # update strength and alpha according to the receive_param
                if isinstance(enhance_param, dict):
                    receive_param = enhance_param.get("strength", None)
                    if isinstance(strength, float) and receive_param > 0 and receive_param < 1:
                        refine_strength = receive_param
                    receive_param = enhance_param.get("alpha_ratio", None)
                    if isinstance(alpha_ratio, float) and receive_param > 0 and receive_param < 1:
                        alpha_ratio = receive_param

                # enhance and gen images
                enhance_img, _ = enhance_character(it_img,
                                                   resize_crop_grey, start_x, start_y, fg_color,
                                                   bg_color, alpha_ratio,
                                                   b_bg=b_complex)

                refine_image = WordArtModel.ip_model.generate(
                    pil_image=image, num_samples=1, num_inference_steps=num_inference_steps,
                    image=enhance_img,
                    strength=refine_strength,
                    prompt=refine_prompt,
                    negative_prompt=refine_negative_prompt)[0]
            else:  # multichar enhance
                alpha_template = style_config_dict[style_name]['enhance'][
                    'word_' + word_type + '_alpha_ratio']
                alpha_ratio = choice(alpha_template)
                refine_strength = choice(
                    style_config_dict[style_name]['enhance']['word_' + word_type + '_strength'])

                # update strength and alpha according to the receive_param
                if isinstance(enhance_param, dict):
                    receive_param = enhance_param.get("strength", None)
                    if isinstance(receive_param, float) and receive_param > 0 and receive_param < 1:
                        refine_strength = receive_param
                    receive_param = enhance_param.get("alpha_ratio", None)
                    if isinstance(alpha_ratio, float) and receive_param > 0 and receive_param < 1:
                        alpha_ratio = receive_param
                alpha_ratio_list = [max(alpha_template) if it_complex else alpha_ratio for it_complex in
                                    b_complex_list]

                # CN need to enhance
                if word_type == "CN":
                    enhance_img, _ = enhance_word_CN(it_img,
                                                     resize_crop_list, start_x, start_y, fg_color,
                                                     bg_color, alpha_ratio_list, b_complex_list)
                else:
                    enhance_img = it_img

                # start to refine
                refine_image = WordArtModel.ip_model.multidiffusion_generate(
                    pil_image=image, num_samples=1, views=views,
                    num_inference_steps=num_inference_steps,
                    image=enhance_img,
                    strength=refine_strength,
                    prompt=refine_prompt,
                    negative_prompt=refine_negative_prompt)[0]

            # zip to output
            if len(text_to_draw) == 1:

                output_image_list.append(ImageOutput(image=image_to_base64(refine_image),
                                                     extra_image={'loop1_images': image_to_base64(it_img),
                                                                  'preenhance_images': image_to_base64(enhance_img)}))
            else:
                output_image_list.append(ImageOutput(image=image_to_base64(refine_image),
                                                     extra_image={}))
    else:
        for i, it_img in enumerate(loop1_images):
            # zip to output
            output_image_list.append(ImageOutput(image=image_to_base64(it_img),
                                                 extra_image={}))
    extra_infor["receive_infor"] = receive_infor
    # print log
    b_enhance = "enhance" in style_config_dict[style_name]
    log_dict = {
        "style": style_name,
        "style_img_name": full_style_name,
        "word": text_to_draw,
        "font_style": font_style,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "strength": strength if strength is not None else strength_list,
        "b_complexity": b_complex if b_complex is not None else b_complex_list,
        ########## enhance
        "refine_prompt": None if not b_enhance else refine_prompt,
        "refine_negative_prompt": None if not b_enhance else refine_negative_prompt,
        "refine_strength": None if not b_enhance else refine_strength,
        "alpha_ratio": None if not b_enhance else alpha_ratio
    }
    print("#" * 40)
    print(log_dict)


    return output_image_list, extra_infor, err_code
