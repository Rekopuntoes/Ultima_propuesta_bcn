"""Genera las texturas gráficas (dibones, toldos, pantallas) para la escena 3D del Mercat Pure Fresh."""
import os, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "3D", "tex")
os.makedirs(OUT, exist_ok=True)

AV = "/System/Library/Fonts/Avenir Next.ttc"
CH = "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"
def F(size, w="heavy"):
    idx = {"heavy": 8, "bold": 0, "demi": 2, "med": 5, "reg": 7}[w]
    return ImageFont.truetype(AV, size, index=idx)
def C(size, w=2):
    return ImageFont.truetype(CH, size, index=w)

BROWN = (74, 38, 24); DARK = (46, 26, 18); ORANGE = (226, 96, 27); CREAM = (251, 243, 232)
PEA = (92, 154, 46); YEL = (242, 194, 48); WHITE = (255, 255, 255); CHALK = (36, 40, 38)

def ctext(d, cx, y, s, font, fill):
    w = d.textlength(s, font=font)
    d.text((cx - w / 2, y), s, font=font, fill=fill)

def paste_fit(base, img_path, box, keep=True):
    im = Image.open(img_path).convert("RGBA")
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    r = min(bw / im.width, bh / im.height) if keep else max(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    px = x0 + (bw - im.width) // 2; py = y0 + (bh - im.height) // 2
    base.alpha_composite(im, (px, py)) if base.mode == "RGBA" else base.paste(im, (px, py), im)

def save(im, name):
    im.convert("RGB").save(os.path.join(OUT, name), quality=92) if name.endswith(".jpg") else im.save(os.path.join(OUT, name))

# 1 · Toldo a rayas con borde festoneado (alpha)
def awning():
    W, H = 2048, 512
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sw = 128
    for i in range(W // sw + 1):
        col = ORANGE if i % 2 == 0 else CREAM
        d.rectangle([i * sw, 0, i * sw + sw, H - 90], fill=col)
        d.pieslice([i * sw, H - 90 - sw // 2, i * sw + sw, H - 90 + sw // 2], 0, 180, fill=col)
    save(im, "awning.png")

# 2 · Pared Parada de la Carne (301 x 260 cm)
def wall_carne():
    W, H = 3010, 2600
    im = Image.new("RGBA", (W, H), ORANGE + (255,)); d = ImageDraw.Draw(im)
    # banda inferior marrón
    d.rectangle([0, 1650, W, H], fill=BROWN)
    ctext(d, W / 2, 1720, "70% CARNE FRESCA", F(190), CREAM)
    ctext(d, W / 2, 1960, "Sin harinas cárnicas · Sin cereales · Prensado en frío", F(80, "demi"), (240, 200, 170))
    # rótulo superior
    ctext(d, W / 2, 330, "EL PLATÓ DEL CUENCO LIMPIO", F(130), WHITE)
    im = logo(im, W / 2, 160, 560)
    save(im, "wall_carne.jpg")

# 3 · Pantalla LED cronómetro
def led():
    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), (20, 12, 9)); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 60, "RETO CUENCO LIMPIO", F(110), WHITE)
    d.rounded_rectangle([360, 230, 1560, 520], 40, fill=(40, 26, 20), outline=ORANGE, width=10)
    ctext(d, W / 2, 255, "00:12,4", F(200), YEL)
    ctext(d, W / 2, 560, "RÉCORD DEL DÍA · MINI / MEDMAX", F(56, "demi"), ORANGE)
    rows = [("1", "NALA · Gràcia", "00:09,8"), ("2", "TOBY · Eixample", "00:11,2"), ("3", "COCO · Sants", "00:12,4")]
    for i, (n, name, t) in enumerate(rows):
        y = 660 + i * 125
        d.rounded_rectangle([300, y, 1620, y + 105], 30, fill=(60, 40, 30))
        d.text((340, y + 18), n, font=F(64), fill=ORANGE)
        d.text((440, y + 22), name, font=F(58, "demi"), fill=WHITE)
        tw = d.textlength(t, font=F(64)); d.text((1580 - tw, y + 18), t, font=F(64), fill=YEL)
    save(im, "led.jpg")

# 4 · Frontal del mostrador (madera + etiqueta pizarra)
def counter_front():
    W, H = 2000, 950
    im = Image.new("RGBA", (W, H), (176, 122, 78, 255)); d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for y in range(0, H, 6):
        c = 160 + rnd.randint(-14, 14)
        d.line([(0, y), (W, y + rnd.randint(-3, 3))], fill=(c, int(c * 0.7), int(c * 0.45)), width=6)
    for x in range(0, W, 250):
        d.line([(x, 0), (x, H)], fill=(120, 80, 50), width=8)
    # pizarra
    d.rounded_rectangle([560, 230, 1440, 760], 40, fill=CHALK, outline=(150, 105, 70), width=24)
    ctext(d, 1000, 280, "70% carne fresca", C(96), WHITE)
    ctext(d, 1000, 430, "desde 0,83€", C(130), YEL)
    ctext(d, 1000, 600, "al día", C(80), WHITE)
    save(im, "counter_front.jpg")

# 5 · Alfombra del reto (redonda, alpha)
def cata_mat():
    S = 1600
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, S, S], fill=CREAM + (255,), outline=ORANGE + (255,), width=40)
    d.ellipse([S * 0.32, S * 0.32, S * 0.68, S * 0.68], outline=ORANGE + (255,), width=16)
    ctext(d, S / 2, S * 0.12, "CUENCO LIMPIO", F(100), BROWN)
    ctext(d, S / 2, S * 0.76, "¡A POR ÉL!", F(110), ORANGE)
    save(im, "cata_mat.png")

