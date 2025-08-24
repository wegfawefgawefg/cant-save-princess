import pygame, sys, math, random

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)

# Low-res render surface.
LOW_RES = (320, 240)
SCREEN_SIZE = (640, 480)
screen = pygame.display.set_mode(SCREEN_SIZE)
render_surf = pygame.Surface(LOW_RES)
clock = pygame.time.Clock()

# Colors
DARK_GREY = (50, 50, 60)
DIM_YELLOW = (180, 180, 0)
BUTTON_COLOR = (100, 100, 220)
BUTTON_SHADOW = DARK_GREY
SELECT_RECT = (200, 200, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND = (40, 40, 40)
RED = (220, 20, 60)
GREEN = (0, 200, 0)

# For secondary stripes (yellow)
YELLOW = (255, 255, 0)

# Load music and sound effects
MENU_MUSIC_FILE = "play_music.ogg"
PLAY_MUSIC_FILE = "play_music.ogg"
COUNTDOWN_SOUND_FILE = "boop.ogg"
GO_SOUND_FILE = "level_start.ogg"

# Preload sound effects.
countdown_sound = pygame.mixer.Sound(COUNTDOWN_SOUND_FILE)
go_sound = pygame.mixer.Sound(GO_SOUND_FILE)

# Global to track current music ("menu" or "play")
current_music = None


# ---------- Helper Drawing Functions ----------
def draw_text_shadow(surface, text, font, pos, color, shadow_color, offset=(2, 2)):
    # No antialiasing (False).
    shadow_surf = font.render(text, False, shadow_color)
    text_surf = font.render(text, False, color)
    surface.blit(shadow_surf, (pos[0] + offset[0], pos[1] + offset[1]))
    surface.blit(text_surf, pos)


def draw_billboard(surface, text, rect):
    box_shadow = rect.copy()
    box_shadow.x += 2
    box_shadow.y += 2
    pygame.draw.rect(surface, (30, 30, 30), box_shadow)
    pygame.draw.rect(surface, SELECT_RECT, rect, 1)
    billboard_font = pygame.font.SysFont("Arial", 24)
    padded_text = text + " " * 30
    text_surf = billboard_font.render(padded_text, False, WHITE)
    text_width = text_surf.get_width()
    clip = surface.get_clip()
    surface.set_clip(rect)
    scroll_speed = 0.03
    x_offset = -((pygame.time.get_ticks() * scroll_speed) % (text_width + rect.width))
    pos = x_offset
    while pos < rect.right:
        surface.blit(
            text_surf,
            (rect.x + pos, rect.y + (rect.height - text_surf.get_height()) // 2),
        )
        pos += text_width
    surface.set_clip(clip)


def draw_banner(surface, rect, text, font_size=12):
    box_shadow = rect.copy()
    box_shadow.x += 2
    box_shadow.y += 2
    pygame.draw.rect(surface, (30, 30, 30), box_shadow)
    pygame.draw.rect(surface, SELECT_RECT, rect, 1)
    font = pygame.font.SysFont("Arial", font_size)
    text_surf = font.render(text, False, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


def draw_apple(surface, center, score):
    radius = 15
    x, y = center
    # Drop shadow.
    if score <= 35:
        pygame.draw.circle(surface, (30, 30, 30), (x + 3, y + 3), radius)
    # Apple body.
    pygame.draw.circle(surface, RED, (x, y), radius)
    # Stem.
    if score <= 30:
        pygame.draw.line(
            surface, (80, 50, 20), (x, y - radius + 2), (x, y - radius - 8), 3
        )
    # Leaf.
    if score <= 25:
        leaf_points = [
            (x, y - radius - 8),
            (x + 8, y - radius - 2),
            (x, y - radius + 2),
        ]
        pygame.draw.polygon(surface, GREEN, leaf_points)


def draw_score(surface, score):
    font = pygame.font.SysFont("Arial", 14)
    text = f"Score: {score}"
    # Center the score at the bottom.
    text_surf = font.render(text, False, WHITE)
    text_rect = text_surf.get_rect(center=(LOW_RES[0] // 2, LOW_RES[1] - 10))
    draw_text_shadow(surface, text, font, (text_rect.x, text_rect.y), WHITE, DARK_GREY)


def draw_game_over(surface):
    font = pygame.font.SysFont("Arial", 40)
    text = "YOU LOSE"
    text_surf = font.render(text, False, WHITE)
    text_rect = text_surf.get_rect(center=(LOW_RES[0] // 2, LOW_RES[1] // 2))
    draw_text_shadow(surface, text, font, (text_rect.x, text_rect.y), WHITE, DARK_GREY)


def draw_background(surface, offset, score):
    surface.fill(DARK_GREY)
    stripe_width = 20
    slow_offset = offset // 10
    # Primary stripes (slope -1).
    primary_color = RED if score >= 5 else DIM_YELLOW
    for i in range(-LOW_RES[1] * 2, LOW_RES[0] + LOW_RES[1], stripe_width * 2):
        pos = i + (slow_offset % (stripe_width * 2))
        start_pos = (pos, 0)
        end_pos = (pos - LOW_RES[1], LOW_RES[1])
        pygame.draw.line(surface, primary_color, start_pos, end_pos, stripe_width)
    # Secondary stripes (slope +1) appear at score 15.
    if score >= 15:
        secondary_color = RED if score >= 20 else YELLOW
        for i in range(-LOW_RES[1] * 2, LOW_RES[0] + LOW_RES[1], stripe_width * 2):
            pos = i + (slow_offset % (stripe_width * 2))
            start_pos = (pos, 0)
            end_pos = (pos + LOW_RES[1], LOW_RES[1])
            pygame.draw.line(surface, secondary_color, start_pos, end_pos, stripe_width)


def draw_custom_mouse(surface):
    mx, my = pygame.mouse.get_pos()
    mx = int(mx * LOW_RES[0] / SCREEN_SIZE[0])
    my = int(my * LOW_RES[1] / SCREEN_SIZE[1])
    arrow = [(mx, my), (mx + 10, my + 5), (mx + 7, my + 7), (mx + 5, my + 10)]
    shadow = [(x + 2, y + 2) for (x, y) in arrow]
    pygame.draw.polygon(surface, BUTTON_SHADOW, shadow)
    pygame.draw.polygon(surface, BUTTON_COLOR, arrow)


# ---------- Basic UI Classes ----------
class Button:
    def __init__(self, rect, text):
        self.base_rect = pygame.Rect(rect)
        self.text = text
        self.pressed = False
        self.clicked = False
        self.font = pygame.font.SysFont("Arial", 12)
        self.shadow_offset = 4
        self.current_scale = 1.0
        self.target_scale = 1.0

    def update(self, events):
        self.clicked = False
        mx, my = pygame.mouse.get_pos()
        mouse = (mx * LOW_RES[0] / SCREEN_SIZE[0], my * LOW_RES[1] / SCREEN_SIZE[1])
        if self.base_rect.collidepoint(mouse):
            self.target_scale = 1.1
        else:
            self.target_scale = 1.0
        self.current_scale += (self.target_scale - self.current_scale) * 0.2
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if self.base_rect.collidepoint(mouse):
                    self.pressed = True
            if ev.type == pygame.MOUSEBUTTONUP:
                if self.pressed and self.base_rect.collidepoint(mouse):
                    self.clicked = True
                self.pressed = False

    def draw(self, surface):
        wiggle = (
            10 * math.sin(pygame.time.get_ticks() / 100)
            if self.base_rect.collidepoint(
                (
                    pygame.mouse.get_pos()[0] * LOW_RES[0] / SCREEN_SIZE[0],
                    pygame.mouse.get_pos()[1] * LOW_RES[1] / SCREEN_SIZE[1],
                )
            )
            else 5 * math.sin(pygame.time.get_ticks() / 500)
        )
        scale = self.current_scale
        sw = int(self.base_rect.width * scale)
        sh = int(self.base_rect.height * scale)
        scaled_rect = pygame.Rect(0, 0, sw, sh)
        scaled_rect.center = self.base_rect.center
        button_offset = self.shadow_offset if self.pressed else 0
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        shadow_surf.fill(BUTTON_SHADOW)
        shadow_rot = pygame.transform.rotate(shadow_surf, wiggle)
        shadow_rot_rect = shadow_rot.get_rect(
            center=(
                scaled_rect.centerx + self.shadow_offset,
                scaled_rect.centery + self.shadow_offset,
            )
        )
        surface.blit(shadow_rot, shadow_rot_rect)
        btn_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        btn_surf.fill(BUTTON_COLOR)
        text_surf = self.font.render(self.text, False, WHITE)
        text_rect = text_surf.get_rect(center=(sw // 2, sh // 2))
        btn_surf.blit(text_surf, text_rect)
        rotated = pygame.transform.rotate(btn_surf, wiggle)
        rot_rect = rotated.get_rect(
            center=(
                scaled_rect.centerx + button_offset,
                scaled_rect.centery + button_offset,
            )
        )
        surface.blit(rotated, rot_rect)


class Scrollbar:
    def __init__(self, rect, content_height, view_height):
        self.rect = pygame.Rect(rect)
        self.content_height = content_height
        self.view_height = view_height
        self.scroll = 0
        self.dragging = False
        self.handle_height = max(
            20, self.rect.height * self.view_height / self.content_height
        )
        self.handle_rect = pygame.Rect(
            self.rect.x, self.rect.y, self.rect.width, self.handle_height
        )

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        mouse = (mx * LOW_RES[0] / SCREEN_SIZE[0], my * LOW_RES[1] / SCREEN_SIZE[1])
        for ev in events:
            if ev.type == pygame.MOUSEWHEEL:
                self.scroll -= ev.y * 0.05
                self.scroll = max(0, min(1, self.scroll))
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if self.handle_rect.collidepoint(mouse):
                    self.dragging = True
                    self.mouse_offset = mouse[1] - self.handle_rect.y
            if ev.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
        if self.dragging:
            new_y = mouse[1] - self.mouse_offset
            new_y = max(
                self.rect.y, min(new_y, self.rect.bottom - self.handle_rect.height)
            )
            self.handle_rect.y = new_y
            self.scroll = (self.handle_rect.y - self.rect.y) / (
                self.rect.height - self.handle_rect.height
            )
        else:
            self.handle_rect.y = self.rect.y + self.scroll * (
                self.rect.height - self.handle_rect.height
            )

    def draw(self, surface):
        track_shadow = self.rect.copy()
        track_shadow.x += 2
        track_shadow.y += 2
        pygame.draw.rect(surface, BACKGROUND, track_shadow)
        pygame.draw.rect(surface, (160, 160, 160), self.rect)
        shadow = self.handle_rect.copy()
        shadow.x += 2
        shadow.y += 2
        pygame.draw.rect(surface, BUTTON_SHADOW, shadow)
        pygame.draw.rect(surface, (200, 200, 200), self.handle_rect)


class ArrowButton:
    def __init__(self, rect, direction):
        self.base_rect = pygame.Rect(rect)
        self.direction = direction  # "left" or "right"
        self.shadow_offset = 2
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.pressed = False

    def update(self, events):
        mx, my = pygame.mouse.get_pos()
        mouse = (mx * LOW_RES[0] / SCREEN_SIZE[0], my * LOW_RES[1] / SCREEN_SIZE[1])
        hovered = self.base_rect.collidepoint(mouse)
        self.target_scale = 1.1 if hovered else 1.0
        self.current_scale += (self.target_scale - self.current_scale) * 0.2
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(ev, "button") and ev.button in (4, 5):
                    continue
                if hovered:
                    self.pressed = True
            if ev.type == pygame.MOUSEBUTTONUP:
                if hasattr(ev, "button") and ev.button in (4, 5):
                    continue
                if self.pressed and hovered:
                    self.pressed = False
                    return True
                self.pressed = False
        return False

    def draw(self, surface):
        constant_offset = self.shadow_offset
        arrow_offset = self.shadow_offset if self.pressed else 0
        scale = self.current_scale
        r = self.base_rect
        width = int(r.width * scale)
        height = int(r.height * scale)
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        arrow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        if self.direction == "left":
            points = [
                (width * 0.3, height / 2),
                (width * 0.75, height * 0.25),
                (width * 0.75, height * 0.75),
            ]
        else:
            points = [
                (width * 0.7, height / 2),
                (width * 0.25, height * 0.25),
                (width * 0.25, height * 0.75),
            ]
        shadow_points = [(x + 2, y + 2) for (x, y) in points]
        pygame.draw.polygon(shadow_surf, BUTTON_SHADOW, shadow_points)
        pygame.draw.polygon(arrow_surf, BUTTON_COLOR, points)
        wiggle = (
            10 * math.sin(pygame.time.get_ticks() / 100)
            if self.base_rect.collidepoint(
                (
                    pygame.mouse.get_pos()[0] * LOW_RES[0] / SCREEN_SIZE[0],
                    pygame.mouse.get_pos()[1] * LOW_RES[1] / SCREEN_SIZE[1],
                )
            )
            else 5 * math.sin(pygame.time.get_ticks() / 500)
        )
        rotated_shadow = pygame.transform.rotate(shadow_surf, wiggle)
        rotated_arrow = pygame.transform.rotate(arrow_surf, wiggle)
        shadow_rect = rotated_shadow.get_rect(
            center=(
                self.base_rect.centerx + constant_offset,
                self.base_rect.centery + constant_offset,
            )
        )
        arrow_rect = rotated_arrow.get_rect(
            center=(
                self.base_rect.centerx + arrow_offset,
                self.base_rect.centery + arrow_offset,
            )
        )
        surface.blit(rotated_shadow, shadow_rect)
        surface.blit(rotated_arrow, arrow_rect)


class OptionItem:
    def __init__(self, rect, label, choices, current=0):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.choices = choices
        self.current = current
        self.hovered = False
        self.text_area = pygame.Rect(
            self.rect.x, self.rect.y, self.rect.width - 50, self.rect.height
        )
        self.arrow_area = pygame.Rect(
            self.rect.right - 50, self.rect.y, 50, self.rect.height
        )
        self.left_button = ArrowButton(
            pygame.Rect(
                self.arrow_area.x, self.arrow_area.y, 25, self.arrow_area.height
            ),
            "left",
        )
        self.right_button = ArrowButton(
            pygame.Rect(
                self.arrow_area.x + 25, self.arrow_area.y, 25, self.arrow_area.height
            ),
            "right",
        )
        self.current_scale = 1.0
        self.target_scale = 1.0

    def update(self, events, offset_y):
        effective_rect = self.rect.copy()
        effective_rect.y += offset_y
        mx, my = pygame.mouse.get_pos()
        mx = int(mx * LOW_RES[0] / SCREEN_SIZE[0])
        my = int(my * LOW_RES[1] / SCREEN_SIZE[1])
        self.hovered = effective_rect.collidepoint(mx, my)
        self.target_scale = 1.1 if self.hovered else 1.0
        self.current_scale += (self.target_scale - self.current_scale) * 0.2
        effective_arrow = self.arrow_area.copy()
        effective_arrow.y += offset_y
        self.left_button.base_rect = pygame.Rect(
            effective_arrow.x,
            effective_arrow.y,
            effective_arrow.width // 2,
            effective_arrow.height,
        )
        self.right_button.base_rect = pygame.Rect(
            effective_arrow.x + effective_arrow.width // 2,
            effective_arrow.y,
            effective_arrow.width // 2,
            effective_arrow.height,
        )
        if self.left_button.update(events):
            self.current = (self.current - 1) % len(self.choices)
        if self.right_button.update(events):
            self.current = (self.current + 1) % len(self.choices)

    def draw(self, surface, offset_y):
        pad = 4
        scale = self.current_scale
        ta = self.text_area.copy()
        ta.y += offset_y - pad
        ta.width = int(ta.width * scale)
        ta.height = int(ta.height * scale)
        ta.center = (
            self.text_area.move(0, offset_y).centerx,
            self.text_area.move(0, offset_y).centery - 2,
        )
        font_size = int(12 * scale)
        combined_text = f"{self.label} : {self.choices[self.current]}"
        draw_banner(surface, ta, combined_text, font_size=font_size)
        self.left_button.draw(surface)
        self.right_button.draw(surface)


class OptionSlider:
    def __init__(self, rect, label, min_val=0, max_val=100, start_val=50):
        self.full_rect = pygame.Rect(rect)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.dragging = False
        self.hovered = False
        self.current_scale = 1.0
        self.target_scale = 1.0
        self.text_box = pygame.Rect(
            self.full_rect.x, self.full_rect.y, 100, self.full_rect.height
        )
        track_width = self.full_rect.width - 110
        track_height = int(self.full_rect.height * 0.4)
        track_y = self.full_rect.y + (self.full_rect.height - track_height) // 2
        self.slider_box = pygame.Rect(
            self.full_rect.x + 105, track_y, track_width, track_height
        )
        self.knob_width = 10
        self.knob_height = 20
        self.handle_rect = pygame.Rect(0, 0, self.knob_width, self.knob_height)
        self.update_handle()

    def update_handle(self):
        handle_x = (
            self.slider_box.x
            + (self.value - self.min_val)
            / (self.max_val - self.min_val)
            * self.slider_box.width
        )
        self.handle_rect.x = int(handle_x - self.handle_rect.width / 2)
        self.handle_rect.y = (
            self.slider_box.y + (self.slider_box.height - self.handle_rect.height) // 2
        )

    def update(self, events, offset_y):
        effective_full = self.full_rect.copy()
        effective_full.y += offset_y
        mx, my = pygame.mouse.get_pos()
        mx = int(mx * LOW_RES[0] / SCREEN_SIZE[0])
        my = int(my * LOW_RES[1] / SCREEN_SIZE[1])
        self.hovered = effective_full.collidepoint(mx, my)
        self.target_scale = 1.1 if self.hovered else 1.0
        self.current_scale += (self.target_scale - self.current_scale) * 0.2
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if self.slider_box.move(0, offset_y).collidepoint(mx, my):
                    self.dragging = True
            if ev.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
        if self.dragging:
            effective_slider = self.slider_box.copy()
            effective_slider.y += offset_y
            x = max(effective_slider.x, min(mx, effective_slider.right))
            self.value = (x - effective_slider.x) / effective_slider.width * (
                self.max_val - self.min_val
            ) + self.min_val
            self.update_handle()

    def draw(self, surface, offset_y):
        pad = 4
        scale = self.current_scale
        tb = self.text_box.copy()
        tb.y += offset_y - pad
        tb.width = int(tb.width * scale)
        tb.height = int(tb.height * scale)
        tb.center = (
            self.text_box.move(0, offset_y).centerx,
            self.text_box.move(0, offset_y).centery - 2,
        )
        font_size = int(12 * scale)
        combined_text = f"{self.label} : {int(self.value)}"
        draw_banner(surface, tb, combined_text, font_size=font_size)
        sb = self.slider_box.copy()
        sb.y += offset_y
        shadow_sb = sb.copy()
        shadow_sb.x += 2
        shadow_sb.y += 2
        pygame.draw.rect(surface, (30, 30, 30), shadow_sb)
        pygame.draw.rect(surface, (180, 180, 180), sb)
        rotation = (
            10 * math.sin(pygame.time.get_ticks() / 100)
            if self.dragging
            else 3 * math.sin(pygame.time.get_ticks() / 500)
        )
        knob_surf = pygame.Surface(
            (self.handle_rect.width, self.handle_rect.height), pygame.SRCALPHA
        )
        knob_surf.fill(BUTTON_COLOR)
        rotated_knob = pygame.transform.rotate(knob_surf, rotation)
        knob_rect = rotated_knob.get_rect(
            center=(self.handle_rect.centerx, self.handle_rect.centery + offset_y)
        )
        knob_shadow_surf = pygame.Surface(
            (self.handle_rect.width, self.handle_rect.height), pygame.SRCALPHA
        )
        knob_shadow_surf.fill(BUTTON_SHADOW)
        rotated_knob_shadow = pygame.transform.rotate(knob_shadow_surf, rotation)
        knob_shadow_rect = rotated_knob_shadow.get_rect(
            center=(
                self.handle_rect.centerx + 2,
                self.handle_rect.centery + 2 + offset_y,
            )
        )
        surface.blit(rotated_knob_shadow, knob_shadow_rect)
        surface.blit(rotated_knob, knob_rect)


# ---------- Main Menu Setup ----------
button_width, button_height = 80, 30
button_x = (LOW_RES[0] - button_width) // 2
main_buttons = [
    Button((button_x, 70, button_width, button_height), "Play"),
    Button((button_x, 110, button_width, button_height), "Options"),
    Button((button_x, 150, button_width, button_height), "Quit"),
]
x_button = Button((LOW_RES[0] - 40, 10, 30, 30), "X")
billboard_main = pygame.Rect(10, 10, LOW_RES[0] - 70, 30)

# ---------- Options Screen Setup ----------
options_container = pygame.Rect(60, 60, 240, 160)
item_height = 35
content_height = 12 * item_height
options_scrollbar = Scrollbar(
    (options_container.right - 12, options_container.y, 12, options_container.height),
    content_height,
    options_container.height,
)

option_items = []
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y,
            options_container.width - 15,
            item_height,
        ),
        "Resolution",
        ["640x480", "800x600", "1024x768", "1280x720"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + item_height,
            options_container.width - 15,
            item_height,
        ),
        "Graphics",
        ["Low", "Med", "High"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 2 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Antialias",
        ["Off", "On"],
    )
)
option_items.append(
    OptionSlider(
        pygame.Rect(
            options_container.x,
            options_container.y + 3 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Volume",
        0,
        100,
        50,
    )
)
option_items.append(
    OptionSlider(
        pygame.Rect(
            options_container.x,
            options_container.y + 4 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Brightness",
        0,
        100,
        75,
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 5 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Shadow",
        ["Off", "On"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 6 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Texture",
        ["Low", "Med", "High"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 7 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "VSync",
        ["Off", "On"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 8 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Music",
        ["Off", "On"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 9 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "SFX",
        ["Off", "On"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 10 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Language",
        ["EN", "ES", "FR", "DE", "JP"],
    )
)
option_items.append(
    OptionItem(
        pygame.Rect(
            options_container.x,
            options_container.y + 11 * item_height,
            options_container.width - 15,
            item_height,
        ),
        "Difficulty",
        ["Easy", "Normal", "Hard"],
    )
)

back_button = Button((5, options_container.y + 5, 40, 25), "Back")
billboard_options = pygame.Rect(10, 10, LOW_RES[0] - 20, 30)

# ---------- Play Mode Variables ----------
apple_exists = False
apple_spawn_time = 0
apple_center = (0, 0)
score = 0
# play_phase: "countdown", "active", "gameover"
play_phase = "countdown"
countdown_start_time = 0
game_over_time = 0
last_countdown = None
countdown_go_played = False


def spawn_apple():
    margin = 20
    x = random.randint(margin, LOW_RES[0] - margin)
    y = random.randint(margin, LOW_RES[1] - margin - 20)
    return (x, y)


# ---------- Main Loop ----------
current_screen = "main"  # "main", "options", or "play"

while True:
    events = pygame.event.get()
    for ev in events:
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    scroll_events = [ev for ev in events if ev.type == pygame.MOUSEWHEEL]
    other_events = [
        ev
        for ev in events
        if not (
            ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
            and hasattr(ev, "button")
            and ev.button in (4, 5)
        )
    ]

    # Set music based on screen.
    if current_screen == "main" and current_music != "menu":
        pygame.mixer.music.load(MENU_MUSIC_FILE)
        pygame.mixer.music.play(-1)
        current_music = "menu"
    elif current_screen == "play" and current_music != "play":
        pygame.mixer.music.load(PLAY_MUSIC_FILE)
        pygame.mixer.music.play(-1)
        current_music = "play"

    # Use score in background drawing in play mode; otherwise pass 0.
    bg_score = score if current_screen == "play" else 0
    draw_background(render_surf, pygame.time.get_ticks(), bg_score)

    if current_screen == "main":
        draw_billboard(
            render_surf,
            "M   A   I   N       M   E   N   U",
            pygame.Rect(10, 10, LOW_RES[0] - 60, 30),
        )
        for btn in main_buttons:
            btn.update(other_events)
        x_button.update(other_events)
        if main_buttons[0].clicked:
            # Setup play mode with countdown.
            current_screen = "play"
            play_phase = "countdown"
            countdown_start_time = pygame.time.get_ticks()
            score = 0
            apple_exists = False
            game_over_time = 0
            last_countdown = None
            countdown_go_played = False
        if main_buttons[1].clicked:
            current_screen = "options"
        if main_buttons[2].clicked:
            pygame.quit()
            sys.exit()
        if x_button.clicked:
            pygame.quit()
            sys.exit()
        for btn in main_buttons:
            btn.draw(render_surf)
        x_button.draw(render_surf)

    elif current_screen == "options":
        draw_billboard(render_surf, "O   P   T   I   O   N   S", billboard_options)
        back_button.update(other_events)
        if back_button.clicked:
            current_screen = "main"
        back_button.draw(render_surf)
        options_scrollbar.update(scroll_events)
        clip_rect = options_container.inflate(20, 0)
        offset_y = -options_scrollbar.scroll * (
            content_height - options_container.height
        )
        clip = render_surf.get_clip()
        render_surf.set_clip(clip_rect)
        for item in reversed(option_items):
            item.update(other_events, offset_y)
            item.draw(render_surf, offset_y)
        render_surf.set_clip(clip)
        options_scrollbar.draw(render_surf)

    elif current_screen == "play":
        current_time = pygame.time.get_ticks()
        if play_phase == "countdown":
            # Draw "CLICK THE APPLE" instruction centered.
            font_inst = pygame.font.SysFont("Arial", 20)
            inst_text = "CLICK THE APPLE"
            inst_surf = font_inst.render(inst_text, False, WHITE)
            inst_rect = inst_surf.get_rect(center=(LOW_RES[0] // 2, 20))
            draw_text_shadow(
                render_surf,
                inst_text,
                font_inst,
                (inst_rect.x, inst_rect.y),
                WHITE,
                DARK_GREY,
            )
            # Countdown sequence: each number lasts 500ms.
            elapsed = current_time - countdown_start_time
            countdown_text = ""
            if elapsed < 500:
                countdown_text = "3"
            elif elapsed < 1000:
                countdown_text = "2"
            elif elapsed < 1500:
                countdown_text = "1"
            elif elapsed < 2000:
                # "GO!!!!" phase with blinking (via fast oscillation of scale and color).
                countdown_text = "GO!!!!"
                t = elapsed - 1500
                scale = 1 + 0.2 * math.sin(t / 50.0)
                col = WHITE if math.sin(t / 50.0) > 0 else DIM_YELLOW
                font_count = pygame.font.SysFont("Arial", int(40 * scale))
                count_surf = font_count.render(countdown_text, False, col)
                count_rect = count_surf.get_rect(
                    center=(LOW_RES[0] // 2, LOW_RES[1] // 2)
                )
                draw_text_shadow(
                    render_surf,
                    countdown_text,
                    font_count,
                    (count_rect.x, count_rect.y),
                    col,
                    DARK_GREY,
                )
                if not countdown_go_played:
                    go_sound.play()
                    countdown_go_played = True
            else:
                play_phase = "active"
                apple_exists = True
                apple_center = spawn_apple()
                apple_spawn_time = pygame.time.get_ticks()
            # For numbers (3,2,1), play countdown sound when value changes.
            if countdown_text in ["3", "2", "1"]:
                if countdown_text != last_countdown:
                    countdown_sound.play()
                    last_countdown = countdown_text
                font_count = pygame.font.SysFont("Arial", 40)
                count_surf = font_count.render(countdown_text, False, WHITE)
                count_rect = count_surf.get_rect(
                    center=(LOW_RES[0] // 2, LOW_RES[1] // 2)
                )
                draw_text_shadow(
                    render_surf,
                    countdown_text,
                    font_count,
                    (count_rect.x, count_rect.y),
                    WHITE,
                    DARK_GREY,
                )
            # Draw score (which is 0 at start) with shadow.
            draw_score(render_surf, score)

        elif play_phase == "active":
            # Allow 0.7 seconds to click the apple.
            if current_time - apple_spawn_time > 750:
                play_phase = "gameover"
                game_over_time = current_time
            # Handle mouse clicks on the apple.
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    mouse = (
                        int(mx * LOW_RES[0] / SCREEN_SIZE[0]),
                        int(my * LOW_RES[1] / SCREEN_SIZE[1]),
                    )
                    ax, ay = apple_center
                    if math.hypot(mouse[0] - ax, mouse[1] - ay) <= 15:
                        score += 1
                        apple_center = spawn_apple()
                        apple_spawn_time = pygame.time.get_ticks()
            if apple_exists:
                draw_apple(render_surf, apple_center, score)
            draw_score(render_surf, score)

        elif play_phase == "gameover":
            draw_game_over(render_surf)
            draw_score(render_surf, score)
            # After 5 seconds, return to main menu.
            if current_time - game_over_time > 5000:
                current_screen = "main"

    draw_custom_mouse(render_surf)
    scaled = pygame.transform.scale(render_surf, SCREEN_SIZE)
    screen.blit(scaled, (0, 0))
    pygame.display.flip()
    clock.tick(144)
    render_surf.fill(DARK_GREY)
