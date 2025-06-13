from flask import Flask, abort, request, jsonify, Blueprint, current_app
from shared_models import Article, Checklist, AdminUser, PlatformChecklist, PlatformChecklistQuestion, db,  ChecklistQuestion
from flask_login import current_user,login_required


checklist_bp = Blueprint('checklist', __name__)

@checklist_bp.route('/platform_checklists', methods=['GET'])
def get_platform_checklists():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    # 查询主版本 (parent_id 为 null 表示主版本)
    paginated_checklists = PlatformChecklist.query.filter_by(parent_id=None).order_by(PlatformChecklist.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)

    checklist_data = []
    
    # 遍历主版本并查询其子版本
    for checklist in paginated_checklists.items:
        checklist_info = {
            'id': checklist.id,
            'name': checklist.name,
            'description': checklist.description,
            'clone_count':checklist.clone_count,
            'version': checklist.version,
            'can_update': True,
            'versions': []  # 初始化子版本列表
        }

        # 查询当前主版本的子版本
        child_checklists = PlatformChecklist.query.filter_by(parent_id=checklist.id).order_by(PlatformChecklist.version.desc()).all()
        
        # 将子版本添加到主版本中
        for child in child_checklists:
            checklist_info['versions'].append({
                'id': child.id,
                'version': child.version,
                'description': child.description,
                'clone_count': child.clone_count,
                'can_update': False
            })
        
        checklist_data.append(checklist_info)

    return jsonify({
        'checklists': checklist_data,
        'total_pages': paginated_checklists.pages,
        'current_page': paginated_checklists.page,
        'total_items': paginated_checklists.total
    }), 200

@checklist_bp.route('/platform_checklists', methods=['POST'])
@login_required
def create_platform_checklist():
    data = request.get_json()
    name = data.get('name')
    mermaid_code = data.get('mermaid_code')
    description = data.get('description')
    questions = data.get('questions')

    if not name or not questions:
        return jsonify({'error': 'Checklist name and questions are required'}), 400

    checklist = PlatformChecklist(user_id=current_user.id,name=name,mermaid_code=mermaid_code, description=description, version=1)
    db.session.add(checklist)
    db.session.commit()

    # 临时ID到真实ID的映射
    id_mapping = {}
    parent_mapping = {}  # 存储问题与其父问题的关系
    # 第一遍：创建所有问题（不处理关系）
    for item in questions:
        question_text = item.get('question')
        description_text = item.get('description', '')  # 默认为空字符串

        # 检查问题内容是否有效
        if not question_text:
            return jsonify({'error': 'Each question must have text'}), 400

        question = PlatformChecklistQuestion(
            checklist_id=checklist.id,
            type=item.get('type', 'text'),
            question=question_text,
            description=description_text,  # 将描述信息一起保存
            options=item.get('options', []) if item.get('type') == 'choice' else None
        )
        db.session.add(question)
        db.session.flush()  # 生成ID但不提交事务
        
        if 'tempId' in item:
            id_mapping[item['tempId']] = question.id
                # 记录父问题信息
        if 'parentTempId' in item:
            parent_mapping[question.id] = item['parentTempId']    

    # 第二遍：建立层级关系
    for question_id, parent_temp_id in parent_mapping.items():
        if parent_temp_id in id_mapping:
            question = PlatformChecklistQuestion.query.get(question_id)
            question.parent_id = id_mapping[parent_temp_id]
            
    # 第三遍：处理选择题的follow-up关系
    for item in questions:
        if item.get('type') != 'choice' or 'tempId' not in item:
            continue
            
        question_id = id_mapping[item['tempId']]
        question = PlatformChecklistQuestion.query.get(question_id)
        
        # 处理follow-up问题
        follow_ups = {}
        for opt_index, follow_ids in item.get('followUpQuestions', {}).items():
            if isinstance(follow_ids, list):  # 处理数组形式的follow-up IDs
                follow_ups[opt_index] = [id_mapping[id] for id in follow_ids if id in id_mapping]
            elif follow_ids in id_mapping:  # 处理单个ID的情况（向后兼容）
                follow_ups[opt_index] = [id_mapping[follow_ids]]
        
        question.follow_up_questions = follow_ups if follow_ups else None

    db.session.commit()
    return jsonify({'message': 'Checklist created successfully', 'checklist_id': checklist.id,
        'id_mapping': id_mapping}), 201


@checklist_bp.route('/platform_checklists/<int:checklist_id>', methods=['GET'])
def get_platform_checklist_details(checklist_id):
    """
    获取最新 Checklist 的详细信息。
    入参 checklist_id 是父版本的 Checklist ID，此接口会自动获取最新版本的数据。
    """

    # 获取当前 checklist 或返回 404
    checklist = Checklist.query.get_or_404(checklist_id)

    # 获取所有相关版本的 Checklist
    if checklist.parent_id:
        versions = Checklist.query.filter(
            (Checklist.parent_id == checklist.parent_id) | (Checklist.id == checklist.parent_id)
        ).order_by(Checklist.version.desc()).all()
    else:
        versions = Checklist.query.filter(
            (Checklist.parent_id == checklist.id) | (Checklist.id == checklist.id)
        ).order_by(Checklist.version.desc()).all()

    # 找到最新版本的 Checklist
    latest_version = versions[0]  # 因为已按版本降序排序，第一个即为最新版本

    # 获取最新版本的 ChecklistQuestion
    questions = ChecklistQuestion.query.filter_by(checklist_id=latest_version.id).all()
    questions_data = [{'id': question.id, 'question': question.question, 'description': question.description} for question in questions]

    # 版本信息数据
    versions_data = [{'id': version.id, 'version': version.version} for version in versions]

    return jsonify({
        'id': latest_version.id,
        'name': latest_version.name,
        'mermaid_code': latest_version.mermaid_code,
        'description': latest_version.description,
        'version': latest_version.version,
        'questions': questions_data,
        'versions': versions_data
    }), 200

