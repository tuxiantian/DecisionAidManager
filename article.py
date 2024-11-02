from flask import Flask, request, jsonify, Blueprint
from sqlalchemy import desc
from shared_models import PlatformArticle, db
from datetime import datetime as dt
from flask_login import current_user

article_bp = Blueprint('article', __name__)

@article_bp.route('/articles', methods=['POST'])
def create_article():
    data = request.get_json()
    new_article = PlatformArticle(
        title=data['title'],
        content=data['content'],
        author=data['author'],
        tags=data['tags'],
        keywords=data['keywords']
    )
    new_article.created_at=dt.utcnow()
    new_article.updated_at=dt.utcnow()
    db.session.add(new_article)
    db.session.commit()
    return jsonify({'message': 'PlatformArticle created successfully', 'article': data}), 201

@article_bp.route('/articles', methods=['GET'])
def get_articles():
    search = request.args.get('search', '')
    tag = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    print(current_user.id)
    query = PlatformArticle.query

    if search:
        query = query.filter(
            (PlatformArticle.title.ilike(f"%{search}%")) |
            (PlatformArticle.keywords.ilike(f"%{search}%"))
        )
    if tag:
        query = query.filter(PlatformArticle.tags == tag)

    paginated_articles = query.order_by(desc(PlatformArticle.reference_count), desc(PlatformArticle.created_at)).paginate(page=page, per_page=page_size, error_out=False)
    articles = paginated_articles.items

    results = [
        {
            'id': article.id,
            'title': article.title,
            'author': article.author,
            'tags': article.tags,
            'keywords': article.keywords,
            'created_at': article.created_at,
            'updated_at': article.updated_at,
            'reference_count': article.reference_count
        } for article in articles
    ]

    return jsonify({
        'articles': results,
        'total_pages': paginated_articles.pages,
        'current_page': paginated_articles.page,
        'total_items': paginated_articles.total
    }), 200

@article_bp.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = PlatformArticle.query.get(id)
    if not article:
        return jsonify({'error': 'PlatformArticle not found'}), 404

    result = {
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'author': article.author,
        'tags': article.tags,
        'keywords': article.keywords,
        'created_at': article.created_at,
        'updated_at': article.updated_at,
        'reference_count': article.reference_count
    }
    return jsonify(result), 200

@article_bp.route('/articles/<int:id>', methods=['PUT'])
def update_article(id):
    article = PlatformArticle.query.get(id)
    if not article:
        return jsonify({'error': 'PlatformArticle not found'}), 404

    data = request.get_json()
    article.title = data.get('title', article.title)
    article.content = data.get('content', article.content)
    article.author = data.get('author', article.author)
    article.tags = data.get('tags')
    article.keywords = data.get('keywords', article.keywords)
    article.updated_at = dt.utcnow()

    db.session.commit()
    return jsonify({'message': 'PlatformArticle updated successfully'}), 200

@article_bp.route('/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    article = PlatformArticle.query.get(id)
    if not article:
        return jsonify({'error': 'PlatformArticle not found'}), 404

    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'PlatformArticle deleted successfully'}), 200