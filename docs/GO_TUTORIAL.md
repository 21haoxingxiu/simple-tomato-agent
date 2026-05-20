# Go 语言学习教程 - 前端开发者视角

> 本教程基于 AgentStudio 项目中的 Gateway 代码，帮助前端开发者快速入门 Go 语言。

## 目录

1. [Go vs JavaScript 核心差异](#1-go-vs-javascript-核心差异)
2. [项目架构与框架](#2-项目架构与框架)
3. [基础语法对照](#3-基础语法对照)
4. [路由与中间件](#4-路由与中间件)
5. [结构体与方法](#5-结构体与方法)
6. [错误处理](#6-错误处理)
7. [并发编程](#7-并发编程)
8. [数据库设计](#8-数据库设计)
9. [调试与问题排查](#9-调试与问题排查)
10. [实战练习](#10-实战练习)

---

## 1. Go vs JavaScript 核心差异

### 1.1 类型系统

```go
// ============ Go (强类型、静态类型) ============
var name string = "hello"           // 显式声明
age := 25                           // 类型推断 (自动推断为 int)
var scores []int = []int{1, 2, 3}   // 切片 (类似数组)
var userMap map[string]int          // map (类似对象)

// 结构体 (类似 TypeScript 的 interface，但运行时存在)
type User struct {
    ID   string `json:"id"`         // 标签，用于 JSON 序列化
    Name string `json:"name"`
    Age  int    `json:"age"`
}

// ============ JavaScript (弱类型、动态类型) ============
const name = "hello"
let age = 25
const scores = [1, 2, 3]
const userMap = {}

// TypeScript 的 interface (仅编译时)
interface User {
    id: string
    name: string
    age: number
}
```

### 1.2 变量声明对比

| 特性 | Go | JavaScript |
|------|-----|------------|
| 声明方式 | `var`, `const`, `:=` | `var`, `let`, `const` |
| 类型推断 | ✅ `:=` 短声明 | ✅ 自动 |
| 作用域 | 块级 | 块级 (let/const) |
| 必须使用 | ✅ 未使用会报错 | ❌ 不强制 |
| 命名规范 | 驼峰式，首字母大写=公开 | 驼峰式 |

```go
// ============ Go 变量声明 ============
var a int           // 默认值 0
var b string        // 默认值 ""
var c bool          // 默认值 false
var d *int          // 默认值 nil (指针)

// 短声明 (最常用，只能在函数内)
name := "agentstudio"
count := 100
isActive := true

// ============ JavaScript ============
let a;              // undefined
let b = null;
let c = false;
```

### 1.3 函数对比

```go
// ============ Go ============
// 单返回值
func add(a, b int) int {
    return a + b
}

// 多返回值 (Go 特有，类似元组)
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// 调用多返回值函数
result, err := divide(10, 2)
if err != nil {
    // 处理错误
}

// ============ JavaScript ============
function add(a, b) {
    return a + b;
}

// 返回对象模拟多返回值
function divide(a, b) {
    if (b === 0) {
        return { error: new Error("division by zero") };
    }
    return { result: a / b };
}

const { result, error } = divide(10, 2);
```

### 1.4 控制流对比

```go
// ============ Go - 没有 while，只有 for ============
// 传统 for
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// while 风格
i := 0
for i < 10 {
    fmt.Println(i)
    i++
}

// 无限循环
for {
    // break 退出
    if condition {
        break
    }
}

// 遍历切片/数组
items := []string{"a", "b", "c"}
for index, value := range items {
    fmt.Printf("%d: %s\n", index, value)
}

// ============ JavaScript ============
for (let i = 0; i < 10; i++) { }
while (i < 10) { }
for (const [index, value] of items.entries()) { }
```

---

## 2. 项目架构与框架

### 2.1 项目结构

```
gateway/
├── main.go           # 入口文件
├── config/
│   └── config.go     # 配置加载
├── handlers/
│   └── proxy.go      # 请求处理器
├── middleware/
│   ├── auth.go       # JWT 认证中间件
│   └── ipallowlist.go # IP 白名单中间件
└── go.mod            # 依赖管理 (类似 package.json)
```

### 2.2 Gin 框架 (类似 Express.js)

```go
// ============ Gin (Go) ============
package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()              // 创建路由引擎 (类似 express())

    // 路由定义
    r.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{          // gin.H 是 map[string]any 的简写
            "status": "ok",
        })
    })

    // 带路径参数
    r.GET("/users/:id", getUser)    // :id 是动态参数

    // 分组路由
    api := r.Group("/api")
    api.Use(AuthMiddleware)         // 应用中间件
    {
        api.GET("/users", listUsers)
        api.POST("/users", createUser)
    }

    r.Run(":8080")                  // 启动服务器
}

// ============ Express.js (JavaScript) ============
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.get('/users/:id', getUser);

const api = express.Router();
api.use(authMiddleware);
api.get('/users', listUsers);
api.post('/users', createUser);
app.use('/api', api);

app.listen(8080);
```

### 2.3 Gin Context vs Express Request/Response

```go
// ============ Gin (Go) ============
func handler(c *gin.Context) {
    // 获取路径参数
    id := c.Param("id")             // /users/:id

    // 获取查询参数
    page := c.Query("page")         // ?page=1
    limit := c.DefaultQuery("limit", "10")

    // 获取请求头
    auth := c.GetHeader("Authorization")

    // 获取请求体 (JSON)
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    // 设置响应
    c.Set("user_id", "123")         // 存储到 context (类似 req.xxx)
    c.JSON(200, gin.H{"token": "xxx"})

    // 中断请求
    c.AbortWithStatusJSON(401, gin.H{"error": "unauthorized"})
}

// ============ Express.js (JavaScript) ============
function handler(req, res) {
    const id = req.params.id;
    const page = req.query.page;
    const limit = req.query.limit || '10';
    const auth = req.get('Authorization');

    const body = req.body;  // 需要 body-parser 中间件

    req.userId = '123';
    res.json({ token: 'xxx' });
}
```

---

## 3. 基础语法对照

### 3.1 指针 (Go 特有，前端无对应概念)

```go
// 指针：存储变量的内存地址
func main() {
    a := 10
    p := &a          // p 是 *int 类型，存储 a 的地址

    fmt.Println(a)   // 10
    fmt.Println(*p)  // 10 (解引用，获取地址处的值)

    *p = 20          // 通过指针修改值
    fmt.Println(a)   // 20 (a 被修改了)
}

// 指针作为函数参数 (引用传递)
func increment(n *int) {
    *n++             // 修改原变量
}

func main() {
    count := 10
    increment(&count)
    fmt.Println(count)  // 11
}

// JavaScript 中没有指针，对象是引用类型
// Go 中区分值类型和引用类型：
// - 值类型：int, float, bool, string, struct, array
// - 引用类型：slice, map, channel, pointer
```

### 3.2 切片 (Slice) vs 数组

```go
// ============ Go ============
// 数组 (固定长度，值类型)
var arr [3]int = [3]int{1, 2, 3}

// 切片 (动态长度，引用类型，类似 JS 数组)
var slice []int = []int{1, 2, 3}
slice = append(slice, 4, 5)        // 追加元素

// make 创建切片
s := make([]int, 0, 10)            // 长度0，容量10

// 切片操作
items := []int{1, 2, 3, 4, 5}
fmt.Println(items[1:3])            // [2, 3] (类似 slice)
fmt.Println(items[:3])             // [1, 2, 3]
fmt.Println(items[2:])             // [3, 4, 5]

// ============ JavaScript ============
const arr = [1, 2, 3];
arr.push(4, 5);
console.log(arr.slice(1, 3));      // [2, 3]
```

### 3.3 Map (类似 JavaScript Object)

```go
// ============ Go ============
// 声明和初始化
var m map[string]int               // nil map，不能直接使用
m = make(map[string]int)           // 创建空 map

// 字面量初始化
config := map[string]string{
    "host": "localhost",
    "port": "8080",
}

// 操作
config["host"] = "127.0.0.1"       // 设置
host := config["host"]             // 获取
delete(config, "port")             // 删除

// 检查 key 是否存在
value, exists := config["host"]
if exists {
    fmt.Println(value)
}

// ============ JavaScript ============
const config = {
    host: 'localhost',
    port: '8080',
};
config.host = '127.0.0.1';
delete config.port;
const exists = 'host' in config;
```

---

## 4. 路由与中间件

### 4.1 路由定义 (查看 main.go)

```go
// 文件: gateway/main.go

func main() {
    r := gin.Default()

    // 1. 简单路由
    r.GET("/health", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "ok"})
    })

    // 2. 通配符路由 - 匹配所有 HTTP 方法
    r.Any("/api/auth/*path", proxyHandler.ProxyToAgent)
    // *path 会匹配 /api/auth/login, /api/auth/register 等

    // 3. 路由组 + 中间件
    api := r.Group("/api")
    api.Use(middleware.Auth(cfg.JWTSecret))  // 应用认证中间件
    {
        api.GET("/me", proxyHandler.ProxyToAgentRewrite("/auth/me"))
        api.POST("/chat/stream", proxyHandler.ProxyStream)
        api.GET("/chat/conversations/:id/messages", proxyHandler.ProxyToAgent)
        // :id 是路径参数
    }
}
```

### 4.2 中间件实现 (查看 middleware/auth.go)

```go
// 文件: gateway/middleware/auth.go

// Auth 返回一个 Gin 中间件函数
// 中间件签名: func(*gin.Context)
func Auth(jwtSecret string) gin.HandlerFunc {
    return func(c *gin.Context) {
        // 1. 获取请求头
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            // 中断请求，返回错误响应
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "code":    "UNAUTHORIZED",
                "message": "missing authorization header",
            })
            return  // 重要：必须 return
        }

        // 2. 解析 Bearer Token
        parts := strings.SplitN(authHeader, " ", 2)
        if len(parts) != 2 || !strings.EqualFold(parts[0], "bearer") {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "code":    "INVALID_TOKEN_FORMAT",
                "message": "authorization header format must be: Bearer <token>",
            })
            return
        }

        // 3. 验证 JWT
        token, err := jwt.ParseWithClaims(parts[1], &Claims{}, func(t *jwt.Token) (interface{}, error) {
            // 验证签名算法
            if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
                return nil, jwt.ErrSignatureInvalid
            }
            return []byte(jwtSecret), nil
        })

        if err != nil || !token.Valid {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "code":    "INVALID_TOKEN",
                "message": "token is invalid or expired",
            })
            return
        }

        // 4. 提取 claims 并存入 context
        claims, ok := token.Claims.(*Claims)
        if !ok {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"code": "INVALID_CLAIMS"})
            return
        }

        // 存储到 context，后续处理器可以获取
        c.Set("user_id", claims.UserID)
        c.Set("workspace_id", claims.WorkspaceID)

        // 5. 调用下一个处理器
        c.Next()
    }
}

// 对比 Express.js 中间件
/*
function authMiddleware(req, res, next) {
    const authHeader = req.get('Authorization');
    if (!authHeader) {
        return res.status(401).json({ error: 'unauthorized' });
    }

    const token = authHeader.split(' ')[1];
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.userId = decoded.user_id;
        next();  // 继续
    } catch (err) {
        res.status(401).json({ error: 'invalid token' });
    }
}
*/
```

### 4.3 中间件执行流程

```
请求 → IP白名单中间件 → CORS中间件 → Auth中间件 → 业务处理器
         ↓                  ↓             ↓              ↓
      检查IP            检查来源       验证JWT         处理请求
         ↓                  ↓             ↓              ↓
      通过/拒绝         通过/拒绝      通过/拒绝       返回响应
                                                    ↑
                                            c.Next() 返回
```

---

## 5. 结构体与方法

### 5.1 结构体定义 (类似 Class)

```go
// 文件: gateway/handlers/proxy.go

// 定义结构体 (类似 class)
type ProxyHandler struct {
    agentServiceURL string        // 私有字段 (小写开头)
    client          *http.Client  // 公开字段 (大写开头)
    streamClient    *http.Client
}

// 构造函数 (Go 没有构造函数，通常用 NewXxx 函数)
func NewProxyHandler(agentURL string) *ProxyHandler {
    return &ProxyHandler{
        agentServiceURL: strings.TrimRight(agentURL, "/"),
        client:          &http.Client{Timeout: 60 * time.Second},
        streamClient:    &http.Client{},  // SSE 不超时
    }
}

// 方法 (值接收者)
func (h *ProxyHandler) ProxyToAgent(c *gin.Context) {
    h.forwardSync(c, stripAPIPrefix(c.Request.URL.Path))
}

// 私有方法
func (h *ProxyHandler) forwardSync(c *gin.Context, agentPath string) {
    // ...
}

// ============ JavaScript Class ============
/*
class ProxyHandler {
    constructor(agentURL) {
        this.agentServiceURL = agentURL.replace(/\/$/, '');
        this.client = new HttpClient({ timeout: 60000 });
        this.streamClient = new HttpClient();
    }

    proxyToAgent(c) {
        this.forwardSync(c, stripAPIPrefix(c.request.url.path));
    }

    forwardSync(c, agentPath) {
        // ...
    }
}
*/
```

### 5.2 方法接收者：值 vs 指针

```go
// 值接收者 - 操作副本，不修改原结构体
func (h ProxyHandler) GetValue() string {
    return h.agentServiceURL
}

// 指针接收者 - 可以修改原结构体，性能更好（不复制）
func (h *ProxyHandler) SetURL(url string) {
    h.agentServiceURL = url  // 修改原结构体
}

// 经验法则：
// 1. 需要修改结构体 → 用指针接收者
// 2. 结构体较大 → 用指针接收者（避免复制）
// 3. 一致性：一个类型的方法，要么全用值，要么全用指针
```

### 5.3 结构体标签 (JSON 序列化)

```go
type Claims struct {
    UserID      string `json:"user_id"`       // JSON 字段名
    WorkspaceID string `json:"workspace_id"`
    jwt.RegisteredClaims                    // 嵌入其他结构体
}

// 序列化
claims := Claims{UserID: "123", WorkspaceID: "456"}
data, _ := json.Marshal(claims)
// 输出: {"user_id":"123","workspace_id":"456",...}

// 反序列化
var c Claims
json.Unmarshal(data, &c)
```

---

## 6. 错误处理

### 6.1 Go 的错误处理哲学

```go
// Go 没有 try-catch，使用显式错误返回
func doSomething() (string, error) {
    if somethingWrong {
        return "", errors.New("something went wrong")
    }
    return "success", nil
}

// 调用时必须检查错误
result, err := doSomething()
if err != nil {
    // 处理错误
    log.Printf("error: %v", err)
    return err  // 向上传递错误
}
// 使用 result

// ============ JavaScript ============
/*
try {
    const result = doSomething();
} catch (err) {
    console.error(err);
}
*/
```

### 6.2 项目中的错误处理示例

```go
// 文件: gateway/handlers/proxy.go

func (h *ProxyHandler) forwardSync(c *gin.Context, agentPath string) {
    targetURL := h.agentServiceURL + agentPath

    // 创建请求
    req, err := http.NewRequestWithContext(c.Request.Context(), c.Request.Method, targetURL, c.Request.Body)
    if err != nil {
        // 错误处理：返回 500
        c.JSON(http.StatusInternalServerError, gin.H{
            "code":    "PROXY_ERROR",
            "message": err.Error(),
        })
        return  // 必须返回
    }

    // 发送请求
    resp, err := h.client.Do(req)
    if err != nil {
        // 错误处理：返回 502
        c.JSON(http.StatusBadGateway, gin.H{
            "code":    "AGENT_UNAVAILABLE",
            "message": err.Error(),
        })
        return
    }
    defer resp.Body.Close()  // 确保关闭响应体

    // ...
}
```

### 6.3 defer 关键字 (延迟执行)

```go
// defer 会在函数返回前执行，类似 finally
func example() {
    file, err := os.Open("test.txt")
    if err != nil {
        return
    }
    defer file.Close()  // 函数返回前自动关闭

    // 多个 defer 按 LIFO 顺序执行
    defer fmt.Println("1")
    defer fmt.Println("2")
    defer fmt.Println("3")
    // 输出: 3, 2, 1
}

// 常见用法
func (h *ProxyHandler) forwardSync(c *gin.Context, agentPath string) {
    resp, err := h.client.Do(req)
    if err != nil { return }
    defer resp.Body.Close()  // 确保资源释放

    // ... 其他逻辑
}
```

---

## 7. 并发编程

### 7.1 Goroutine (轻量级线程)

```go
// 启动 goroutine
go func() {
    fmt.Println("异步执行")
}()

// 带参数的 goroutine
go func(msg string) {
    fmt.Println(msg)
}("hello")

// ============ JavaScript ============
/*
// Promise
Promise.resolve().then(() => {
    console.log('异步执行');
});

// async/await
(async () => {
    console.log('异步执行');
})();
*/
```

### 7.2 Channel (goroutine 间通信)

```go
// 创建 channel
ch := make(chan string)

// 发送数据
go func() {
    ch <- "hello"  // 发送
}()

// 接收数据
msg := <-ch       // 阻塞等待
fmt.Println(msg)

// 带缓冲的 channel
bufCh := make(chan int, 10)  // 缓冲区大小 10
bufCh <- 1                   // 不阻塞（缓冲区未满）
value := <-bufCh             // 接收

// 关闭 channel
close(ch)

// 遍历 channel
for msg := range ch {
    fmt.Println(msg)  // channel 关闭后退出循环
}
```

### 7.3 Context (取消/超时控制)

```go
// 文件: gateway/handlers/proxy.go

func (h *ProxyHandler) forwardStream(c *gin.Context, agentPath string) {
    // 创建可取消的 context
    ctx, cancel := context.WithCancel(c.Request.Context())
    defer cancel()  // 函数返回时取消

    // 使用 context 创建请求
    req, err := http.NewRequestWithContext(ctx, c.Request.Method, targetURL, c.Request.Body)
    // ...
}

// Context 用途：
// 1. 取消操作：ctx.Done() 返回一个 channel，关闭时表示取消
// 2. 超时控制：context.WithTimeout(5 * time.Second)
// 3. 传递值：context.WithValue(ctx, "key", value)
```

---

## 8. 数据库设计

### 8.1 Python Agent 数据库模型 (SQLAlchemy)

```python
# 文件: agent/db/models.py

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    # 字段定义
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    default_workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系 (一对多)
    workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace", back_populates="owner", cascade="all, delete-orphan"
    )

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # 外键
        nullable=False,
        index=True,  # 创建索引
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 反向关系
    owner: Mapped["User"] = relationship("User", back_populates="workspaces")
```

### 8.2 数据库关系图

```
┌──────────────┐       ┌──────────────┐
│    User      │       │  Workspace   │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ owner_id(FK) │
│ email        │  1:N  │ id (PK)      │
│ name         │       │ name         │
│ password_hash│       │ description  │
│ default_ws_id│       └──────────────┘
└──────────────┘              │
                              │ 1:N
                              ▼
                       ┌──────────────┐
                       │ KnowledgeBase│
                       ├──────────────┤
                       │ id (PK)      │
                       │ workspace_id │
                       │ name         │
                       │ doc_count    │
                       └──────────────┘
                              │
                              │ 1:N
                              ▼
                       ┌──────────────┐
                       │   Document   │
                       ├──────────────┤
                       │ id (PK)      │
                       │ kb_id (FK)   │
                       │ filename     │
                       │ status       │
                       └──────────────┘
```

### 8.3 Go 中如何访问数据库

```go
// Go 项目中 Gateway 不直接访问数据库
// 但可以使用 GORM (类似 SQLAlchemy)

/*
import "gorm.io/gorm"

type User struct {
    gorm.Model
    Email    string `gorm:"uniqueIndex"`
    Name     string
    Password string
}

// 查询
var user User
db.First(&user, "email = ?", "test@example.com")

// 创建
db.Create(&User{Email: "test@example.com", Name: "Test"})

// 更新
db.Model(&user).Update("Name", "New Name")

// 删除
db.Delete(&user)
*/
```

---

## 9. 调试与问题排查

### 9.1 日志记录

```go
// 标准库 log
package main

import "log"

func main() {
    log.Println("应用启动")
    log.Printf("用户登录: %s, 时间: %v", "test@example.com", time.Now())
    log.Fatal("严重错误")  // 打印后退出程序
}

// Gin 框架日志
// gin.Default() 默认包含 Logger 和 Recovery 中间件
// gin.New() 不包含中间件，需要手动添加
```

### 9.2 查看日志

```bash
# 启动 Gateway 查看日志
cd gateway && go run .

# 输出示例
[GIN-debug] GET    /health                   --> main.main.func1 (5 handlers)
[GIN-debug] POST   /api/chat/stream          --> ...
2026/05/19 08:44:26 Gateway listening on 127.0.0.1:8080

# 请求日志
[GIN] 2026/05/19 - 08:44:50 | 200 |     98.25µs | 127.0.0.1 | POST "/api/auth/login"
```

### 9.3 调试技巧

```bash
# 1. 检查服务状态
curl http://localhost:8080/health

# 2. 检查端口占用
lsof -i :8080

# 3. 查看进程
ps aux | grep gateway

# 4. 测试 API
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'

# 5. 查看 Go 环境变量
go env

# 6. 格式化代码
go fmt ./...

# 7. 静态检查
go vet ./...
```

### 9.4 常见问题排查

```bash
# 问题1: 端口被占用
# 解决: 杀掉占用进程
lsof -i :8080
kill -9 <PID>

# 问题2: 模块依赖问题
# 解决: 重新下载依赖
go mod tidy
go mod download

# 问题3: CORS 错误
# 检查: gateway/main.go 中的 CORS 配置
# 确保前端地址在 AllowOrigins 中

# 问题4: JWT 验证失败
# 检查: JWT_SECRET 环境变量是否一致
# 检查: token 是否过期
```

### 9.5 使用 Delve 调试器

```bash
# 安装 Delve
go install github.com/go-delve/delve/cmd/dlv@latest

# 调试程序
dlv debug ./gateway

# 常用命令
# break main.main    - 在 main 函数设置断点
# continue           - 继续执行
# next               - 执行下一行
# step               - 进入函数
# print <变量>        - 打印变量值
# locals             - 打印本地变量
# goroutines         - 列出所有 goroutine
# quit               - 退出
```

---

## 10. 实战练习

### 练习1: 添加新的 API 路由

**任务**: 添加 `/api/version` 接口返回版本信息

```go
// 在 main.go 中添加
r.GET("/api/version", func(c *gin.Context) {
    c.JSON(200, gin.H{
        "version": "1.0.0",
        "service": "gateway",
    })
})
```

### 练习2: 创建新的中间件

**任务**: 创建请求日志中间件

```go
// middleware/logger.go
package middleware

import (
    "log"
    "time"

    "github.com/gin-gonic/gin"
)

func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()

        c.Next()  // 处理请求

        duration := time.Since(start)
        log.Printf("[%s] %s %s %dms",
            c.Request.Method,
            c.Request.URL.Path,
            c.ClientIP(),
            duration.Milliseconds(),
        )
    }
}

// 在 main.go 中使用
r.Use(middleware.Logger())
```

### 练习3: 添加健康检查详情

**任务**: 扩展 /health 接口，检查依赖服务

```go
r.GET("/health", func(c *gin.Context) {
    // 检查 Agent 服务
    agentHealth := checkAgentHealth(cfg.AgentServiceURL)

    c.JSON(200, gin.H{
        "status": "ok",
        "service": "gateway",
        "dependencies": gin.H{
            "agent": agentHealth,
        },
    })
})

func checkAgentHealth(agentURL string) string {
    resp, err := http.Get(agentURL + "/health")
    if err != nil {
        return "unhealthy: " + err.Error()
    }
    defer resp.Body.Close()
    if resp.StatusCode == 200 {
        return "healthy"
    }
    return "unhealthy: status " + resp.Status
}
```

---

## 附录: 学习资源

### 官方资源
- [Go 官方教程](https://go.dev/tour/)
- [Go by Example](https://gobyexample.com/)
- [Effective Go](https://go.dev/doc/effective_go)

### 框架文档
- [Gin Web Framework](https://gin-gonic.com/docs/)
- [GORM](https://gorm.io/docs/)

### 项目文件对照表

| 文件 | 学习重点 |
|------|---------|
| `main.go` | 程序入口、路由定义、中间件使用 |
| `config/config.go` | 结构体、环境变量、函数 |
| `middleware/auth.go` | 中间件模式、JWT、错误处理 |
| `middleware/ipallowlist.go` | 网络编程、安全中间件 |
| `handlers/proxy.go` | HTTP 客户端、流式处理、结构体方法 |

---

## 学习建议

1. **边看边写**: 对照代码，理解每一行的作用
2. **修改代码**: 尝试添加新功能，观察效果
3. **阅读文档**: Gin 框架文档写得很清晰
4. **调试运行**: 使用 `fmt.Println` 或日志观察程序行为
5. **对比学习**: 用 TypeScript/Express 知识帮助理解 Go 概念
