from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

# rgb
color_dict = {
    "butterflygirl_black": {"bg_color": (250, 248, 235), "fg_color": (85, 82, 79), },
    "cartoongirl_black": {"bg_color": (230, 221, 214), "fg_color": (64, 74, 75), },
    "cartoongirl2_while": {"bg_color": (149, 190, 196), "fg_color": (243, 251, 242), },
    "cartoongirl3_green": {"bg_color": (199, 221, 209), "fg_color": (45, 108, 72), },
    "dunhuanggirl_yellow": {"bg_color": (31, 66, 64), "fg_color": (243, 206, 159), },
    "fengjingwood_black": {"bg_color": (214, 219, 222), "fg_color": (70, 88, 100), },
    "god_white": {"bg_color": (176, 116, 66), "fg_color": (243, 244, 235), },
    "gufenggirl_black": {"bg_color": (181, 197, 201), "fg_color": (67, 64, 65), },
    "gufenggirl_white": {"bg_color": (19, 48, 78), "fg_color": (232, 232, 232), },
    "male_black": {"bg_color": (247, 248, 242), "fg_color": (58, 72, 71), },
    "phoenix_red": {"bg_color": (229, 200, 151), "fg_color": (139, 76, 41), },
    "phoenix_white": {"bg_color": (47, 74, 95), "fg_color": (215, 224, 226), },
    "qianxun_black": {"bg_color": (108, 138, 160), "fg_color": (38, 40, 59), },
    "shuimocartoon_green": {"bg_color": (229, 248, 233), "fg_color": (0, 120, 118), },
    "shuimocartoonfox_black": {"bg_color": (246, 244, 231), "fg_color": (101, 94, 95), },
    "shuimocartoongirl_black": {"bg_color": (228, 226, 213), "fg_color": (57, 84, 130), },
    "shuimocartoongirl2_green": {"bg_color": (247, 243, 231), "fg_color": (101, 129, 118), },
    "shuimoflower_black": {"bg_color": (243, 234, 219), "fg_color": (125, 104, 93), },
    "shuimohuizhou_black": {"bg_color": (232, 227, 217), "fg_color": (95, 91, 88), },
    "shuimowood_black": {"bg_color": (252, 248, 236), "fg_color": (101, 114, 118), },
    "shuimowood2_black": {"bg_color": (250, 241, 225), "fg_color": (98, 104, 114), },
    "tiankongzhicheng_black": {"bg_color": (204, 214, 213), "fg_color": (9, 15, 28), },
    "tree_black": {"bg_color": (252, 246, 234), "fg_color": (107, 116, 119), },
    "treewoodcartoon_green": {"bg_color": (230, 230, 217), "fg_color": (63, 82, 108), },
    "winter_black": {"bg_color": (233, 237, 235), "fg_color": (86, 76, 81), },
    "wood_black": {"bg_color": (169, 182, 199), "fg_color": (54, 61, 77), },
    "woodboat_black": {"bg_color": (214, 211, 214), "fg_color": (99, 111, 138), },
    "prince_black": {"bg_color": (224, 236, 228), "fg_color": (45, 52, 64), }
}


def is_chinese(char):
    # Check if a character is Chinese
    return '\u4e00' <= char <= '\u9fff'


def create_text_image_RGB(text, bg_color, fg_color, font_path, font_size, img_h=1024, img_w=1024, ):
    # Create a new image with specified background color
    # bg_color = color_dict[color_style]['bg_color']
    # fg_color = color_dict[color_style]['fg_color']
    # font_size = color_dict[color_style]['font_size']

    # bg image
    image_bg = Image.new("RGB", (img_w, img_h), bg_color)  # RGB, not RGBA
    # draw = ImageDraw.Draw(image)

    # Determine text to draw based on input language
    if is_chinese(text[0]):
        text_to_draw = text[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)
    else:
        text_to_draw = text.split()[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)

    # Calculate text size and position
    # import pdb
    # pdb.set_trace()
    corpus_w, corpus_h = font.getsize(text_to_draw)
    w_offset, h_offset = font.getoffset(text_to_draw)

    # text_width, text_height = draw.textsize(text_to_draw, font=font)

    # img text
    image_text = Image.new("RGB", (corpus_w - w_offset, corpus_h - h_offset), bg_color)  # RGB, not RGBA
    draw = ImageDraw.Draw(image_text)
    draw.text((-w_offset, -h_offset), text_to_draw, font=font, fill=fg_color)

    # text_x = int((img_w - tmp_w) / 2)
    # text_y = int((img_h - tmp_h) / 2)
    # # Draw text on image
    # draw.text((text_x, text_y), text_to_draw, font=font, fill=fg_color)

    # merge img_bg and img_text
    text_w, text_h = image_text.size
    start_x = int((img_w - text_w) / 2)
    start_y = int((img_h - text_h) / 2)
    image_bg.paste(image_text, (start_x, start_y, start_x + text_w, start_y + text_h))

    return image_bg


