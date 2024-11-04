from flask import Flask, jsonify, request, Blueprint
from datetime import datetime, timedelta
from shared_models import ChecklistDecision, db, User, Article, Checklist, AHPHistory, BalancedDecision

statistics_bp = Blueprint('statistics', __name__)

# Example: User Statistics Endpoint
@statistics_bp.route('/api/statistics/users', methods=['GET'])
def get_user_statistics():
    # Get time range from request parameters
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query total user count
    total_users = User.query.count()

    # Query new users in the given time range
    new_users = db.session.query(
        db.func.date(User.created_at), db.func.count(User.id)
    ).filter(User.created_at >= start_date).group_by(db.func.date(User.created_at)).all()

    # Format data for the front-end
    new_users_data = [{"date": date.isoformat(), "count": count} for date, count in new_users]

    return jsonify({
        "total_users": total_users,
        "new_users_trend": new_users_data
    })

# Example: Article Statistics Endpoint
@statistics_bp.route('/api/statistics/articles', methods=['GET'])
def get_article_statistics():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total_articles = Article.query.count()

    new_articles = db.session.query(
        db.func.date(Article.created_at), db.func.count(Article.id)
    ).filter(Article.created_at >= start_date).group_by(db.func.date(Article.created_at)).all()

    new_articles_data = [{"date": date.isoformat(), "count": count} for date, count in new_articles]

    return jsonify({
        "total_articles": total_articles,
        "new_articles_trend": new_articles_data
    })

# Example: Checklist Statistics Endpoint
@statistics_bp.route('/api/statistics/checklists', methods=['GET'])
def get_checklist_statistics():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total_checklists = Checklist.query.count()
    total_clones = Checklist.query.filter(Checklist.is_clone == True).count()

    checklist_trend = db.session.query(
        db.func.date(Checklist.created_at), db.func.count(Checklist.id)
    ).filter(Checklist.created_at >= start_date).group_by(db.func.date(Checklist.created_at)).all()

    checklist_trend_data = [{"date": date.isoformat(), "count": count} for date, count in checklist_trend]

    return jsonify({
        "total_checklists": total_checklists,
        "total_clones": total_clones,
        "checklist_trend": checklist_trend_data
    })

@statistics_bp.route('/api/statistics/checklist_decisions', methods=['GET'])
def get_checklist_decision_statistics():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 查询总决策数
    total_decisions = ChecklistDecision.query.count()

    # 查询指定时间范围内的决策趋势
    decision_trend = db.session.query(
        db.func.date(ChecklistDecision.created_at), db.func.count(ChecklistDecision.id)
    ).filter(ChecklistDecision.created_at >= start_date).group_by(db.func.date(ChecklistDecision.created_at)).all()

    decision_trend_data = [{"date": date.isoformat(), "count": count} for date, count in decision_trend]

    return jsonify({
        "total_decisions": total_decisions,
        "decision_trend": decision_trend_data
    })

# Example: AHP and BalancedDecision Data Statistics Endpoint
@statistics_bp.route('/api/statistics/decision_data', methods=['GET'])
def get_decision_data_statistics():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total_ahp_data = AHPHistory.query.count()
    total_balanced_decision_data = BalancedDecision.query.count()

    ahp_trend = db.session.query(
        db.func.date(AHPHistory.created_at), db.func.count(AHPHistory.id)
    ).filter(AHPHistory.created_at >= start_date).group_by(db.func.date(AHPHistory.created_at)).all()

    balanced_decision_trend = db.session.query(
        db.func.date(BalancedDecision.created_at), db.func.count(BalancedDecision.id)
    ).filter(BalancedDecision.created_at >= start_date).group_by(db.func.date(BalancedDecision.created_at)).all()

    ahp_trend_data = [{"date": date.isoformat(), "count": count} for date, count in ahp_trend]
    balanced_decision_trend_data = [{"date": date.isoformat(), "count": count} for date, count in balanced_decision_trend]

    return jsonify({
        "total_ahp_data": total_ahp_data,
        "total_balanced_decision_data": total_balanced_decision_data,
        "ahp_trend": ahp_trend_data,
        "balanced_decision_trend": balanced_decision_trend_data
    })
