#!/usr/bin/env python3
"""
Willow Real Estate — "CERTAIN"
Brand Introduction Film — Motion Graphics Version
90 seconds | 1920×1080 | 24fps
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    ImageClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, VideoClip, vfx
)
import os, sys

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
W, H   = 1920, 1080
FPS    = 24
OUT    = "WILLOW_CERTAIN_BrandFilm.mp4"

# Brand palette (RGB)
DARK_BROWN  = (40,  32,  24)
BEIGE       = (242, 238, 235)
BLACK_BG    = (22,  22,  22)
WHITE       = (255, 255, 255)
WARM_GOLD   = (210, 160,  70)
COBALT      = (18,  38,  80)
AMBER       = (160,  90,  30)
SAGE        = (60,  80,  55)

# Fonts
SERIF      = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS       = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ── IMAGE PRIMITIVES ──────────────────────────────────────────────────────────

def solid(colour, w=W, h=H):
    return np.full((h, w, 3), colour, dtype=np.uint8)

def gradient_v(c1, c2, w=W, h=H):
    t   = np.linspace(0, 1, h)[:, None, None]
    c1a = np.array(c1, dtype=float)
    c2a = np.array(c2, dtype=float)
    arr = (c1a * (1 - t) + c2a * t).astype(np.uint8)
    return np.broadcast_to(arr, (h, w, 3)).copy()

def gradient_h(c1, c2, w=W, h=H):
    t   = np.linspace(0, 1, w)[None, :, None]
    c1a = np.array(c1, dtype=float)
    c2a = np.array(c2, dtype=float)
    arr = (c1a * (1 - t) + c2a * t).astype(np.uint8)
    return np.broadcast_to(arr, (h, w, 3)).copy()

def radial_glow(centre_colour, edge_colour, cx_frac=0.5, cy_frac=0.4, w=W, h=H):
    cx, cy = int(w * cx_frac), int(h * cy_frac)
    y, x   = np.mgrid[0:h, 0:w]
    r      = np.sqrt(((x - cx) / (w * 0.6))**2 + ((y - cy) / (h * 0.6))**2)
    r      = np.clip(r, 0, 1)
    c1a    = np.array(centre_colour, dtype=float)
    c2a    = np.array(edge_colour,   dtype=float)
    arr    = (c1a * (1 - r[:, :, None]) + c2a * r[:, :, None]).astype(np.uint8)
    return arr

def blend(a, b, t):
    return (np.array(a, float) * (1 - t) + np.array(b, float) * t).astype(np.uint8)


# ── TEXT RENDERING ────────────────────────────────────────────────────────────

def pil_text(text, font_path, size, colour=(255,255,255), tracking=0):
    """Render text to RGBA numpy array via PIL."""
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception:
        font = ImageFont.load_default()
    dummy = Image.new("RGBA", (1, 1))
    dd    = ImageDraw.Draw(dummy)
    bbox  = dd.textbbox((0, 0), text, font=font)
    tw    = bbox[2] - bbox[0] + 20
    th    = bbox[3] - bbox[1] + 20
    img   = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw  = ImageDraw.Draw(img)
    draw.text((10, 10), text, font=font, fill=(*colour, 255))
    return np.array(img)

def pil_multiline(text, font_path, size, colour=(255,255,255),
                  max_w=1400, line_spacing=1.4):
    """Word-wrap text and render to RGBA numpy array."""
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception:
        font = ImageFont.load_default()

    words  = text.split()
    lines  = []
    line   = []
    dummy  = Image.new("RGBA", (1, 1))
    dd     = ImageDraw.Draw(dummy)

    for word in words:
        test = " ".join(line + [word])
        bbox = dd.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_w and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))

    line_h = int(size * line_spacing)
    total_h = line_h * len(lines) + 20
    max_lw  = 0
    for l in lines:
        bb  = dd.textbbox((0, 0), l, font=font)
        max_lw = max(max_lw, bb[2] - bb[0])

    img  = Image.new("RGBA", (max_lw + 40, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        bb = draw.textbbox((0, 0), l, font=font)
        lw = bb[2] - bb[0]
        x  = (max_lw + 40 - lw) // 2
        draw.text((x, 10 + i * line_h), l, font=font, fill=(*colour, 255))
    return np.array(img)


def overlay_text_arr(bg_arr, text_arr, cx_frac=0.5, cy_frac=0.5):
    """Composite an RGBA text array onto an RGB background array."""
    bg  = bg_arr.copy()
    th, tw = text_arr.shape[:2]
    cx  = int(W * cx_frac) - tw // 2
    cy  = int(H * cy_frac) - th // 2
    cx  = max(0, min(cx, W - tw))
    cy  = max(0, min(cy, H - th))
    alpha = text_arr[:, :, 3:4] / 255.0
    region = bg[cy:cy+th, cx:cx+tw]
    if region.shape[0] != th or region.shape[1] != tw:
        return bg
    bg[cy:cy+th, cx:cx+tw] = (
        region * (1 - alpha) + text_arr[:, :, :3] * alpha
    ).astype(np.uint8)
    return bg


def make_static_scene(bg_arr, text_lines, duration, fade_in=0.6, fade_out=0.6):
    """
    Build a VideoClip from a background array + list of text overlays.
    text_lines: list of dicts {arr, cy_frac, start, end, opacity_fn}
    """
    def make_frame(t):
        frame = bg_arr.copy()
        for tl in text_lines:
            t_start = tl.get("start", 0)
            t_end   = tl.get("end",   duration)
            if t < t_start or t > t_end:
                continue
            local   = t - t_start
            span    = t_end - t_start
            # opacity: fade in / fade out
            fi = tl.get("fi", 0.5)
            fo = tl.get("fo", 0.5)
            if local < fi:
                alpha = local / fi
            elif span - local < fo:
                alpha = (span - local) / fo
            else:
                alpha = 1.0
            alpha  = max(0.0, min(1.0, alpha))
            arr    = (tl["arr"] * np.array([1,1,1,alpha])).astype(np.uint8)
            arr[:,:,3] = (tl["arr"][:,:,3] * alpha).astype(np.uint8)
            frame  = overlay_text_arr(frame, arr,
                                      cx_frac=tl.get("cx", 0.5),
                                      cy_frac=tl.get("cy", 0.5))
        # Scene-level fade
        fade = 1.0
        if t < fade_in:
            fade = t / fade_in
        elif duration - t < fade_out:
            fade = (duration - t) / fade_out
        fade    = max(0.0, min(1.0, fade))
        bg_flat = bg_arr.copy()
        return (frame * fade).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


# ── THIN RULE ──────────────────────────────────────────────────────────────────

def rule_arr(colour=BEIGE, w=600, thick=1):
    """A thin horizontal rule as RGBA array."""
    arr          = np.zeros((thick + 4, w, 4), dtype=np.uint8)
    arr[2:2+thick, :, :3] = colour
    arr[2:2+thick, :, 3]  = 180
    return arr


# ── SCENE FACTORIES ──────────────────────────────────────────────────────────

def scene_01():
    """THE STILL MORNING — 6s — Warm light beam on dark floor."""
    duration = 6.0

    def make_frame(t):
        # Base: dark brown floor
        base = solid(DARK_BROWN)
        # Animated warm beam: a diagonal stripe that gently brightens
        progress  = t / duration  # 0→1
        beam_x    = int(W * 0.35)
        beam_w    = int(W * 0.18 + W * 0.04 * progress)
        y, x      = np.mgrid[0:H, 0:W]
        # Diagonal beam angle
        diag      = (x - beam_x) - (y - H) * 0.3
        beam_mask = np.exp(-0.5 * (diag / (beam_w * 0.5))**2)
        intensity = 0.35 + 0.15 * progress
        glow      = np.array(WARM_GOLD, dtype=float) * intensity
        base      = base.astype(float)
        base      += glow[None, None, :] * beam_mask[:, :, None]
        base      = np.clip(base, 0, 255).astype(np.uint8)

        # Dust motes: small bright circles at random positions
        np.random.seed(42)
        for i in range(18):
            mx = int((W * 0.28 + W * 0.2 * np.random.rand()) %
                     W)
            my = int((H * 0.1 + H * 0.8 * np.random.rand()) %
                     H)
            # Slight drift over time
            mx = int((mx + t * (15 + 5 * i)) % W)
            my = int((my + t * (3  + 2 * i)) % H)
            radius = 2 + i % 3
            y2, x2 = np.mgrid[
                max(0, my-radius):min(H, my+radius+1),
                max(0, mx-radius):min(W, mx+radius+1)
            ]
            mask = ((x2-mx)**2 + (y2-my)**2 <= radius**2)
            brightness = 0.6 + 0.3 * beam_mask[
                max(0,my-radius):min(H,my+radius+1),
                max(0,mx-radius):min(W,mx+radius+1)
            ]
            base[
                max(0,my-radius):min(H,my+radius+1),
                max(0,mx-radius):min(W,mx+radius+1),
                :
            ][mask] = np.clip(
                base[
                    max(0,my-radius):min(H,my+radius+1),
                    max(0,mx-radius):min(W,mx+radius+1),
                    :
                ][mask].astype(float) + 60, 0, 255
            ).astype(np.uint8)

        # Scene-level fade in
        fi = min(1.0, t / 1.2)
        return (base * fi).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_02():
    """THE WEIGHT OF CONSIDERATION — 8s"""
    duration = 8.0

    vo_arr   = pil_multiline(
        '"At some point..."',
        SERIF, 64, colour=BEIGE, max_w=900
    )
    sub_arr  = pil_multiline(
        "~ voiceover begins ~",
        SANS, 28, colour=(180, 170, 160), max_w=600
    )

    def make_frame(t):
        # Warm dark interior with a left-side window light suggestion
        base = gradient_h(
            (55, 42, 30),   # warm brown left (window)
            (28, 22, 16),   # darker right
        )
        # Vignette
        y, x    = np.mgrid[0:H, 0:W]
        vx      = ((x - W/2) / (W/2))**2
        vy      = ((y - H/2) / (H/2))**2
        vig     = np.clip(1 - (vx + vy) * 0.5, 0.35, 1)
        base    = (base * vig[:,:,None]).astype(np.uint8)

        frame   = base.copy()

        # VO text fades in at t=1.5
        if t > 1.5:
            local = t - 1.5
            span  = duration - 1.5
            fi_   = min(1.0, local / 0.8)
            fo_   = min(1.0, (span - local) / 0.5) if span - local < 0.5 else 1.0
            alpha = fi_ * fo_
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.78)

        # Scene fade
        fi  = min(1.0, t / 0.6)
        fo  = min(1.0, (duration - t) / 0.4)
        fade= fi * fo
        return (frame * fade).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_03():
    """ADELAIDE — 6s — Dusk gradient"""
    duration = 6.0

    vo_arr  = pil_multiline(
        "...you'll make a decision that will change everything.",
        SERIF, 58, colour=BEIGE, max_w=1100
    )
    loc_arr = pil_text(
        "Adelaide, South Australia",
        SANS, 30, colour=(200, 195, 188)
    )

    def make_frame(t):
        progress = t / duration
        # Sky: cobalt top → amber horizon → dark ground
        sky_top  = blend(COBALT, (25, 45, 90),  progress * 0.3)
        sky_mid  = blend((140, 80, 30), (160, 95, 40), progress * 0.2)
        sky_bot  = blend((20, 15, 10), (30, 22, 14), 0)

        frame    = np.zeros((H, W, 3), dtype=np.uint8)
        h_sky    = int(H * 0.65)
        h_mid    = int(H * 0.20)
        h_bot    = H - h_sky - h_mid

        frame[:h_sky] = gradient_v(sky_top, sky_mid, h=h_sky)[:h_sky]
        frame[h_sky:h_sky+h_mid] = gradient_v(sky_mid, sky_bot, h=h_mid)
        frame[h_sky+h_mid:] = solid(sky_bot, h=h_bot)[:h_bot]

        # City silhouette: simple dark bars
        city_y = int(H * 0.52)
        buildings = [
            (200, 280, int(H*0.25)),
            (320, 400, int(H*0.30)),
            (450, 490, int(H*0.22)),
            (550, 640, int(H*0.28)),
            (700, 760, int(H*0.18)),
            (820, 920, int(H*0.32)),
            (960, 1010, int(H*0.20)),
            (1060, 1150, int(H*0.27)),
            (1200, 1290, int(H*0.24)),
            (1360, 1420, int(H*0.19)),
            (1480, 1580, int(H*0.29)),
            (1640, 1720, int(H*0.22)),
            (1760, 1860, int(H*0.26)),
        ]
        silhouette_colour = np.array([12, 10, 8], dtype=np.uint8)
        for (bx1, bx2, bh) in buildings:
            by  = city_y - bh
            frame[by:city_y, bx1:bx2] = silhouette_colour

        # Ground
        frame[city_y:] = gradient_v((15, 12, 8), (8, 6, 4), h=H-city_y)

        # Slow camera-pan illusion: shift image slightly over time
        shift = int(t * 8)
        frame = np.roll(frame, -shift, axis=1)

        # VO text
        if t > 1.0:
            local = t - 1.0
            span  = duration - 1.0
            alpha = min(1.0, local / 0.8) * min(1.0, (span - local) / 0.5)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.80)

        # Location tag (bottom left)
        if t > 2.0 and t < 5.5:
            local = t - 2.0
            alpha = min(1.0, local / 0.6) * min(1.0, (5.5 - t) / 0.5)
            loc   = loc_arr.copy()
            loc[:,:,3] = (loc[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, loc, cx_frac=0.12, cy_frac=0.93)

        fi   = min(1.0, t / 0.5)
        fo   = min(1.0, (duration - t) / 0.5)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_04():
    """THE DETAIL SEQUENCE — 8s (4 × 2s)"""
    duration = 8.0

    vo_arr  = pil_multiline(
        "Your home is not a transaction.",
        SERIF, 62, colour=WHITE, max_w=900
    )

    # Four detail labels
    details = [
        {"label": "The Door",     "bg": gradient_v((55,38,22),(22,16,10)), "t0": 0, "t1": 2},
        {"label": "The Signature","bg": gradient_v((38,30,20),(18,14,8)),  "t0": 2, "t1": 4},
        {"label": "The Key",      "bg": gradient_v((45,35,22),(20,15,9)),  "t0": 4, "t1": 6},
        {"label": "The Beginning","bg": gradient_v((60,45,30),(28,20,12)), "t0": 6, "t1": 8},
    ]
    detail_arrs = [
        pil_text(d["label"], SANS, 34, colour=(180,168,150))
        for d in details
    ]

    # ECU-style glow circles for each detail
    def detail_glow(centre_colour, progress):
        arr = solid(DARK_BROWN)
        cx, cy = W//2, H//2
        y, x   = np.mgrid[0:H, 0:W]
        r      = np.sqrt(((x-cx)/(W*0.22))**2 + ((y-cy)/(H*0.22))**2)
        glow   = np.exp(-r*r) * (0.6 + 0.2*progress)
        arr    = arr.astype(float)
        arr   += np.array(centre_colour, float)[None,None,:] * glow[:,:,None] * 0.9
        return np.clip(arr, 0, 255).astype(np.uint8)

    glow_colours = [WARM_GOLD, (190,170,140), (200,190,180), WARM_GOLD]

    def make_frame(t):
        seg   = int(t / 2)
        seg   = min(seg, 3)
        local = t - seg * 2
        prog  = local / 2.0

        bg    = detail_glow(glow_colours[seg], prog)

        # Hard-cut flash on new segment (first 0.05s slightly brighter)
        if local < 0.08 and seg > 0:
            flash = min(1.0, local / 0.08)
            bg    = blend(WHITE, bg, flash)

        # Detail label
        darr  = detail_arrs[seg].copy()
        label_alpha = min(1.0, local / 0.3) * min(1.0, (2 - local) / 0.3)
        darr[:,:,3] = (darr[:,:,3] * label_alpha).astype(np.uint8)
        frame = overlay_text_arr(bg, darr, cx_frac=0.5, cy_frac=0.88)

        # VO text in second half
        if t > 4.0:
            alpha = min(1.0, (t - 4.0) / 0.8) * min(1.0, (duration - t) / 0.5)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.75)

        return frame

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_05():
    """THE AGENT: QUIET AUTHORITY — 8s"""
    duration = 8.0

    vo_arr = pil_multiline(
        "It's where your story lives.",
        SERIF, 64, colour=BEIGE, max_w=900
    )

    def make_frame(t):
        progress = t / duration
        # Brooding premium interior — dark warm → window light right
        base = gradient_h(
            (22, 17, 12),
            blend((90, 70, 45), (40, 30, 18), 1 - progress * 0.5),
        )
        # Slow camera-pan: subtle shift
        shift = int(t * 5)
        base  = np.roll(base, shift, axis=1)

        # City window glow on right side
        y, x   = np.mgrid[0:H, 0:W]
        wg     = np.exp(-((x - W*0.75) / (W*0.18))**2) * np.exp(-((y - H*0.5) / (H*0.45))**2)
        base   = (base.astype(float) + np.array((80, 90, 120), float)[None,None,:] * wg[:,:,None] * 0.4).astype(np.uint8)

        frame  = base.copy()
        if t > 2.0:
            alpha = min(1.0, (t-2.0)/0.9) * min(1.0, (duration-t)/0.5)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.80)

        fi = min(1.0, t/0.5); fo = min(1.0, (duration-t)/0.5)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_06():
    """THE CONVERSATION — 8s"""
    duration = 8.0

    vo_arr   = pil_multiline(
        "We understand that.",
        SERIF, 72, colour=WHITE, max_w=800
    )
    rule_a   = rule_arr(colour=BEIGE, w=500)

    def make_frame(t):
        # Warm meeting table interior
        base  = radial_glow(
            blend((80, 60, 38), (100, 75, 45), min(1, t/duration)),
            (18, 14, 10),
            cx_frac=0.5, cy_frac=0.42
        )
        frame = base.copy()

        # Thin rule appears first
        if t > 1.5:
            ralpha = min(1.0, (t-1.5)/0.5)
            ra     = rule_a.copy()
            ra[:,:,3] = (ra[:,:,3] * ralpha).astype(np.uint8)
            frame  = overlay_text_arr(frame, ra, cx_frac=0.5, cy_frac=0.73)

        # VO
        if t > 2.2:
            alpha = min(1.0, (t-2.2)/0.8) * min(1.0, (duration-t)/0.5)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.78)

        fi = min(1.0, t/0.5); fo = min(1.0, (duration-t)/0.5)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_07():
    """ADELAIDE LIFE — 10s — Five lifestyle moments"""
    duration = 10.0

    segments = [
        {
            "label":   "The Shore",
            "bg_top":  (40,  65, 100),
            "bg_bot":  (20,  35,  55),
            "accent":  (180, 140,  70),
        },
        {
            "label":   "The Home",
            "bg_top":  (60,  50,  35),
            "bg_bot":  (28,  22,  14),
            "accent":  WARM_GOLD,
        },
        {
            "label":   "The Market",
            "bg_top":  (50,  45,  30),
            "bg_bot":  (25,  20,  12),
            "accent":  (160, 120,  60),
        },
        {
            "label":   "The Interior",
            "bg_top":  (70,  62,  50),
            "bg_bot":  (30,  25,  18),
            "accent":  BEIGE,
        },
        {
            "label":   "The Garden",
            "bg_top":  (45,  55,  30),
            "bg_bot":  (22,  28,  14),
            "accent":  WARM_GOLD,
        },
    ]
    seg_dur    = duration / 5.0  # 2s each
    seg_labels = [pil_text(s["label"], SANS, 32, colour=(200,190,175)) for s in segments]

    vo_arr     = pil_multiline(
        "Every property we represent carries the weight of someone's future.",
        SERIF, 56, colour=BEIGE, max_w=1200
    )

    def make_frame(t):
        seg     = min(int(t / seg_dur), 4)
        local   = t - seg * seg_dur
        s       = segments[seg]

        # Cross-dissolve between segments
        if local < 0.35 and seg > 0:
            alpha_blend = local / 0.35
            prev        = segments[seg - 1]
            bg_a        = gradient_v(prev["bg_top"], prev["bg_bot"])
            bg_b        = gradient_v(s["bg_top"],    s["bg_bot"])
            base        = blend(bg_a, bg_b, alpha_blend)
        else:
            base = gradient_v(s["bg_top"], s["bg_bot"])

        # Radial accent glow
        y, x   = np.mgrid[0:H, 0:W]
        r      = np.sqrt(((x - W/2)/(W*0.45))**2 + ((y - H*0.4)/(H*0.4))**2)
        glow   = np.exp(-r * 1.5) * 0.35
        base   = (base.astype(float) + np.array(s["accent"], float)[None,None,:] * glow[:,:,None]).astype(np.uint8)

        frame  = base.copy()

        # Segment label
        la     = seg_labels[seg].copy()
        l_alp  = min(1.0, local/0.3) * min(1.0, (seg_dur - local)/0.3)
        la[:,:,3] = (la[:,:,3] * l_alp).astype(np.uint8)
        frame  = overlay_text_arr(frame, la, cx_frac=0.5, cy_frac=0.90)

        # VO from t=2
        if t > 2.0:
            alpha = min(1.0, (t-2.0)/1.0) * min(1.0, (duration-t)/0.6)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.80)

        fi = min(1.0, t/0.5); fo = min(1.0, (duration-t)/0.5)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_08():
    """THE WORK — 10s"""
    duration = 10.0

    moments = [
        "The Analysis",
        "The Inspection",
        "The Advocacy",
        "The Team",
    ]
    m_dur     = duration / 4.0
    m_arrs    = [pil_text(m, SANS, 30, colour=(180,170,155)) for m in moments]
    vo1_arr   = pil_multiline(
        "...and every client we serve",
        SERIF, 56, colour=BEIGE, max_w=1000
    )
    vo2_arr   = pil_multiline(
        "deserves more than a transaction.",
        SERIF, 56, colour=BEIGE, max_w=1000
    )
    vo_bgs    = [
        (gradient_v((22,20,18),(10,9,8)),  (50,50,80)),
        (gradient_v((18,20,16),(9,10,8)),  (30,50,30)),
        (gradient_v((20,18,16),(10,9,8)),  (50,40,20)),
        (gradient_v((25,22,18),(12,10,8)), (30,30,30)),
    ]

    def make_frame(t):
        seg    = min(int(t / m_dur), 3)
        local  = t - seg * m_dur

        bg, accent = vo_bgs[seg]

        # Glow
        y, x   = np.mgrid[0:H, 0:W]
        r      = np.sqrt(((x - W*0.6)/(W*0.4))**2 + ((y - H*0.4)/(H*0.4))**2)
        glow   = np.exp(-r * 2.0) * 0.25
        base   = (bg.astype(float) + np.array(accent, float)[None,None,:] * glow[:,:,None]).astype(np.uint8)

        # Hard cut flash on segment boundary
        if local < 0.07 and seg > 0:
            flash = local / 0.07
            base  = blend(
                np.full_like(base, 40),
                base, flash
            )

        frame  = base.copy()
        marr   = m_arrs[seg].copy()
        m_alp  = min(1.0, local/0.3) * min(1.0, (m_dur - local)/0.3)
        marr[:,:,3] = (marr[:,:,3] * m_alp).astype(np.uint8)
        frame  = overlay_text_arr(frame, marr, cx_frac=0.5, cy_frac=0.90)

        # VO line 1 from t=3
        if t > 3.0:
            alpha = min(1.0, (t-3.0)/0.8) * min(1.0, (7.0-t)/0.5 if t<7 else 1)
            alpha = max(0, alpha)
            txt   = vo1_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.75)

        # VO line 2 from t=5.5
        if t > 5.5:
            alpha = min(1.0, (t-5.5)/0.8) * min(1.0, (duration-t)/0.5)
            txt   = vo2_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.83)

        fi = min(1.0, t/0.4); fo = min(1.0, (duration-t)/0.5)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_09():
    """THE AFTER — 10s — GOLDEN PEAK"""
    duration = 10.0

    vo_arr  = pil_multiline(
        "They deserve certainty.",
        SERIF_BOLD, 82, colour=WHITE, max_w=900
    )
    sub_arr = pil_multiline(
        "The moment after the achievement.",
        SANS, 34, colour=(210, 195, 170), max_w=800
    )

    def make_frame(t):
        progress = t / duration

        # Deep golden exterior — warm afternoon light
        gold_top = blend((80, 55, 18), (100, 70, 22), progress * 0.2)
        gold_bot = blend((35, 25, 10), (45,  32, 12), progress * 0.2)
        base     = gradient_v(gold_top, gold_bot)

        # Warm sun glow from upper-right
        y, x     = np.mgrid[0:H, 0:W]
        sg       = np.exp(-((x - W*0.75)/(W*0.35))**2 - ((y - H*0.15)/(H*0.35))**2)
        sg      *= (0.5 + 0.3 * progress)
        base     = (base.astype(float) + np.array((220,160,60), float)[None,None,:] * sg[:,:,None] * 0.6).astype(np.uint8)

        # Long shadow band across ground
        shadow   = np.exp(-((y - H*0.7)/(H*0.04))**2) * 0.3
        base     = (base.astype(float) * (1 - shadow[:,:,None])).astype(np.uint8)

        # Silhouette of couple (two rectangles)
        couple_y = int(H * 0.50)
        for cx_ in [W//2 - 55, W//2 + 10]:
            bw = 40; bh = int(H*0.28)
            base[couple_y:couple_y+bh, cx_:cx_+bw] = (8, 6, 4)

        # Home silhouette in background
        home_y   = int(H * 0.25)
        base[home_y:int(H*0.52), int(W*0.25):int(W*0.75)] = np.minimum(
            base[home_y:int(H*0.52), int(W*0.25):int(W*0.75)],
            np.full_like(base[home_y:int(H*0.52), int(W*0.25):int(W*0.75)], (140, 110, 60))
        )

        frame    = base.copy()

        if t > 2.5:
            alpha = min(1.0, (t-2.5)/1.0) * min(1.0, (duration-t)/0.7)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.82)

        if t > 4.5:
            alpha = min(1.0, (t-4.5)/0.8) * min(1.0, (duration-t)/0.7)
            txt   = sub_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.91)

        fi = min(1.0, t/0.5); fo = min(1.0, (duration-t)/1.2)
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_10():
    """THE WILLOW REVEAL — 10s — Pure black, logo materialises"""
    duration = 10.0

    # Logo text elements
    w_arr   = pil_text("WILLOW",         SERIF_BOLD, 140, colour=WHITE)
    re_arr  = pil_text("REAL ESTATE",    SERIF,       54, colour=BEIGE)
    tag_arr = pil_multiline(
        "Adelaide's Premium Property Partner",
        SANS, 36, colour=(200, 195, 188), max_w=900
    )
    url_arr = pil_text(
        "willowrealestate.com.au",
        SANS, 32, colour=(160, 155, 150)
    )
    rule_a  = rule_arr(colour=BEIGE, w=700)

    def make_frame(t):
        base  = solid(BLACK_BG)
        frame = base.copy()

        # WILLOW fades in letter by letter: each letter appears at t=1 + i*0.12
        if t > 1.0:
            # Render each letter with staggered alpha
            letters = list("WILLOW")
            # Measure letter widths
            try:
                font = ImageFont.truetype(SERIF_BOLD, 140)
            except Exception:
                font = ImageFont.load_default()
            total_w = 0
            widths  = []
            for ch in letters:
                dummy = Image.new("RGBA", (1,1))
                dd    = ImageDraw.Draw(dummy)
                bb    = dd.textbbox((0,0), ch, font=font)
                widths.append(bb[2]-bb[0]+8)
                total_w += bb[2]-bb[0]+8

            start_x = W//2 - total_w//2
            cx_     = start_x
            cy_     = H//2 - 100
            for i, (ch, cw) in enumerate(zip(letters, widths)):
                t_start = 1.0 + i * 0.14
                local   = t - t_start
                alpha   = max(0.0, min(1.0, local / 0.35))
                if alpha <= 0:
                    cx_ += cw
                    continue
                ch_arr  = pil_text(ch, SERIF_BOLD, 140, colour=WHITE)
                ch_arr[:,:,3] = (ch_arr[:,:,3] * alpha).astype(np.uint8)
                # Blit at cx_, cy_
                th_, tw_ = ch_arr.shape[:2]
                yy = max(0, min(cy_, H - th_))
                xx = max(0, min(cx_, W - tw_))
                slice_y  = frame[yy:yy+th_, xx:xx+tw_]
                if slice_y.shape[0] == th_ and slice_y.shape[1] == tw_:
                    a4 = ch_arr[:,:,3:4] / 255.0
                    frame[yy:yy+th_, xx:xx+tw_] = (
                        slice_y * (1 - a4) + ch_arr[:,:,:3] * a4
                    ).astype(np.uint8)
                cx_ += cw

        # REAL ESTATE
        if t > 2.8:
            alpha = min(1.0, (t-2.8)/0.6)
            ra    = re_arr.copy()
            ra[:,:,3] = (ra[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, ra, cx_frac=0.5, cy_frac=0.495)

        # Rule
        if t > 3.8:
            alpha = min(1.0, (t-3.8)/0.5)
            rl    = rule_a.copy()
            rl[:,:,3] = (rl[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, rl, cx_frac=0.5, cy_frac=0.56)

        # Tagline
        if t > 4.5:
            alpha = min(1.0, (t-4.5)/0.7)
            tg    = tag_arr.copy()
            tg[:,:,3] = (tg[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, tg, cx_frac=0.5, cy_frac=0.63)

        # URL
        if t > 5.5:
            alpha = min(1.0, (t-5.5)/0.6)
            ur    = url_arr.copy()
            ur[:,:,3] = (ur[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, ur, cx_frac=0.5, cy_frac=0.70)

        fi = min(1.0, t/0.4)
        return (frame * fi).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def scene_11():
    """THE INVITATION — 6s — Window, more light, the door opens"""
    duration = 6.0

    vo_arr   = pil_multiline(
        "Your next chapter begins here.",
        SERIF_BOLD, 72, colour=WHITE, max_w=900
    )
    url_arr  = pil_text("willowrealestate.com.au", SANS, 34, colour=(200,190,178))

    def make_frame(t):
        progress = t / duration

        # Return to warm morning light — but more open, more light
        warmth   = 0.5 + 0.5 * progress
        base     = solid(
            tuple(int(DARK_BROWN[i] + (50 + 60 * warmth) *
                  [0.9, 0.6, 0.2][i]) for i in range(3))
        )

        # Window: a bright vertical band that expands over time
        y, x     = np.mgrid[0:H, 0:W]
        win_cx   = W * 0.42
        win_w    = W * (0.12 + 0.15 * progress)
        wg       = np.exp(-0.5 * ((x - win_cx) / win_w)**2)
        wg      *= np.exp(-0.5 * ((y - H*0.5) / (H*0.6))**2)
        base     = (base.astype(float) +
                    np.array((255,220,140), float)[None,None,:] *
                    wg[:,:,None] * (0.6 + 0.3 * progress)).astype(np.uint8)

        # Floor grain (matching scene 01)
        np.random.seed(42)
        grain = np.random.normal(0, 3, base.shape).astype(float)
        base  = np.clip(base.astype(float) + grain, 0, 255).astype(np.uint8)

        # Camera push: slight zoom-in illusion via crop-and-resize
        scale   = 1.0 + 0.03 * progress
        crop_h  = int(H / scale)
        crop_w  = int(W / scale)
        off_y   = (H - crop_h) // 2
        off_x   = (W - crop_w) // 2
        cropped = base[off_y:off_y+crop_h, off_x:off_x+crop_w]
        pil_img = Image.fromarray(cropped).resize((W, H), Image.LANCZOS)
        frame   = np.array(pil_img)

        # VO
        if t > 1.0:
            alpha = min(1.0, (t-1.0)/0.8) * min(1.0, (duration-t)/0.6)
            txt   = vo_arr.copy()
            txt[:,:,3] = (txt[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, txt, cx_frac=0.5, cy_frac=0.76)

        # URL
        if t > 2.8:
            alpha = min(1.0, (t-2.8)/0.6) * min(1.0, (duration-t)/0.6)
            ur    = url_arr.copy()
            ur[:,:,3] = (ur[:,:,3] * alpha).astype(np.uint8)
            frame = overlay_text_arr(frame, ur, cx_frac=0.5, cy_frac=0.86)

        fi = min(1.0, t/0.5)
        fo = min(1.0, (duration-t)/1.5)   # long fade to black at end
        return (frame * fi * fo).astype(np.uint8)

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


# ── ASSEMBLE & EXPORT ─────────────────────────────────────────────────────────

def main():
    print("Building Willow Real Estate — 'CERTAIN' Brand Film...")
    print("1920×1080  |  24fps  |  90 seconds\n")

    clips = []
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

    for fn, label in scene_fns:
        print(f"  Rendering Scene {label}...")
        clips.append(fn())

    print("\nConcatenating all scenes...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"Exporting {OUT}  ({final.duration:.1f}s)...")
    final.write_videofile(
        OUT,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="medium",
        ffmpeg_params=["-crf", "20"],
        logger="bar",
    )
    print(f"\nDone — {OUT}")


if __name__ == "__main__":
    main()
