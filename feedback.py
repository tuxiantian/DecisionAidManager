from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from shared_models import Feedback,db

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_id = current_user.id
    description = data.get('description')
    contact_info = data.get('contact_info')

    feedback = Feedback(
        user_id=user_id,
        description=description,
        contact_info=contact_info,
        created_at=datetime.utcnow()
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({"message": "反馈已提交"}), 201

@feedback_bp.route('/api/admin/feedback', methods=['GET'])
def get_feedback():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示 5 条记录
    feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    feedback_data = [{
        "id": fb.id,
        "user_id": fb.user_id,
        "description": fb.description,
        "contact_info": fb.contact_info,
        "response": fb.response,
        "created_at": fb.created_at,
        "responded_at": fb.responded_at,
        "status": fb.status
    } for fb in feedback_list]

    return jsonify({
            "status": "success",
            "data": feedback_data,
            "total_pages": feedback_list.pages,
            "current_page": feedback_list.page
    }), 200

@feedback_bp.route('/api/admin/feedback/<int:id>/respond', methods=['POST'])
def respond_to_feedback(id):
    feedback = Feedback.query.get(id)
    if not feedback:
        return jsonify({"error": "Feedback not found"}), 404

    response = request.json.get('response')
    print(request.json)
    feedback.response = response
    feedback.responded_at = datetime.utcnow()
    feedback.status = "已回复"
    db.session.commit()

    return jsonify({"message": "回复已保存"}), 200
