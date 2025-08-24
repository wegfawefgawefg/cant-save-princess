import pygame, math, sys, random

pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 14)

# ------------------
# Camera settings.
camera_pos = pygame.Vector2(0, 0)
camera_target = pygame.Vector2(0, 0)
camera_lerp = 0.1  # How fast camera follows target.
camera_bias_dist = 50  # How far ahead the camera biases.

# ------------------
# Rock grid settings.
tile_size = 300
tiles = {}  # (tx, ty) -> list of rock dicts


def generate_tile(tx, ty):
    """Generates a list of rock dicts for tile (tx, ty)."""
    rocks = []
    count = random.randint(3, 7)
    for _ in range(count):
        x = tx * tile_size + random.uniform(0, tile_size)
        y = ty * tile_size + random.uniform(0, tile_size)
        w_top = random.uniform(20, 40)
        w_bottom = w_top + random.uniform(10, 20)
        h = random.uniform(10, 30)
        poly = [
            (x - w_top / 2, y),
            (x + w_top / 2, y),
            (x + w_bottom / 2, y + h),
            (x - w_bottom / 2, y + h),
        ]
        if random.random() < 0.5:
            grey = random.randint(80, 140)
            color = (grey, grey, grey)
        else:
            r = random.randint(80, 120)
            g = random.randint(40, 70)
            b = random.randint(20, 40)
            color = (r, g, b)
        avg_y = sum(p[1] for p in poly) / len(poly)
        rocks.append({"poly": poly, "color": color, "avg_y": avg_y})
    return rocks


def get_tile(tx, ty):
    if (tx, ty) not in tiles:
        tiles[(tx, ty)] = generate_tile(tx, ty)
    return tiles[(tx, ty)]


def world_to_screen(world_pos, cam_pos):
    return world_pos - cam_pos + pygame.Vector2(width / 2, height / 2)


# ------------------
# Spider settings.
body_pos = pygame.Vector2(width / 2, height / 2)  # True physics center.
body_radius = 20
body_velocity = pygame.Vector2(0, 0)
acceleration = 1000  # Pixels per second^2.
friction = 500  # Pixels per second^2.
max_speed = 200

# Suspension: drawn body is offset upward relative to true center.
base_draw_offset = -20  # Base offset.
max_extra_offset = -20  # Maximum additional upward offset.
suspension_offset = base_draw_offset


def update_suspension(dt):
    global suspension_offset
    speed = body_velocity.length()
    extra = max_extra_offset * min(speed / max_speed, 1)
    desired_offset = base_draw_offset + extra
    damping = 5.0
    suspension_offset += (desired_offset - suspension_offset) * damping * dt


def get_draw_pos():
    return body_pos + pygame.Vector2(0, suspension_offset)


# Leg/foot settings.
foot_target_distance = 60
comfort_radius = 60
step_speed = 8
num_legs = 8
random_offset_magnitude = 2
min_step_delay = 0.001
max_step_delay = 0.05
min_step_distance = 2
step_multiplier = 0.9

# IK settings.
thigh_length = foot_target_distance * 0.6
shin_length = foot_target_distance * 1.0

leg_angles_deg = [-30, -15, 15, 30, 150, 165, 195, 210]
legs = []
for i in range(num_legs):
    angle = math.radians(leg_angles_deg[i])
    base_offset = (
        pygame.Vector2(math.cos(angle), math.sin(angle)) * foot_target_distance
    )
    legs.append(
        {
            "default_angle": angle,
            "base_offset": base_offset,
            "target": body_pos + base_offset,
            "current": body_pos + base_offset,
            "stepping": False,
            "progress": 0,
            "start": None,
            "pending_delay": None,
        }
    )

foot_placement_max = 20
offset_speed = 5
foot_offset = pygame.Vector2(0, 0)


