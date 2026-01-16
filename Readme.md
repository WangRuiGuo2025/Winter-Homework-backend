# DEV-BLOG后端

> 基于Python Fastapi和数据库Sqllite制作的Dev-blog后端

## 项目简介

本项目用于锻炼后端项目的制作，完成寒假大作业

## 技术栈

### 核心框架/库

- **后端**：Python Fastapi、Sqllite

## 实现功能

### 核心功能

1. 实现用户注册、登录、基础权限控制
2. 实现了发表的文章的存储功能
3. 实现了对应文章的评论、点赞的存储功能

## 快速开始

### 环境要求

- 操作系统：Windows/macOS/Linux
- 运行环境：Python

### 安装与启动步骤

#### 1. 克隆项目

```bash
git clone https://github.com/WangRuiGuo2025/Winter-Homework-backend.git
cd Winter-Homework-backend
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 启动项目

```bash
uvicorn main:app --reload
```

#### 4. 访问项目

- 后端接口地址：http://localhost:8000
- 接口文档地址：http://localhost:8000/docs
