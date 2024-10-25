import gradio as gr

import numpy as np
from interface_modules.X2Painting.template_config import style_example, style_example_word
from interface_modules.X2Painting.client_process import send_to_server


def on_select_char(evt: gr.SelectData):
    index = evt.index
    style_name = list(style_example.values())[index]
    print("char style:", style_name)
    return gr.update(value=style_name)


def on_select_word(evt: gr.SelectData):
    index = evt.index
    style_name = list(style_example_word.values())[index]
    print("word style:", style_name)
    return gr.update(value=style_name)


# init model
from server_models.X2Painting.wordart_model import IPAdapterImg2ImgBaseModel
from server_models.X2Painting.model_config import WordArtImg2ImgConfig
WordArtModel = IPAdapterImg2ImgBaseModel(WordArtImg2ImgConfig)

css = """
        .gradio-container {background-color: #F0F5FF; width: 95% !important}
        """
title = r"""
    </br>
    <h1 align="center" style="font-size: 42px;">X2Painting</h1>
    </br>

    <br>
<div style="text-align: center;">
    <h2>
        <span style="color: red;">Word</span> &lt;---
        <span style="color: black;">Zoom out </span>
        <a href='https://github.com/antarestcguo/X2Painting' target="_blank" style="display: inline-block; text-decoration: none; color: black; vertical-align: middle;">
            <img src='https://img.shields.io/badge/Github-Repo-blue' alt="GitHub" style="width: auto; height: 20px;">
        </a>
        <span style="color: black;"> Zoom in ---&gt;</span>
        <span style="color: red;">Painting</span>
    </h2>
</div>
<br>


    </br>   
    <img src="https://raw.githubusercontent.com/antarestcguo/X2Painting/main/resources/x2painting_intro.png" style="display: block; margin: 0 auto; max-height: 384px;">

    </br>
    <h2 style="text-align: center;">===================🤪🥳 Have a Try 🤩😄===================</h2>
    """
# https://raw.githubusercontent.com/antarestcguo/X2Painting/main/resources/x2painting_intro.png
# https://raw.githubusercontent.com/antarestcguo/X2Painting/main/resources/xword_intro.png
# https://raw.githubusercontent.com/antarestcguo/X2Painting/main/resources/loves.jpg

with gr.Blocks(css=css) as demo:
    # description
    gr.HTML(title)
    with gr.Tab("Character2Painting", elem_classes="CharTab") as Tab_Char:
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("""
                    <h1>⭐️ User Tips </h1>
                    <h2> <p><b>step1：</b> Input a Character.</p>
                    <p><b>step2：</b> Select a style in the Gallery</p>
                    <p><b>step3：</b> Click Run, Waiting for about 1 Min. Enjoy</p></h2>
                """)
                word_char = gr.Textbox(
                    label="Input Character",
                    info="please type Character, such as 李. (输入文字，例如，李)",
                    value="李",
                    elem_id="InputCha"
                )

                submit_char = gr.ClearButton(value="RunChar", elem_id="RunBtnChar")
                style_name_char = gr.Textbox(
                    label="style_name_char",
                    info="style_name_char",
                    value="", visible=False,
                )

            with gr.Column(scale=6):
                gr.HTML("""
                <h1 align="center">Style Gallery</h1>
                """)
                example_gallery_char = gr.Gallery(label="style_type_char", show_label=True,
                                                  elem_id="example_gallery_char",
                                                  value=list(style_example.keys()), columns=10
                                                  )
        # vis result gallery
        gr.HTML("""
        <h1 align="center">Result Gallery</h1>
        """)
        final_gallery_char = gr.Gallery(
            label="最终生成图",
            show_label=False,
            elem_classes="final_gallery_char", columns=[4], rows=[2]
        )

        submit_char.add([final_gallery_char])
        submit_char.click(send_to_server,
                          inputs=[word_char, style_name_char,WordArtModel],
                          outputs=[final_gallery_char])
        example_gallery_char.select(on_select_char, None,
                                    [style_name_char])
    with gr.Tab("Word2Painting", elem_classes="WordTab") as Tab_Word:
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("""
                    <h1>⭐️ User Tips </h1>
                    <h2> <p><b>step1：</b> Input a word. Max length: 4 for Chinese and 9 for English. </p>
                    <p><b>step2：</b> Select a style in the Gallery</p>
                    <p><b>step3：</b> Click Run, Waiting for about 1 Min. Enjoy</p></h2>
                """)
                word_word = gr.Textbox(
                    label="Input Word",
                    info="please type Word, such as 暴富. (输入词语，例如，暴富)",
                    value="暴富",
                    elem_id="InputWord"
                )

                submit_word = gr.ClearButton(value="RunWord", elem_id="RunBtnWord")
                style_name_word = gr.Textbox(
                    label="style_name_word",
                    info="style_name_word",
                    value="", visible=False,
                )

            with gr.Column(scale=6):
                gr.HTML("""
                <h1 align="center">Style Gallery</h1>
                """)
                example_gallery_word = gr.Gallery(label="style_type_word", show_label=True,
                                                  elem_id="example_gallery_word",
                                                  value=list(style_example_word.keys()), columns=5,
                                                  allow_preview=True, selected_index=0,
                                                  preview=True,
                                                  object_fit="scale-down",
                                                  )
        # vis result gallery
        gr.HTML("""
        <h1 align="center">Result Gallery</h1>
        """)
        final_gallery_word = gr.Gallery(
            label="最终生成图",
            show_label=False,
            elem_classes="final_gallery", columns=1,
            allow_preview=True, selected_index=0,
            preview=True,
            object_fit="scale-down",
        )

        submit_word.add([final_gallery_word])
        submit_word.click(send_to_server,
                          inputs=[word_word, style_name_word],
                          outputs=[final_gallery_word])
        example_gallery_word.select(on_select_word, None,
                                    [style_name_word])

    with gr.Tab("X2Painting", elem_classes="XTab") as Tab_X:
        gr.HTML("""
        <h1 align="center">Give me some time to train the model</h1>
    </br>
    <img src="https://raw.githubusercontent.com/antarestcguo/X2Painting/main/resources/loves.jpg" style="display: block; margin: 0 auto; max-height: 384px;">
    </br>
                        """)

demo.queue()
demo.launch(share=True, server_name="0.0.0.0", server_port=12404)
# demo.launch(share=True)