def solve_two_segment_ik(hip, foot, l1, l2, default_angle):
    to_target = foot - hip
    d = to_target.length()
    d = min(d, l1 + l2 - 0.0001)
    base_angle = math.atan2(to_target.y, to_target.x)
    cos_angle = (l1**2 + d**2 - l2**2) / (2 * l1 * d)
    cos_angle = max(-1, min(1, cos_angle))
    angle_offset = math.acos(cos_angle)
    hip_angle1 = base_angle + angle_offset
    knee1 = hip + pygame.Vector2(math.cos(hip_angle1), math.sin(hip_angle1)) * l1
    hip_angle2 = base_angle - angle_offset
    knee2 = hip + pygame.Vector2(math.cos(hip_angle2), math.sin(hip_angle2)) * l1
    if knee1.y < hip.y and knee2.y >= hip.y:
        return knee1
    elif knee2.y < hip.y and knee1.y >= hip.y:
        return knee2
    else:
        return knee1 if knee1.y < knee2.y else knee2


prev_body_pos = body_pos.copy()
cycle_duration = 0.4

# Colors.
body_color = (30, 30, 30)  # super dark grey
leg_color = (139, 69, 19)  # brown
bristle_color = (0, 0, 0)  # black
foot_color = (0, 0, 0)  # black
eye_color = (255, 0, 0)  # red
fang_color = (255, 255, 255)  # white
rock_color = (100, 100, 100)  # base grey

