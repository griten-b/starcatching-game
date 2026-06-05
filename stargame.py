import pygame
import random
import json
import os
import sys

# 게임 초기화
pygame.init()

WIDTH = 600
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("별 찾기 게임 v4")

# 색상 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)

clock = pygame.time.Clock()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 리더보드(데이터 저장) 설정 ---
LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_leaderboard(scores):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(scores, f)

top_scores = load_leaderboard()

TARGET_FPS = 144

# 플레이어(바) 설정
bar_width = 100
bar_height = 20
bar_x_float = float(WIDTH // 2 - bar_width // 2) 
bar_rect = pygame.Rect(int(bar_x_float), HEIGHT - 50, bar_width, bar_height)
bar_speed = 5 

# 별 및 장애물 설정
star_size = 35 
stars = [] 
base_speed = 1.667
spawn_timer = 0

bomb_size = 35 
bombs = [] 
bomb_spawn_timer = 0

# 이미지 불러오기
try:
    # 이미지 로드
    star_img = pygame.image.load(resource_path("star.png")).convert_alpha()
    star_img = pygame.transform.scale(star_img, (star_size, star_size))
    bomb_img = pygame.image.load(resource_path("bomb.png")).convert_alpha()
    bomb_img = pygame.transform.scale(bomb_img, (bomb_size, bomb_size))
except FileNotFoundError:
    print("\n[오류] 이미지 파일을 찾을 수 없습니다!")
    pygame.quit()
    sys.exit()

try:
    # 사운드 로드
    star_sound = pygame.mixer.Sound(resource_path("star_sound.wav"))
    bomb_sound = pygame.mixer.Sound(resource_path("bomb_sound.wav"))
    # 소리가 너무 크면 여기서 볼륨을 줄일 수 있습니다 (0.0 ~ 1.0)
    star_sound.set_volume(0.5) 
    bomb_sound.set_volume(0.7)
except FileNotFoundError:
    print("\n[경고] 사운드 파일을 찾을 수 없습니다. 소리 없이 게임이 진행됩니다.")
    star_sound = None
    bomb_sound = None

# 점수, 목숨 및 상태 설정
score = 0
lives = 4
show_start_screen = True # 시작 화면 표시 여부 변수 추가
game_over = False
last_star_x = WIDTH // 2 

# --- 폰트 설정 (한글 지원 폰트로 변경) ---
if sys.platform == 'win32':
    korean_font = "malgungothic"
else:
    korean_font = "AppleGothic"

try:
    font = pygame.font.SysFont(korean_font, 48)
    large_font = pygame.font.SysFont(korean_font, 72)
    instruction_font = pygame.font.SysFont(korean_font, 36)
    button_font = pygame.font.SysFont(korean_font, 40)
except:
    # 폰트를 찾지 못했을 경우 기본 폰트로 폴백 (영어 기본)
    font = pygame.font.SysFont(None, 48)
    large_font = pygame.font.SysFont(None, 72)
    instruction_font = pygame.font.SysFont(None, 36)
    button_font = pygame.font.SysFont(None, 40)

# 텍스트 렌더링 캐싱 변수
cached_score = -1
cached_lives = -1
score_surface = None
lives_surface = None

# 버튼 영역 설정
start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 50)
restart_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 220, 200, 50)
start_ticks = 0 # 게임 시작 시간을 0으로 초기화