@checklist_bp.route('/platform_checklists/<int:id>', methods=['PUT'])
def update_platform_checklist(id):
    data = request.get_json()
    # Validate input
    if not data.get('name'):
        return jsonify({'error': 'Checklist name is required'}), 400

    # 查询 parent_id 等于参数 id 的最高版本
    latest_checklist = PlatformChecklist.query.filter_by(parent_id=id).order_by(PlatformChecklist.version.desc()).first()

    # 如果找不到，使用当前的 id 对应的 checklist
    if latest_checklist is None:
        latest_checklist = PlatformChecklist.query.get(id)
    
    # 如果仍然没有找到，则返回 404
    if latest_checklist is None:
        abort(404, description="Checklist not found")

    # 创建新版本的 checklist
    new_checklist = PlatformChecklist(
        name=latest_checklist.name,
        description=data.get('description', latest_checklist.description),
        mermaid_code=data.get('mermaid_code'),
        user_id=latest_checklist.user_id,
        version=latest_checklist.version + 1,
        parent_id=latest_checklist.parent_id or id  # 设置 parent_id 为最初的 checklist id
    )
    db.session.add(new_checklist)
    db.session.flush()  # 获取新 checklist 的 id

    questions = data.get('questions', [])
    id_mapping = {}  # tempId to real ID mapping
    parent_mapping = {}  # child question ID to parent tempId
    # 添加问题
    for item in questions:
        question_text = item.get('question')
        description_text = item.get('description', '')  # 默认为空字符串

        # 检查问题内容是否有效
        if not question_text:
            return jsonify({'error': 'Each question must have text'}), 400

        question = PlatformChecklistQuestion(
            checklist_id=new_checklist.id,
            type=item.get('type', 'text'),
            question=question_text,
            description=description_text,  # 将描述信息一起保存
            options=item.get('options', []) if item.get('type') == 'choice' else None

        )
        db.session.add(question)
        db.session.flush()
        # 记录所有可能的ID映射关系
        if 'tempId' in item:  # 新问题
            id_mapping[str(item['tempId'])] = question.id
        
        # 记录父问题关系
        if 'parentTempId' in item:
            parent_mapping[question.id] = str(item['parentTempId'])
    
    # Second pass: establish parent-child relationships
    for question_id, parent_temp_id in parent_mapping.items():
        if parent_temp_id in id_mapping:
            question = ChecklistQuestion.query.get(question_id)
            question.parent_id = id_mapping[parent_temp_id]

    # Third pass: process follow-up questions for choice questions
    for item in questions:
        if item.get('type') != 'choice' or 'tempId' not in item:
            continue
            
        question_id = id_mapping[item['tempId']]
        question = ChecklistQuestion.query.get(question_id)
        
        follow_ups = {}
        for opt_index, follow_ids in item.get('followUpQuestions', {}).items():
            if isinstance(follow_ids, list):  # 处理数组形式的follow-up IDs
                follow_ups[opt_index] = [id_mapping[str(id)] for id in follow_ids if str(id) in id_mapping]
            elif follow_ids in id_mapping:  # 处理单个ID的情况（向后兼容）
                follow_ups[opt_index] = [id_mapping[follow_ids]]
        
        question.follow_up_questions = follow_ups if follow_ups else None

    try:
        db.session.commit()
        return jsonify({'message': 'Checklist updated successfully',
            'checklist_id': new_checklist.id,
            'id_mapping': id_mapping}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"update_platform_checklist failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@checklist_bp.route('/platform_checklists/<int:checklist_id>/delete-with-children', methods=['DELETE'])
def delete_platform_checklist_with_children(checklist_id):
    """
    删除父版本及其所有子版本，以及关联的 ChecklistQuestion、ChecklistAnswer、ChecklistDecision 和 Review 数据。
    """
    checklist = PlatformChecklist.query.get_or_404(checklist_id)
    
    # 检查是否为父版本
    if checklist.parent_id is not None:
        return jsonify({'error': 'This is not a parent checklist.'}), 400

    try:
        # 找到所有相关的子版本
        all_versions = PlatformChecklist.query.filter(
            (PlatformChecklist.parent_id == checklist_id) | (PlatformChecklist.id == checklist_id)
        ).all()

        for version in all_versions:
            # 删除关联的 ChecklistQuestion、ChecklistAnswer、ChecklistDecision 和 Review 数据
            delete_related_data(version.id)
            db.session.delete(version)

        db.session.commit()
        return jsonify({'message': 'Parent checklist and all related versions deleted successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@checklist_bp.route('/platform_checklists/<int:checklist_id>', methods=['DELETE'])
def delete_platform_single_checklist(checklist_id):
    """
    仅删除指定的 checklist 子版本及其相关的 ChecklistQuestion、ChecklistAnswer、ChecklistDecision 和 Review 数据。
    """
    checklist = PlatformChecklist.query.get_or_404(checklist_id)

    try:
        # 删除关联数据
        delete_related_data(checklist.id)

        # 删除当前 Checklist
        db.session.delete(checklist)
        db.session.commit()
        return jsonify({'message': 'Checklist deleted successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def delete_related_data(checklist_id):
    """
    删除与指定 checklist 相关的所有 ChecklistQuestion、ChecklistAnswer、ChecklistDecision 和 Review 数据。
    """
    # 删除 ChecklistQuestion
    PlatformChecklistQuestion.query.filter_by(checklist_id=checklist_id).delete() 