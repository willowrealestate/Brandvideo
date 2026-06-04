#!/usr/bin/env python3
"""
Willow Real Estate — "CERTAIN" Brand Film v2
Editorial Premium — Higgsfield-inspired cinematic motion graphics
1920×1080 | 24fps | 90 seconds
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from moviepy import ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips, VideoClip
import os, sys, math, random

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
W, H   = 1920, 1080
FPS    = 24
OUT    = "WILLOW_CERTAIN_v2_Editorial.mp4"

# Cinematic letterbox: 2.39:1 aspect → bars ~11% top & bottom
BAR_H  = int(H * 0.111)   # 120px bars on 1080
SAFE_Y0 = BAR_H
SAFE_Y1 = H - BAR_H
SAFE_H  = SAFE_Y1 - SAFE_Y0  # 840px active image height

# Brand palette
DARK_BROWN  = (40,  32,  24)
BEIGE       = (242, 238, 235)
BEIGE_DIM   = (180, 172, 165)
BLACK_BG    = (16,  16,  16)
WHITE       = (255, 255, 255)
WARM_GOLD   = (205, 155,  65)
COBALT      = (18,  34,  72)
AMBER_DEEP  = (150,  80,  20)

# Fonts
SERIF_R = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_R  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ── LOGO GENERATION ───────────────────────────────────────────────────────────

def draw_willow_logomark(size=480, colour=BEIGE):
    """
    Programmatic recreation of the Willow branching-arch logomark.
    5 upward-arching branch forms in symmetric arrangement.
    Returns RGBA PIL Image.
    """
    W_, H_ = size, int(size * 1.08)
    img    = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d      = ImageDraw.Draw(img)
    fill   = (*colour, 255)
    stroke = max(8, int(size * 0.112))

    # 5 branches: (cx_frac, bottom_frac, total_h_frac, lean: -1/0/1, arc_spread_frac)
    branches = [
        (0.11, 1.00, 0.44, -1, 0.28),   # far-left  (shorter)
        (0.30, 1.00, 0.70, -1, 0.22),   # inner-left
        (0.50, 1.00, 0.86,  0, 0.00),   # centre    (tallest)
        (0.70, 1.00, 0.70,  1, 0.22),   # inner-right
        (0.89, 1.00, 0.44,  1, 0.28),   # far-right (shorter)
    ]

    for cx_f, bot_f, h_f, lean, spread in branches:
        cx      = int(W_ * cx_f)
        bot_y   = int(H_ * bot_f)
        bh      = int(H_ * h_f)
        top_y   = bot_y - bh

        x0 = cx - stroke // 2
        x1 = cx + stroke // 2

        if lean == 0:
            # Centre branch: pill/tombstone shape
            d.rectangle([x0, top_y + stroke // 2, x1, bot_y], fill=fill)
            d.ellipse(  [x0, top_y,  x1, top_y + stroke],     fill=fill)
        else:
            # Side branch: arc top + vertical stem
            arc_spread = int(W_ * spread)
            arc_h      = int(stroke * 2.8)

            # Stem: from where the arc ends downward
            stem_top = top_y + arc_h
            d.rectangle([x0, stem_top, x1, bot_y], fill=fill)

            # Arc: a wide shallow ellipse, only the outer half visible
            if lean == -1:
                arc_cx = cx - arc_spread
                el_x0  = arc_cx - stroke // 2
                el_x1  = cx     + stroke // 2
                el_y0  = top_y
                el_y1  = top_y + arc_h * 2
                # Draw thick arc (270→360 sweeps the top-right quarter → curves left)
                d.arc([el_x0, el_y0, el_x1, el_y1],
                      start=0, end=100, fill=fill, width=stroke)
                # Fill the stem connection
                d.rectangle([x0, top_y + arc_h, x1, stem_top + stroke], fill=fill)
            else:
                arc_cx = cx + arc_spread
                el_x0  = cx     - stroke // 2
                el_x1  = arc_cx + stroke // 2
                el_y0  = top_y
                el_y1  = top_y + arc_h * 2
                d.arc([el_x0, el_y0, el_x1, el_y1],
                      start=80, end=180, fill=fill, width=stroke)
                d.rectangle([x0, top_y + arc_h, x1, stem_top + stroke], fill=fill)

    return img


def draw_willow_wordmark(target_w=620, colour=BEIGE):
    """
    Render 'Willow' wordmark in bold — all lowercase except W.
    Returns RGBA PIL Image.
    """
    text = "Willow"
    try:
        # Use the boldest available font and scale to target width
        font_test = ImageFont.truetype(SANS_B, 180)
        dummy     = Image.new("RGBA", (1, 1))
        dd        = ImageDraw.Draw(dummy)
        bb        = dd.textbbox((0, 0), text, font=font_test)
        rendered_w = bb[2] - bb[0]
        # Scale font size to match target width
        font_size  = int(180 * target_w / rendered_w)
        font       = ImageFont.truetype(SANS_B, font_size)
    except Exception:
        font = ImageFont.load_default()

    dummy = Image.new("RGBA", (1, 1))
    dd    = ImageDraw.Draw(dummy)
    bb    = dd.textbbox((0, 0), text, font=font)
    tw    = bb[2] - bb[0] + 20
    th    = bb[3] - bb[1] + 20

    img  = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10 - bb[0], 10 - bb[1]), text, font=font, fill=(*colour, 255))
    return img


def draw_tagline(text, size=36, colour=BEIGE_DIM, max_w=800):
    """Render tagline with letter-spacing effect (editorial style)."""
    # Add extra space between chars for tracked/airy feel
    spaced = "  ".join(list(text.upper()))
    try:
        font = ImageFont.truetype(SANS_R, size)
    except Exception:
        font = ImageFont.load_default()
    dummy = Image.new("RGBA", (1,1))
    dd    = ImageDraw.Draw(dummy)
    bb    = dd.textbbox((0,0), spaced, font=font)
    tw    = bb[2] - bb[0] + 20
    th    = bb[3] - bb[1] + 20
    img   = Image.new("RGBA", (max(tw, 20), max(th, 20)), (0,0,0,0))
    draw  = ImageDraw.Draw(img)
    draw.text((10 - bb[0], 10 - bb[1]), spaced, font=font,
              fill=(*colour, 255))
    return img


# ── FRAME PRIMITIVES ──────────────────────────────────────────────────────────

def solid(c, w=W, h=H):
    return np.full((h, w, 3), c, dtype=np.uint8)

def gradient_v(c1, c2, w=W, h=H):
    t   = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(c1, float) * (1-t) + np.array(c2, float) * t)
    return np.broadcast_to(arr, (h, w, 3)).copy().astype(np.uint8)

def gradient_h(c1, c2, w=W, h=H):
    t   = np.linspace(0, 1, w)[None, :, None]
    arr = (np.array(c1, float) * (1-t) + np.array(c2, float) * t)
    return np.broadcast_to(arr, (h, w, 3)).copy().astype(np.uint8)

def radial(centre, edge, cx_f=0.5, cy_f=0.5, spread=0.55, w=W, h=H):
    y, x = np.mgrid[0:h, 0:w]
    r    = np.sqrt(((x/w - cx_f)/spread)**2 + ((y/h - cy_f)/spread)**2)
    r    = np.clip(r, 0, 1)
    return (np.array(centre, float)*(1-r[:,:,None]) +
            np.array(edge,   float)* r[:,:,None]).astype(np.uint8)

def vignette(frame, strength=0.55):
    h_, w_ = frame.shape[:2]
    y, x   = np.mgrid[0:h_, 0:w_]
    vx     = ((x / w_ - 0.5) * 2) ** 2
    vy     = ((y / h_ - 0.5) * 2) ** 2
    v      = np.clip(1 - (vx + vy) * strength, 0.0, 1.0)
    return (frame.astype(float) * v[:,:,None]).astype(np.uint8)

def film_grain(frame, t, amount=6):
    rng  = np.random.default_rng(int(t * 1000) % 9999)
    g    = rng.normal(0, amount, frame.shape).astype(float)
    return np.clip(frame.astype(float) + g, 0, 255).astype(np.uint8)

def letterbox(frame):
    """Paint the cinematic top and bottom bars onto the frame."""
    f = frame.copy()
    f[:BAR_H]  = 0
    f[SAFE_Y1:] = 0
    return f

def blend_frames(a, b, t):
    return (np.array(a, float) * (1-t) + np.array(b, float) * t).astype(np.uint8)


# ── COMPOSITE HELPER ──────────────────────────────────────────────────────────

def paste_rgba(base, rgba_arr, cx_f=0.5, cy_f=0.5, alpha_scale=1.0):
    """Blit an RGBA numpy array centred at (cx_f*W, cy_f*H) onto base."""
    base = base.copy()
    th, tw = rgba_arr.shape[:2]
    bh, bw = base.shape[:2]
    px  = int(bw * cx_f) - tw // 2
    py  = int(bh * cy_f) - th // 2
    px  = max(0, min(px, bw - tw))
    py  = max(0, min(py, bh - th))
    ah  = min(th, bh - py)
    aw  = min(tw, bw - px)
    if ah <= 0 or aw <= 0:
        return base
    alpha = rgba_arr[:ah, :aw, 3:4].astype(float) / 255.0 * alpha_scale
    region = base[py:py+ah, px:px+aw].astype(float)
    src    = rgba_arr[:ah, :aw, :3].astype(float)
    base[py:py+ah, px:px+aw] = np.clip(region*(1-alpha) + src*alpha, 0, 255).astype(np.uint8)
    return base

def pil_to_rgba_arr(pil_img):
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")
    return np.array(pil_img)

def text_arr(text, font_path, size, colour=BEIGE):
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception:
        font = ImageFont.load_default()
    dummy = Image.new("RGBA",(1,1))
    dd    = ImageDraw.Draw(dummy)
    bb    = dd.textbbox((0,0), text, font=font)
    tw    = max(bb[2]-bb[0]+20, 1)
    th    = max(bb[3]-bb[1]+20, 1)
    img   = Image.new("RGBA",(tw,th),(0,0,0,0))
    ImageDraw.Draw(img).text((10-bb[0], 10-bb[1]), text, font=font,
                              fill=(*colour, 255))
    return np.array(img)

def multiline_arr(text, font_path, size, colour=BEIGE, max_w=1300):
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception:
        font = ImageFont.load_default()
    dummy = Image.new("RGBA",(1,1))
    dd    = ImageDraw.Draw(dummy)
    words = text.split()
    lines = []
    line  = []
    for w_ in words:
        test = " ".join(line + [w_])
        bb   = dd.textbbox((0,0), test, font=font)
        if bb[2]-bb[0] > max_w and line:
            lines.append(" ".join(line))
            line = [w_]
        else:
            line.append(w_)
    if line:
        lines.append(" ".join(line))
    lh    = int(size * 1.45)
    tot_h = lh * len(lines) + 20
    max_lw = max((dd.textbbox((0,0),l,font=font)[2] for l in lines), default=1)
    img   = Image.new("RGBA",(max_lw+40, tot_h),(0,0,0,0))
    draw  = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        bb = draw.textbbox((0,0), l, font=font)
        lw = bb[2]-bb[0]
        x  = (max_lw+40-lw)//2
        draw.text((x, 10+i*lh-bb[1]), l, font=font, fill=(*colour,255))
    return np.array(img)


def fade_text(arr, t, t_in, t_out, dur, drift=True):
    """Apply fade-in / fade-out + optional subtle upward drift to a text arr."""
    if t < t_in:
        a = 0.0
    elif t - t_in < 0.5:
        a = (t - t_in) / 0.5
    elif dur - t < t_out:
        a = max(0.0, (dur - t) / t_out)
    else:
        a = 1.0
    out = arr.copy()
    out[:,:,3] = (out[:,:,3] * a).astype(np.uint8)
    return out


# ── THIN RULE ─────────────────────────────────────────────────────────────────

def rule_rgba(w=700, thick=1, colour=BEIGE_DIM, opacity=140):
    arr = np.zeros((thick+6, w, 4), dtype=np.uint8)
    arr[3:3+thick, :, :3] = colour
    arr[3:3+thick, :,  3] = opacity
    return arr


# ── SCENE BUILDERS ────────────────────────────────────────────────────────────

def scene_01():
    """THE STILL MORNING — 6s — Warm light beam, dark floor, dust motes."""
    dur = 6.0
    def frame(t):
        base   = solid(DARK_BROWN)
        prog   = t / dur

        # Beam: warm angled stripe
        y_, x_ = np.mgrid[0:H, 0:W]
        bx     = W * 0.38
        bw     = W * (0.14 + 0.05 * prog)
        diag   = (x_ - bx) - (y_ - H) * 0.25
        beam   = np.exp(-0.5 * (diag / (bw * 0.5))**2)
        inten  = 0.30 + 0.18 * prog
        f      = base.astype(float) + np.array(WARM_GOLD, float) * inten * beam[:,:,None]

        # Floor highlight gradient
        floor_g = np.exp(-((y_ - H*0.85)/(H*0.12))**2) * 0.12
        f      += np.array((80,55,20), float) * floor_g[:,:,None]

        # Dust motes
        rng = np.random.default_rng(42)
        for i in range(22):
            mx = int((rng.random() * W * 0.3 + W * 0.25 + t * (10+i*4)) % W)
            my = int((rng.random() * H * 0.7 + H * 0.1 + t * (2+i*1.5)) % H)
            r2 = max(2, i % 3 + 2)
            yy, xx = np.mgrid[max(0,my-r2):min(H,my+r2+1),
                               max(0,mx-r2):min(W,mx+r2+1)]
            mask  = ((xx-mx)**2+(yy-my)**2) <= r2**2
            b_val = beam[max(0,my-r2):min(H,my+r2+1),
                         max(0,mx-r2):min(W,mx+r2+1)]
            f[max(0,my-r2):min(H,my+r2+1),
              max(0,mx-r2):min(W,mx+r2+1)][mask] += 55 * b_val[mask][:,None]

        f = np.clip(f, 0, 255).astype(np.uint8)
        f = vignette(f, 0.65)
        f = film_grain(f, t, 4)
        fi = min(1.0, t / 1.5)
        fo = min(1.0, (dur - t) / 0.7)
        f  = (f * fi * fo).astype(np.uint8)
        return letterbox(f)
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_02():
    """THE WEIGHT OF CONSIDERATION — 8s"""
    dur  = 8.0
    vo   = multiline_arr('"At some point..."', SERIF_I, 62, BEIGE, 900)

    def frame(t):
        prog = t / dur
        # Warm interior — strong left light
        base = gradient_h((68, 50, 32), (20, 15, 10))
        # Strong window slash of light
        y_, x_ = np.mgrid[0:H, 0:W]
        wl = np.exp(-0.5*((x_-W*0.18)/(W*0.09))**2)
        wl *= np.exp(-0.5*((y_-H*0.48)/(H*0.52))**2)
        base = (base.astype(float) + np.array((120,90,40),float)*wl[:,:,None]*0.55).astype(np.uint8)
        base = vignette(base, 0.72)
        base = film_grain(base, t, 5)

        # Subtle camera push: slight crop-resize
        scale  = 1.0 + 0.015 * prog
        ch     = int(H / scale); cw = int(W / scale)
        oy     = (H-ch)//2;     ox = (W-cw)//2
        base   = np.array(Image.fromarray(base[oy:oy+ch, ox:ox+cw]).resize((W,H),Image.LANCZOS))

        if t > 1.8:
            vo_f = fade_text(vo, t, 1.8, 0.5, dur)
            # Drift upward slightly
            drift_y = int((1.0 - min(1.0,(t-1.8)/1.0)) * 18)
            base = paste_rgba(base, vo_f, 0.5, 0.76 - drift_y/H)

        fi = min(1.0, t/0.6); fo = min(1.0,(dur-t)/0.5)
        return letterbox((base * fi * fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_03():
    """ADELAIDE — 6s — Dusk gradient, city silhouette"""
    dur  = 6.0
    vo   = multiline_arr(
        "...you'll make a decision that will change everything.",
        SERIF_I, 56, BEIGE, 1150)
    loc  = text_arr("ADELAIDE   ·   SOUTH AUSTRALIA", SANS_R, 26, BEIGE_DIM)

    def frame(t):
        prog = t / dur
        sky_top = tuple(int(COBALT[i]*(1-prog*0.15) + (0,5,20)[i]*prog*0.15) for i in range(3))
        sky_mid = (140, 78, 28)
        sky_bot = (12, 9, 6)

        f = np.zeros((H,W,3),np.uint8)
        hs = int(H*0.60); hm = int(H*0.22)
        f[:hs]    = gradient_v(sky_top, sky_mid, h=hs)[:hs]
        f[hs:hs+hm] = gradient_v(sky_mid, sky_bot, h=hm)
        f[hs+hm:] = solid(sky_bot, h=H-hs-hm)[:H-hs-hm]

        # Atmospheric glow near horizon
        y_,x_ = np.mgrid[0:H,0:W]
        hor = np.exp(-((y_-H*0.60)/(H*0.06))**2)
        f = (f.astype(float) + np.array((180,100,30),float)*hor[:,:,None]*0.4).astype(np.uint8)

        # City silhouette — pan slowly right
        shift = int(t * 10)
        city_y = int(H*0.50)
        blds = [(150,230,int(H*.28)),(270,380,int(H*.34)),(410,455,int(H*.24)),
                (500,610,int(H*.30)),(660,720,int(H*.20)),(780,895,int(H*.36)),
                (940,1010,int(H*.22)),(1060,1170,int(H*.29)),(1220,1310,int(H*.26)),
                (1360,1440,int(H*.21)),(1490,1590,int(H*.31)),(1650,1730,int(H*.24)),
                (1770,1870,int(H*.28)),(50,130,int(H*.18)),(1900,1980,int(H*.19))]
        sil = (10,8,6)
        for bx1,bx2,bh in blds:
            bx1_s = (bx1+shift)%W; bx2_s = (bx2+shift)%W
            by = city_y - bh
            if bx1_s < bx2_s:
                f[by:city_y, bx1_s:bx2_s] = sil
            else:
                f[by:city_y, bx1_s:] = sil
                f[by:city_y, :bx2_s] = sil
        f[city_y:] = gradient_v((14,10,6),(6,4,2),h=H-city_y)

        f = vignette(f, 0.55)
        f = film_grain(f, t, 4)

        if t > 1.0:
            vo_f = fade_text(vo, t, 1.0, 0.5, dur)
            f    = paste_rgba(f, vo_f, 0.5, 0.80)
        if 1.8 < t < 5.5:
            la = loc.copy()
            a  = min(1.0,(t-1.8)/0.6) * min(1.0,(5.5-t)/0.5)
            la[:,:,3] = (la[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, la, 0.13, 0.92)

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/0.6)
        return letterbox((f*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_04():
    """THE DETAIL — 8s — 4 ECU segments"""
    dur    = 8.0
    vo     = multiline_arr("Your home is not a transaction.", SERIF_I, 64, WHITE, 950)
    labels = ["The Door","The Signature","The Key","The Beginning"]
    label_arrs = [text_arr(l.upper(), SANS_R, 28, BEIGE_DIM) for l in labels]
    glow_cs = [WARM_GOLD, (185,165,130), (195,185,175), WARM_GOLD]

    def frame(t):
        seg   = min(int(t/2), 3)
        local = t - seg*2
        prog  = local/2.0

        # ECU radial glow
        y_,x_ = np.mgrid[0:H,0:W]
        cx_,cy_ = W*0.5, H*0.48
        r  = np.sqrt(((x_-cx_)/(W*0.20))**2+((y_-cy_)/(H*0.20))**2)
        gw = np.exp(-r*r)*(0.55+0.15*prog)
        gc = np.array(glow_cs[seg], float)
        base = solid(DARK_BROWN).astype(float)
        base += gc*gw[:,:,None]*0.85
        base = np.clip(base,0,255).astype(np.uint8)

        # Hard-cut brightness flash
        if local < 0.06 and seg > 0:
            fl = local/0.06
            base = blend_frames(np.full_like(base,30), base, fl)

        base = vignette(base, 0.80)
        base = film_grain(base, t, 3)
        f    = base.copy()

        la = label_arrs[seg].copy()
        a  = min(1.0,local/0.35)*min(1.0,(2-local)/0.35)
        la[:,:,3] = (la[:,:,3]*a).astype(np.uint8)
        f  = paste_rgba(f, la, 0.5, 0.88)

        if t > 4.2:
            vo_f = fade_text(vo, t, 4.2, 0.5, dur)
            f    = paste_rgba(f, vo_f, 0.5, 0.75)

        fi = min(1.0,t/0.3); fo = min(1.0,(dur-t)/0.4)
        return letterbox((f*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_05():
    """THE AGENT — 8s — Premium interior, window city glow"""
    dur = 8.0
    vo  = multiline_arr("It's where your story lives.", SERIF_I, 66, BEIGE, 950)

    def frame(t):
        prog = t/dur
        base = gradient_h((18,13,8),(55,42,28))
        y_,x_ = np.mgrid[0:H,0:W]
        # City window: bright vertical band right side
        wg = np.exp(-((x_-W*0.78)/(W*0.14))**2)*np.exp(-((y_-H*0.5)/(H*0.5))**2)
        base = (base.astype(float)+np.array((70,85,130),float)*wg[:,:,None]*0.45).astype(np.uint8)
        # Warm floor bounce
        fg = np.exp(-((y_-H*0.90)/(H*0.12))**2)*0.25
        base = (base.astype(float)+np.array(WARM_GOLD,float)*fg[:,:,None]).astype(np.uint8)

        # Subtle pan
        shift = int(t * 6)
        base  = np.roll(base, shift, axis=1)

        base = vignette(base, 0.70)
        base = film_grain(base, t, 5)

        # Push: slight zoom
        scale = 1.0 + 0.018*prog
        ch = int(H/scale); cw = int(W/scale)
        oy = (H-ch)//2; ox = (W-cw)//2
        base = np.array(Image.fromarray(base[oy:oy+ch,ox:ox+cw]).resize((W,H),Image.LANCZOS))

        if t > 2.2:
            vo_f = fade_text(vo, t, 2.2, 0.5, dur)
            f    = paste_rgba(base, vo_f, 0.5, 0.80)
        else:
            f = base

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/0.5)
        return letterbox((f*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_06():
    """THE CONVERSATION — 8s — Warm table, being heard"""
    dur  = 8.0
    vo   = multiline_arr("We understand that.", SERIF_I, 76, WHITE, 850)
    rl   = rule_rgba(w=540, colour=BEIGE_DIM, opacity=160)

    def frame(t):
        base = radial((85,65,40),(15,11,7),cx_f=0.5,cy_f=0.42,spread=0.52)
        base = (base.astype(float)*
                (1.0 + 0.08*min(1.0,t/dur))).clip(0,255).astype(np.uint8)
        base = vignette(base, 0.72)
        base = film_grain(base, t, 4)

        if t > 1.5:
            a = min(1.0,(t-1.5)/0.5)
            r = rl.copy(); r[:,:,3]=(r[:,:,3]*a).astype(np.uint8)
            base = paste_rgba(base, r, 0.5, 0.72)
        if t > 2.3:
            vo_f = fade_text(vo, t, 2.3, 0.5, dur)
            base = paste_rgba(base, vo_f, 0.5, 0.78)

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/0.5)
        return letterbox((base*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_07():
    """ADELAIDE LIFE — 10s — 5 lifestyle segments"""
    dur  = 10.0
    segs = [
        {"top":(32,55,90), "bot":(12,25,45), "acc":(160,130,60),  "lbl":"THE SHORE"},
        {"top":(55,44,28), "bot":(22,17,10), "acc":WARM_GOLD,     "lbl":"THE HOME"},
        {"top":(45,40,25), "bot":(20,16,9),  "acc":(150,110,50),  "lbl":"THE MARKET"},
        {"top":(65,58,44), "bot":(28,22,15), "acc":BEIGE_DIM,     "lbl":"THE INTERIOR"},
        {"top":(42,52,26), "bot":(18,24,12), "acc":(170,135,55),  "lbl":"THE GARDEN"},
    ]
    seg_d   = dur / 5
    lbl_arrs = [text_arr(s["lbl"], SANS_R, 28, BEIGE_DIM) for s in segs]
    vo      = multiline_arr(
        "Every property we represent carries the weight of someone's future.",
        SERIF_I, 56, BEIGE, 1250)

    def frame(t):
        si    = min(int(t/seg_d), 4)
        loc_t = t - si*seg_d
        s     = segs[si]

        # Cross-dissolve
        if loc_t < 0.38 and si > 0:
            a   = loc_t/0.38
            ps  = segs[si-1]
            bg_a = gradient_v(ps["top"],ps["bot"])
            bg_b = gradient_v(s["top"], s["bot"])
            base = blend_frames(bg_a, bg_b, a)
        else:
            base = gradient_v(s["top"], s["bot"])

        y_,x_ = np.mgrid[0:H,0:W]
        r = np.sqrt(((x_/W-0.5)/0.48)**2+((y_/H-0.42)/0.42)**2)
        gw = np.exp(-r*1.6)*0.38
        base = (base.astype(float)+np.array(s["acc"],float)*gw[:,:,None]).astype(np.uint8)
        base = vignette(base, 0.65)
        base = film_grain(base, t, 4)

        la = lbl_arrs[si].copy()
        la[:,:,3] = (la[:,:,3]*min(1.0,loc_t/0.3)*min(1.0,(seg_d-loc_t)/0.3)).astype(np.uint8)
        f = paste_rgba(base, la, 0.5, 0.90)

        if t > 2.2:
            vo_f = fade_text(vo, t, 2.2, 0.7, dur)
            f    = paste_rgba(f, vo_f, 0.5, 0.80)

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/0.5)
        return letterbox((f*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_08():
    """THE WORK — 10s"""
    dur   = 10.0
    lbls  = ["THE ANALYSIS","THE INSPECTION","THE ADVOCACY","THE TEAM"]
    l_arrs= [text_arr(l, SANS_R, 28, BEIGE_DIM) for l in lbls]
    vo1   = multiline_arr("...and every client we serve",         SERIF_I, 56, BEIGE, 1050)
    vo2   = multiline_arr("deserves more than a transaction.",    SERIF_I, 56, BEIGE, 1050)
    bgs   = [
        (gradient_v((20,18,16),(9,8,7)),   (45,45,78)),
        (gradient_v((16,18,14),(8,9,7)),   (28,48,28)),
        (gradient_v((18,16,14),(9,8,7)),   (60,42,18)),
        (gradient_v((22,20,17),(11,10,8)), (28,28,28)),
    ]
    seg_d = dur / 4

    def frame(t):
        si    = min(int(t/seg_d), 3)
        loc_t = t - si*seg_d
        bg, acc = bgs[si]
        y_,x_ = np.mgrid[0:H,0:W]
        r = np.sqrt(((x_-W*0.62)/(W*0.42))**2+((y_-H*0.42)/(H*0.42))**2)
        gw = np.exp(-r*2.2)*0.22
        base = (bg.astype(float)+np.array(acc,float)*gw[:,:,None]).astype(np.uint8)
        if loc_t < 0.07 and si > 0:
            fl = loc_t/0.07
            base = blend_frames(np.full_like(base,22), base, fl)
        base = vignette(base, 0.72)
        base = film_grain(base, t, 4)

        la = l_arrs[si].copy()
        la[:,:,3]=(la[:,:,3]*min(1.0,loc_t/0.3)*min(1.0,(seg_d-loc_t)/0.3)).astype(np.uint8)
        f  = paste_rgba(base, la, 0.5, 0.90)

        if t > 3.2:
            v1 = fade_text(vo1, t, 3.2, 0.5, min(dur, 7.5))
            f  = paste_rgba(f, v1, 0.5, 0.75)
        if t > 5.8:
            v2 = fade_text(vo2, t, 5.8, 0.5, dur)
            f  = paste_rgba(f, v2, 0.5, 0.83)

        fi = min(1.0,t/0.4); fo = min(1.0,(dur-t)/0.5)
        return letterbox((f*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_09():
    """THE AFTER — 10s — Golden emotional peak"""
    dur  = 10.0
    vo   = multiline_arr("They deserve certainty.", SERIF_B, 88, WHITE, 950)
    sub  = multiline_arr("The moment after the achievement.", SANS_R, 34, BEIGE_DIM, 800)

    def frame(t):
        prog = t/dur
        g1   = blend_frames((75,52,16),(95,68,20), prog*0.2)
        g2   = blend_frames((30,22,8), (42,30,10), prog*0.2)
        base = gradient_v(g1, g2)

        y_,x_ = np.mgrid[0:H,0:W]
        # Sun glow upper right
        sg = np.exp(-((x_-W*0.78)/(W*0.32))**2-((y_-H*0.12)/(H*0.28))**2)
        sg *= (0.55+0.25*prog)
        base = (base.astype(float)+np.array((225,165,55),float)*sg[:,:,None]*0.65).astype(np.uint8)
        # Ground warmth
        gnd = np.exp(-((y_-H*0.78)/(H*0.15))**2)*0.20
        base = (base.astype(float)+np.array((180,120,40),float)*gnd[:,:,None]).astype(np.uint8)

        # Couple silhouette (two shapes)
        cy_ = int(H*0.46)
        for cx_ in [W//2-62, W//2+14]:
            bw_ = 44; bh_ = int(H*0.30)
            base[cy_:cy_+bh_, cx_:cx_+bw_] = (6,4,2)

        # House silhouette
        hy = int(H*0.18); hxl = int(W*0.22); hxr = int(W*0.78)
        pts = np.array([(W//2,hy),(hxr,int(H*0.38)),(hxr,int(H*0.47)),
                        (hxl,int(H*0.47)),(hxl,int(H*0.38))])
        pil_f = Image.fromarray(base)
        pil_d = ImageDraw.Draw(pil_f)
        pil_d.polygon([tuple(p) for p in pts], fill=(110,85,42))
        base  = np.array(pil_f)

        # Very slow push-in
        scale = 1.0+0.025*prog
        ch = int(H/scale); cw = int(W/scale)
        oy = (H-ch)//2; ox = (W-cw)//2
        base = np.array(Image.fromarray(base[oy:oy+ch,ox:ox+cw]).resize((W,H),Image.LANCZOS))

        base = vignette(base, 0.60)
        base = film_grain(base, t, 4)

        if t > 2.8:
            vo_f = fade_text(vo, t, 2.8, 0.7, dur)
            base = paste_rgba(base, vo_f, 0.5, 0.82)
        if t > 5.0:
            sf   = fade_text(sub, t, 5.0, 0.7, dur)
            base = paste_rgba(base, sf, 0.5, 0.91)

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/1.5)
        return letterbox((base*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_10():
    """THE WILLOW REVEAL — 10s — Pure black, logo materialises"""
    dur = 10.0

    # Pre-render logo assets
    print("    Rendering logomark...", flush=True)
    lm_pil   = draw_willow_logomark(size=320, colour=BEIGE)
    lm_arr   = pil_to_rgba_arr(lm_pil)

    print("    Rendering wordmark...", flush=True)
    wm_pil   = draw_willow_wordmark(target_w=580, colour=BEIGE)
    wm_arr   = pil_to_rgba_arr(wm_pil)

    sub_arr  = draw_tagline("Real Estate", size=38, colour=BEIGE_DIM)
    tag_arr  = draw_tagline("Adelaide's Premium Property Partner", size=30, colour=BEIGE_DIM)
    url_arr  = text_arr("willowrealestate.com.au", SANS_R, 30, (145,138,132))
    rl       = rule_rgba(w=600, colour=BEIGE_DIM, opacity=120)

    def frame(t):
        base = solid(BLACK_BG)
        # Subtle warm vignette-glow in centre
        y_,x_ = np.mgrid[0:H,0:W]
        cg = np.exp(-((x_-W*0.5)/(W*0.5))**2-((y_-H*0.5)/(H*0.5))**2)*0.08
        base = (base.astype(float)+np.array((60,45,30),float)*cg[:,:,None]).astype(np.uint8)
        base = film_grain(base, t, 3)
        f    = base.copy()

        # Logomark (emerges 0.8s)
        if t > 0.8:
            a  = min(1.0,(t-0.8)/1.2)
            lm = lm_arr.copy(); lm[:,:,3]=(lm[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, lm, 0.5, 0.33)

        # Wordmark (emerges 2.0s — letter-by-letter alpha cascade)
        if t > 2.0:
            # Each "W-i-l-l-o-w" letter staggered by 0.12s
            try:
                font = ImageFont.truetype(SANS_B, 130)
            except Exception:
                font = ImageFont.load_default()
            text_str = "Willow"
            dummy    = Image.new("RGBA",(1,1))
            dd       = ImageDraw.Draw(dummy)
            total_w_ = sum(dd.textbbox((0,0),ch,font=font)[2]-dd.textbbox((0,0),ch,font=font)[0]+4
                           for ch in text_str)
            cx_cur   = W//2 - total_w_//2
            cy_w     = int(H*0.535) - 65

            for i, ch in enumerate(text_str):
                t0    = 2.0 + i*0.12
                a_ch  = max(0.0, min(1.0,(t-t0)/0.30))
                if a_ch <= 0:
                    bb  = dd.textbbox((0,0),ch,font=font)
                    cx_cur += bb[2]-bb[0]+4
                    continue
                ch_img = Image.new("RGBA",(200,200),(0,0,0,0))
                ImageDraw.Draw(ch_img).text((0,0),ch,font=font,fill=(*BEIGE,255))
                ch_arr = np.array(ch_img)
                ch_arr[:,:,3]=(ch_arr[:,:,3]*a_ch).astype(np.uint8)
                f = paste_rgba(f, ch_arr, cx_f=(cx_cur+50)/W, cy_f=(cy_w+100)/H)
                bb  = dd.textbbox((0,0),ch,font=font)
                cx_cur += bb[2]-bb[0]+4

        # "Real Estate" subtext
        if t > 3.6:
            a  = min(1.0,(t-3.6)/0.6)
            sa = sub_arr.copy(); sa[:,:,3]=(sa[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, sa, 0.5, 0.595)

        # Rule
        if t > 4.5:
            a  = min(1.0,(t-4.5)/0.5)
            r  = rl.copy(); r[:,:,3]=(r[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, r, 0.5, 0.650)

        # Tagline
        if t > 5.2:
            a  = min(1.0,(t-5.2)/0.7)
            ta = tag_arr.copy(); ta[:,:,3]=(ta[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, ta, 0.5, 0.710)

        # URL
        if t > 6.2:
            a  = min(1.0,(t-6.2)/0.6)
            ua = url_arr.copy(); ua[:,:,3]=(ua[:,:,3]*a).astype(np.uint8)
            f  = paste_rgba(f, ua, 0.5, 0.760)

        fi = min(1.0,t/0.5)
        return letterbox((f*fi).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


def scene_11():
    """THE INVITATION — 6s — Light expands, door opens"""
    dur  = 6.0
    vo   = multiline_arr("Your next chapter begins here.", SERIF_B, 74, WHITE, 950)
    url  = text_arr("willowrealestate.com.au", SANS_R, 34, BEIGE_DIM)

    def frame(t):
        prog = t/dur
        base = solid(DARK_BROWN)
        y_,x_ = np.mgrid[0:H,0:W]

        # Expanding window light
        win_cx = W*0.42
        win_w  = W*(0.10+0.22*prog)
        wg = np.exp(-0.5*((x_-win_cx)/win_w)**2)*np.exp(-0.5*((y_-H*0.5)/(H*0.65))**2)
        base = (base.astype(float)+np.array((255,215,130),float)*wg[:,:,None]*(0.65+0.3*prog)).astype(np.uint8)

        # Floor warmth
        fg = np.exp(-((y_-H*0.88)/(H*0.10))**2)*0.18
        base = (base.astype(float)+np.array(WARM_GOLD,float)*fg[:,:,None]).astype(np.uint8)

        # Camera push toward light
        scale = 1.0+0.04*prog
        ch = int(H/scale); cw = int(W/scale)
        oy = (H-ch)//2; ox = (W-cw)//2
        base = np.array(Image.fromarray(base[oy:oy+ch,ox:ox+cw]).resize((W,H),Image.LANCZOS))

        base = vignette(base, 0.68)
        base = film_grain(base, t, 4)

        if t > 1.2:
            vo_f = fade_text(vo, t, 1.2, 0.8, dur)
            base = paste_rgba(base, vo_f, 0.5, 0.76)
        if t > 3.0:
            uf = url.copy()
            a  = min(1.0,(t-3.0)/0.6)*min(1.0,(dur-t)/0.7)
            uf[:,:,3]=(uf[:,:,3]*a).astype(np.uint8)
            base = paste_rgba(base, uf, 0.5, 0.86)

        fi = min(1.0,t/0.5); fo = min(1.0,(dur-t)/1.8)
        return letterbox((base*fi*fo).astype(np.uint8))
    return VideoClip(frame, duration=dur).with_fps(FPS)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  WILLOW REAL ESTATE — 'CERTAIN' v2  Editorial   ║")
    print("║  1920×1080  |  24fps  |  90 seconds             ║")
    print("╚══════════════════════════════════════════════════╝\n")

    scene_fns = [
        (scene_01, "01 — The Still Morning"),
        (scene_02, "02 — The Weight of Consideration"),
        (scene_03, "03 — Adelaide"),
        (scene_04, "04 — The Detail"),
        (scene_05, "05 — The Agent: Quiet Authority"),
        (scene_06, "06 — The Conversation"),
        (scene_07, "07 — Adelaide Life"),
        (scene_08, "08 — The Work"),
        (scene_09, "09 — The After"),
        (scene_10, "10 — The Willow Reveal"),
        (scene_11, "11 — The Invitation"),
    ]

    clips = []
    for fn, label in scene_fns:
        print(f"  Rendering Scene {label}...", flush=True)
        clips.append(fn())

    print("\n  Concatenating scenes...", flush=True)
    final = concatenate_videoclips(clips, method="compose")

    print(f"  Exporting {OUT}  ({final.duration:.0f}s)...", flush=True)
    final.write_videofile(
        OUT, fps=FPS, codec="libx264", audio=False,
        preset="medium", ffmpeg_params=["-crf","18"],
        logger="bar",
    )
    print(f"\n  ✓  {OUT}")

if __name__ == "__main__":
    main()