# 게임 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 마우스 클릭 이벤트 처리
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 1. 시작 화면에서 'Game Start' 클릭 시
            if show_start_screen and start_button_rect.collidepoint(event.pos):
                show_start_screen = False
                score = 0
                lives = 4
                stars.clear()
                bombs.clear()
                bar_x_float = float(WIDTH // 2 - bar_width // 2)
                bar_rect.x = int(bar_x_float)
                start_ticks = pygame.time.get_ticks() # 이때부터 진짜 플레이 타임 측정 시작
                spawn_timer = 0
                bomb_spawn_timer = 0
                last_star_x = WIDTH // 2
                cached_score = -1 
                
            # 2. 게임 오버 화면에서 'Play Again' 클릭 시
            elif game_over and restart_button_rect.collidepoint(event.pos):
                score = 0
                lives = 4
                stars.clear()
                bombs.clear()
                bar_x_float = float(WIDTH // 2 - bar_width // 2)
                bar_rect.x = int(bar_x_float)
                start_ticks = pygame.time.get_ticks()
                spawn_timer = 0
                bomb_spawn_timer = 0
                game_over = False
                last_star_x = WIDTH // 2
                cached_score = -1 

    # 시작 화면도 아니고 게임 오버 상태도 아닐 때만 게임 로직 실행
    if not show_start_screen and not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and bar_x_float > 0:
            bar_x_float -= bar_speed
        if keys[pygame.K_RIGHT] and bar_x_float < WIDTH - bar_width:
            bar_x_float += bar_speed
        
        bar_rect.x = int(bar_x_float)
        elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000
        current_speed = base_speed + (elapsed_time * 0.0833)

        # 별 생성
        spawn_timer += 1
        spawn_rate = max(36, 144 - int(elapsed_time * 1.2)) 
        
        if spawn_timer > spawn_rate:
            spawn_timer = 0
            max_travel_distance = spawn_rate * bar_speed
            reachable_radius = int(max_travel_distance * 0.8)
            
            min_x = max(0, last_star_x - reachable_radius)
            max_x = min(WIDTH - star_size, last_star_x + reachable_radius)
            
            new_star_x = random.randint(int(min_x), int(max_x))
            stars.append([0.0, pygame.Rect(new_star_x, 0, star_size, star_size)])
            last_star_x = new_star_x

        # 장애물 생성
        bomb_spawn_timer += 1
        bomb_spawn_rate = max(72, 216 - int(elapsed_time * 1.2))
        
        if bomb_spawn_timer > bomb_spawn_rate:
            bomb_spawn_timer = 0
            bombs.append([0.0, pygame.Rect(random.randint(0, WIDTH - bomb_size), 0, bomb_size, bomb_size)])

        # 별 이동 및 충돌
        surviving_stars = []
        for star in stars:
            star[0] += current_speed
            star[1].y = int(star[0]) 

            if star[1].colliderect(bar_rect):
                score += 1
                if star_sound:
                    star_sound.play()
            elif star[1].y > HEIGHT:
                lives -= 1
                if lives <= 0 and not game_over:
                    game_over = True
                    top_scores.append(score)
                    top_scores.sort(reverse=True)
                    top_scores = top_scores[:5]
                    save_leaderboard(top_scores)
            else:
                surviving_stars.append(star)
        stars = surviving_stars

        # 장애물 이동 및 충돌
        surviving_bombs = []
        for bomb in bombs:
            bomb[0] += current_speed
            bomb[1].y = int(bomb[0])

            if bomb[1].colliderect(bar_rect):
                score -= 3
                if bomb_sound:
                    bomb_sound.play()
            elif bomb[1].y > HEIGHT:
                pass
            else:
                surviving_bombs.append(bomb)
        bombs = surviving_bombs

    # --- 화면 그리기 ---
    screen.fill(BLACK) 

    if show_start_screen:
        # --- 시작 화면 렌더링 ---
        title_text = large_font.render("별 찾기 게임", True, YELLOW)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 250))

        inst1 = instruction_font.render("별을 먹을 시 : +1점", True, WHITE)
        inst2 = instruction_font.render("폭탄을 먹을 시 : -3점", True, WHITE)
        inst3 = instruction_font.render("별을 4번 놓치면 : 게임 오버", True, RED)

        # 설명 간격 맞춤
        screen.blit(inst1, (WIDTH // 2 - inst1.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(inst2, (WIDTH // 2 - inst2.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(inst3, (WIDTH // 2 - inst3.get_width() // 2, HEIGHT // 2 + 20))

        # 게임 시작 버튼
        pygame.draw.rect(screen, GRAY, start_button_rect)
        start_btn_text = button_font.render("Game Start", True, BLACK)
        screen.blit(start_btn_text, start_btn_text.get_rect(center=start_button_rect.center))

    elif not game_over:
        # --- 실제 플레이 화면 렌더링 ---
        pygame.draw.rect(screen, WHITE, bar_rect)
        
        for star in stars:
            screen.blit(star_img, star[1]) 
            
        for bomb in bombs:
            screen.blit(bomb_img, bomb[1])

        if score != cached_score:
            score_surface = font.render(f"Score: {score}", True, WHITE)
            cached_score = score
        if lives != cached_lives:
            lives_surface = font.render(f"Lives: {lives}", True, RED)
            cached_lives = lives

        screen.blit(score_surface, (10, 10))
        screen.blit(lives_surface, (WIDTH - 180, 10))
        
    else:
        # --- 게임 오버 및 리더보드 화면 렌더링 ---
        game_over_text = large_font.render("GAME OVER", True, RED)
        final_score_text = font.render(f"Final Score: {score}", True, WHITE)
        
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 220))
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 140))

        leaderboard_title = button_font.render("--- TOP 5 SCORES ---", True, YELLOW)
        screen.blit(leaderboard_title, (WIDTH // 2 - leaderboard_title.get_width() // 2, HEIGHT // 2 - 50))

        for i, top_score in enumerate(top_scores):
            rank_text = button_font.render(f"{i + 1}. {top_score} pts", True, WHITE)
            screen.blit(rank_text, (WIDTH // 2 - rank_text.get_width() // 2, HEIGHT // 2 + (i * 40)))

        pygame.draw.rect(screen, GRAY, restart_button_rect)
        button_text = button_font.render("Play Again", True, BLACK)
        text_rect = button_text.get_rect(center=restart_button_rect.center)
        screen.blit(button_text, text_rect)

    pygame.display.flip()
    clock.tick(TARGET_FPS)

pygame.quit()