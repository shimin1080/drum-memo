# Android のアイコンと起動画面を、iPhone 版と同じ 4x4 のマスの絵で書き出す。
# 使い方: python3 scripts/android-assets.py （Pillow が必要）
from PIL import Image, ImageDraw
import os

RES = os.path.join(os.path.dirname(__file__), '..', 'android', 'app', 'src', 'main', 'res')
ON = [[0, 1, 0, 0], [1, 0, 1, 1], [0, 1, 0, 1], [1, 0, 1, 0]]   # 塗るマス（アイコン・起動アニメーションと同じ）
LINE, FILL = (0x33, 0x33, 0x33, 255), (0xA0, 0xA0, 0xA0, 255)
DENS = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
SS = 4   # なめらかにするため大きく描いて縮める

# 1dp あたりの大きさ。アダプティブアイコンは 108dp のうち中央 72dp が見え、iPhone のアイコンと同じくその 60% をマスにする
GRID_ICON = 72 * 0.6            # ランチャーのアイコン（dp）
GRID_SPLASH = 116   # Android 12 以降の起動画面に出るマスの実測値（dp）。index.html の .is-android .intro-grid と同じ


def grid(img, cx, cy, g):
    """中心 (cx, cy)、一辺 g ピクセルのマスの絵を描く（寸法は index.html の .intro-grid と同じ比率）"""
    d = ImageDraw.Draw(img)
    cell, pitch, border, radius = g * .1934, g * .2705, g * .0164, g * .036
    x0, y0 = cx - g / 2, cy - g / 2
    for r in range(4):
        for c in range(4):
            x, y = x0 + c * pitch, y0 + r * pitch
            d.rounded_rectangle([x, y, x + cell, y + cell], radius=radius,
                                fill=FILL if ON[r][c] else (255, 255, 255, 255), outline=LINE, width=max(1, round(border)))


def render(w, h, draw):
    big = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    draw(big, SS)
    return big.resize((w, h), Image.LANCZOS)


def save(img, folder, name):
    path = os.path.join(RES, folder, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


for q, s in DENS.items():
    # アダプティブアイコンの前景（背景色は values/ic_launcher_background.xml の白）
    n = round(108 * s)
    save(render(n, n, lambda im, k: grid(im, n * k / 2, n * k / 2, GRID_ICON * s * k)), f'mipmap-{q}', 'ic_launcher_foreground.png')

    # Android 7 以前用の四角・丸のアイコン（48dp の中に 44dp の白地）
    n = round(48 * s)
    def square(im, k):
        m, e = 2 * s * k, n * k - 2 * s * k
        ImageDraw.Draw(im).rounded_rectangle([m, m, e, e], radius=8 * s * k, fill=(255, 255, 255, 255), outline=(0, 0, 0, 30), width=round(s * k / 2) or 1)
        grid(im, n * k / 2, n * k / 2, 44 * .6 * s * k)
    def circle(im, k):
        m, e = 2 * s * k, n * k - 2 * s * k
        ImageDraw.Draw(im).ellipse([m, m, e, e], fill=(255, 255, 255, 255), outline=(0, 0, 0, 30), width=round(s * k / 2) or 1)
        grid(im, n * k / 2, n * k / 2, 44 * .55 * s * k)
    save(render(n, n, square), f'mipmap-{q}', 'ic_launcher.png')
    save(render(n, n, circle), f'mipmap-{q}', 'ic_launcher_round.png')

# Android 11 以前の起動画面（全面の画像）。中央のマスは 12 以降・起動アニメーションと同じ大きさ
for f in os.listdir(RES):
    p = os.path.join(RES, f, 'splash.png')
    if not os.path.exists(p):
        continue
    w, h = Image.open(p).size
    q = f.split('-')[-1]
    s = DENS.get(q, 1)
    def splash(im, k):
        ImageDraw.Draw(im).rectangle([0, 0, w * k, h * k], fill=(255, 255, 255, 255))
        grid(im, w * k / 2, h * k / 2, GRID_SPLASH * s * k)
    save(render(w, h, splash).convert('RGB'), f, 'splash.png')

print(f'アイコンのマス {GRID_ICON:.1f}dp、起動画面のマス {GRID_SPLASH:.1f}dp で書き出しました')