# 6 · Puente agility (vista superior)
def bridge():
    W, H = 2000, 400
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
    for i in range(W // 2):
        t = i / (W / 2)
    d.rectangle([0, 0, W // 2, H], fill=(196, 160, 120))
    d.rectangle([W // 2, 0, W, H], fill=ORANGE)
    d.text((80, 110), "PUENTE", font=F(170), fill=BROWN)
    d.text((W // 2 + 120, 110), "PURE FRESH →", font=F(150), fill=WHITE)
    for x in range(0, W, 100):
        d.rectangle([x, 0, x + 8, 30], fill=WHITE); d.rectangle([x, H - 30, x + 8, H], fill=WHITE)
    save(im, "bridge.jpg")

# 7 · Rótulos de cabecera genéricos
def header(name, text, sub, bg, fg, W=2000, H=400):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 70 if sub else 120, text, F(150), fg)
    if sub: ctext(d, W / 2, 260, sub, F(70, "demi"), fg)
    save(im, name)

# 8 · Plinko 70/30
def plinko():
    W, H = 1100, 1800
    im = Image.new("RGB", (W, H), BROWN); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 40, "PLINKO", F(150), WHITE)
    ctext(d, W / 2, 220, "70 / 30", F(110), ORANGE)
    d.rectangle([60, 380, W - 60, 1450], fill=CREAM)
    for r in range(11):
        for c in range(9):
            x = 120 + c * 105 + (52 if r % 2 else 0)
            y = 440 + r * 92
            if x < W - 90: d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(150, 110, 80))
    slots = ["MINI", "BOLSA", "MEDMAX", "6 KG", "MINI", "LLAVERO", "MEDMAX", "HUERTA"]
    sw = (W - 120) / len(slots)
    for i, s in enumerate(slots):
        x0 = 60 + i * sw
        d.rectangle([x0 + 4, 1460, x0 + sw - 4, 1760], fill=ORANGE if i < 6 else PEA)
        f = F(34)
        tw = d.textlength(s, font=f)
        tmp = Image.new("RGBA", (int(tw) + 10, 60), (0, 0, 0, 0)); ImageDraw.Draw(tmp).text((5, 5), s, font=f, fill=WHITE)
        tmp = tmp.rotate(90, expand=True)
        im.paste(tmp, (int(x0 + sw / 2 - tmp.width / 2), 1480), tmp)
    save(im, "plinko.jpg")

# 9 · Mosaico Muro de las 1.000 Miradas
def mosaic():
    pack = Image.open(os.path.join(A, "pack-salmon.png")).convert("RGBA")
    cols, rows = 40, 31
    small = Image.new("RGBA", pack.size, CREAM + (255,)); small.alpha_composite(pack)
    small = small.convert("RGB").resize((cols, rows // 1), Image.BILINEAR)
    small = Image.new("RGB", (cols, rows), CREAM)
    pk = pack.copy(); r = min(cols / pk.width, rows / pk.height) * 0.92
    pk = pk.resize((max(1, int(pk.width * r)), max(1, int(pk.height * r))), Image.BILINEAR)
    small.paste(pk, ((cols - pk.width) // 2, (rows - pk.height) // 2), pk)
    T = 64; W, H = cols * T, rows * T
    im = Image.new("RGB", (W, H), (240, 232, 220)); d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for y in range(rows):
        for x in range(cols):
            base = small.getpixel((x, y))
            if rnd.random() < 0.18 and base == CREAM:
                continue  # huecos aún sin foto
            k = 8 if base == CREAM else 22
            j = lambda v: max(0, min(255, v + rnd.randint(-k, k)))
            col = tuple(j(v) for v in base)
            x0, y0 = x * T + 3, y * T + 3
            d.rectangle([x0, y0, x0 + T - 6, y0 + T - 6], fill=col)
            # "foto": silueta suave de dos cabezas mirándose
            sh = tuple(max(0, v - 35) for v in col)
            d.ellipse([x0 + 10, y0 + 22, x0 + 26, y0 + 40], fill=sh)
            d.ellipse([x0 + 34, y0 + 26, x0 + 52, y0 + 44], fill=sh)
    save(im, "mosaic.jpg")

# 10 · Fondo del fotomatón (alcoba 170 x 260)
def backdrop():
    W, H = 1700, 2600
    im = Image.new("RGB", (W, H), (247, 232, 214)); d = ImageDraw.Draw(im)
    d.ellipse([-300, 1500, W + 300, H + 900], fill=(240, 220, 196))
    ctext(d, W / 2, 260, "Lo que de verdad", F(120, "demi"), BROWN)
    ctext(d, W / 2, 420, "le gusta", F(150), ORANGE)
    im = logo(im, W / 2, 2330, 420)
    save(im, "backdrop.jpg")

# 11 · Columna E (Huerta)
def huerta():
    W, H = 688, 2600
    im = Image.new("RGBA", (W, H), PEA + (255,)); d = ImageDraw.Draw(im)
    im = logo(im, W / 2, 2180, 560); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 120, "PARADA DE", F(70), WHITE)
    ctext(d, W / 2, 210, "LA HUERTA", F(92), WHITE)
    ctext(d, W / 2, 400, "+30%", F(200), YEL)
    ctext(d, W / 2, 640, "frutas y verduras", F(56, "demi"), WHITE)
    paste_fit(im, os.path.join(A, "bowl-burst.png"), (40, 950, W - 40, 1900))
    save(im, "huerta.png")

# 12 · Recepción A1
def recepcion():
    W, H = 1830, 2600
    im = Image.new("RGBA", (W, H), BROWN + (255,)); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 140, "BENVINGUTS AL", F(110), CREAM)
    ctext(d, W / 2, 290, "MERCAT", F(230), ORANGE)
    im = logo(im, W / 2, 680, 700); d = ImageDraw.Draw(im)
    kv = Image.open(os.path.join(A, "keyvisual.jpg")).convert("RGBA")
    r = W / kv.width; kv = kv.resize((W, int(kv.height * r)))
    im.alpha_composite(kv, (0, 900))
    d.rounded_rectangle([W / 2 - 260, 2020, W / 2 + 260, 2480], 30, fill=WHITE)
    ctext(d, W / 2, 2050, "CHECK-IN", F(70), BROWN)
    # QR simulado
    rnd = random.Random(1)
    for i in range(21):
        for j in range(21):
            if rnd.random() < 0.5 or (i < 7 and j < 7) or (i < 7 and j > 13) or (i > 13 and j < 7):
                if not ((1 < i < 5 and 1 < j < 5) or (1 < i < 5 and 15 < j < 19) or (15 < i < 19 and 1 < j < 5)) or (i in (2,3,4) and j in (2,3,4)):
                    d.rectangle([W / 2 - 157 + j * 15, 2150 + i * 15, W / 2 - 143 + j * 15, 2164 + i * 15], fill=DARK)
    save(im, "recepcion.png")

# 13 · Vinilo de suelo (camino de puntos)
def floor_dots():
    im = Image.new("RGBA", (2000, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in range(30, 2000, 120):
        d.ellipse([x, 20, x + 60, 80], fill=ORANGE + (255,))
    save(im, "dots.png")

# 14 · Sobre de muestra
def sachet():
    W, H = 500, 700
    im = Image.new("RGB", (W, H), ORANGE); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 90], fill=BROWN)
    ctext(d, W / 2, 140, "Pure", F(90), WHITE); ctext(d, W / 2, 240, "Fresh", F(90), WHITE)
    ctext(d, W / 2, 420, "MINI 100 g", F(50), CREAM)
    save(im, "sachet.jpg")

def bandana(col, name):
    im = Image.new("RGB", (400, 400), col); d = ImageDraw.Draw(im)
    for x in range(0, 400, 50):
        for y in range(0, 400, 50): d.ellipse([x + 18, y + 18, x + 32, y + 32], fill=CREAM)
    save(im, name)

def charms():
    W, H = 800, 500
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
    cols = [ORANGE, PEA, YEL, BROWN, (230, 120, 150), (90, 150, 210)]
    rnd = random.Random(7)
    for gx in range(4):
        for gy in range(3):
            x0, y0 = 20 + gx * 195, 20 + gy * 160
            d.rectangle([x0, y0, x0 + 180, y0 + 145], fill=(240, 230, 218), outline=(200, 185, 170), width=4)
            c = cols[(gx + gy * 4) % len(cols)]
            for _ in range(7):
                cx, cy = x0 + rnd.randint(25, 155), y0 + rnd.randint(25, 120)
                d.ellipse([cx - 14, cy - 10, cx + 14, cy + 16], fill=c)
                for k in (-14, -5, 5, 14): d.ellipse([cx + k - 5, cy - 24, cx + k + 5, cy - 14], fill=c)
    save(im, "charms.jpg")

def escaparate():
    W, H = 3000, 420
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    im = logo(im, 420, 200, 560); d = ImageDraw.Draw(im)
    ctext(d, W / 2 + 280, 20, "EL MERCAT PURE FRESH", F(150), WHITE)
    ctext(d, W / 2 + 280, 230, "70% carne fresca · Reto Cuenco Limpio", F(110, "demi"), YEL)
    save(im, "escaparate.png")

def alcove_street():
    W, H = 1640, 2200
    im = Image.new("RGBA", (W, H), ORANGE + (255,)); d = ImageDraw.Draw(im)
    im = logo(im, W / 2, 210, 640); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 400, "¿Cuánto tarda el tuyo?", F(96), WHITE)
    paste_fit(im, os.path.join(A, "pack-salmon.png"), (300, 560, W - 300, 1840))
    d.rounded_rectangle([200, 1880, W - 200, 2100], 40, fill=BROWN)
    ctext(d, W / 2, 1925, "Reserva su reto en la app", F(80), WHITE)
    save(im, "alcove_street.jpg")


# ===== Llavero de Recuerdo (fotomatón FunCity + taller) =====
DOGS = [os.path.join(A, f) for f in ("dog_a.jpg", "dog_b.jpg", "dog_c.jpg")]
def dogfit(path, w, h):
    im = Image.open(path).convert("RGB"); r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x = (im.width - w) // 2; y = (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

def paws(d, box, col, n, seed):
    r = random.Random(seed); x0, y0, x1, y1 = box
    for _ in range(n):
        cx, cy, k = r.randint(x0, x1), r.randint(y0, y1), r.uniform(0.6, 1.2)
        d.ellipse([cx - 22 * k, cy - 16 * k, cx + 22 * k, cy + 24 * k], fill=col)
        for dx in (-24, -8, 8, 24): d.ellipse([cx + dx * k - 8 * k, cy - 40 * k, cx + dx * k + 8 * k, cy - 22 * k], fill=col)

def photobooth_skin():
    S = 2048; BR2 = (107, 58, 36)
    im = Image.new("RGBA", (S, S), BR2 + (255,)); d = ImageDraw.Draw(im)
    # laterales (crema con huellas y círculo naranja abajo)
    for (x0, x1) in ((24, 380), (964, 1320)):
        d.rectangle([x0, 260, x1, 1126], fill=CREAM)
        paws(d, (x0 + 40, 320, x1 - 40, 800), (240, 210, 175), 6, x0)
        d.ellipse([x1 - 260, 900, x1 + 120, 1280], fill=ORANGE)
        im = logo(im, (x0 + x1) / 2, 560, (x1 - x0) * 0.8); d = ImageDraw.Draw(im)
    # frontal
    d.rectangle([416, 260, 930, 1126], fill=ORANGE)
    d.ellipse([800, 210, 1000, 410], fill=YEL); d.ellipse([360, 950, 560, 1150], fill=BROWN)
    ctext(d, 673, 760, "¡Foto al", F(78), WHITE); ctext(d, 673, 850, "instante!", F(78), WHITE)
    d.rounded_rectangle([470, 970, 876, 1050], 40, fill=BROWN)
    ctext(d, 673, 985, "3 FOTOS · 1 LLAVERO", F(40), CREAM)
    # cabecera superior
    d.rectangle([1340, 24, 1852, 580], fill=CREAM)
    im = logo(im, 1596, 250, 420); d = ImageDraw.Draw(im)
    ctext(d, 1596, 400, "Pure Fresh", F(60), ORANGE)
    # texto del pie
    ctext(d, 1600, 905, "LLAVERO DE RECUERDO", F(40), CREAM); ctext(d, 1600, 970, "ULTIMA PURE FRESH", F(40), YEL)
    d.rectangle([476, 1130, 874, 1696], fill=BROWN)
    d.rectangle([988, 1188, 1558, 1648], fill=ORANGE)
    d.rectangle([1588, 1172, 1904, 1340], fill=(25, 25, 25))
    # pantalla táctil
    d.rectangle([1588, 1386, 2016, 1624], fill=CREAM)
    im = logo(im, 1690, 1430, 150); d = ImageDraw.Draw(im)
    d.text((1610, 1480), "Toca para", font=F(36), fill=BROWN); d.text((1610, 1525), "empezar", font=F(36), fill=BROWN)
    d.ellipse([1840, 1430, 2000, 1590], fill=ORANGE); ctext(d, 1920, 1490, "FOTO", F(34), WHITE)
    d.rectangle([56, 1744, 520, 2024], fill=(25, 25, 25)); d.rectangle([140, 1770, 436, 1974], fill=BROWN)
    save(im, "photobooth_ultima.png")

def tira_fotomaton():
    W, H = 360, 1080
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
    for i, p in enumerate(DOGS):
        im.paste(dogfit(p, 320, 290), (20, 20 + i * 305))
    d.rectangle([0, 935, W, H], fill=ORANGE)
    im = logo(im, W / 2, 985, 200); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 1035, "Mercat Pure Fresh · BCN", F(24, "demi"), WHITE)
    save(im.convert("RGB"), "tira_fotomaton.png")

def foto_troquelada():
    save(dogfit(DOGS[0], 512, 495), "foto_troquelada.png")

def llavero_mock(w):
    h = int(w * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([w * 0.35, 0, w * 0.65, w * 0.3], outline=(190, 190, 195, 255), width=max(4, w // 40))
    d.rounded_rectangle([0, w * 0.3, w, h], w // 10, fill=(235, 242, 245, 230), outline=(200, 210, 215, 255), width=max(3, w // 60))
    im.paste(dogfit(DOGS[2], int(w * 0.8), int(w * 0.95)), (int(w * 0.1), int(w * 0.42)))
    d = ImageDraw.Draw(im); r = w * 0.17
    d.ellipse([w * 0.08, w * 0.22, w * 0.08 + 2 * r, w * 0.22 + 2 * r], fill=(196, 160, 80, 255))
    im = logo(im, w * 0.08 + r, w * 0.22 + r, r * 1.7); return im

def d1_pasos():
    W, H = 2550, 1730; BR2 = (107, 58, 36)
    im = Image.new("RGBA", (W, H), BR2 + (255,)); d = ImageDraw.Draw(im)
    im = logo(im, 330, 150, 460); d = ImageDraw.Draw(im)
    ctext(d, W / 2 + 200, 80, "TU LLAVERO EN 3 PASOS", F(140), CREAM)
    steps = [("1", "FOTO", "Posa en el fotomatón"), ("2", "TROQUELA", "Elige tu favorita"), ("3", "MONTA", "Placa y charms")]
    for i, (n, t, sub) in enumerate(steps):
        x0 = 120 + i * 620; d.rounded_rectangle([x0, 330, x0 + 560, 1580], 50, fill=CREAM)
        d.ellipse([x0 + 200, 380, x0 + 360, 540], fill=ORANGE); ctext(d, x0 + 280, 395, n, F(110), WHITE)
        ctext(d, x0 + 280, 1330, t, F(90), BROWN); ctext(d, x0 + 280, 1450, sub, F(50, "demi"), ORANGE)
        if i == 0: im.paste(dogfit(DOGS[1], 380, 640), (x0 + 90, 600))
        if i == 1:
            tira = Image.open(os.path.join(OUT, "tira_fotomaton.png")).resize((230, 690)); im.paste(tira, (x0 + 165, 590))
        if i == 2:
            pp = os.path.join(OUT, "_charms_src.png")
            ch = Image.open(os.path.join(OUT, "charms.jpg")).resize((460, 290)); im.paste(ch, (x0 + 50, 960))
            k = llavero_mock(260); im.alpha_composite(k, (x0 + 150, 570))
        d = ImageDraw.Draw(im)
    k = llavero_mock(560); im.alpha_composite(k, (1950, 420)); d = ImageDraw.Draw(im)
    ctext(d, 2230, 1300, "Su perro,", F(80), YEL); ctext(d, 2230, 1400, "en tus llaves", F(80), YEL)
    save(im, "d1_pasos.jpg")

def cartel_a4():
    W, H = 1240, 1754
    im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
    im = logo(im, W / 2, 200, 600); d = ImageDraw.Draw(im)
    ctext(d, W / 2, 420, "Tu llavero", F(130), BROWN); ctext(d, W / 2, 570, "en 3 pasos", F(130), ORANGE)
    for i, t in enumerate(["Hazte la foto en el fotomatón", "Elige tu favorita y troquélala", "Móntala en el llavero y elige charms"]):
        y = 820 + i * 260; d.ellipse([110, y, 270, y + 160], fill=ORANGE); ctext(d, 190, y + 20, str(i + 1), F(100), WHITE)
        d.text((320, y + 45), t, font=F(56, "demi"), fill=BROWN)
    save(im, "cartel_llavero.jpg")

LOGO = os.path.join(A, "logo-ultima.png")
def logo(im, cx, cy, w):
    lg = Image.open(LOGO).convert("RGBA"); h = int(lg.height * w / lg.width)
    lg = lg.resize((int(w), h), Image.LANCZOS)
    if im.mode != "RGBA":
        base = im.convert("RGBA"); base.alpha_composite(lg, (int(cx - w / 2), int(cy - h / 2))); return base
    im.alpha_composite(lg, (int(cx - w / 2), int(cy - h / 2))); return im

def brand_panel(name, W, H, bg, title=None, sub=None, logo_w=0.7, logo_y=0.22, kv=None, fg=WHITE, accent=YEL):
    im = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(im)
    im = logo(im, W / 2, H * logo_y, W * logo_w); d = ImageDraw.Draw(im)
    y = H * logo_y + W * logo_w * 0.32
    if title:
        for line in title.split("\n"):
            f = F(int(min(W * 0.11, 150))); ctext(d, W / 2, y, line, f, fg); y += f.size * 1.15
    if sub:
        for line in sub.split("\n"):
            f = F(int(min(W * 0.055, 70)), "demi"); ctext(d, W / 2, y + 20, line, f, accent); y += f.size * 1.3
    if kv:
        k = Image.open(kv).convert("RGBA"); r = W / k.width; k = k.resize((W, int(k.height * r)))
        im.alpha_composite(k, (0, H - k.height))
    save(im, name)

def brand_all():
    BR2 = (107, 58, 36)
    brand_panel("brand_B1.jpg", 2800, 2220, BR2, "Todo lo bueno de la comida fresca\nen un pienso", "70% carne fresca · prensado en frío", 0.34, 0.13,
                kv=os.path.join(A, "keyvisual.jpg"))
    brand_panel("brand_A5.jpg", 1020, 2220, ORANGE, "70%", "carne fresca", 0.78, 0.16)
    brand_panel("brand_C3.jpg", 1155, 2220, PEA, "RETO\n7 DÍAS\nFRESH", "Escanea · prueba · gana", 0.72, 0.15)
    brand_panel("brand_corto_o.jpg", 670, 2220, ORANGE, None, None, 0.86, 0.2)
    brand_panel("brand_corto_b.jpg", 490, 2220, BR2, None, None, 0.86, 0.2)
    brand_panel("brand_verde.jpg", 540, 2220, PEA, None, None, 0.86, 0.2)
    brand_panel("brand_B2.jpg", 1110, 2220, ORANGE, None, None, 0.7, 0.1)

if __name__ == "__main__":
    awning(); wall_carne(); led(); counter_front(); cata_mat(); bridge()
    header("hdr_cabina.jpg", "CÁMARA DE FRÍO", "Prensado en frío", BROWN, CREAM)
    header("hdr_gancho.jpg", "EL GANCHO FRESH", None, ORANGE, WHITE)
    header("hdr_muro.jpg", "MURO DE LAS 1.000 MIRADAS", None, BROWN, CREAM, W=2800, H=300)
    header("hdr_personaliza.jpg", "CREA SU LLAVERO", None, YEL, BROWN, W=2000, H=300)
    header("hdr_reto.jpg", "EMPIEZA TU RETO 7 DÍAS FRESH", "Escanea · prueba · gana", PEA, WHITE)
    plinko(); mosaic(); backdrop(); huerta(); recepcion(); floor_dots(); sachet()
    escaparate(); alcove_street(); brand_all(); bandana(ORANGE, "bandana_o.jpg"); bandana(PEA, "bandana_g.jpg"); charms()
    photobooth_skin(); tira_fotomaton(); foto_troquelada(); d1_pasos(); cartel_a4()
    print("ok", sorted(os.listdir(OUT)))