def create_maxtext_image_RGB(text, bg_color, fg_color, font_path, font_size, img_h=1024, img_w=1024, text_ratio=0.85):
    # bg image
    image_bg = Image.new("RGB", (img_w, img_h), bg_color)  # RGB, not RGBA

    # Determine text to draw based on input language
    if is_chinese(text[0]):
        text_to_draw = text[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)
    else:
        text_to_draw = text.split()[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)

    # Calculate text size and position
    corpus_w, corpus_h = font.getsize(text_to_draw)
    w_offset, h_offset = font.getoffset(text_to_draw)

    # img text
    image_text = Image.new("RGB", (corpus_w - w_offset, corpus_h - h_offset), bg_color)  # RGB, not RGBA
    draw = ImageDraw.Draw(image_text)
    draw.text((-w_offset, -h_offset), text_to_draw, font=font, fill=fg_color)

    # cv2 compute bbox
    image_text_grey = Image.new("RGB", (corpus_w - w_offset, corpus_h - h_offset), (0, 0, 0))  # RGB, not RGBA
    draw_grey = ImageDraw.Draw(image_text_grey)
    draw_grey.text((-w_offset, -h_offset), text_to_draw, font=font, fill=(255, 255, 255))
    # convert 2 opencv , compute the min bbox
    cv_img = cv2.cvtColor(np.asarray(image_text_grey), cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(cv_img, 127, 255, cv2.THRESH_BINARY)
    x, y, w, h = cv2.boundingRect(binary)

    # merge img_bg and img_text
    image_text = image_text.crop((x, y, x + w, y + h))
    text_w, text_h = image_text.size

    # resize the image
    text_max_side = max(text_w, text_h)
    resize_max = int(img_h * text_ratio)  # default img_h == img_w
    new_text_w = int(resize_max * text_w / text_max_side)
    new_text_h = int(resize_max * text_h / text_max_side)
    resize_image_text = image_text.resize((new_text_w, new_text_h), Image.ANTIALIAS)

    # re-compute the w and h
    text_w, text_h = resize_image_text.size

    start_x = int((img_w - text_w) / 2)
    start_y = int((img_h - text_h) / 2)
    image_bg.paste(resize_image_text, (start_x, start_y, start_x + text_w, start_y + text_h))

    return image_bg


def polybox2points(box):
    points = []
    for it in box:
        points.append(tuple(it[0]))

    return points

def paste_maxtext(text, ori_image, fg_color, bg_color, font_path, font_size, alpha_ratio, text_ratio=0.85, b_bg=False):
    img_w, img_h = ori_image.size

    # modify color
    fg_color_list = list(fg_color)
    fg_color_list.append(int(255 * alpha_ratio))
    fg_color = tuple(fg_color_list)

    bg_color_list = list(bg_color)
    bg_color_list.append(int(255 * alpha_ratio))
    bg_color = tuple(bg_color_list)

    # Determine text to draw based on input language
    if is_chinese(text[0]):
        text_to_draw = text[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)
    else:
        text_to_draw = text.split()[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)

        # img text

    # cv2 compute bbox
    image_text_grey = Image.new("RGB", (img_w, img_h), (0, 0, 0))  # RGB, not RGBA
    draw_grey = ImageDraw.Draw(image_text_grey)
    draw_grey.text((0, 0), text_to_draw, font=font, fill=(255, 255, 255))
    # convert 2 opencv , compute the min bbox
    cv_img = cv2.cvtColor(np.asarray(image_text_grey), cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(cv_img, 20, 255, cv2.THRESH_BINARY)
    x, y, w, h = cv2.boundingRect(binary)

    # draw text
    image_text = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))  # RGBA
    draw = ImageDraw.Draw(image_text)

    # compute polylines
    if b_bg:
        contours, _ = cv2.findContours(cv_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            epsilon = 0.01 * cv2.arcLength(cont, True)
            box = cv2.approxPolyDP(cont, epsilon=epsilon, closed=True)
            draw.polygon(polybox2points(box), fill=bg_color)

    draw.text((0, 0), text_to_draw, font=font, fill=fg_color)

    # merge img_bg and img_text
    image_text = image_text.crop((x, y, x + w, y + h))
    text_w, text_h = image_text.size

    # resize the image
    text_max_side = max(text_w, text_h)
    resize_max = int(img_h * text_ratio)  # default img_h == img_w
    new_text_w = int(resize_max * text_w / text_max_side)
    new_text_h = int(resize_max * text_h / text_max_side)
    resize_image_text = image_text.resize((new_text_w, new_text_h), Image.ANTIALIAS)

    # re-compute the w and h
    text_w, text_h = resize_image_text.size

    # add alpha
    r, g, b, a = resize_image_text.split()

    start_x = int((img_w - text_w) / 2)
    start_y = int((img_h - text_h) / 2)
    ori_image = ori_image.convert("RGBA")
    ori_image.paste(resize_image_text, (start_x, start_y, start_x + text_w, start_y + text_h), mask=a)

    return ori_image.convert("RGB"), resize_image_text.convert("RGB")


def compute_complex_word(text, font_path, font_size, img_w=1024, img_h=1024):
    # Determine text to draw based on input language
    if is_chinese(text[0]):
        text_to_draw = text[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)
    else:
        text_to_draw = text.split()[0]
        # Load font
        font = ImageFont.truetype(font_path, font_size)

    image_text = Image.new("RGBA", (img_w, img_h), (0, 0, 0))  # RGB
    draw = ImageDraw.Draw(image_text)
    draw.text((0, 0), text_to_draw, font=font, fill=(255, 255, 255))

    # cv2 compute bbox
    image_text_grey = Image.new("RGB", (img_w, img_h), (0, 0, 0))  # RGB, not RGBA
    draw_grey = ImageDraw.Draw(image_text_grey)
    draw_grey.text((0, 0), text_to_draw, font=font, fill=(255, 255, 255))

    # convert 2 opencv , compute the min bbox
    cv_img = cv2.cvtColor(np.asarray(image_text_grey), cv2.COLOR_BGR2GRAY)
    x, y, w, h = cv2.boundingRect(cv_img)
    crop_grey = cv_img[y:y + h, x:x + w]

    # compute white:text, bg:black ratio
    white_idx = len(np.where(crop_grey > 127)[0])
    black_idx = len(np.where(crop_grey < 127)[0])

    new_h, new_w = crop_grey.shape

    return float(white_idx) / (new_h * new_w), float(black_idx) / (new_h * new_w)
