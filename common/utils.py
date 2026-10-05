"""通用工具：图形登录验证码（Pillow 绘制）、ORM 实体转字典、上传图片等比压缩。"""
import random
import string
from datetime import datetime

from io import BytesIO

# PIL是来自pillow第三方库中的
from PIL import Image, ImageFont, ImageDraw

# 登录验证码生成
class ImageCode():

    def get_text(self):
        list = random.sample(string.ascii_letters+string.digits,4)
        # print(list)
        return "".join(list)

    # 字符串颜色设置
    def rand_color(self):
        #rgb的颜色
        red = random.randint(0,255)
        blue = random.randint(0,255)
        green = random.randint(0,255)
        return (red, blue, green)

    # 干扰线设置
    def draw_lines(self,draw,num,width,height):
        for i in range(num):
            x1 = random.randint(0,width)
            y1 = random.randint(0,height)
            x2 = random.randint(0, width / 2)
            y2 = random.randint(height / 2, height)
            x3 = random.randint(0, width / 2)
            y3 = random.randint(0, height )
            draw.line([(x1,y1),(x2,y2)],fill=self.rand_color(),width=2)

    def draw_verify_code(self):
        # 生成随机字符串
        code = self.get_text()
        print(code)
        #设置图片的宽和高，在实际项目中最好和前端显示的图片大小一致，避免前端代码在重写
        width,height = 120,50
        img = Image.new("RGB",(width,height),"white")
        # font = ImageFont.truetype("arial.ttf",40)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except OSError:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(img)
        # 绘制字符串
        for i in range(4):
            draw.text((random.randint(3,10)+25*i,random.randint(3,10))
                      ,text=code[i],fill=self.rand_color(),font=font)

        # 绘制干扰线
        self.draw_lines(draw,3,width,height)

        # img.show()
        return img,code

    def get_code(self):
        image,code = self.draw_verify_code()
        buf = BytesIO()
        image.save(buf, format='JPEG')
        image_b_string = buf.getvalue()
        return code,image_b_string

# image_code = ImageCode()
# image_code.draw_verify_code()

# 评论实现的工具,转json的工具
def model_to_json(result):
    if result is None:
        return None
    dict = {}
    for k,v in result.__dict__.items():
        if not k.startswith("_sa_"):
            if isinstance(v,datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            dict[k] = v
    return dict

# UE图片压缩
def compress_image(source,dest,width=1200):
    im = Image.open(source)
    # 获取图片的宽和高
    x,y = im.size
    if x > width:
        #进行等比例压缩
        ys = int(y*width/x)
        xs = width
        #调整图片大小（Pillow 10+ 移除了 ANTIALIAS，改用 LANCZOS）
        temp = im.resize((xs,ys),Image.LANCZOS)
        temp.save(dest,quality=90)
    else:
        im.save(dest,quality=90)