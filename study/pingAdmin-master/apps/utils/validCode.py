import random

def get_random_color():
    """
    生产随机 颜色
    :return:
    """
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return color


def get_valid_code_img(request):
    """
    生产随机验证码图片
    :param request:
    :return:
    """
    # 图片生成模块  pip3 install pillow
    from PIL import Image
    # 画板工具
    from PIL import ImageDraw
    # 图片字体模块
    from PIL import ImageFont
    # 内存管理工具
    from io import BytesIO

    # 生成图片
    width = 270
    height = 40
    img = Image.new('RGB', (width, height), color=get_random_color())
    # 画板工具 写入文字
    draw = ImageDraw.Draw(img)
    # 字体设置
    set_font = ImageFont.truetype('static/blog/font/AaMangXiaoGuo-2.ttf', size=24)
    # 制作随机字符5位
    valid_code_str = ''  # 验证码字符串
    for i in range(5):
        random_num = str(random.randint(0, 9))  # 随机数字
        random_low_alpha = chr(random.randint(95, 122))  # 随机小写
        random_upper_alpha = chr(random.randint(65, 90))  # 随机大写
        # 随机选择一个
        random_char = random.choice([random_num, random_low_alpha, random_upper_alpha])
        # 写入字
        draw.text((i*50+20, 5), random_char, get_random_color(), font=set_font)  # 参数：位置，内容，颜色，字体
        # 保存验证码字符串,用来比对用户输入
        valid_code_str += random_char

    # 制作噪点，直线和点
    for i in range(3):
        x1 = random.randint(0, width)
        x2 = random.randint(0, width)
        y1 = random.randint(0, height)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=get_random_color())  # 画线

    for i in range(10):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=get_random_color())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x+4, y+4), 0, 90, fill=get_random_color())

    # 储存验证码值到Session中(便于分离各个用户)
    request.session['valid_code_str'] = valid_code_str
    f = BytesIO()  # 内存具柄
    img.save(f, 'png')
    data = f.getvalue()

    return data