# ------------------
# Main loop.
running = True
while running:
    dt = clock.tick(60) / 1000.0
    current_time = pygame.time.get_ticks() / 1000.0
    phase = (current_time % cycle_duration) / cycle_duration
    allowed_parity = 0 if phase < 0.5 else 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

    # --- Input ---
    input_dir = pygame.Vector2(0, 0)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        input_dir.y -= 1
    if keys[pygame.K_s]:
        input_dir.y += 1
    if keys[pygame.K_a]:
        input_dir.x -= 1
    if keys[pygame.K_d]:
        input_dir.x += 1
    if input_dir.length_squared() > 0:
        input_dir = input_dir.normalize()

    # --- Update Spider Physics ---
    if input_dir.length_squared() > 0:
        body_velocity += input_dir * acceleration * dt
    else:
        if body_velocity.length() > 0:
            decel = friction * dt
            if decel > body_velocity.length():
                body_velocity = pygame.Vector2(0, 0)
            else:
                body_velocity -= body_velocity.normalize() * decel
    if body_velocity.length() > max_speed:
        body_velocity.scale_to_length(max_speed)
    body_pos += body_velocity * dt

    update_suspension(dt)  # update dynamic suspension

    # --- Update Leg Simulation (simulation uses true center) ---
    # For simulation, use true center for the hip.
    for idx, leg in enumerate(legs):
        sim_hip = (
            body_pos
            + pygame.Vector2(
                math.cos(leg["default_angle"]), math.sin(leg["default_angle"])
            )
            * body_radius
        )
        ideal = sim_hip + leg["base_offset"] + foot_offset
        if not leg["stepping"] and leg["pending_delay"] is None:
            if (idx % 2) == allowed_parity:
                if (leg["current"] - ideal).length() > comfort_radius:
                    leg["pending_delay"] = random.uniform(
                        min_step_delay, max_step_delay
                    )
        if leg["pending_delay"] is not None:
            leg["pending_delay"] -= dt
            if leg["pending_delay"] <= 0:
                leg["pending_delay"] = None
                leg["stepping"] = True
                leg["progress"] = 0
                leg["start"] = leg["current"].copy()
                deviation = (leg["current"] - ideal).length()
                step_dist = max(min_step_distance, deviation * step_multiplier)
                if body_velocity.length() > 0:
                    step_dir = body_velocity.normalize()
                    leg["target"] = ideal + step_dir * step_dist
                else:
                    leg["target"] = ideal.copy()
                random_offset = pygame.Vector2(
                    random.uniform(-random_offset_magnitude, random_offset_magnitude),
                    random.uniform(-random_offset_magnitude, random_offset_magnitude),
                )
                leg["target"] += random_offset
        if leg["stepping"]:
            leg["progress"] += dt * step_speed
            if leg["progress"] >= 1:
                leg["progress"] = 1
                leg["stepping"] = False
                leg["current"] = leg["target"].copy()
            else:
                leg["current"] = leg["start"].lerp(leg["target"], leg["progress"])

    # --- Update Camera ---
    motion_dir = (
        body_velocity.normalize() if body_velocity.length_squared() > 0 else input_dir
    )
    if motion_dir.length_squared() > 0:
        camera_target = body_pos + motion_dir * camera_bias_dist
    else:
        camera_target = body_pos.copy()
    camera_pos = camera_pos.lerp(camera_target, camera_lerp)

    # --- Draw ---
    BACKGROUND_COLOR = (50, 50, 50)
    screen.fill(BACKGROUND_COLOR)

    # --- Draw background rocks ---
    margin = 100
    top_left = camera_pos - pygame.Vector2(width / 2 + margin, height / 2 + margin)
    bottom_right = camera_pos + pygame.Vector2(width / 2 + margin, height / 2 + margin)
    tx0 = int(math.floor(top_left.x / tile_size))
    ty0 = int(math.floor(top_left.y / tile_size))
    tx1 = int(math.ceil(bottom_right.x / tile_size))
    ty1 = int(math.ceil(bottom_right.y / tile_size))
    rocks_to_draw = []
    for tx in range(tx0, tx1):
        for ty in range(ty0, ty1):
            for rock in get_tile(tx, ty):
                rocks_to_draw.append(rock)
    rocks_to_draw.sort(key=lambda r: r["avg_y"])
    for rock in rocks_to_draw:
        poly = [pygame.Vector2(p) for p in rock["poly"]]
        poly_screen = [world_to_screen(p, camera_pos) for p in poly]
        base_y = max(p.y for p in poly_screen)
        xs = [p.x for p in poly_screen]
        min_x, max_x = min(xs), max(xs)
        shadow_rect = pygame.Rect(min_x, base_y - 3, max_x - min_x, 8)
        shadow_surf = pygame.Surface(
            (shadow_rect.width, shadow_rect.height), pygame.SRCALPHA
        )
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect())
        screen.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
        pygame.draw.polygon(screen, rock["color"], poly_screen)

    # --- Draw spider ---
    # Draw spider shadow around true center.
    true_center_screen = world_to_screen(body_pos, camera_pos)
    spider_shadow_radius = body_radius + 15
    spider_shadow_surf = pygame.Surface(
        (spider_shadow_radius * 2, spider_shadow_radius), pygame.SRCALPHA
    )
    pygame.draw.ellipse(
        spider_shadow_surf, (0, 0, 0, 120), spider_shadow_surf.get_rect()
    )
    screen.blit(
        spider_shadow_surf,
        (
            true_center_screen.x - spider_shadow_radius,
            true_center_screen.y - spider_shadow_radius / 2 + 35,
        ),
    )

    # For drawing legs, use drawn body as hip.
    draw_pos = get_draw_pos()
    for leg in legs:
        hip_draw = (
            draw_pos
            + pygame.Vector2(
                math.cos(leg["default_angle"]), math.sin(leg["default_angle"])
            )
            * body_radius
        )
        foot = leg["current"]  # feet remain simulated relative to true center.
        knee = solve_two_segment_ik(
            hip_draw, foot, thigh_length, shin_length, leg["default_angle"]
        )
        pygame.draw.line(
            screen,
            leg_color,
            world_to_screen(hip_draw, camera_pos),
            world_to_screen(knee, camera_pos),
            4,
        )
        pygame.draw.line(
            screen,
            leg_color,
            world_to_screen(knee, camera_pos),
            world_to_screen(foot, camera_pos),
            4,
        )
        for seg in [(hip_draw, knee), (knee, foot)]:
            p1, p2 = seg
            seg_vec = p2 - p1
            if seg_vec.length() == 0:
                continue
            seg_dir = seg_vec.normalize()
            perp = pygame.Vector2(-seg_dir.y, seg_dir.x)
            mid_point = (p1 + p2) * 0.5
            to_mid = mid_point - draw_pos
            if perp.dot(to_mid) < 0:
                perp = -perp
            for fraction in [0.3, 0.6]:
                point = p1 + seg_vec * fraction
                bristle_length = 5
                end_point = point + perp * bristle_length
                pygame.draw.line(
                    screen,
                    bristle_color,
                    world_to_screen(point, camera_pos),
                    world_to_screen(end_point, camera_pos),
                    1,
                )
        pygame.draw.circle(
            screen,
            foot_color,
            (
                int(world_to_screen(foot, camera_pos).x),
                int(world_to_screen(foot, camera_pos).y),
            ),
            3,
        )

    # Draw spider body at drawn position.
    pygame.draw.circle(
        screen,
        body_color,
        (
            int(world_to_screen(draw_pos, camera_pos).x),
            int(world_to_screen(draw_pos, camera_pos).y),
        ),
        body_radius,
    )

    # Draw eyes and fangs relative to drawn body.
    eye_offset = pygame.Vector2(0, -3)  # relative to drawn body.
    eye_horiz_offset = body_radius * 0.4
    left_eye = draw_pos + pygame.Vector2(-eye_horiz_offset, 0) + eye_offset
    right_eye = draw_pos + pygame.Vector2(eye_horiz_offset, 0) + eye_offset
    eye_radius = int(body_radius * 0.15)
    pygame.draw.circle(
        screen,
        eye_color,
        (
            int(world_to_screen(left_eye, camera_pos).x),
            int(world_to_screen(left_eye, camera_pos).y),
        ),
        eye_radius,
    )
    pygame.draw.circle(
        screen,
        eye_color,
        (
            int(world_to_screen(right_eye, camera_pos).x),
            int(world_to_screen(right_eye, camera_pos).y),
        ),
        eye_radius,
    )
    extra_eye1 = draw_pos + pygame.Vector2(-body_radius * 0.6, -8)
    extra_eye2 = draw_pos + pygame.Vector2(body_radius * 0.6, -8)
    small_eye_radius = int(body_radius * 0.1)
    pygame.draw.circle(
        screen,
        eye_color,
        (
            int(world_to_screen(extra_eye1, camera_pos).x),
            int(world_to_screen(extra_eye1, camera_pos).y),
        ),
        small_eye_radius,
    )
    pygame.draw.circle(
        screen,
        eye_color,
        (
            int(world_to_screen(extra_eye2, camera_pos).x),
            int(world_to_screen(extra_eye2, camera_pos).y),
        ),
        small_eye_radius,
    )
    fang_size = int(body_radius * 0.2)
    fang_left_start = draw_pos + pygame.Vector2(-fang_size, 0)
    fang_right_start = draw_pos + pygame.Vector2(fang_size, 0)
    pygame.draw.line(
        screen,
        fang_color,
        world_to_screen(fang_left_start, camera_pos),
        world_to_screen(
            fang_left_start + pygame.Vector2(-fang_size * 0.5, fang_size), camera_pos
        ),
        2,
    )
    pygame.draw.line(
        screen,
        fang_color,
        world_to_screen(fang_right_start, camera_pos),
        world_to_screen(
            fang_right_start + pygame.Vector2(fang_size * 0.5, fang_size), camera_pos
        ),
        2,
    )

    # --- Debug Info ---
    debug_texts = [
        f"Camera Target: {camera_target.x:.1f}, {camera_target.y:.1f}",
        f"Camera Pos: {camera_pos.x:.1f}, {camera_pos.y:.1f}",
        f"Body Pos: {body_pos.x:.1f}, {body_pos.y:.1f}",
        f"Body Velocity: {body_velocity.x:.1f}, {body_velocity.y:.1f}",
        f"Suspension Offset: {suspension_offset:.1f}",
    ]
    for i, txt in enumerate(debug_texts):
        debug_surf = font.render(txt, True, (255, 255, 255))
        screen.blit(debug_surf, (10, 10 + i * 16))

    pygame.display.flip()

pygame.quit()
sys.exit()
