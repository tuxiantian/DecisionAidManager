from datetime import datetime as dt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from flask_login import UserMixin # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # 用户名
    email = db.Column(db.String(120), unique=True, nullable=False)     # 邮箱
    password_hash = db.Column(db.String(168), nullable=False)          # 密码哈希
    avatar_url = db.Column(db.String(255), nullable=True)              # 头像URL
    created_at = db.Column(db.DateTime, default=dt.utcnow)       # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow)      # 更新时间

    def set_password(self, password):
        """使用密码哈希存储密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证用户输入的密码是否正确"""
        return check_password_hash(self.password_hash, password)

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # 用户名
    email = db.Column(db.String(120), unique=True, nullable=False)     # 邮箱
    password_hash = db.Column(db.String(168), nullable=False)          # 密码哈希
    avatar_url = db.Column(db.String(255), nullable=True)              # 头像URL
    created_at = db.Column(db.DateTime, default=dt.utcnow)       # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=dt.utcnow)      # 更新时间

    # 手动定义反向关系
    decision_groups = db.relationship('DecisionGroup', secondary='group_members', back_populates='members')
    def set_password(self, password):
        """使用密码哈希存储密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证用户输入的密码是否正确"""
        return check_password_hash(self.password_hash, password)    
    
class AHPHistory(db.Model):
    __tablename__ = 'ahp_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alternative_names = db.Column(db.String(255), nullable=False)
    criteria_names = db.Column(db.String(255), nullable=False)
    best_choice_name = db.Column(db.String(255), nullable=False)
    request_data = db.Column(JSON, nullable=False)
    response_data = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow)

class DecisionGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    checklist_decision_id = db.Column(db.Integer, db.ForeignKey('checklist_decision.id'), nullable=False)  # 与决策关联
    # 手动定义双向关系，避免冲突
    members = db.relationship('User', secondary='group_members', back_populates='decision_groups')
    # 建立关联关系
    checklist_decision = db.relationship('ChecklistDecision', backref='decision_groups')
    # 定义 owner 关系
    owner = db.relationship('User', backref='owned_groups', foreign_keys=[owner_id])

class GroupMembers(db.Model):
    group_id = db.Column(db.Integer, db.ForeignKey('decision_group.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

# 定义BalancedDecision模型
class BalancedDecision(db.Model):
    __tablename__ = 'balanced_decisions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    decision_name = db.Column(db.String(255), nullable=False)
    conditions = db.Column(db.Text, nullable=False)
    comparisons = db.Column(db.Text, nullable=False)
    groups = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    keywords = db.Column(db.String(255), nullable=True)
    reference_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=dt.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow)

class PlatformArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    keywords = db.Column(db.String(255), nullable=True)
    reference_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=dt.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow)

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum('today','tomorrow', 'this_week', 'this_month','one_week','one_month', 'custom'), nullable=False)
    status = db.Column(db.Enum('not_started', 'in_progress', 'completed', 'ended'), default='not_started')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    importance = db.Column(db.Boolean, default=False)
    urgency = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.utcnow, onupdate=dt.utcnow)

class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    parent_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    mermaid_code = db.Column(db.Text, nullable=True)  # 存储流程图代码
    is_clone = db.Column(db.Boolean, nullable=True)
    platform_checklist_id = db.Column(db.Integer, db.ForeignKey('platform_checklist.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.utcnow)

class PlatformChecklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    parent_id = db.Column(db.Integer, db.ForeignKey('platform_checklist.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    mermaid_code = db.Column(db.Text, nullable=True)  # 存储流程图代码
    created_at = db.Column(db.DateTime, default=dt.utcnow)    

class ChecklistQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

class PlatformChecklistQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('platform_checklist.id'), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

class ChecklistAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_decision_id = db.Column(db.Integer, db.ForeignKey('checklist_decision.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('checklist_question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 记录回答用户
    referenced_articles = db.Column(db.String(255), nullable=True)  # 引用的文章ID，以逗号分隔
    answer = db.Column(db.Text, nullable=False)

class ChecklistDecision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    decision_name = db.Column(db.String(100), nullable=False)
    final_decision = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.utcnow)


# Review 数据模型
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('checklist_decision.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    referenced_articles = db.Column(db.String(255))  # 保存引用的文章 ID，多个用逗号分隔
    created_at = db.Column(db.DateTime, default=dt.utcnow)

# 定义逻辑错误模型
class LogicError(db.Model):
    __tablename__ = 'logic_errors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    term = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text, nullable=False)

# 创建 analysis_content 表
class AnalysisContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    content = db.Column(db.Text, nullable=False)  # 添加摘要字段，保存分析内容的简要描述

# 创建 analysis_data 表
class AnalysisData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_content_id = db.Column(db.Integer, db.ForeignKey('analysis_content.id'), nullable=False)
    facts = db.Column(db.JSON)
    opinion = db.Column(db.Text)
    error = db.Column(db.String(255), nullable=False)
    analysis_content = db.relationship('AnalysisContent', backref=db.backref('analysis_data', lazy=True))