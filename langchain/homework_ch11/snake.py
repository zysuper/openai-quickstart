import pygame                                                                                                                                                                                                                   
import random                                                                                                                                                                                                                   
                                                                                                                                                                                                                                 
# Define constants for colors and game dimensions                                                                                                                                                                               
WIDTH, HEIGHT = 800, 600                                                                                                                                                                                                        
WHITE = (255, 255, 255)                                                                                                                                                                                                         
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)  # 草地颜色
RED = (255, 0, 0)    # 食物颜色
BROWN = (139, 69, 19)  # 树干颜色
BLUE = (135, 206, 235)  # 天空颜色
                                                                                                                                                                                                                                 
class Food:                                                                                                                                                                                                                     
    def __init__(self):                                                                                                                                                                                                         
         self.x = random.randint(0, WIDTH // 10 - 1) * 10                                                                                                                                                                        
         self.y = random.randint(0, HEIGHT // 10 - 1) * 10                                                                                                                                                                       
                                                                                                                                                                                                                                 
    def set_new_food(self, x, y):                                                                                                                                                                                               
        self.x = x                                                                                                                                                                                                              
        self.y = y                                                                                                                                                                                                              
                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                 
class Snake:                                                                                                                                                                                                                    
    def __init__(self):                                                                                                                                                                                                         
        self.body = [(100, 100)]  # Initialize snake body with a single point                                                                                                                                                   
        self.length = 3                                                                                                                                                                                                         
                                                                                                                                                                                                                                 
    def move(self, direction):
        """Move the snake in the specified direction"""
        head = self.body[-1]
        
        # 计算新的蛇头位置
        if direction == 'up':
            new_head = (head[0], max(0, head[1] - 10))
        elif direction == 'down':  
            new_head = (head[0], min(HEIGHT - 10, head[1] + 10))
        elif direction == 'left':
            new_head = (max(0, head[0] - 10), head[1])
        elif direction == 'right':
            new_head = (min(WIDTH - 10, head[0] + 10), head[1])
        else:
            return
            
        # 更新蛇身
        self.body.append(new_head)
        
        # 如果蛇身长度超过设定长度,删除最老的一节
        while len(self.body) > self.length:
            self.body.pop(0)
                                                                                                                                                                                                                                 
    def grow(self):                                                                                                                                                                                                      
        """Grow the snake by increasing its length"""                                                                                                                                                         
        self.length += 1                                                                                                                                                                                                        
                                                                                                                                                                                                                                 
    def is_out_of_bounds(self):                                                                                                                                                                                                 
        head = self.body[-1]                                                                                                                                                                                                    
        return (head[0] < 0 or                                                                                                                                                                                                  
                head[0] >= WIDTH or                                                                                                                                                                                             
                head[1] < 0 or                                                                                                                                                                                                  
                head[1] >= HEIGHT)                                                                                                                                                                                              
                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                 
class Game:                                                                                                                                                                                                                     
    def __init__(self):                                                                                                                                                                                                         
        self.snake = Snake()                                                                                                                                                                                                    
        self.food = Food()                                                                                                                                                                                                      
                                                                                                                                                                                                                                 
    def new_game(self):                                                                                                                                                                                                         
        """Initialize a new game"""                                                                                                                                                                                             
        self.snake.body = [(100, 100)]                                                                                                                                                                                          
        self.food.x = random.randint(0, WIDTH // 10 - 1) * 10                                                                                                                                                                   
        self.food.y = random.randint(0, HEIGHT // 10 - 1) * 10                                                                                                                                                                  
                                                                                                                                                                                                                                 
    def get_action(self):                                                                                                                                                                                                       
        """Get user input for the next game state"""                                                                                                                                                                            
        return 'up' # placeholder function for now                                                                                                                                                                              
                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                 
class main:                                                                                                                                                                                                                     
    def __init__(self):                                                                                                                                                                                                         
        pygame.init()                                                                                                                                                                                                           
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))                                                                                                                                                                  
        self.clock = pygame.time.Clock()                                                                                                                                                                                             
                                                                                                                                                                                                                                 
        self.game = Game()                                                                                                                                                                                                      
                                                                                                                                                                                                                                 
    def get_action(self):
        """获取键盘输入并返回移动方向"""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            return 'up'
        elif keys[pygame.K_DOWN]:
            return 'down'
        elif keys[pygame.K_LEFT]:
            return 'left'
        elif keys[pygame.K_RIGHT]:
            return 'right'
        return None  # 如果没有按键按下，返回None
        
    def draw_background(self):
        """绘制游戏背景"""
        # 绘制天空
        pygame.draw.rect(self.screen, BLUE, (0, 0, WIDTH, HEIGHT//2))
        
        # 绘制草地
        pygame.draw.rect(self.screen, GREEN, (0, HEIGHT//2, WIDTH, HEIGHT//2))
        
        # 绘制装饰性的树
        for x in range(0, WIDTH, 200):
            # 树干
            pygame.draw.rect(self.screen, BROWN, (x, HEIGHT//2 - 100, 20, 100))
            # 树冠
            pygame.draw.circle(self.screen, GREEN, (x + 10, HEIGHT//2 - 120), 40)
        
    def run(self, actions=None):
        self.clock.tick(30)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                action = self.get_action()  # 现在这行代码可以正常工作了
                if action:  # 如果有有效的动作，移动蛇
                    self.game.snake.move(action)
                    
                    # 检查是否吃到食物
                    snake_head = self.game.snake.body[-1]
                    if snake_head[0] == self.game.food.x and snake_head[1] == self.game.food.y:
                        self.game.snake.grow()
                        # 生成新的食物位置
                        self.game.food.x = random.randint(0, WIDTH // 10 - 1) * 10
                        self.game.food.y = random.randint(0, HEIGHT // 10 - 1) * 10
            
            # 绘制背景
            self.draw_background()
            
            # 绘制蛇
            for segment in self.game.snake.body:
                pygame.draw.rect(self.screen, WHITE, (segment[0], segment[1], 10, 10))
            
            # 绘制食物
            pygame.draw.rect(self.screen, RED, (self.game.food.x, self.game.food.y, 10, 10))
            
            pygame.display.update()
                                                                                                                                                                                                                                 
def main_game(actions=None):                                                                                                                                                                                                    
    game = main()                                                                                                                                                                                                               
    game.run()                                                                                                                                                                                                                  
                                                                                                                                                                                                                                 
main_game()                                                                                                                                                                                                                     
pygame.quit() 