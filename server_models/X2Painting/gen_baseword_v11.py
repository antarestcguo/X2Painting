from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from fontTools.ttLib import TTFont
from random import choice
from server_models.X2Painting.template_config import v11_base_config

complex_CN_param = v11_base_config['complex_CN_param']
word_space_ratio_CN = v11_base_config['word_space_ratio_CN']
base_pixel_number = v11_base_config['base_pixel_number']


def is_chinese(char):
    # Check if a character is Chinese
    return '\u4e00' <= char <= '\u9fff'


def gen_img_grey(text_to_draw, font, text_ratio):  # return cv2.img pad_grey_binary,crop_grey_binary
    # no matther text_to_draw is character or word
    text_width, text_height = font.getsize(text_to_draw)
    # cv2 compute bbox
    image_text_grey = Image.new("RGB", (text_width, text_height), (255, 255, 255))  # RGB, not RGBA
    draw_grey = ImageDraw.Draw(image_text_grey)
    draw_grey.text((0, 0), text_to_draw, font=font, fill=(0, 0, 0))
    # convert 2 opencv , compute the min bbox
    cv_img = cv2.cvtColor(np.asarray(image_text_grey), cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(cv_img, 127, 255, cv2.THRESH_BINARY)
    x, y, w, h = cv2.boundingRect(255 - binary)
    # compute final image w and h
    if len(text_to_draw) == 1:
        text_max_side = max(w, h)
        img_w = img_h = int(float(text_max_side) / text_ratio)
    else:
        img_w = int(float(w) / text_ratio)
        img_h = int(float(h) / text_ratio)

    pad_image = np.ones((img_h, img_w), dtype=np.uint8) * 255
    start_x = int((img_w - w) / 2)
    start_y = int((img_h - h) / 2)
    pad_image[start_y:start_y + h, start_x:start_x + w] = binary[y:y + h, x:x + w]

    return pad_image, binary[y:y + h, x:x + w]


def fill_color(binary_cvimg, bg_color, fg_color, color_img=None):  # if RGBA, process bg/fg color outside
    # fill fg/bg color
    h, w = binary_cvimg.shape
    if color_img is None:
        color_img = np.zeros([h, w, len(fg_color)], dtype=np.uint8)
    if bg_color is not None:
        color_img[(binary_cvimg == 255), :] = bg_color
    color_img[(binary_cvimg == 0), :] = fg_color

    return color_img


def polybox2points(box):
    points = []
    for it in box:
        points.append(tuple(it[0]))

    return points


def b_text_can_be_draw(font_path, text_to_draw):
    b_draw = False
    font = TTFont(font_path)

    glyph_name = None
    for table in font['cmap'].tables:
        glyph_name = table.cmap.get(ord(text_to_draw))
        if glyph_name is not None:
            break

    if glyph_name is not None:
        glyf = font['glyf']
        if glyf.has_key(glyph_name):
            a = glyf[glyph_name].getCoordinates(0)[0]
            if len(a) > 0:
                b_draw = True
    return b_draw


def obtain_draw_font(text, font_path, default_font_path_list):
    b_draw = True
    select_font_path = font_path
    for it_text in text:
        b_draw = b_text_can_be_draw(font_path, it_text)
        if not b_draw:
            for it_default_font_path in default_font_path_list:
                b_draw = b_text_can_be_draw(it_default_font_path, it_text)
                if b_draw:
                    select_font_path = it_default_font_path
                    break
        if not b_draw:
            return None
    return select_font_path


def b_complex_CN(font, text, crop_grey):
    text_width, text_height = font.getsize(text)

    idx = np.sum(crop_grey == 0)
    ratio = float(idx) / text_width / text_height

    if ratio > complex_CN_param:
        return True
    else:
        return False


def gen_character(text, font_path, default_font_path_list, fg_color, bg_color, char_type, font_size=812,
                  text_ratio=0.85,
                  max_side=1024, min_side=1024):  # return final_img, resize_crop_grey,start_x,start_y,b_complex
    # determin if can be draw
    select_font_path = obtain_draw_font(text, font_path, default_font_path_list)
    if select_font_path is None:
        return None, None, None, None, None

    # draw binary_grey img
    font = ImageFont.truetype(select_font_path, font_size)
    pad_grey, crop_grey = gen_img_grey(text, font, text_ratio)

    # compute complex
    b_complex = False if char_type == "EN" else b_complex_CN(font, text, crop_grey)

    # fill color
    pad_color = fill_color(pad_grey, bg_color, fg_color)

    # convert to PIL Image
    img = Image.fromarray(pad_color)
    # compute resize ratio and resize all
    pad_w, pad_h = img.size
    crop_w, crop_h = crop_grey.shape[::-1]
    resize_ratio = float(max_side) / pad_w
    assert resize_ratio == float(max_side) / pad_h, "resize size error"

    # resize final img
    final_img = img.resize((max_side, max_side), Image.BILINEAR)
    # resize_crop_grey
    crop_resize_w = int(crop_w * resize_ratio)
    crop_resize_h = int(crop_h * resize_ratio)
    crop_resize = cv2.resize(crop_grey, (crop_resize_w, crop_resize_h))
    # binary again
    _, crop_grey = cv2.threshold(crop_resize, 127, 255, cv2.THRESH_BINARY)
    start_x = int((max_side - crop_resize_w) / 2)
    start_y = int((max_side - crop_resize_h) / 2)

    return final_img, crop_grey, start_x, start_y, b_complex


def gen_word_CN(text, font_path, default_font_path_list,
                fg_color, bg_color,
                font_size=812, text_ratio=0.85,
                max_side=4096, min_side=1024):
    # return final_img,views,resize_crop_list,start_x,start_y,b_complex_list
    select_font_path = obtain_draw_font(text, font_path, default_font_path_list)
    if select_font_path is None:
        return None,None, None, None, None, None

    font = ImageFont.truetype(select_font_path, font_size)

    b_complex_list = []

    # gen each text and it's complex
    tmp_crop_list = []
    tmp_character_width_list = []
    tmp_character_height_list = []
    for it in text:
        _, crop_grey = gen_img_grey(it, font, text_ratio)
        tmp_crop_list.append(crop_grey)
        h, w = crop_grey.shape
        tmp_character_width_list.append(w)
        tmp_character_height_list.append(h)
        b_complex_list.append(b_complex_CN(font, it, crop_grey))

    # merge
    merge_w = tmp_character_width_list[0]
    for i in range(1, len(tmp_character_width_list)):
        merge_w = merge_w + tmp_character_width_list[i - 1] * word_space_ratio_CN + tmp_character_width_list[i]
    merge_h = np.max(tmp_character_height_list)
    # compute ratio
    if float(merge_w / merge_h) > 4:
        text_ratio_x = text_ratio
        text_ratio_y = text_ratio - 0.1
    else:
        text_ratio_x = text_ratio
        text_ratio_y = text_ratio

    pad_merge_h = int(merge_h / text_ratio_y)
    pad_merge_w = int(merge_w / text_ratio_x)

    # merge all the crop grey image
    merge_img = np.ones([pad_merge_h, pad_merge_w], dtype=np.uint8) * 255
    start_x = int((pad_merge_w - merge_w) / 2)
    offset_x = int((pad_merge_w - merge_w) / 2)
    for i, it in enumerate(tmp_crop_list):
        start_y = int((pad_merge_h - tmp_character_height_list[i]) / 2)
        merge_img[start_y:start_y + tmp_character_height_list[i], start_x:start_x + tmp_character_width_list[i]] = it
        start_x = int(start_x + tmp_character_width_list[i] * (1.0 + word_space_ratio_CN))

    # fill color
    pad_color = fill_color(merge_img, bg_color, fg_color)

    # convert to PIL Image and resize
    img = Image.fromarray(pad_color)
    img_w, img_h = img.size

    ratio = min_side / min(img_h, img_w)
    img_w, img_h = round(ratio * img_w), round(ratio * img_h)
    ratio = max_side / max(img_h, img_w)
    if ratio > 1:
        final_w = img_w // base_pixel_number * base_pixel_number
        final_h = img_h // base_pixel_number * base_pixel_number
    else:
        final_w = round(ratio * img_w) // base_pixel_number * base_pixel_number
        final_h = round(ratio * img_h) // base_pixel_number * base_pixel_number
    final_img = img.resize((final_w, final_h), Image.BILINEAR)

    # compute ratio
    resize_ratio = float(final_h) / img.size[1]

    # resize crop_grey according to the ratio
    resize_crop_list = []
    tmp_resize_character_width_list = []
    tmp_resize_character_height_list = []
    for i, it in enumerate(tmp_crop_list):
        crop_h, crop_w = tmp_character_height_list[i], tmp_character_width_list[i]
        resize_crop_h, resize_crop_w = int(crop_h * resize_ratio // base_pixel_number * base_pixel_number), int(
            crop_w * resize_ratio // base_pixel_number * base_pixel_number)
        tmp_resize_character_width_list.append(resize_crop_w)
        tmp_resize_character_height_list.append(resize_crop_h)
        resize_crop = cv2.resize(it, (resize_crop_w, resize_crop_h))
        _, resize_crop_grey = cv2.threshold(resize_crop, 127, 255, cv2.THRESH_BINARY)
        resize_crop_list.append(resize_crop_grey)

    # resize offset
    resize_offset_x = int(offset_x * resize_ratio // base_pixel_number * base_pixel_number)
    resize_start_y = int((final_h - tmp_resize_character_height_list[0]) / 2)  # according to the first resize_crop_grey

    # slice views (h_start, h_end, w_start, w_end)
    slice_view_list = []
    end_x = int(resize_offset_x + tmp_resize_character_width_list[0] * (
            1 + word_space_ratio_CN)) // base_pixel_number * base_pixel_number

    slice_view_list.append((0, final_h // base_pixel_number, 0, end_x // base_pixel_number))
    start_x = end_x - int(word_space_ratio_CN * tmp_resize_character_width_list[0])
    for i in range(1, len(resize_crop_list) - 1):
        end_x = int(start_x + tmp_resize_character_width_list[i - 1] * word_space_ratio_CN +
                    tmp_resize_character_width_list[i] * (
                            1 + word_space_ratio_CN)) // base_pixel_number * base_pixel_number
        slice_view_list.append(
            (0, final_h // base_pixel_number, start_x // base_pixel_number, end_x // base_pixel_number))
        start_x = end_x - int(word_space_ratio_CN * tmp_resize_character_width_list[i])
    slice_view_list.append(
        (0, final_h // base_pixel_number, start_x // base_pixel_number, final_w // base_pixel_number))

    return final_img, slice_view_list, resize_crop_list, resize_offset_x, resize_start_y, b_complex_list


def split_string(input_str):
    # 初始化结果列表
    result = []

    # 每次迭代处理2到3个字母
    i = 0
    while i < len(input_str):
        fragment_length = 2  # choice([2, 3])  # 随机选择片段长度为2或3
        if i + fragment_length <= len(input_str):
            result.append(input_str[i:i + fragment_length])
            i += fragment_length
        else:
            # 处理最后一个片段
            remaining_length = len(input_str) - i
            if remaining_length == 3:  # 如果剩余长度为3，则直接添加
                result.append(input_str[i:])
            else:  # 如果剩余长度为2，则随机选择长度为2或3
                result.append(input_str[i:i + choice([2])])
            break

    # 如果最后一个片段长度为1，与前一个片段合并
    # if len(result[-1]) == 1:
    #     last_fragment = result.pop()
    #     last_fragment_2 = result.pop()
    #
    #     if len(last_fragment_2) == 2:
    #         result.append(last_fragment_2 + last_fragment)
    #     else:
    #         new_str = last_fragment_2 + last_fragment
    #         result.append(new_str[:2])
    #         result.append(new_str[2:])

    # 返回结果
    return result


def split_string2char(input_str):
    # 初始化结果列表
    result = [it for it in input_str]
    return result


def check_view(ori_views):  # views need overlap
    for i in range(1, len(ori_views)):
        pre_start_h, pre_end_h, pre_start_w, pre_end_w = ori_views[i - 1]
        cur_start_h, cur_end_h, cur_start_w, cur_end_w = ori_views[i]
        if pre_end_w < cur_start_w:
            pre_end_w, cur_start_w = cur_start_w, pre_end_w
            ori_views[i - 1] = (pre_start_h, pre_end_h, pre_start_w, pre_end_w)
            ori_views[i] = (cur_start_h, cur_end_h, cur_start_w, cur_end_w)
    return ori_views


def gen_word_EN(text, font_path, default_font_path_list,
                fg_color, bg_color,
                font_size=812, text_ratio=0.85,
                max_side=4096, min_side=1024):
    # return final_img,views,start_x,start_y
    select_font_path = obtain_draw_font(text, font_path, default_font_path_list)
    if select_font_path is None:
        return None,None,None,None,None,None

    font = ImageFont.truetype(select_font_path, font_size)

    # split EN word to slice
    if len(text) > 2:
        EN_str_slice_list = split_string(text)
    else:
        EN_str_slice_list = split_string2char(text)

    # complex All False
    b_complex_list = [False for i in range(len(EN_str_slice_list))]

    # gen final image
    pad_grey, crop_grey = gen_img_grey(text, font, text_ratio)
    crop_h, crop_w = crop_grey.shape
    pad_h, pad_w = pad_grey.shape
    offset_x = int((pad_w - crop_w) / 2)

    # fill color
    pad_color = fill_color(pad_grey, bg_color, fg_color)

    # convert to PIL Image and resize
    img = Image.fromarray(pad_color)
    img_w, img_h = img.size

    ratio = min_side / min(img_h, img_w)
    img_w, img_h = round(ratio * img_w), round(ratio * img_h)
    ratio = max_side / max(img_h, img_w)
    if ratio > 1:
        final_w = img_w // base_pixel_number * base_pixel_number
        final_h = img_h // base_pixel_number * base_pixel_number
    else:
        final_w = round(ratio * img_w) // base_pixel_number * base_pixel_number
        final_h = round(ratio * img_h) // base_pixel_number * base_pixel_number
    final_img = img.resize((final_w, final_h), Image.BILINEAR)

    # compute ratio
    resize_ratio = float(final_h) / img.size[1]

    # resize offset
    resize_offset_x = int(offset_x * resize_ratio // base_pixel_number * base_pixel_number)

    # early return
    if len(EN_str_slice_list) == 1:
        return final_img, [], None, resize_offset_x, 0, b_complex_list
    # gen patch
    patch_start_list = []
    patch_start_list.append(0)
    gen_text = ""
    for it in EN_str_slice_list[:-1]:
        gen_text = gen_text + it
        _, it_crop_grey = gen_img_grey(gen_text, font, text_ratio)
        patch_h, patch_w = it_crop_grey.shape
        patch_start_list.append(patch_w)

    patch_end_list = []  # need to reverse
    gen_text = ""
    for it in EN_str_slice_list[::-1][:-1]:
        gen_text = gen_text + it
        _, it_crop_grey = gen_img_grey(gen_text, font, text_ratio)
        patch_h, patch_w = it_crop_grey.shape
        patch_end_list.append(crop_w - patch_w)
    patch_end_list = patch_end_list[::-1]
    patch_end_list.append(final_w / resize_ratio)

    # resize crop_grey according to the ratio
    views = []  # slice views (h_start, h_end, w_start, w_end)
    h_start = 0  # fixed constant
    h_end = final_h // base_pixel_number  # fixed constant
    w_start = 0
    w_end = resize_offset_x // base_pixel_number
    for it_start_w, it_end_w in zip(patch_start_list, patch_end_list):
        resize_start = int(w_start + np.ceil(it_start_w * resize_ratio) // base_pixel_number)
        resize_end = int(w_end + np.floor(it_end_w * resize_ratio) // base_pixel_number)
        views.append((h_start, h_end, resize_start, resize_end))
        w_start = resize_offset_x // base_pixel_number
        w_end = resize_offset_x // base_pixel_number
    views[-1] = (h_start, h_end, resize_start, final_w // base_pixel_number)

    views = check_view(views)
    return final_img, views, None, resize_offset_x, 0, b_complex_list


def enhance_character(ori_img, resize_crop_grey, start_x, start_y, fg_color, bg_color, alpha_ratio, b_bg=False):
    # early return
    if alpha_ratio == 0:  # EN_char
        return ori_img,None

    crop_h, crop_w = resize_crop_grey.shape

    # b_complex b_bg
    if b_bg:
        text_bg_img = Image.new("RGBA", (crop_w, crop_h), (0, 0, 0, 0))  # RGBA
        draw = ImageDraw.Draw(text_bg_img)
        # modify color
        bg_color_list = list(bg_color)
        bg_color_list.append(int(255 * alpha_ratio))
        bg_color = tuple(bg_color_list)
        contours, _ = cv2.findContours(255 - resize_crop_grey, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            epsilon = 0.01 * cv2.arcLength(cont, True)
            box = cv2.approxPolyDP(cont, epsilon=epsilon, closed=True)
            try:
                draw.polygon(polybox2points(box), fill=bg_color)
            except:
                print("err", box)

        # convert to nparray
        text_bg_img_array = np.array(text_bg_img)
        # add text fill color
        fg_color_list = list(fg_color)
        fg_color_list.append(int(255 * alpha_ratio))
        fg_color = tuple(fg_color_list)
        crop_rgba = fill_color(resize_crop_grey, None, fg_color, text_bg_img_array)
    else:
        # fill color and gen rgba image, keep fg color
        crop_color = fill_color(resize_crop_grey, None, fg_color)
        crop_rgba = np.concatenate((crop_color, np.expand_dims((255 - resize_crop_grey) * alpha_ratio, axis=2)), axis=2)

    # convert crop_rgba to PIL.Image and merge
    crop_image = Image.fromarray(crop_rgba.astype(np.uint8))
    r, g, b, a = crop_image.split()

    ori_img = ori_img.convert("RGBA")
    ori_img.paste(crop_image, (start_x, start_y, start_x + crop_w, start_y + crop_h), mask=a)

    return ori_img.convert("RGB"), crop_image.convert("RGB")


def enhance_word_CN(ori_img, resize_crop_grey_list, start_x, start_y, fg_color, bg_color, alpha_ratio_list, b_bg_list):
    img_w, img_h = ori_img.size
    ori_img = ori_img.convert("RGBA")

    cp_start_x = start_x
    cp_start_y = start_y
    for it_crop, it_alpha, it_complex in zip(resize_crop_grey_list, alpha_ratio_list, b_bg_list):

        crop_h, crop_w = it_crop.shape
        cp_start_y = int((img_h - crop_h) / 2) // base_pixel_number * base_pixel_number

        if it_alpha == 0:
            cp_start_x = int(cp_start_x + crop_w * (1 + word_space_ratio_CN)) // base_pixel_number * base_pixel_number
            continue

        if it_complex:
            text_bg_img = Image.new("RGBA", (crop_w, crop_h), (0, 0, 0, 0))  # RGBA
            draw = ImageDraw.Draw(text_bg_img)
            # modify color
            bg_color_list = list(bg_color)
            bg_color_list.append(int(255 * it_alpha))
            bg_color_alpha = tuple(bg_color_list)
            contours, _ = cv2.findContours(255 - it_crop, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for cont in contours:
                epsilon = 0.01 * cv2.arcLength(cont, True)
                box = cv2.approxPolyDP(cont, epsilon=epsilon, closed=True)
                draw.polygon(polybox2points(box), fill=bg_color_alpha)

            # convert to nparray
            text_bg_img_array = np.array(text_bg_img)
            # add text fill color
            fg_color_list = list(fg_color)
            fg_color_list.append(int(255 * it_alpha))
            fg_color_alpha = tuple(fg_color_list)
            crop_rgba = fill_color(it_crop, None, fg_color_alpha, text_bg_img_array)
        else:
            # fill color and gen rgba image, keep fg color
            crop_color = fill_color(it_crop, None, fg_color)
            crop_rgba = np.concatenate((crop_color, np.expand_dims((255 - it_crop) * it_alpha, axis=2)),
                                       axis=2)

        # convert crop_rgba to PIL.Image and merge
        crop_image = Image.fromarray(crop_rgba.astype(np.uint8))
        r, g, b, a = crop_image.split()
        ori_img.paste(crop_image, (cp_start_x, cp_start_y, cp_start_x + crop_w, cp_start_y + crop_h), mask=a)

        cp_start_x = int(cp_start_x + crop_w * (1 + word_space_ratio_CN)) // base_pixel_number * base_pixel_number

    return ori_img.convert("RGB"), None
