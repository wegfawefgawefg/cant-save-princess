import pygame, sys, math, random

# Settings
WIDTH, HEIGHT = 800, 600
LOWRES_WIDTH, LOWRES_HEIGHT = 400, 300

# Container dimensions (small and shallow)
CONT_WIDTH = 150
CONT_HEIGHT = 80

GRAVITY = 0.5
DT = 1
SUBSTEPS = 16  # Increased substeps for more precise collision checking
PARTICLE_RADIUS = 4
RESTITUTION = 0.6
CELL_SIZE = PARTICLE_RADIUS * 4
THRESHOLD_SQ = (2 * PARTICLE_RADIUS) ** 2
MAX_PARTICLES = 1000
SPLASH_COLLISION_THRESHOLD = 5

# Extra margin to shrink collision bounds
MARGIN = 4

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
lowres_surf = pygame.Surface((LOWRES_WIDTH, LOWRES_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)


def rotate_point(pt, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x, y = pt
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a)


# --- Container class with labels ---
class Container:
    def __init__(self, center, width, height, angle_func, open_side, label):
        self.center = center
        self.width = width
        self.height = height
        self.angle_func = angle_func  # function of time t
        self.angle = 0
        self.open_top = True  # always open on top
        self.open_side = open_side  # "left" or "right" (the open side)
        self.label = label

    def update(self, t):
        self.angle = self.angle_func(t)

    def in_bounds(self, particle):
        # Transform particle center into container-local coordinates.
        rx = particle.x - self.center[0]
        ry = particle.y - self.center[1]
        lx, ly = rotate_point((rx, ry), -self.angle)
        # Check within container rectangle.
        if lx < -self.width / 2 or lx > self.width / 2:
            return False
        if ly < -self.height / 2 or ly > self.height / 2:
            return False
        return True

    def apply_collision(self, particle):
        rx = particle.x - self.center[0]
        ry = particle.y - self.center[1]
        lx, ly = rotate_point((rx, ry), -self.angle)
        lvx, lvy = rotate_point((particle.vx, particle.vy), -self.angle)
        collided = False
        # Use margin to shrink effective collision bounds.
        if self.open_side != "left" and lx < -self.width / 2 + PARTICLE_RADIUS + MARGIN:
            lx = -self.width / 2 + PARTICLE_RADIUS + MARGIN
            lvx = -lvx * RESTITUTION
            collided = True
        if self.open_side != "right" and lx > self.width / 2 - PARTICLE_RADIUS - MARGIN:
            lx = self.width / 2 - PARTICLE_RADIUS - MARGIN
            lvx = -lvx * RESTITUTION
            collided = True
        if ly > self.height / 2 - PARTICLE_RADIUS - MARGIN:
            ly = self.height / 2 - PARTICLE_RADIUS - MARGIN
            lvy = -lvy * RESTITUTION
            collided = True
        if collided:
            new_rx, new_ry = rotate_point((lx, ly), self.angle)
            particle.x = self.center[0] + new_rx
            particle.y = self.center[1] + new_ry
            new_vx, new_vy = rotate_point((lvx, lvy), self.angle)
            particle.vx, particle.vy = new_vx, new_vy


# --- Drawing helper for containers ---
def draw_container(container, surf, scale_x, scale_y):
    cont_surf = pygame.Surface((container.width, container.height), pygame.SRCALPHA)
    cont_surf.fill((0, 0, 0, 0))
    # Draw bottom wall always.
    pygame.draw.line(
        cont_surf,
        (200, 200, 200),
        (0, container.height),
        (container.width, container.height),
        3,
    )
    # Draw left wall if not open.
    if container.open_side != "left":
        pygame.draw.line(cont_surf, (200, 200, 200), (0, 0), (0, container.height), 3)
    # Draw right wall if not open.
    if container.open_side != "right":
        pygame.draw.line(
            cont_surf,
            (200, 200, 200),
            (container.width, 0),
            (container.width, container.height),
            3,
        )
    # Draw label at top center.
    label_surf = font.render(container.label, True, (200, 200, 200))
    lx = (container.width - label_surf.get_width()) // 2
    cont_surf.blit(label_surf, (lx, 2))
    rotated = pygame.transform.rotate(cont_surf, -math.degrees(container.angle))
    rotated = pygame.transform.scale(
        rotated,
        (int(rotated.get_width() * scale_x), int(rotated.get_height() * scale_y)),
    )
    cont_center = (
        int(container.center[0] * scale_x),
        int(container.center[1] * scale_y),
    )
    rect = rotated.get_rect(center=cont_center)
    surf.blit(rotated, rect.topleft)


# --- Particle classes ---
class Particle:
    __slots__ = ("x", "y", "vx", "vy")

    def __init__(self, pos):
        self.x, self.y = pos
        self.vx, self.vy = 0, 0

    def update(self, dt):
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf, scale_x, scale_y):
        sx = int(self.x * scale_x)
        sy = int(self.y * scale_y)
        temp = pygame.Surface(
            (PARTICLE_RADIUS * 2, PARTICLE_RADIUS * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            temp,
            (0, 100, 255, 180),
            (PARTICLE_RADIUS, PARTICLE_RADIUS),
            PARTICLE_RADIUS,
        )
        surf.blit(temp, (sx - PARTICLE_RADIUS, sy - PARTICLE_RADIUS))


class SplashParticle:
    __slots__ = ("x", "y", "vx", "vy", "lifetime", "alpha")

    def __init__(self, pos, vx, vy):
        self.x, self.y = pos
        if vy > 0:
            vy = -abs(vy)
        self.vx, self.vy = vx, vy
        self.lifetime = random.randint(5, 10)
        self.alpha = 255

    def update(self, dt):
        self.vy += GRAVITY * 1.4 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= 1
        self.alpha = int(255 * (self.lifetime / 15))

    def is_dead(self):
        return self.lifetime <= 0

    def draw(self, surf, scale_x, scale_y):
        sx = int(self.x * scale_x)
        sy = int(self.y * scale_y)
        r = max(1, PARTICLE_RADIUS // 2)
        temp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (255, 255, 255, self.alpha), (r, r), r)
        surf.blit(temp, (sx - r, sy - r))


# --- Create three containers arranged in a downward chain ---
# Container A: positioned near the vertical center line, a bit to the left.
# Container B: moved further right.
# Container C: same x as A, at a lower height.
containerA = Container(
    center=(WIDTH // 2 - 50, HEIGHT // 3 - 20),
    width=CONT_WIDTH,
    height=CONT_HEIGHT,
    angle_func=lambda t: math.radians(5) * math.sin(t),
    open_side="right",  # spills to right into B
    label="A",
)
containerB = Container(
    center=(WIDTH // 2 + 100, HEIGHT // 2),
    width=CONT_WIDTH,
    height=CONT_HEIGHT,
    angle_func=lambda t: math.radians(5) * math.sin(t + math.pi / 4),
    open_side="left",  # spills to left into C
    label="B",
)
containerC = Container(
    center=(WIDTH // 2 - 50, 2 * HEIGHT // 3 + 20),
    width=CONT_WIDTH,
    height=CONT_HEIGHT,
    angle_func=lambda t: math.radians(5) * math.sin(t + math.pi / 2),
    open_side="right",
    label="C",
)
containers = [containerA, containerB, containerC]

particles = []
splash_particles = []
time_elapsed = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)
        ):
            running = False

    time_elapsed += 0.02
    for cont in containers:
        cont.update(time_elapsed)

    # Only spawn water into container A.
    if clock.get_fps() >= 60 and random.random() < 0.5:
        local_x = random.uniform(-containerA.width / 2 + 10, containerA.width / 2 - 10)
        local_y = -containerA.height / 2 + 5
        ox, oy = rotate_point((local_x, local_y), -containerA.angle)
        spawn_pos = (containerA.center[0] + ox, containerA.center[1] + oy)
        particles.append(Particle(spawn_pos))
    if len(particles) > MAX_PARTICLES:
        particles = particles[-MAX_PARTICLES:]

    # Update particles with substepping.
    for p in particles:
        for _ in range(SUBSTEPS):
            p.update(DT / SUBSTEPS)
            for cont in containers:
                if cont.in_bounds(p):
                    cont.apply_collision(p)
                    break

    # --- Optional: Water particle collision detection (unchanged) ---
    grid = {}
    for p in particles:
        cell = (int(p.x // CELL_SIZE), int(p.y // CELL_SIZE))
        grid.setdefault(cell, []).append(p)
    for cell_particles in grid.values():
        n = len(cell_particles)
        for i in range(n):
            p1 = cell_particles[i]
            for j in range(i + 1, n):
                p2 = cell_particles[j]
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dsq = dx * dx + dy * dy
                if dsq < THRESHOLD_SQ and dsq > 0:
                    dist = math.sqrt(dsq)
                    overlap = 2 * PARTICLE_RADIUS - dist
                    inv_dist = 1 / dist
                    nx = dx * inv_dist
                    ny = dy * inv_dist
                    sep = overlap * 0.5
                    p1.x -= nx * sep
                    p1.y -= ny * sep
                    p2.x += nx * sep
                    p2.y += ny * sep
                    rvx = p2.vx - p1.vx
                    rvy = p2.vy - p1.vy
                    rel_norm = rvx * nx + rvy * ny
                    if rel_norm < 0:
                        impulse = -(1 + RESTITUTION) * rel_norm * 0.5
                        p1.vx -= impulse * nx
                        p1.vy -= impulse * ny
                        p2.vx += impulse * nx
                        p2.vy += impulse * ny
                        if impulse > SPLASH_COLLISION_THRESHOLD:
                            cx = (p1.x + p2.x) / 2
                            cy = (p1.y + p2.y) / 2
                            for _ in range(random.randint(1, 2)):
                                angle_offset = random.uniform(-math.pi / 4, math.pi / 4)
                                base_speed = impulse * 0.8
                                splash_vx = -nx * base_speed
                                splash_vy = -ny * base_speed
                                cos_off = math.cos(angle_offset)
                                sin_off = math.sin(angle_offset)
                                new_vx = splash_vx * cos_off - splash_vy * sin_off
                                new_vy = splash_vx * sin_off + splash_vy * cos_off
                                if new_vy > 0:
                                    new_vy = -abs(new_vy)
                                splash_particles.append(
                                    SplashParticle((cx, cy), new_vx, new_vy)
                                )
    # (Neighbor cell collisions omitted for brevity.)

    for s in splash_particles[:]:
        s.update(DT)
        if s.is_dead():
            splash_particles.remove(s)

    lowres_surf.fill((30, 30, 30))
    scale_x = LOWRES_WIDTH / WIDTH
    scale_y = LOWRES_HEIGHT / HEIGHT
    for cont in containers:
        draw_container(cont, lowres_surf, scale_x, scale_y)
    for p in particles:
        p.draw(lowres_surf, scale_x, scale_y)
    for s in splash_particles:
        s.draw(lowres_surf, scale_x, scale_y)
    fps = clock.get_fps()
    info_text = font.render(
        f"P: {len(particles)} FPS: {fps:.1f}", True, (255, 255, 255)
    )
    lowres_surf.blit(info_text, (10, 10))
    final = pygame.transform.scale(lowres_surf, (WIDTH, HEIGHT))
    screen.blit(final, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
