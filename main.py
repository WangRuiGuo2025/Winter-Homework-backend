import sqlalchemy
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from starlette.responses import JSONResponse, FileResponse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta,timezone
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 这一段肯定不会，绝对是抄的，不用想，但是我尽可能的去理解了
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明模型基类
Base = declarative_base()

CST = timezone(timedelta(hours=8))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    publisher = Column(String, index=True)
    publish_time = Column(
        DateTime,
        default=lambda: datetime.now(CST)  # 中国当前时间（AI帮助）
    )


# 新增点赞表
class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    like_time = Column(DateTime, default=lambda: datetime.now(CST))

    # 唯一约束：一个用户只能给一篇文章点一次赞
    __table_args__ = (
        sqlalchemy.UniqueConstraint('article_id', 'username', name='unique_article_user_like'),
    )

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    content = Column(String, nullable=False)
    comment_time = Column(DateTime, default=lambda: datetime.now(CST))

Base.metadata.create_all(bind=engine)


#（AI帮助）忘记了这里不能直接用数据库模型：（
class ArticleSubmit(BaseModel):
    title: str
    content: str
    publisher: str


class LikeRequest(BaseModel):
    article_id: int
    username: str


class CommentRequest(BaseModel):
    article_id: int
    username: str
    content: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/login")
async def login(username: str, password: str,db:Session=Depends(get_db)):
    user =db.query(User).filter(User.username == username,User.password == password).first()
    if user:
        return {"code": 1}
    else:
        return {"code": 0}

@app.get("/register")
async def register(username: str,password: str,db:Session=Depends(get_db)):
    try:
        newuser = User(username=username,password=password)
        db.add(newuser)
        db.commit()
        db.refresh(newuser)
        return {"code": 1}
    except Exception as e:
        db.rollback()
        return {"code": 0}

@app.get("/about")
async def about():
    return FileResponse(
        path="./about.json",
        media_type="application/json",
    )

@app.post("/articles/submit")
async def submit_article(article:ArticleSubmit,db:Session=Depends(get_db)):
    try:
        publisher = db.query(User).filter(User.username == article.publisher).first()
        if not publisher:
            return {"code": 0}
        newarticle = Article(
            title=article.title,
            content=article.content,
            publisher=article.publisher,
        )
        db.add(newarticle)
        db.commit()
        db.refresh(newarticle)
        return {"code": 1}
    except Exception as e:
        db.rollback()
        return {"code": 0}

@app.get("/articles/list")
async def get_article_list(db: Session = Depends(get_db)):

    articles = db.query(Article).order_by(Article.publish_time.desc()).all()

    articlelist = []
    for art in articles:
        articlelist.append({
            "id": art.id,
            "title": art.title,
            "content": art.content,
            "publisher": art.publisher,
            "publish_time": art.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
            "like_count": db.query(Like).filter(Like.article_id == art.id).count()#AI帮助，AI告诉我这里返回点赞数量更好
        })
    return {"code": 1, "data": articlelist}

@app.post("/articles/like")
async def like_article(like_req: LikeRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == like_req.username).first()
        if not user:
            return {"code": 0}

        likes = db.query(Like).filter(
            Like.article_id == like_req.article_id,
            Like.username == like_req.username
        ).first()
        if likes:
            return {"code": 0}

        newlike = Like(
            article_id=like_req.article_id,
            username=like_req.username
        )
        db.add(newlike)
        db.commit()

        newlikecount = db.query(Like).filter(Like.article_id == like_req.article_id).count()
        return {"code": 1, "like_count": newlikecount}

    except Exception as e:
        db.rollback()
        if "unique_article_user_like" in str(e):#AI帮助
            return {"code": 0}
        return {"code": 0}

@app.delete("/articles/unlike")
async def unlike_article(like_req: LikeRequest, db: Session = Depends(get_db)):
    try:
        like = db.query(Like).filter(
            Like.article_id == like_req.article_id,
            Like.username == like_req.username
        ).first()

        if not like:
            return {"code": 0}

        db.delete(like)
        db.commit()

        newlikecount = db.query(Like).filter(Like.article_id == like_req.article_id).count()
        return {"code": 1,"like_count": newlikecount}

    except Exception as e:
        db.rollback()
        return {"code": 0}

@app.get("/articles/check_like")
async def check_like(article_id: int, username: str, db: Session = Depends(get_db)):
    like = db.query(Like).filter(
        Like.article_id == article_id,
        Like.username == username
    ).first()
    return {"code": 1}

@app.post("/articles/comment")
async def add_comment(comment_req: CommentRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == comment_req.username).first()
        if not user:
            return {"code": 0}
        newcomment = Comment(
            article_id=comment_req.article_id,
            username=comment_req.username,
            content=comment_req.content.strip()
        )
        db.add(newcomment)
        db.commit()
        db.refresh(newcomment)
        return {"code": 1}
    except Exception as e:
        db.rollback()
        return {"code": 0}

@app.get("/articles/comments")
async def get_article_comments(article_id: int, db: Session = Depends(get_db)):
    try:
        comments = db.query(Comment).filter(
            Comment.article_id == article_id
        ).order_by(Comment.comment_time.desc()).all()
        commentlist = [{
            "username": c.username,
            "content": c.content,
            "comment_time": c.comment_time.strftime("%Y-%m-%d %H:%M:%S")
        } for c in comments]
        return {"code": 1, "data": commentlist}
    except Exception as e:
        return {"code": 0}